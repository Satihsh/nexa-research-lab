//+------------------------------------------------------------------+
//| NEXA_EA.mq5 -- NEXA Autonomous Trading AI                          |
//|                                                                    |
//| Attach one instance per chart (EURUSD/GBPUSD/USDJPY/XAUUSD) with   |
//| IDENTICAL InpMagic so shared risk state and portfolio checks work. |
//|                                                                    |
//| EXECUTION MODEL: with InpAsyncExecution=true the order is          |
//| dispatched asynchronously. The position does not exist when the    |
//| call returns, so a per-symbol in-flight guard (GlobalVariable +    |
//| timestamp) is raised BEFORE dispatch and released only when        |
//| OnTradeTransaction observes the confirming DEAL_ENTRY_IN, or on    |
//| timeout. Trade context is staged under the symbol key pre-send and |
//| migrated to the position-id key on confirmation.                   |
//|                                                                    |
//| AMBIGUOUS EXECUTION RESULTS ARE NEVER RETRIED. A TIMEOUT or        |
//| CONNECTION retcode means the server MAY have accepted the order;   |
//| resending would risk a duplicate. Only definitive rejections       |
//| (REQUOTE / PRICE_CHANGED / PRICE_OFF) are retried.                 |
//|                                                                    |
//| RISK: every hard gate reads live broker state. AI output can       |
//| only veto, never authorise. The shadow ledger gates nothing.       |
//+------------------------------------------------------------------+
#property copyright "NEXA"
#property version   "4.00"

#include <Trade\Trade.mqh>
#include "NEXA_Common.mqh"
#include "NEXA_Features.mqh"
#include "NEXA_Risk.mqh"
#include "NEXA_Intelligence.mqh"
#include "NEXA_Microstructure.mqh"
#include "NEXA_Advanced_Ingest.mqh"
#include "NEXA_FOMC.mqh"
#include "NEXA_Liquidity.mqh"
#include "NEXA_Safety.mqh"
#include "NEXA_PositionMgmt.mqh"

input string   InpComment            = "NEXA";
input int      InpMagic              = 26011900;
input double   InpBreakevenAtR       = 1.00;
input int      InpTimeExitBars       = 48;
input double   InpMinTP_R            = 1.50;   // asymmetric R:R floor
input double   InpMaxTP_R            = 4.00;   // EV matrix ceiling
input bool     InpRequireDemoAccount = true;
input bool     InpEnableTrading      = true;
input bool     InpRequireAIConfirmation = false; // TRUE => no valid model = NO TRADE (fail closed)
input bool     InpRequireHTFAlignment   = true;
input int      InpMinQualityScore       = 5;   // of 10 quality points
input bool     InpAsyncExecution     = true;
input int      InpMaxRetries         = 3;
input int      InpRetryBaseDelayMs   = 300;
input int      InpInFlightTimeoutSec = 20;
input double   InpPartialCloseAtR    = 1.50;
input double   InpPartialClosePct    = 50.0;
input bool     InpSessionFilterEnabled = false;
input int      InpSessionStartGMT    = 7;
input int      InpSessionEndGMT      = 16;
input bool     InpHardCloseEnabled   = false;
input int      InpHardCloseGMTHour   = 21;
input bool     InpCloseBeforeWeekend = true;
input int      InpWeekendCloseHour   = 21;      // server hour on Friday
input double   InpStopPadATR         = 0.15;    // ATR fraction beyond the structural invalidation

CTrade     trade;
datetime   g_lastBarTime = 0;
datetime   g_closeReqSentAt = 0;     // async close/modify de-dup on the tick path
ulong      g_closeReqTicket = 0;
long       g_rowSeq = 0;              // monotonic, makes row_id unique within a run
datetime   g_lastDispatchTs = 0;      // set at dispatch, read by the FILL row
NexaSignal g_sig;
bool       g_sigValid = false;
ENUM_ACCOUNT_MARGIN_MODE g_marginMode = ACCOUNT_MARGIN_MODE_RETAIL_NETTING;
datetime   g_modifyReqSentAt = 0;     // SL-modify throttle (separate from the close de-dup)
ulong      g_modifyReqTicket = 0;
ulong      g_noRiskRefWarned = 0;     // warn once per position without an initial-risk reference
ulong      g_unsplittableWarned = 0;  // warn once per position too small for the partial close
ulong      g_historyUnreadableWarned = 0;
ulong      g_partialConfirmedPos = 0;  // partial already seen in deal history: skip further history reads
double     g_portfolioLockAt = 0;     // >0 while THIS instance holds the portfolio entry lock

//==================== FORWARD DECLARATIONS ====================
void   InitJournal();
struct NexaJournalRow;
void   LogRow(const NexaSignal &s, NexaJournalRow &r);
void   LogDecision(const NexaSignal &s, int dir, string reason);
void   LogTradeOpen(const NexaSignal &s, int dir, double lots, double e, double sl, double tp);
bool   SafeModifySL(ulong ticket, double newSL, double tp, long posType, double currentSL);
bool   SelectNexaPosition(ulong &ticket);
bool   NexaOrderPending();
bool   PositionFullyClosedByHistory(ulong posId);
int    PositionExitDealState(ulong posId);
bool   PositionHasPendingCloseOrder(ulong posId);
void   MigratePendingToPosition(string sym, ulong posId);
void   ClearPendingContext(string sym);
void   CloseNexaPositionIfAny(string why);
bool   ModifyThrottled(ulong ticket);
void   MarkModifySent(ulong ticket);

//==================== POSITION OWNERSHIP (magic + symbol, both margin modes) ====================
// PositionSelect(symbol) is ambiguous under hedging and can land on another EA's
// position under netting. This iterates and selects only a position that is ours.
bool SelectNexaPosition(ulong &ticket)
  {
   ticket = 0;
   int total = PositionsTotal();
   for(int i = 0; i < total; i++)
     {
      ulong t = PositionGetTicket(i);
      if(t == 0) continue;
      if(PositionGetString(POSITION_SYMBOL) != _Symbol) continue;
      if((long)PositionGetInteger(POSITION_MAGIC) != InpMagic) continue;
      ticket = t;                     // PositionGetTicket already selected it
      return true;
     }
   return false;
  }

//--- Any live order (not yet a position) that is ours on this symbol?
bool NexaOrderPending()
  {
   int total = OrdersTotal();
   for(int i = 0; i < total; i++)
     {
      ulong t = OrderGetTicket(i);
      if(t == 0) continue;
      if(OrderGetString(ORDER_SYMBOL) != _Symbol) continue;
      if((long)OrderGetInteger(ORDER_MAGIC) != InpMagic) continue;
      return true;
     }
   return false;
  }

//--- Authoritative full-close test from DEAL HISTORY, independent of whether the
//--- terminal's position record has caught up with the deal that just arrived.
bool PositionFullyClosedByHistory(ulong posId)
  {
   if(!HistorySelectByPosition(posId)) return false;
   double volIn = 0, volOut = 0;
   int n = HistoryDealsTotal();
   for(int i = 0; i < n; i++)
     {
      ulong d = HistoryDealGetTicket(i);
      if(d == 0) continue;
      if((ulong)HistoryDealGetInteger(d, DEAL_POSITION_ID) != posId) continue;
      ENUM_DEAL_ENTRY e = (ENUM_DEAL_ENTRY)HistoryDealGetInteger(d, DEAL_ENTRY);
      double v = HistoryDealGetDouble(d, DEAL_VOLUME);
      if(e == DEAL_ENTRY_IN)  volIn  += v;
      if(e == DEAL_ENTRY_OUT || e == DEAL_ENTRY_OUT_BY) volOut += v;   // OUT_BY: close-by counts as an exit
      if(e == DEAL_ENTRY_INOUT) { volIn += v; volOut += v; }
     }
   double step = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   double eps  = (step > 0) ? step * 0.5 : 1e-8;
   return (volIn > 0 && volOut >= volIn - eps);
  }

//==================== INPUT VALIDATION ====================
bool ValidateInputs(string &why)
  {
   why = "";
   if(InpRiskPercent <= 0 || InpRiskPercent > 5)         { why = "InpRiskPercent must be in (0,5]"; return false; }
   if(InpHardRiskCeiling <= 0 || InpHardRiskCeiling > 5) { why = "InpHardRiskCeiling must be in (0,5]"; return false; }
   if(InpRiskPercent > InpHardRiskCeiling)               { why = "InpRiskPercent exceeds InpHardRiskCeiling"; return false; }
   if(InpMaxDailyLossPct <= 0 || InpMaxDailyLossPct > 50){ why = "InpMaxDailyLossPct out of range"; return false; }
   if(InpMaxDrawdownPct <= 0 || InpMaxDrawdownPct > 90)  { why = "InpMaxDrawdownPct out of range"; return false; }
   if(InpMaxTradesPerDay < 0)                            { why = "InpMaxTradesPerDay negative"; return false; }
   if(InpMaxSpreadATRRatio <= 0 || InpMaxSpreadATRRatio > 1){ why = "InpMaxSpreadATRRatio must be in (0,1]"; return false; }
   if(InpMaxMarginUsagePct <= 0 || InpMaxMarginUsagePct > 100){ why = "InpMaxMarginUsagePct out of range"; return false; }
   if(InpMinTP_R < 1.0)                                  { why = "InpMinTP_R must be >= 1.0"; return false; }
   if(InpMaxTP_R < InpMinTP_R)                           { why = "InpMaxTP_R < InpMinTP_R"; return false; }
   if(InpATRPeriod < 2)                                  { why = "InpATRPeriod < 2"; return false; }
   if(InpSwingLookback < 1)                              { why = "InpSwingLookback < 1"; return false; }
   if(InpDisplacementATRMin <= 0)                        { why = "InpDisplacementATRMin <= 0"; return false; }
   if(InpMTFCacheBars < InpSwingLookback * 2 + 10)       { why = "InpMTFCacheBars too small"; return false; }
   if(InpReplayBars < 0 || InpReplayBars > InpMTFCacheBars){ why = "InpReplayBars out of range"; return false; }
   if(InpMinQualityScore < 0 || InpMinQualityScore > 10) { why = "InpMinQualityScore must be 0..10"; return false; }
   if(InpMaxRetries < 1 || InpMaxRetries > 10)           { why = "InpMaxRetries must be 1..10"; return false; }
   if(InpRetryBaseDelayMs < 0)                           { why = "InpRetryBaseDelayMs negative"; return false; }
   if(InpInFlightTimeoutSec < 1)                         { why = "InpInFlightTimeoutSec < 1"; return false; }
   if(InpPartialClosePct < 0 || InpPartialClosePct >= 100){ why = "InpPartialClosePct must be [0,100)"; return false; }
   if(InpTickFlowWindow < 2)                             { why = "InpTickFlowWindow < 2"; return false; }
   if(InpMinSampleForSurvival < 1)                       { why = "InpMinSampleForSurvival < 1"; return false; }
   if(InpStressSpreadMultiplier < 1)                     { why = "InpStressSpreadMultiplier < 1"; return false; }
   if(InpMinSweepExcursionATR < 0 || InpMaxSweepExcursionATR <= InpMinSweepExcursionATR)
                                                         { why = "sweep excursion bounds invalid"; return false; }
   if(InpMaxBarsBeyond < 1 || InpResponseWindowBars < 1 || InpEventValidBars < 1)
                                                         { why = "liquidity bar windows must be >= 1"; return false; }
   if(InpGMTOffset < -12 || InpGMTOffset > 14)           { why = "InpGMTOffset out of range"; return false; }
   if(InpStopPadATR < 0 || InpStopPadATR > 1)            { why = "InpStopPadATR must be [0,1]"; return false; }
   if(InpPreflightMaxMarginPct <= 0 || InpPreflightMaxMarginPct > 100){ why = "InpPreflightMaxMarginPct out of range"; return false; }
   if(InpSessionStartGMT < 0 || InpSessionStartGMT > 23 || InpSessionEndGMT < 0 || InpSessionEndGMT > 23)
                                                         { why = "session GMT hours must be 0..23"; return false; }
   if(InpHardCloseGMTHour < 0 || InpHardCloseGMTHour > 23){ why = "InpHardCloseGMTHour must be 0..23"; return false; }
   if(InpWeekendCloseHour < 0 || InpWeekendCloseHour > 23){ why = "InpWeekendCloseHour must be 0..23"; return false; }
   if(InpCorrelationBars < 3)                            { why = "InpCorrelationBars < 3"; return false; }
   if(InpNewsBufferMinutes < 0)                          { why = "InpNewsBufferMinutes negative"; return false; }
   if(InpTimeExitBars < 0)                               { why = "InpTimeExitBars negative"; return false; }
   return true;
  }

//==================== IN-FLIGHT GUARD ====================
string InFlightKey(string sym)   { return GV("InFlight_" + sym); }
string InFlightTsKey(string sym) { return GV("InFlightTs_" + sym); }

bool OrderInFlight(string sym)
  {
   if(!GlobalVariableCheck(InFlightKey(sym))) return false;
   if(GlobalVariableGet(InFlightKey(sym)) < 1) return false;
   if(GlobalVariableCheck(InFlightTsKey(sym)))
     {
      datetime sent = (datetime)GlobalVariableGet(InFlightTsKey(sym));
      if(TimeCurrent() - sent > InpInFlightTimeoutSec)
        {
         // Timeout is NOT proof of failure. Before releasing, check the broker:
         //  * an order still pending -> keep the guard (server may still fill it)
         //  * a NEXA position now exists -> the DEAL_ENTRY_IN was missed; adopt it
         //    (migrate the staged context) and release
         //  * neither -> nothing landed; release
         if(NexaOrderPending()) return true;
         ulong t;
         if(SelectNexaPosition(t))
           {
            Print("NEXA WARNING: in-flight timeout but a NEXA position exists on ", sym,
                  " -- confirmation was missed; adopting position ", t, " and releasing guard.");
            MigratePendingToPosition(sym, t);
            GlobalVariableSet(InFlightKey(sym), 0);
            return false;
           }
         Print("NEXA WARNING: in-flight guard timed out on ", sym, " with no order and no position -- releasing.");
         GlobalVariableSet(InFlightKey(sym), 0);
         ClearPendingContext(sym);
         return false;
        }
     }
   return true;
  }

void SetInFlight(string sym, bool on)
  {
   GlobalVariableSet(InFlightKey(sym), on ? 1 : 0);
   if(on) GlobalVariableSet(InFlightTsKey(sym), (double)TimeCurrent());
  }

void StagePendingContext(string sym, int dir, double entry, double riskDist,
                          ENUM_NEXA_REGIME_TREND trend, ENUM_NEXA_REGIME_VOL vol, double targetR)
  {
   GlobalVariableSet(GV("PendDir_"   + sym), (double)dir);
   GlobalVariableSet(GV("PendEntry_" + sym), entry);
   GlobalVariableSet(GV("PendRisk_"  + sym), riskDist);
   GlobalVariableSet(GV("PendTrend_" + sym), (double)trend);
   GlobalVariableSet(GV("PendVol_"   + sym), (double)vol);
   GlobalVariableSet(GV("PendTgtR_"  + sym), targetR);
  }

void ClearPendingContext(string sym)
  {
   string k[6] = {"PendDir_","PendEntry_","PendRisk_","PendTrend_","PendVol_","PendTgtR_"};
   for(int i = 0; i < 6; i++) { string key = GV(k[i] + sym); if(GlobalVariableCheck(key)) GlobalVariableDel(key); }
  }

void MigratePendingToPosition(string sym, ulong posId)
  {
   string k[6] = {"PendDir_","PendEntry_","PendRisk_","PendTrend_","PendVol_","PendTgtR_"};
   string d[6] = {"Dir_","Entry_","RiskDist_","Trend_","Vol_","TgtR_"};
   for(int i = 0; i < 6; i++)
     {
      string src = GV(k[i] + sym);
      if(!GlobalVariableCheck(src)) continue;
      GlobalVariableSet(GV(d[i] + IntegerToString(posId)), GlobalVariableGet(src));
      GlobalVariableDel(src);
     }
   GlobalVariableSet(GV("PartialDone_" + IntegerToString(posId)), 0);
  }

//==================== SAFETY WRAPPERS (safety audit 2026-09-29; primitives in NEXA_Safety.mqh) ====================
bool ModifyThrottled(ulong ticket)
  {
   return (ticket == g_modifyReqTicket && TimeCurrent() - g_modifyReqSentAt <= InpInFlightTimeoutSec);
  }

void MarkModifySent(ulong ticket) { g_modifyReqTicket = ticket; g_modifyReqSentAt = TimeCurrent(); }

// All NEXA instances share one terminal. Without a lock, two instances deciding on the same bar can
// both pass ExposureCapOK/CorrelationCapOK/the daily trade limit before either position exists and
// jointly exceed limits each check enforces alone. The terminal-global entry lock is held from the
// portfolio checks until this instance's order is resolved (position visible, rejected or timed out).
// A lock whose holder vanished is reclaimed after 2 x InpInFlightTimeoutSec. Policy is unchanged:
// this only enforces the EXISTING caps and can only block.
string PortfolioLockKey() { return GV("PortfolioEntryLock"); }

bool AcquirePortfolioLock()
  {
   return NexaAcquireLock(PortfolioLockKey(), (double)TimeCurrent(), 2.0 * InpInFlightTimeoutSec, g_portfolioLockAt);
  }

void ReleasePortfolioLock() { NexaReleaseLock(PortfolioLockKey(), g_portfolioLockAt); }

// The held lock is released once this instance has nothing unresolved in flight.
void MaintainPortfolioLock()
  {
   if(g_portfolioLockAt <= 0) return;
   if(!OrderInFlight(_Symbol)) ReleasePortfolioLock();
  }

// Atomically take one of the InpMaxTradesPerDay slots (shared GV "TradesToday"), counted at dispatch
// exactly as before; a send that never reached the server gives the slot back.
bool ReserveTradeSlot() { return NexaReserveSlot(GV("TradesToday"), (double)InpMaxTradesPerDay); }
void ReleaseTradeSlot() { NexaReleaseSlot(GV("TradesToday")); }

//==================== INIT ====================
int OnInit()
  {
   string why;
   if(!ValidateInputs(why)) { Print("NEXA INIT FAILED: invalid input -- ", why); return INIT_PARAMETERS_INCORRECT; }

   if(!SymbolSelect(_Symbol, true)) { Print("NEXA INIT FAILED: symbol not available: ", _Symbol); return INIT_FAILED; }
   if(SymbolInfoDouble(_Symbol, SYMBOL_POINT) <= 0) { Print("NEXA INIT FAILED: invalid symbol point"); return INIT_FAILED; }
   if(SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN) <= 0 || SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP) <= 0)
     { Print("NEXA INIT FAILED: invalid broker volume spec"); return INIT_FAILED; }

   g_marginMode = (ENUM_ACCOUNT_MARGIN_MODE)AccountInfoInteger(ACCOUNT_MARGIN_MODE);
   // One NEXA position per symbol is enforced by SelectNexaPosition() + the in-flight
   // guard, which is correct under both netting and hedging. Mode is logged, not assumed.

   if(InpRequireDemoAccount &&
      (ENUM_ACCOUNT_TRADE_MODE)AccountInfoInteger(ACCOUNT_TRADE_MODE) != ACCOUNT_TRADE_MODE_DEMO)
     { Print("NEXA INIT FAILED: not a demo account and InpRequireDemoAccount=true."); return INIT_FAILED; }

   trade.SetExpertMagicNumber(InpMagic);
   trade.SetTypeFillingBySymbol(_Symbol);
   trade.SetDeviationInPoints(20);
   trade.SetAsyncMode(InpAsyncExecution);

   // Order matters: Features_Init performs the causal liquidity replay internally.
   // Liquidity_Init is NOT called again here -- doing so would wipe that state.
   if(!Features_Init()) { Print("NEXA INIT FAILED: Features_Init (indicator handles)"); return INIT_FAILED; }
   Microstructure_Init();
   AdvancedIngest_Init();
   FOMC_Init();
   bool aiLoaded = AI_Init();

   if(InpRequireAIConfirmation && !aiLoaded)
      Print("NEXA WARNING: InpRequireAIConfirmation=true and no valid model is loaded. ",
            "The EA will initialise but will NOT open trades (fail-closed).");

   // Restart recovery. The in-flight guard cannot survive a restart meaningfully,
   // so it is released. Staged context is NOT discarded: if an order filled while
   // the terminal was down, the position exists but its context was never migrated
   // (no DEAL_ENTRY_IN was observed). Adopt it now so its close is still recorded.
   // Safety audit 2026-09-29: an order sent before the restart may still be PENDING at the
   // broker. Releasing the guard then would allow a duplicate entry. Keep it raised (fresh
   // timestamp); OrderInFlight()'s broker-state timeout logic resolves it.
   bool pendingAtBroker = NexaOrderPending();
   SetInFlight(_Symbol, pendingAtBroker);
   if(pendingAtBroker) Print("NEXA: restart recovery -- a NEXA order is still pending at the broker; in-flight guard kept.");
   g_rowSeq = (long)TimeLocal() * 1000000;   // row_id stays unique across restarts (seq is run-seeded)
   ulong t;
   if(SelectNexaPosition(t))
     {
      bool hasCtx = GlobalVariableCheck(GV("RiskDist_" + IntegerToString(t)));
      bool hasPend = GlobalVariableCheck(GV("PendRisk_" + _Symbol));
      if(!hasCtx && hasPend) { MigratePendingToPosition(_Symbol, t); Print("NEXA: restart recovery -- adopted staged context for position ", t); }
      else if(!hasCtx)        Print("NEXA WARNING: restart recovery -- position ", t, " has no risk context; its close will not update expectancy stats.");
      else                    Print("NEXA: restart recovery -- resuming position ", t);
     }
   else if(!pendingAtBroker)
      ClearPendingContext(_Symbol);   // nothing landed: stale staging must not attach to a future fill

   InitJournal();
   Print("NEXA init on ", _Symbol, " | marginMode=", EnumToString(g_marginMode),
         " | async=", InpAsyncExecution, " | spread cap=", DoubleToString(InpMaxSpreadATRRatio * 100, 1),
         "% ATR | AI=", (aiLoaded ? "LOADED" : "NONE"), " | schema v", NEXA_AI_SCHEMA_VERSION);
   return INIT_SUCCEEDED;
  }

void OnDeinit(const int reason) { ReleasePortfolioLock(); Features_Deinit(); AI_Deinit(); }

//==================== EV MATRIX: DYNAMIC TARGETING ====================
double NearestAnchorAbove(double from, const NexaSignal &s)
  {
   double c[7];
   c[0] = s.camR3; c[1] = s.camR4; c[2] = s.m15SwingHigh; c[3] = s.h1SwingHigh;
   c[4] = s.asiaHigh; c[5] = s.londonHigh; c[6] = s.nyHigh;
   double best = 0;
   for(int i = 0; i < 7; i++)
      if(c[i] > 0 && c[i] > from && (best == 0 || c[i] < best)) best = c[i];
   return best;
  }

double NearestAnchorBelow(double from, const NexaSignal &s)
  {
   double c[7];
   c[0] = s.camS3; c[1] = s.camS4; c[2] = s.m15SwingLow; c[3] = s.h1SwingLow;
   c[4] = s.asiaLow; c[5] = s.londonLow; c[6] = s.nyLow;
   double best = 0;
   for(int i = 0; i < 7; i++)
      if(c[i] > 0 && c[i] < from && (best == 0 || c[i] > best)) best = c[i];
   return best;
  }

// TP price, or 0 if insufficient structural room. Target R clamped to [Min,Max].
double CalcDynamicTP(int dir, double entry, double stopPrice, NexaSignal &s, string &reason)
  {
   double riskDist = MathAbs(entry - stopPrice);
   if(riskDist <= 0 || !NexaFinite(riskDist)) { reason = "ZERO_RISK_DISTANCE"; return 0; }

   double anchor = (dir > 0) ? NearestAnchorAbove(entry, s) : NearestAnchorBelow(entry, s);
   double targetR;
   if(anchor <= 0) { targetR = InpMaxTP_R; reason = "TP_NO_ANCHOR_CEILING"; }
   else
     {
      double anchorR = MathAbs(anchor - entry) / riskDist;
      if(anchorR < InpMinTP_R) { s.dynamicTargetR = anchorR; reason = "INSUFFICIENT_TARGET_ROOM"; return 0; }
      targetR = MathMin(anchorR, InpMaxTP_R);
      reason = StringFormat("TP_ANCHOR_%.2fR", targetR);
     }
   s.dynamicTargetR = targetR;
   double tp = (dir > 0) ? entry + riskDist * targetR : entry - riskDist * targetR;
   return NexaFinite(tp) ? tp : 0;
  }

//==================== SETUP-AWARE STOP ====================
// REVERSAL: the thesis is "price took the liquidity and rejected it", so the stop
//   sits beyond the sweep EXTREME -- if that is revisited the thesis is dead.
// CONTINUATION: the thesis is "price took the level and is holding through it", so
//   the stop sits beyond the RECLAIMED LEVEL itself -- if price falls back through
//   the level it failed to hold, the thesis is dead. The sweep extreme is on the
//   WRONG side of entry for a continuation and must not be used.
// The stop is then validated to lie on the correct side of the market with at
// least the broker's minimum stop distance; otherwise NO TRADE.
double CalcSetupStop(int dir, const NexaSignal &s, int pe, string &reason)
  {
   reason = "";
   double pad = s.atrValue * InpStopPadATR;
   double stop = 0;

   if(pe >= 0 && pe < NEXA_LVL_COUNT && g_liqEvents[pe].state == NEXA_SWEEP_CONFIRMED)
     {
      double ext = g_liqEvents[pe].extremeBeyond;
      double lvl = g_liqEvents[pe].levelPrice;
      if(g_liqEvents[pe].resolution == NEXA_RESOLVE_REVERSAL && ext > 0)
         stop = (dir > 0) ? ext - pad : ext + pad;
      else if(g_liqEvents[pe].resolution == NEXA_RESOLVE_CONTINUATION && lvl > 0)
         stop = (dir > 0) ? lvl - pad : lvl + pad;
     }
   if(stop <= 0)
      stop = (dir > 0) ? s.entrySwingLow : s.entrySwingHigh;   // structural fallback
   if(stop <= 0 || !NexaFinite(stop)) { reason = "NO_STRUCTURAL_STOP"; return 0; }

   double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID), ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   if(bid <= 0 || ask <= 0) { reason = "INVALID_QUOTE"; return 0; }
   double minDist = SymbolInfoInteger(_Symbol, SYMBOL_TRADE_STOPS_LEVEL) * SymbolInfoDouble(_Symbol, SYMBOL_POINT);

   if(dir > 0 && !(stop < bid - minDist)) { reason = "STOP_ON_WRONG_SIDE_LONG"; return 0; }
   if(dir < 0 && !(stop > ask + minDist)) { reason = "STOP_ON_WRONG_SIDE_SHORT"; return 0; }
   return stop;
  }

//==================== COMPOSITE GATE ====================
int ComputeCompositeScore(const NexaSignal &s, int &outQuality)
  {
   outQuality = 0;
   // TIER 1: a confirmed, resolved liquidity event is REQUIRED
   if(!s.liqEventActive) return 0;
   if(s.liqResponseDirection == 0) return 0;

   // TIER 2: direction from the OBSERVED structural response
   int dir = s.liqResponseDirection;

   // TIER 3: hard vetoes -- reject only
   if(s.sessionTag == "LATE")                       return 0;
   if(s.spreadATRRatio > InpMaxSpreadATRRatio)      return 0;
   if(s.newsRiskActive)                             return 0;
   // A failed breakout vetoes only a trade in the SAME direction as the break that
   // failed. A failed UPSIDE break is consistent with a reversal SHORT (that is what a
   // sweep-and-reject looks like) and must not veto it. It DOES veto an upside
   // continuation LONG, which would be trading a direction that just failed.
   if(s.breakoutState == NEXA_BREAKOUT_FALSE && s.breakoutDirection == dir) return 0;
   if(InpRequireHTFAlignment && s.htfAlignment != 0 && s.htfAlignment != dir) return 0;

   // TIER 4: quality -- independent sources only; correlated confirmations not stacked
   int quality = 0;
   if(s.liqMssAfter || s.liqDisplacementAfter || s.liqFvgAfter) quality++;   // impulse family: ONE point
   if(s.liqWickBodyRatio >= InpMinRejectionWickBody)            quality++;
   if(s.liqExcursionATR >= InpMinSweepExcursionATR && s.liqExcursionATR <= 1.0) quality++;
   if(s.liqBarsBeyond <= 2)                                     quality++;
   if(s.liqBarsSinceReclaim <= 3)                               quality++;
   if(s.htfAlignment == dir)                                    quality++;
   if(dir > 0 ? (s.obiProxy > 0.15) : (s.obiProxy < -0.15))     quality++;
   if(s.volState != NEXA_VOL_HIGH)                              quality++;
   if(!s.regimeTransitioning)                                   quality++;
   if(s.liqOrigin == NEXA_ORIGIN_LIVE)                          quality++;   // reconstructed events forfeit this
   // usdCompositeDirection deliberately NOT scored: it is derived from the traded symbols

   outQuality = quality;
   if(quality < InpMinQualityScore) return 0;
   return dir * 2;
  }

//==================== EXECUTION ====================
void ExecuteSignal(int dir, double stopPrice, NexaSignal &s)
  {
   ulong existing;
   if(OrderInFlight(_Symbol))        { LogDecision(s, dir, "SKIP_ORDER_IN_FLIGHT"); return; }
   if(SelectNexaPosition(existing))  { LogDecision(s, dir, "SKIP_POSITION_ALREADY_OPEN"); return; }

   double entry = (dir > 0) ? SymbolInfoDouble(_Symbol, SYMBOL_ASK) : SymbolInfoDouble(_Symbol, SYMBOL_BID);
   if(entry <= 0 || !NexaFinite(entry)) { LogDecision(s, dir, "NO_TRADE_INVALID_QUOTE"); return; }
   double riskDist = MathAbs(entry - stopPrice);

   string advReason;
   if(!AdversarialCheck(s, dir, riskDist, advReason)) { LogDecision(s, dir, "NO_TRADE_" + advReason); return; }

   string survReason;
   if(!StrategySurvivalOK(survReason)) { LogDecision(s, dir, "NO_TRADE_" + survReason); return; }

   // AI: fail CLOSED when required. -1 (unavailable/invalid) is never a pass.
   s.aiScore = GetAIScore(s);
   if(InpRequireAIConfirmation)
     {
      if(s.aiScore < 0.0 || s.aiScore > 1.0) { LogDecision(s, dir, "NO_TRADE_AI_UNAVAILABLE_FAILCLOSED"); return; }
      bool agrees = (dir > 0) ? (s.aiScore >= 0.55) : (s.aiScore <= 0.45);
      if(!agrees) { LogDecision(s, dir, "NO_TRADE_AI_DISAGREES"); return; }
     }

   string tpReason;
   double tp = CalcDynamicTP(dir, entry, stopPrice, s, tpReason);
   if(tp <= 0) { LogDecision(s, dir, "NO_TRADE_" + tpReason); return; }

   string sizeReason;
   double lots = CalcLotSizeHardened(dir, entry, stopPrice, sizeReason);
   if(lots <= 0) { LogDecision(s, dir, "NO_TRADE_" + sizeReason); return; }

   // Portfolio checks and dispatch happen under the terminal-global entry lock (see above).
   if(!AcquirePortfolioLock()) { LogDecision(s, dir, "SKIP_PORTFOLIO_ENTRY_LOCK_BUSY"); return; }

   string expReason;
   if(!ExposureCapOK(_Symbol, dir, lots, expReason)) { ReleasePortfolioLock(); LogDecision(s, dir, "NO_TRADE_" + expReason); return; }
   string corrReason;
   if(!CorrelationCapOK(_Symbol, corrReason))        { ReleasePortfolioLock(); LogDecision(s, dir, "NO_TRADE_" + corrReason); return; }

   string preReason;
   if(!PreflightExecutionCheck(dir, lots, entry, preReason)) { ReleasePortfolioLock(); LogDecision(s, dir, "NO_TRADE_" + preReason); return; }

   if(!ReserveTradeSlot()) { ReleasePortfolioLock(); LogDecision(s, dir, "NO_TRADE_DAILY_TRADE_LIMIT_RESERVED"); return; }

   StagePendingContext(_Symbol, dir, entry, riskDist, s.trendState, s.volState, s.dynamicTargetR);
   SetInFlight(_Symbol, true);
   g_lastDispatchTs = TimeCurrent();      // schema v1.0 dispatch_ts

   // Lots were sized for riskDist at the ORIGINAL quote. A resend at a worse quote would raise the
   // monetary risk above what was sized (and may put the stop inside the broker distance or leave
   // less than InpMinTP_R of room), so every attempt re-validates and aborts instead (fail closed).
   double sizedRiskDist = riskDist;
   double minStopDist   = SymbolInfoInteger(_Symbol, SYMBOL_TRADE_STOPS_LEVEL) * SymbolInfoDouble(_Symbol, SYMBOL_POINT);
   bool sent = false, ambiguous = false, revalFail = false;
   for(int attempt = 0; attempt < InpMaxRetries && !sent && !ambiguous; attempt++)
     {
      entry = (dir > 0) ? SymbolInfoDouble(_Symbol, SYMBOL_ASK) : SymbolInfoDouble(_Symbol, SYMBOL_BID);
      double bidNow = SymbolInfoDouble(_Symbol, SYMBOL_BID), askNow = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
      double riskNow = MathAbs(entry - stopPrice);
      bool stopSide  = (dir > 0) ? (stopPrice < bidNow - minStopDist) : (stopPrice > askNow + minStopDist);
      bool roomOK    = (riskNow > 0) && (MathAbs(tp - entry) / riskNow >= InpMinTP_R - 1e-9);
      if(entry <= 0 || !NexaFinite(entry) || !stopSide || !roomOK || riskNow > sizedRiskDist * (1.0 + 1e-9))
        {
         LogDecision(s, dir, StringFormat("SEND_ABORT_att%d_REVALIDATION_%s", attempt + 1,
                     !stopSide ? "STOP_SIDE" : (!roomOK ? "TARGET_ROOM" : "RISK_WOULD_INCREASE")));
         revalFail = true;
         break;
        }
      bool ok = (dir > 0) ? trade.Buy (lots, _Symbol, entry, stopPrice, tp, InpComment)
                          : trade.Sell(lots, _Symbol, entry, stopPrice, tp, InpComment);
      uint rc = trade.ResultRetcode();
      if(ok || rc == TRADE_RETCODE_DONE || rc == TRADE_RETCODE_PLACED || rc == TRADE_RETCODE_DONE_PARTIAL)
        { sent = true; break; }

      bool definitiveReject = (rc == TRADE_RETCODE_REQUOTE || rc == TRADE_RETCODE_PRICE_CHANGED || rc == TRADE_RETCODE_PRICE_OFF);
      bool ambiguousResult  = (rc == TRADE_RETCODE_TIMEOUT || rc == TRADE_RETCODE_CONNECTION);
      LogDecision(s, dir, StringFormat("SEND_FAIL_att%d_rc%u", attempt + 1, rc));
      if(ambiguousResult) { ambiguous = true; break; }   // server may have accepted: never resend
      if(!definitiveReject) break;
      Sleep(InpRetryBaseDelayMs * (int)MathPow(2, attempt));
     }

   if(sent)
     {
      // Counted at dispatch, not at fill (slot reserved atomically above). A dispatch that is
      // later rejected still consumes the slot -- the ceiling is conservative by design.
      // The portfolio lock stays held until this order resolves (MaintainPortfolioLock).
      LogDecision(s, dir, "DISPATCHED_" + sizeReason + "_" + tpReason);
      LogTradeOpen(s, dir, lots, entry, stopPrice, tp);
     }
   else if(ambiguous)
     {
      // Guard, slot and lock stay held; OnTradeTransaction or the timeout resolves it.
      LogDecision(s, dir, "AMBIGUOUS_RESULT_GUARD_HELD");
     }
   else
     {
      ReleaseTradeSlot();                  // nothing reached the server: give the slot back
      SetInFlight(_Symbol, false);
      ClearPendingContext(_Symbol);
      ReleasePortfolioLock();
      LogDecision(s, dir, revalFail ? "SEND_ABORTED_FAIL_CLOSED" : "ALL_RETRIES_FAILED");
     }
  }

//==================== SL RATCHET GUARD ====================
bool SafeModifySL(ulong ticket, double newSL, double tp, long posType, double currentSL)
  {
   bool widening = (posType == POSITION_TYPE_BUY) ? (newSL < currentSL) : (newSL > currentSL);
   if(widening)
     {
      Print("NEXA: REJECTED stop widening on ", _Symbol, " (", DoubleToString(currentSL, _Digits),
            " -> ", DoubleToString(newSL, _Digits), "). Stops ratchet one way only.");
      return false;
     }
   return trade.PositionModify(ticket, newSL, tp);
  }

//==================== POSITION MANAGEMENT (tick-rate, O(1)) ====================
void ManageOpenPosition()
  {
   ulong ticket;
   if(!SelectNexaPosition(ticket)) return;

   double open = PositionGetDouble(POSITION_PRICE_OPEN);
   double sl   = PositionGetDouble(POSITION_SL);
   double tp   = PositionGetDouble(POSITION_TP);
   long   type = PositionGetInteger(POSITION_TYPE);
   double cur  = (type == POSITION_TYPE_BUY) ? SymbolInfoDouble(_Symbol, SYMBOL_BID) : SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   if(cur <= 0 || open <= 0) return;

   // A NEXA position must never sit without a server-side stop. If the SL is
   // missing (stripped, rejected on modify, restart mid-modify), re-apply it from the
   // staged risk distance. Rate-limited so an async modify is not re-sent every tick.
   if(sl <= 0)
     {
      string rk = GV("RiskDist_" + IntegerToString(ticket));
      string dk = GV("Dir_"      + IntegerToString(ticket));
      if(GlobalVariableCheck(rk) && GlobalVariableCheck(dk))
        {
         double rd = GlobalVariableGet(rk); int d = (int)GlobalVariableGet(dk);
         if(rd > 0 && d != 0)
           {
            double reSL = (d > 0) ? open - rd : open + rd;
            if(!StopDistanceAllowed(type, reSL))
              {
               // The intended stop is already breached (or inside the broker distance): a modify
               // would be rejected forever and leave the position unprotected. Exit instead.
               CloseNexaPositionIfAny("stop missing and intended stop already breached");
              }
            else if(!ModifyThrottled(ticket))
              {
               Print("NEXA WARNING: position ", ticket, " has NO stop-loss -- re-applying ", DoubleToString(reSL, _Digits));
               trade.PositionModify(ticket, reSL, tp);
               MarkModifySent(ticket);
              }
           }
        }
      else if(!ModifyThrottled(ticket))
        {
         Print("NEXA CRITICAL: position ", ticket, " has no stop-loss and no staged risk context. Manual intervention required.");
         MarkModifySent(ticket);                                   // rate-limit the alert, not the check
        }
      return;   // do not run R-based management against a zero stop
     }

   // D-PARTIAL-AFTER-BE fix (2026-10-03): R is measured against the ORIGINAL initial risk
   // (staged RiskDist_<posId>), never the current stop. Breakeven sets sl == open, which made the old
   // |open - sl| denominator zero and returned before the partial close and the time exit.
   // Decisions come from NEXA_PositionMgmt.mqh (tested in NEXA_PositionMgmtTest.mq5).
   int    dir    = (type == POSITION_TYPE_BUY) ? 1 : -1;
   ulong  posId  = (ulong)PositionGetInteger(POSITION_IDENTIFIER);
   double vol    = PositionGetDouble(POSITION_VOLUME);
   datetime opened = (datetime)PositionGetInteger(POSITION_TIME);
   // Context keys are written by MigratePendingToPosition / deleted by the close handler under the
   // POSITION IDENTIFIER (DEAL_POSITION_ID); read them under the same key (a ticket can differ).
   string rk = GV("RiskDist_" + IntegerToString(posId));
   string pk = GV("PartialDone_" + IntegerToString(posId));

   NexaMgmtInput in;
   in.dir = dir; in.open = open; in.sl = sl; in.cur = cur;
   in.hasCtx  = GlobalVariableCheck(rk);
   in.ctxRisk = in.hasCtx ? GlobalVariableGet(rk) : 0.0;
   in.volume = vol; in.volStep = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP); in.volMin = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   in.partialAtR = InpPartialCloseAtR; in.partialPct = InpPartialClosePct;
   in.breakevenAtR = InpBreakevenAtR; in.timeExitR = 0.3;
   in.timeExitBars = InpTimeExitBars;
   in.barsHeld = (InpTimeExitBars > 0) ? iBarShift(_Symbol, PERIOD_CURRENT, opened, false) : 0;
   in.partialLastAttemptAt = GlobalVariableCheck(pk) ? GlobalVariableGet(pk) : 0.0;
   in.historyHasExit = false; in.closeOrderPending = false;
   in.now = TimeCurrent(); in.inflightTimeoutSec = InpInFlightTimeoutSec;

   // Deal history decides whether the partial already executed (exactly once across restarts and
   // lost flags); a pending NEXA close order on this position means one is in flight. Read only when a
   // partial could be due and is not already confirmed; an unreadable history blocks the send.
   double rProbe = NexaMgmtR(dir, open, cur, NexaInitialRiskRef(dir, open, sl, in.hasCtx, in.ctxRisk));
   if(InpPartialClosePct > 0 && rProbe >= InpPartialCloseAtR)
     {
      if(g_partialConfirmedPos == posId) in.historyHasExit = true;
      else
        {
         int hs = PositionExitDealState(posId);
         in.historyHasExit = (hs != 0);
         if(hs == 1) g_partialConfirmedPos = posId;
         if(hs < 0 && g_historyUnreadableWarned != posId)
           {
            Print("NEXA WARNING: deal history of position ", posId, " unreadable -- partial close withheld (fail-closed).");
            g_historyUnreadableWarned = posId;
           }
         in.closeOrderPending = PositionHasPendingCloseOrder(posId);
        }
     }

   NexaMgmtAction act = NexaManageStep(in);
   if(!act.rKnown)
     {
      if(g_noRiskRefWarned != ticket)
        {
         Print("NEXA WARNING: position ", ticket, " has no initial-risk reference (no staged context and stop at/beyond entry); R-based management skipped.");
         g_noRiskRefWarned = ticket;
        }
      return;
     }

   if(act.note == "PARTIAL_VOLUME_NOT_SPLITTABLE" && g_unsplittableWarned != posId)
     {
      Print("NEXA: position ", posId, " volume ", DoubleToString(vol, 2), " cannot be split for the ",
            DoubleToString(InpPartialClosePct, 0), "% partial close (broker minimum); it is managed to TP/BE/time exit whole.");
      g_unsplittableWarned = posId;
     }

   if(act.partialVolume > 0)
     {
      GlobalVariableSet(pk, (double)TimeCurrent());      // attempt time: blocks a re-send inside the in-flight window
      if(trade.PositionClosePartial(ticket, act.partialVolume))
         Print("NEXA: partial close sent for ", ticket, " vol=", DoubleToString(act.partialVolume, 2), " at R=", DoubleToString(act.r, 2));
      else
         Print("NEXA WARNING: partial close failed for ", ticket, " rc=", trade.ResultRetcode(),
               " -- retried after ", InpInFlightTimeoutSec, "s unless an exit deal appears in history");
     }

   if(act.moveToBreakeven)
     {
      if(StopDistanceAllowed(type, open) && FreezeLevelAllowsChange(type, sl, tp) && !ModifyThrottled(ticket))
        {
         SafeModifySL(ticket, open, tp, type, sl);
         MarkModifySent(ticket);
        }
     }

   if(act.timeExit) CloseNexaPositionIfAny("time exit");
  }

// A NEXA order that targets this position (an async close request not yet executed) is pending.
bool PositionHasPendingCloseOrder(ulong posId)
  {
   for(int i = OrdersTotal() - 1; i >= 0; i--)
     {
      ulong o = OrderGetTicket(i);
      if(o == 0) continue;
      if(OrderGetString(ORDER_SYMBOL) != _Symbol) continue;
      if((long)OrderGetInteger(ORDER_MAGIC) != InpMagic) continue;
      if((ulong)OrderGetInteger(ORDER_POSITION_ID) == posId) return true;
     }
   return false;
  }

// 1 = the position already has an exit deal (a partial close executed), 0 = none, -1 = history unreadable.
int PositionExitDealState(ulong posId)
  {
   if(!HistorySelectByPosition(posId)) return -1;
   int n = HistoryDealsTotal();
   for(int i = 0; i < n; i++)
     {
      ulong d = HistoryDealGetTicket(i);
      if(d == 0) continue;
      if((ulong)HistoryDealGetInteger(d, DEAL_POSITION_ID) != posId) continue;
      ENUM_DEAL_ENTRY e = (ENUM_DEAL_ENTRY)HistoryDealGetInteger(d, DEAL_ENTRY);
      if(e == DEAL_ENTRY_OUT || e == DEAL_ENTRY_OUT_BY) return 1;
     }
   return 0;
  }

//==================== TRADE DNA -- CANONICAL SCHEMA v1.0 ====================
// One wide row per event. Fields not applicable to an event are written empty or 0;
// they are never omitted, so the column count is constant and the file parses
// positionally as well as by header name.
//
// TIMESTAMP SEMANTICS (normative -- the research tier depends on these exactly):
//   decision_ts  open time of the CLOSED bar whose features drove the decision.
//                Every feature in the row must be computable from data at or
//                before this instant. This is the causality anchor.
//   dispatch_ts  when the order was sent to the server (0 on non-dispatch rows).
//   fill_ts      deal execution time from broker history (FILL rows only).
//   write_ts     wall-clock when the line was written. DIAGNOSTIC ONLY --
//                never use it as a decision or label timestamp.
//
// PROVENANCE: model_id / calibration_id identify which model (if any) produced
// ai_raw_p. calibration_id is "NONE" until seam L1 exists, which means ai_raw_p
// is RAW model output and must NOT be read as an empirical frequency.
//
// mfe_r / mae_r are deliberately ABSENT here: they are reconstructed by the
// Python labeler from M1 history and belong to the training view of the schema,
// not to what MT5 can observe at write time without tick-by-tick tracking.

struct NexaJournalRow
  {
   string   ev;              // DECISION | OPEN | FILL | PARTIAL_CLOSE | CLOSE | REJECTED
   int      dir;
   double   lots;
   double   entryIntended;
   double   entryActual;
   double   sl, tp;
   datetime dispatchTs, fillTs;
   double   slippagePts;
   double   commission, swap;
   double   resultR;
   string   decisionSource;  // RULE_ONLY | RULE_PLUS_AI | SHADOW
   string   reason;
  };

void ResetJournalRow(NexaJournalRow &r)
  {
   r.ev=""; r.dir=0; r.lots=0; r.entryIntended=0; r.entryActual=0; r.sl=0; r.tp=0;
   r.dispatchTs=0; r.fillTs=0; r.slippagePts=0; r.commission=0; r.swap=0; r.resultR=0;
   r.decisionSource="RULE_ONLY"; r.reason="";
  }

string PeriodStr()
  {
   string p = EnumToString((ENUM_TIMEFRAMES)_Period);
   StringReplace(p, "PERIOD_", "");
   return p;
  }

string AIHeaderColumns()
  {
   string h = "";
   for(int i = 0; i < NEXA_AI_FEATURE_COUNT; i++) h += StringFormat(",f%02d", i);
   return h;
  }

string SchemaHeader()
  {
   return "schema_version,row_id,write_ts,decision_ts,dispatch_ts,fill_ts,symbol,timeframe,"
          "event,strategy_id,direction,decision_source,"
          "bid,ask,spread,spread_atr_ratio,atr,atr_m15,session_tag,"
          "regime_trend,regime_vol,regime_transitioning,"
          "pdh,pdl,pdc,pd_src_bar,liq_setup,liq_origin,liq_level,liq_state,"
          "composite_score,quality_score,"
          "entry_intended,entry_actual,sl_price,tp_price,target_r,risk_dist,lots,"
          "slippage_points,commission,swap,result_r,"
          "model_id,model_schema_version,calibration_id,ai_raw_p,"
          + StringSubstr(AIHeaderColumns(), 1) + ",reason";
  }

void InitJournal()
  {
   string fn = "NEXA_TradeDNA_" + _Symbol + ".csv";
   if(FileIsExist(fn, FILE_COMMON))
     {
      // Any file not already at schema v1.0 is moved aside rather than appended to:
      // mixing column layouts inside one file silently corrupts the training set.
      int r = FileOpen(fn, FILE_READ | FILE_TXT | FILE_ANSI | FILE_COMMON);
      if(r != INVALID_HANDLE)
        {
         string first = FileReadString(r);
         FileClose(r);
         if(StringFind(first, "schema_version") == 0 && StringFind(first, ",f00,") >= 0) return;
         string legacy = "NEXA_TradeDNA_" + _Symbol + "_legacy_" + IntegerToString((long)TimeCurrent()) + ".csv";
         if(FileMove(fn, FILE_COMMON, legacy, FILE_COMMON))
            Print("NEXA: pre-v1.0 Trade DNA moved to ", legacy, " -- starting a fresh schema v",
                  NEXA_DNA_SCHEMA_VERSION, " journal.");
         else
           {
            Print("NEXA ERROR: legacy Trade DNA present and could not be moved (err ", GetLastError(),
                  "). Journal disabled to avoid corrupting the dataset.");
            return;
           }
        }
     }
   int h = FileOpen(fn, FILE_WRITE | FILE_TXT | FILE_ANSI | FILE_COMMON);
   if(h == INVALID_HANDLE) { Print("NEXA ERROR: cannot create Trade DNA file, err ", GetLastError()); return; }
   FileWriteString(h, SchemaHeader() + "\r\n");
   FileClose(h);
   Print("NEXA: Trade DNA journal initialised, schema v", NEXA_DNA_SCHEMA_VERSION);
  }

void LogRow(const NexaSignal &s, NexaJournalRow &r)
  {
   string fn = "NEXA_TradeDNA_" + _Symbol + ".csv";
   int h = FileOpen(fn, FILE_WRITE | FILE_READ | FILE_TXT | FILE_ANSI | FILE_COMMON);
   if(h == INVALID_HANDLE) return;            // journalling is not a risk control: never blocks trading
   FileSeek(h, 0, SEEK_END);

   float f[];
   bool packed = PackFeatures(s, f);
   string ai = "";
   for(int i = 0; i < NEXA_AI_FEATURE_COUNT; i++)
      ai += "," + (packed ? DoubleToString((double)f[i], 6) : "");

   g_rowSeq++;
   string rowId = StringFormat("%s:%s:%I64d", _Symbol,
                    TimeToString(s.decisionBarTime, TIME_DATE | TIME_SECONDS), g_rowSeq);

   string line = StringFormat(
      "%s,%s,%s,%s,%s,%s,%s,%s,"          // schema,row_id,write,decision,dispatch,fill,symbol,tf
      "%s,%d,%d,%s,"                       // event,strategy_id,direction,decision_source
      "%.5f,%.5f,%.5f,%.5f,%.5f,%.5f,%s,"  // bid,ask,spread,spreadATR,atr,atrM15,session
      "%d,%d,%d,"                          // regime trend,vol,transitioning
      "%.5f,%.5f,%.5f,%s,%d,%d,%d,%d,"     // pdh,pdl,pdc,pdsrc,setup,origin,level,state
      "%d,%d,"                             // composite,quality
      "%.5f,%.5f,%.5f,%.5f,%.3f,%.5f,%.2f," // entries,sl,tp,targetR,riskdist,lots
      "%.1f,%.2f,%.2f,%.4f,"               // slippage,commission,swap,result_r
      "%s,%s,%s,%.6f%s,%s\r\n",
      NEXA_DNA_SCHEMA_VERSION, rowId,
      TimeToString(TimeCurrent(), TIME_DATE | TIME_SECONDS),
      TimeToString(s.decisionBarTime, TIME_DATE | TIME_SECONDS),
      (r.dispatchTs > 0 ? TimeToString(r.dispatchTs, TIME_DATE | TIME_SECONDS) : ""),
      (r.fillTs     > 0 ? TimeToString(r.fillTs,     TIME_DATE | TIME_SECONDS) : ""),
      _Symbol, PeriodStr(),
      r.ev, 1, r.dir, r.decisionSource,
      s.bid, s.ask, s.spread, s.spreadATRRatio, s.atrValue, s.atrM15, s.sessionTag,
      (int)s.trendState, (int)s.volState, (int)(s.regimeTransitioning ? 1 : 0),
      s.pdh, s.pdl, s.pdc,
      (s.pdSourceBarTime > 0 ? TimeToString(s.pdSourceBarTime, TIME_DATE) : ""),
      (int)s.liqSetup, (int)s.liqOrigin, (int)s.liqLevel, (int)s.liqState,
      s.compositeScore, s.qualityScore,
      r.entryIntended, r.entryActual, r.sl, r.tp, s.dynamicTargetR,
      // risk_dist only exists where a stop does: CLOSE/PARTIAL_CLOSE rows carry sl=0 and
      // previously journaled the entry PRICE as a "distance". 0 = not applicable.
      (r.sl > 0 && r.entryIntended > 0) ? MathAbs(r.entryIntended - r.sl) : 0.0, r.lots,
      r.slippagePts, r.commission, r.swap, r.resultR,
      AI_ModelId(), NEXA_AI_SCHEMA_VERSION, AI_CalibrationId(), s.aiScore,
      ai, r.reason);
   FileWriteString(h, line);
   FileClose(h);
  }

//--- decision_source is factual, not aspirational: RULE_PLUS_AI only when a model
//--- actually returned a usable probability for this decision.
string DecisionSourceOf(const NexaSignal &s)
  {
   return (s.aiScore >= 0.0 && s.aiScore <= 1.0) ? "RULE_PLUS_AI" : "RULE_ONLY";
  }

void LogDecision(const NexaSignal &s, int dir, string reason)
  {
   NexaJournalRow r; ResetJournalRow(r);
   r.ev = "DECISION"; r.dir = dir; r.reason = reason; r.decisionSource = DecisionSourceOf(s);
   LogRow(s, r);
  }

void LogTradeOpen(const NexaSignal &s, int dir, double lots, double e, double sl, double tp)
  {
   NexaJournalRow r; ResetJournalRow(r);
   r.ev = "OPEN"; r.dir = dir; r.lots = lots;
   r.entryIntended = e; r.sl = sl; r.tp = tp;
   r.dispatchTs = g_lastDispatchTs;
   r.decisionSource = DecisionSourceOf(s);
   r.reason = "DISPATCHED";
   LogRow(s, r);
  }

//==================== TRANSACTION HANDLER ====================
void OnTradeTransaction(const MqlTradeTransaction &trans, const MqlTradeRequest &request, const MqlTradeResult &result)
  {
   //--- ASYNC REJECTION PATH. In async mode OrderSendAsync returns PLACED immediately;
   //--- the real verdict (INVALID_STOPS, NO_MONEY, MARKET_CLOSED, REQUOTE...) arrives
   //--- here. Without this branch a rejected order would leave the guard raised until
   //--- timeout and leave an OPEN row in Trade DNA for a trade that never existed.
   //--- Sync mode is excluded: there ExecuteSignal owns the lifecycle and retries, and
   //--- releasing here mid-retry would orphan the staged context.
   if(trans.type == TRADE_TRANSACTION_REQUEST)
     {
      if(!InpAsyncExecution) return;
      if(request.symbol != _Symbol || (long)request.magic != InpMagic) return;
      if(request.action != TRADE_ACTION_DEAL) return;
      if(request.position != 0) return;                       // close/modify requests: not an entry
      uint rc = result.retcode;
      if(rc == TRADE_RETCODE_DONE || rc == TRADE_RETCODE_PLACED || rc == TRADE_RETCODE_DONE_PARTIAL) return;
      NexaSignal blank; ResetSignal(blank);
      NexaJournalRow row; ResetJournalRow(row);
      row.ev = "REJECTED";
      row.dir = (request.type == ORDER_TYPE_BUY) ? 1 : -1;
      row.lots = request.volume; row.entryIntended = request.price;
      row.sl = request.sl; row.tp = request.tp;
      row.dispatchTs = g_lastDispatchTs;
      row.reason = StringFormat("ASYNC_RC_%u", rc);
      LogRow(blank, row);
      SetInFlight(_Symbol, false);
      ClearPendingContext(_Symbol);
      return;
     }

   if(trans.type != TRADE_TRANSACTION_DEAL_ADD) return;
   if(!HistoryDealSelect(trans.deal)) return;
   if(HistoryDealGetString(trans.deal, DEAL_SYMBOL) != _Symbol) return;
   if((long)HistoryDealGetInteger(trans.deal, DEAL_MAGIC) != InpMagic) return;

   ulong posId = (ulong)HistoryDealGetInteger(trans.deal, DEAL_POSITION_ID);
   ENUM_DEAL_ENTRY entryType = (ENUM_DEAL_ENTRY)HistoryDealGetInteger(trans.deal, DEAL_ENTRY);
   double dealPrice = HistoryDealGetDouble(trans.deal, DEAL_PRICE);
   double dealVol   = HistoryDealGetDouble(trans.deal, DEAL_VOLUME);

   if(entryType == DEAL_ENTRY_IN)
     {
      MigratePendingToPosition(_Symbol, posId);
      SetInFlight(_Symbol, false);
      string ek = GV("Entry_" + IntegerToString(posId));
      string dk = GV("Dir_"   + IntegerToString(posId));
      double intended = GlobalVariableCheck(ek) ? GlobalVariableGet(ek) : dealPrice;
      int    dir      = GlobalVariableCheck(dk) ? (int)GlobalVariableGet(dk) : 0;
      double pt = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
      double slipPts = (pt > 0) ? MathAbs(dealPrice - intended) / pt : 0;
      // FILL row carries the ACTUAL fill and the SL/TP as they exist on the server --
      // the exporter pairs this with the preceding OPEN row's feature snapshot.
      double posSL = 0, posTP = 0;
      if(PositionSelectByTicket(posId)) { posSL = PositionGetDouble(POSITION_SL); posTP = PositionGetDouble(POSITION_TP); }
      NexaSignal blank; ResetSignal(blank);
      NexaJournalRow row; ResetJournalRow(row);
      row.ev = "FILL"; row.dir = dir; row.lots = dealVol;
      row.entryIntended = intended;                                    // what the EA asked for
      row.entryActual   = dealPrice;                                   // what the broker gave
      row.sl = posSL; row.tp = posTP;
      row.dispatchTs = g_lastDispatchTs;
      row.fillTs     = (datetime)HistoryDealGetInteger(trans.deal, DEAL_TIME);
      row.slippagePts = slipPts;
      row.commission  = HistoryDealGetDouble(trans.deal, DEAL_COMMISSION);
      row.swap        = HistoryDealGetDouble(trans.deal, DEAL_SWAP);
      row.reason = StringFormat("SLIPPAGE_PTS_%.1f", slipPts);
      LogRow(blank, row);
      return;
     }

   if(entryType != DEAL_ENTRY_OUT && entryType != DEAL_ENTRY_OUT_BY) return;

   string rk = GV("RiskDist_" + IntegerToString(posId));
   if(!GlobalVariableCheck(rk)) return;

   double riskDist = GlobalVariableGet(rk);
   double entry    = GlobalVariableGet(GV("Entry_" + IntegerToString(posId)));
   double dir      = GlobalVariableGet(GV("Dir_"   + IntegerToString(posId)));
   double rPart    = (riskDist > 0 && NexaFinite(riskDist)) ? dir * (dealPrice - entry) / riskDist : 0;

   NexaSignal blank; ResetSignal(blank);

   // Full vs partial is decided from DEAL HISTORY (volume in vs out), which is
   // authoritative regardless of whether the position record has updated yet.
   if(!PositionFullyClosedByHistory(posId))
     {
      NexaJournalRow rowP; ResetJournalRow(rowP);
      rowP.ev = "PARTIAL_CLOSE"; rowP.dir = (int)dir; rowP.lots = dealVol;
      rowP.entryIntended = entry; rowP.entryActual = dealPrice;
      rowP.fillTs = (datetime)HistoryDealGetInteger(trans.deal, DEAL_TIME);
      rowP.commission = HistoryDealGetDouble(trans.deal, DEAL_COMMISSION);
      rowP.swap       = HistoryDealGetDouble(trans.deal, DEAL_SWAP);
      rowP.resultR = rPart;
      rowP.reason = StringFormat("R_PARTIAL_%.3f", rPart);
      LogRow(blank, rowP);
      return;
     }

   ENUM_NEXA_REGIME_TREND t = (ENUM_NEXA_REGIME_TREND)(int)GlobalVariableGet(GV("Trend_" + IntegerToString(posId)));
   ENUM_NEXA_REGIME_VOL   v = (ENUM_NEXA_REGIME_VOL)(int)GlobalVariableGet(GV("Vol_"   + IntegerToString(posId)));
   // Whole-position R (safety audit 2026-09-29): volume-weighted over EVERY exit leg, so a
   // partial close at InpPartialCloseAtR is not lost when the remainder closes elsewhere.
   double rTotal = rPart;
   if(riskDist > 0 && NexaFinite(riskDist) && HistorySelectByPosition(posId))
     {
      double vIn = 0, rv = 0;
      int nd0 = HistoryDealsTotal();
      for(int i = 0; i < nd0; i++)
        {
         ulong dt0 = HistoryDealGetTicket(i);
         if(dt0 == 0 || (ulong)HistoryDealGetInteger(dt0, DEAL_POSITION_ID) != posId) continue;
         ENUM_DEAL_ENTRY e0 = (ENUM_DEAL_ENTRY)HistoryDealGetInteger(dt0, DEAL_ENTRY);
         double v0 = HistoryDealGetDouble(dt0, DEAL_VOLUME), p0 = HistoryDealGetDouble(dt0, DEAL_PRICE);
         if(e0 == DEAL_ENTRY_IN) vIn += v0;
         else if(e0 == DEAL_ENTRY_OUT || e0 == DEAL_ENTRY_OUT_BY) rv += dir * (p0 - entry) / riskDist * v0;
        }
      if(vIn > 0 && NexaFinite(rv / vIn)) rTotal = rv / vIn;
     }
   UpdateExpectancyStats(rTotal, t, v);
   SyncShadowLedger(rTotal, InpRiskPercent);                 // diagnostic only -- gates nothing
   if(g_shadow.tradesCounted > 0 && g_shadow.tradesCounted % 10 == 0) Print("NEXA ", ShadowLedgerReport());
   // Sum realised commission and swap across EVERY deal of this position, so the
   // CLOSE row carries the trade's full execution cost rather than the last leg's.
   double totComm = 0, totSwap = 0;
   if(HistorySelectByPosition(posId))
     {
      int nd = HistoryDealsTotal();
      for(int i = 0; i < nd; i++)
        {
         ulong dt = HistoryDealGetTicket(i);
         if(dt == 0) continue;
         if((ulong)HistoryDealGetInteger(dt, DEAL_POSITION_ID) != posId) continue;
         totComm += HistoryDealGetDouble(dt, DEAL_COMMISSION);
         totSwap += HistoryDealGetDouble(dt, DEAL_SWAP);
        }
     }
   NexaJournalRow rowC; ResetJournalRow(rowC);
   rowC.ev = "CLOSE"; rowC.dir = (int)dir; rowC.lots = dealVol;
   rowC.entryIntended = entry; rowC.entryActual = dealPrice;
   rowC.fillTs = (datetime)HistoryDealGetInteger(trans.deal, DEAL_TIME);
   rowC.commission = totComm; rowC.swap = totSwap;
   rowC.resultR = rTotal;
   rowC.reason = StringFormat("R_RESULT_%.3f", rTotal);
   LogRow(blank, rowC);

   string keys[6] = {"RiskDist_","Entry_","Dir_","Trend_","Vol_","TgtR_"};
   for(int i = 0; i < 6; i++) { string k = GV(keys[i] + IntegerToString(posId)); if(GlobalVariableCheck(k)) GlobalVariableDel(k); }
   string pk = GV("PartialDone_" + IntegerToString(posId));
   if(GlobalVariableCheck(pk)) GlobalVariableDel(pk);
  }

//==================== TIME GATES (single clock: NexaGMTNow) ====================
bool InSessionWindow()
  {
   if(!InpSessionFilterEnabled) return true;
   int h = NexaGMTHourOf(TimeCurrent());
   if(InpSessionStartGMT <= InpSessionEndGMT) return (h >= InpSessionStartGMT && h < InpSessionEndGMT);
   return (h >= InpSessionStartGMT || h < InpSessionEndGMT);
  }

bool HardCloseDue()
  {
   if(!InpHardCloseEnabled) return false;
   return (NexaGMTHourOf(TimeCurrent()) >= InpHardCloseGMTHour);
  }

bool IsWeekendCloseWindow()
  {
   if(!InpCloseBeforeWeekend) return false;
   MqlDateTime dt; TimeToStruct(TimeCurrent(), dt);      // server clock: broker's own Friday
   return (dt.day_of_week == 5 && dt.hour >= InpWeekendCloseHour);
  }

void CloseNexaPositionIfAny(string why)
  {
   ulong t;
   if(!SelectNexaPosition(t)) return;
   // In async mode the position persists for a few ticks after the close is sent.
   // Do not re-send a close for the same ticket inside the confirmation window.
   if(g_closeReqTicket == t && TimeCurrent() - g_closeReqSentAt <= InpInFlightTimeoutSec) return;
   if(trade.PositionClose(t))
     {
      g_closeReqTicket = t; g_closeReqSentAt = TimeCurrent();
      Print("NEXA: close sent for ", _Symbol, " ticket ", t, " -- ", why);
     }
   else
      Print("NEXA WARNING: close request failed for ", t, " rc=", trade.ResultRetcode(), " -- ", why);
  }

//==================== TICK PATH ====================
void OnTick()
  {
   //--- TIER 1: every tick, O(1) only
   UpdateTickFlow();
   MaintainPortfolioLock();
   if(HardCloseDue()) CloseNexaPositionIfAny("hard close hour");
   ManageOpenPosition();

   //--- TIER 2: once per new bar
   datetime bt = iTime(_Symbol, PERIOD_CURRENT, 0);
   if(bt == 0 || bt == g_lastBarTime) return;
   g_lastBarTime = bt;

   RollDailyStateIfNewDay();

   if(IsWeekendCloseWindow()) { CloseNexaPositionIfAny("weekend"); return; }
   if(!InpEnableTrading) return;
   if(EmergencyStopActive()) return;
   if(DailyLossLimitBreached()) { TriggerEmergencyStop("Daily loss limit breached"); return; }
   if(DrawdownLimitBreached())  { TriggerEmergencyStop("Max drawdown limit breached"); return; }
   if(TradeCountLimitBreached()) return;
   if(OrderInFlight(_Symbol)) return;

   if(FOMC_WindowApproaching(1)) CloseNexaPositionIfAny("FOMC window opening");
   if(!InSessionWindow()) return;

   string fomcReason;
   if(FOMC_InBlockedWindow(fomcReason))
     {
      NexaSignal fs; ResetSignal(fs);
      // Anchor even a pre-feature veto to the CLOSED bar (shift 1), exactly as
      // BuildFeatures anchors g_ratesEntry[0]. `bt` is the FORMING bar (shift 0):
      // stamping it made decision_ts == write_ts on every FOMC veto row
      // (51,791 rows in the 2026-09-27 Pepperstone batch), breaking the contract.
      fs.decisionBarTime = iTime(_Symbol, PERIOD_CURRENT, 1);
      LogDecision(fs, 0, "NO_TRADE_" + fomcReason);
      return;
     }

   ResetSignal(g_sig);
   g_sigValid = BuildFeatures(g_sig);
   if(!g_sigValid) return;

   g_sig.obiProxy = GetOBIProxy();
   g_sig.cvdProxy = GetCVDProxy();
   g_sig.newsRiskActive = IsNewsRiskWindow(_Symbol);
   g_sig.usdCompositeDirection = UsdCompositeDirection();

   if(g_sig.spreadATRRatio > InpMaxSpreadATRRatio)
     { LogDecision(g_sig, 0, StringFormat("NO_TRADE_SPREAD_TAX_%.1fPCT", g_sig.spreadATRRatio * 100.0)); return; }
   if(g_sig.newsRiskActive) { LogDecision(g_sig, 0, "NO_TRADE_NEWS_RISK_WINDOW"); return; }

   int qScore = 0;
   g_sig.compositeScore = ComputeCompositeScore(g_sig, qScore);
   g_sig.qualityScore   = qScore;

   if(g_sig.compositeScore >= 2 || g_sig.compositeScore <= -2)
     {
      int dir = (g_sig.compositeScore > 0) ? 1 : -1;
      int pe = SelectPrimaryEvent();
      string stopReason;
      double stopPrice = CalcSetupStop(dir, g_sig, pe, stopReason);
      if(stopPrice <= 0) { LogDecision(g_sig, dir, "NO_TRADE_" + stopReason); return; }
      ExecuteSignal(dir, stopPrice, g_sig);
     }
   else
      LogDecision(g_sig, 0, StringFormat("NO_TRADE_NO_QUALIFIED_LIQUIDITY_EVENT_state%d", (int)g_sig.liqState));
  }
