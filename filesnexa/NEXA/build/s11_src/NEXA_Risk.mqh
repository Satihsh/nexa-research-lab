//+------------------------------------------------------------------+
//| NEXA_Risk.mqh                                                     |
//| Position sizing via the broker's own OrderCalcProfit/Margin.       |
//| Hard risk controls -- absolute, never overridden by AI.            |
//| Portfolio currency-exposure netting and correlation caps.          |
//| Every risk decision here reads LIVE broker state only.             |
//+------------------------------------------------------------------+
#ifndef NEXA_RISK_MQH
#define NEXA_RISK_MQH
#include "NEXA_Common.mqh"

input double   InpRiskPercent        = 0.30;
input double   InpHardRiskCeiling    = 1.00;
input double   InpMaxDailyLossPct    = 2.00;   // halt all trading for the day at -2% equity
input double   InpMaxDrawdownPct     = 10.00;
input int      InpMaxTradesPerDay    = 10;
input double   InpMaxSpreadATRRatio  = 0.15;   // spread may not exceed 15% of ATR
input double   InpMaxMarginUsagePct  = 50.0;   // required margin must not exceed this % of free margin
input int      InpMaxSameCurrencyNet = 2;      // max net lot-equivalent exposure per currency, in min-lot units
input double   InpMaxCorrelation     = 0.75;
input int      InpCorrelationBars    = 100;

//==================== DAILY / PORTFOLIO STATE ====================
void RollDailyStateIfNewDay()
  {
   MqlDateTime dt; TimeToStruct(TimeCurrent(), dt);
   double todayStamp = dt.year * 10000 + dt.mon * 100 + dt.day;
   double storedStamp = GlobalVariableCheck(GV("DayStamp")) ? GlobalVariableGet(GV("DayStamp")) : 0;
   if(storedStamp != todayStamp)
     {
      GlobalVariableSet(GV("DayStamp"), todayStamp);
      GlobalVariableSet(GV("TradesToday"), 0);
      GlobalVariableSet(GV("DailyStartEquity"), AccountInfoDouble(ACCOUNT_EQUITY));
      GlobalVariableSet(GV("EmergencyStop"), 0);
      if(!GlobalVariableCheck(GV("EquityPeak")))
         GlobalVariableSet(GV("EquityPeak"), AccountInfoDouble(ACCOUNT_EQUITY));
      Print("NEXA: new trading day rolled. Start equity=", AccountInfoDouble(ACCOUNT_EQUITY));
     }
  }

bool DailyLossLimitBreached()
  {
   double eq = AccountInfoDouble(ACCOUNT_EQUITY);
   // If the day has not been rolled yet, treat current equity as the start:
   // that yields 0% loss (no false halt) without pretending to know a start value.
   double startEq = GlobalVariableCheck(GV("DailyStartEquity")) ? GlobalVariableGet(GV("DailyStartEquity")) : eq;
   if(startEq <= 0) return true;                // an invalid start equity is a halt condition
   double lossPct = (startEq - eq) / startEq * 100.0;
   return lossPct >= InpMaxDailyLossPct;
  }

bool DrawdownLimitBreached()
  {
   double eq = AccountInfoDouble(ACCOUNT_EQUITY);
   double peak = GlobalVariableCheck(GV("EquityPeak")) ? GlobalVariableGet(GV("EquityPeak")) : eq;
   if(eq > peak) { peak = eq; GlobalVariableSet(GV("EquityPeak"), peak); }
   if(peak <= 0) return true;
   double ddPct = (peak - eq) / peak * 100.0;
   return ddPct >= InpMaxDrawdownPct;
  }

bool TradeCountLimitBreached()
  {
   double count = GlobalVariableCheck(GV("TradesToday")) ? GlobalVariableGet(GV("TradesToday")) : 0;
   return count >= InpMaxTradesPerDay;
  }
void IncrementTradeCount()
  {
   double count = GlobalVariableCheck(GV("TradesToday")) ? GlobalVariableGet(GV("TradesToday")) : 0;
   GlobalVariableSet(GV("TradesToday"), count + 1);
  }
bool EmergencyStopActive()
  {
   return GlobalVariableCheck(GV("EmergencyStop")) && GlobalVariableGet(GV("EmergencyStop")) >= 1;
  }
void TriggerEmergencyStop(string reasonText)
  {
   GlobalVariableSet(GV("EmergencyStop"), 1);
   Print("NEXA EMERGENCY STOP TRIGGERED: ", reasonText);
  }

//==================== PROGRESSIVE DRAWDOWN THROTTLE ====================
// Graduated scaling BEFORE the hard stop. DrawdownLimitBreached() is unchanged and
// still fires at InpMaxDrawdownPct. This multiplier can only reduce size (<= 1.0).
double DrawdownRiskMultiplier()
  {
   double eq = AccountInfoDouble(ACCOUNT_EQUITY);
   double peak = GlobalVariableCheck(GV("EquityPeak")) ? GlobalVariableGet(GV("EquityPeak")) : eq;
   if(peak <= 0) return 0.0;
   double ddPct = (peak - eq) / peak * 100.0;
   if(ddPct >= InpMaxDrawdownPct)        return 0.0;
   if(ddPct >= InpMaxDrawdownPct * 0.75) return 0.25;
   if(ddPct >= InpMaxDrawdownPct * 0.50) return 0.50;
   return 1.0;
  }

//==================== HARDENED SIZING ====================
// Uses OrderCalcProfit at one volume step and scales linearly. After every
// normalisation the ACTUAL monetary risk is recomputed and re-checked against the
// hard ceiling, so no rounding, clamp or throttle can leave risk above the limit.
double CalcLotSizeHardened(int direction, double entry, double stopPrice, string &reason)
  {
   reason = "";
   if(direction == 0 || !NexaFinite(entry) || !NexaFinite(stopPrice) || entry <= 0 || stopPrice <= 0)
     { reason = "INVALID_PRICE_INPUT"; return 0; }

   double equity  = AccountInfoDouble(ACCOUNT_EQUITY);
   double volMin  = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double volStep = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   double volMax  = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);

   if(equity <= 0)                         { reason = "INVALID_EQUITY";       return 0; }
   if(volStep <= 0 || volMin <= 0 || volMax <= 0 || volMax < volMin)
                                           { reason = "INVALID_BROKER_VOLUME_SPEC"; return 0; }
   if(InpRiskPercent <= 0 || InpHardRiskCeiling <= 0)
                                           { reason = "INVALID_RISK_CONFIG";  return 0; }

   ENUM_ORDER_TYPE otype = (direction > 0) ? ORDER_TYPE_BUY : ORDER_TYPE_SELL;
   double riskAtStep = 0;
   if(!OrderCalcProfit(otype, _Symbol, volStep, entry, stopPrice, riskAtStep))
     { reason = "ORDERCALCPROFIT_FAILED"; return 0; }
   riskAtStep = MathAbs(riskAtStep);
   if(!NexaFinite(riskAtStep) || riskAtStep <= 0) { reason = "ZERO_RISK_PER_STEP"; return 0; }

   double riskPerLot = riskAtStep / volStep;             // volStep > 0 guaranteed
   double riskAmountTarget = equity * (InpRiskPercent / 100.0);
   double rawLots = riskAmountTarget / riskPerLot;       // riskPerLot > 0 guaranteed
   double roundedLots = MathFloor(rawLots / volStep) * volStep;

   double finalLots = 0; string sizeMode = "";
   if(roundedLots >= volMin)
     {
      finalLots = MathMin(roundedLots, volMax);
      sizeMode = "OK_TARGET_RISK";
     }
   else
     {
      // Below broker minimum at target risk. Executing the minimum lot is allowed
      // ONLY if it stays inside the hard ceiling; otherwise NO TRADE. Risk is never
      // raised merely because the broker minimum is larger.
      double impliedRiskPct = (riskPerLot * volMin) / equity * 100.0;
      if(impliedRiskPct <= InpHardRiskCeiling)
        { finalLots = volMin; sizeMode = StringFormat("OVERSIZED_VS_TARGET_%.2fPCT", impliedRiskPct); }
      else
        { reason = "MIN_LOT_EXCEEDS_HARD_RISK_CEILING"; return 0; }
     }

   // margin check via the broker's own calculator, against LIVE free margin
   double marginReq = 0;
   if(!OrderCalcMargin(otype, _Symbol, finalLots, entry, marginReq))
     { reason = "ORDERCALCMARGIN_FAILED"; return 0; }
   double freeMargin = AccountInfoDouble(ACCOUNT_MARGIN_FREE);
   if(freeMargin <= 0) { reason = "NO_FREE_MARGIN"; return 0; }
   if(marginReq / freeMargin * 100.0 > InpMaxMarginUsagePct)
     { reason = "MARGIN_USAGE_EXCEEDS_CAP"; return 0; }

   // progressive drawdown throttle -- reduce only
   double ddMult = DrawdownRiskMultiplier();
   finalLots = MathFloor((finalLots * ddMult) / volStep) * volStep;
   if(finalLots < volMin) { reason = "DRAWDOWN_THROTTLE_BELOW_MIN_LOT"; return 0; }

   // FINAL RE-CHECK: actual monetary risk after every normalisation must satisfy
   // the hard ceiling. This is the last word, regardless of how finalLots arose.
   double actualRiskPct = (riskPerLot * finalLots) / equity * 100.0;
   if(!NexaFinite(actualRiskPct) || actualRiskPct > InpHardRiskCeiling)
     { reason = StringFormat("ACTUAL_RISK_%.2fPCT_EXCEEDS_CEILING", actualRiskPct); return 0; }

   reason = sizeMode + (ddMult < 1.0 ? StringFormat("_THROTTLED_%.2fx", ddMult) : "")
            + StringFormat("_RISK%.2fPCT", actualRiskPct);
   return finalLots;
  }

//==================== CORRELATION CAP (fail-closed, time-aligned) ====================
// HUMAN-APPROVED SAFETY FIX (2026-09-29). The former PearsonCorrelation() paired bars by SHIFT
// and returned 0 ("uncorrelated", i.e. PASS) on unreadable history, too few bars, zero variance or
// a non-finite result, so the cap failed OPEN. Policy is unchanged: InpMaxCorrelation over the last
// InpCorrelationBars closed bars of PERIOD_CURRENT. What changed:
//   * returns are paired by BAR OPEN TIME: only intervals [t0,t1] of consecutive closed bars of the
//     new symbol whose two open times BOTH exist in the other symbol;
//   * at least NEXA_CORR_MIN_ALIGNED_FRAC of the window must be aligned;
//   * every data problem (unavailable/unsynchronised/short history, bad price, zero variance,
//     non-finite result, unreadable position) is INSUFFICIENT_DATA, and INSUFFICIENT_DATA BLOCKS.
#define NEXA_CORR_MIN_ALIGNED_FRAC 0.80

enum ENUM_NEXA_CORR_STATE
  {
   NEXA_CORR_OK                = 0,
   NEXA_CORR_BLOCK             = 1,
   NEXA_CORR_INSUFFICIENT_DATA = 2
  };

// Index of x in the strictly ascending array t[], or -1.
int NexaFindTime(const datetime &t[], datetime x)
  {
   int lo = 0, hi = ArraySize(t) - 1;
   while(lo <= hi)
     {
      int mid = (lo + hi) / 2;
      if(t[mid] == x) return mid;
      if(t[mid] < x) lo = mid + 1; else hi = mid - 1;
     }
   return -1;
  }

bool NexaStrictlyAscending(const datetime &t[])
  {
   for(int i = 1; i < ArraySize(t); i++) if(t[i] <= t[i - 1]) return false;
   return true;
  }

// Pure, deterministic core (no terminal access). tA/cA: closed bars of the new symbol, tB/cB: closed
// bars of the other symbol, both ascending by open time. Uses the last barsBack+1 bars of A.
ENUM_NEXA_CORR_STATE NexaCorrelationFromBars(const datetime &tA[], const double &cA[],
                                             const datetime &tB[], const double &cB[],
                                             int barsBack, double threshold, double minAlignedFrac,
                                             double &corr, int &aligned, string &detail)
  {
   corr = 0.0; aligned = 0; detail = "";
   int nA = ArraySize(tA), nB = ArraySize(tB);
   if(barsBack < 3 || !NexaFinite(threshold) || threshold <= 0 || !NexaFinite(minAlignedFrac) || minAlignedFrac <= 0)
     { detail = "INVALID_CONFIG"; return NEXA_CORR_INSUFFICIENT_DATA; }
   if(ArraySize(cA) != nA || ArraySize(cB) != nB)            { detail = "ARRAY_MISMATCH"; return NEXA_CORR_INSUFFICIENT_DATA; }
   if(nA < barsBack + 1)                                     { detail = "HISTORY_SHORT_A"; return NEXA_CORR_INSUFFICIENT_DATA; }
   if(nB < 2)                                                { detail = "HISTORY_SHORT_B"; return NEXA_CORR_INSUFFICIENT_DATA; }
   if(!NexaStrictlyAscending(tA) || !NexaStrictlyAscending(tB)) { detail = "TIME_NOT_ASCENDING"; return NEXA_CORR_INSUFFICIENT_DATA; }

   double ra[], rb[];
   if(ArrayResize(ra, barsBack) != barsBack || ArrayResize(rb, barsBack) != barsBack)
     { detail = "ALLOC"; return NEXA_CORR_INSUFFICIENT_DATA; }
   for(int k = nA - barsBack; k < nA; k++)
     {
      int j0 = NexaFindTime(tB, tA[k - 1]), j1 = NexaFindTime(tB, tA[k]);
      if(j0 < 0 || j1 < 0) continue;                         // interval not present in B: not a pair
      double a0 = cA[k - 1], a1 = cA[k], b0 = cB[j0], b1 = cB[j1];
      if(!NexaFinite(a0) || !NexaFinite(a1) || !NexaFinite(b0) || !NexaFinite(b1) ||
         a0 <= 0 || a1 <= 0 || b0 <= 0 || b1 <= 0) continue; // unreadable price: not a pair (never a zero return)
      ra[aligned] = (a1 - a0) / a0;
      rb[aligned] = (b1 - b0) / b0;
      aligned++;
     }
   int need = (int)MathCeil(minAlignedFrac * barsBack);
   if(aligned < need) { detail = StringFormat("ALIGNED_%d_OF_%d", aligned, barsBack); return NEXA_CORR_INSUFFICIENT_DATA; }

   double meanA = 0, meanB = 0;
   for(int i = 0; i < aligned; i++) { meanA += ra[i]; meanB += rb[i]; }
   meanA /= aligned; meanB /= aligned;
   double cov = 0, varA = 0, varB = 0;
   for(int i = 0; i < aligned; i++)
     {
      cov  += (ra[i] - meanA) * (rb[i] - meanB);
      varA += (ra[i] - meanA) * (ra[i] - meanA);
      varB += (rb[i] - meanB) * (rb[i] - meanB);
     }
   if(!NexaFinite(varA) || !NexaFinite(varB) || varA <= 0 || varB <= 0)
     { detail = "ZERO_OR_INVALID_VARIANCE"; return NEXA_CORR_INSUFFICIENT_DATA; }
   double r = cov / MathSqrt(varA * varB);
   if(!NexaFinite(r)) { detail = "NON_FINITE"; return NEXA_CORR_INSUFFICIENT_DATA; }
   corr = r;
   if(MathAbs(r) >= threshold) return NEXA_CORR_BLOCK;
   return NEXA_CORR_OK;
  }

// Terminal wrapper: reads CLOSED bars (start_pos=1) of both symbols over the same time window.
ENUM_NEXA_CORR_STATE NexaCorrelationState(string symA, string symB, int barsBack,
                                          double &corr, int &aligned, string &detail)
  {
   corr = 0.0; aligned = 0; detail = "";
   if(symA == "" || symB == "" || barsBack < 3)          { detail = "INVALID_ARGS"; return NEXA_CORR_INSUFFICIENT_DATA; }
   if(!SymbolSelect(symB, true))                         { detail = "SYMBOL_UNAVAILABLE"; return NEXA_CORR_INSUFFICIENT_DATA; }
   if(!(bool)SeriesInfoInteger(symA, PERIOD_CURRENT, SERIES_SYNCHRONIZED) ||
      !(bool)SeriesInfoInteger(symB, PERIOD_CURRENT, SERIES_SYNCHRONIZED))
                                                         { detail = "NOT_SYNCHRONIZED"; return NEXA_CORR_INSUFFICIENT_DATA; }
   MqlRates a[], b[];
   ResetLastError();
   int na = CopyRates(symA, PERIOD_CURRENT, 1, barsBack + 1, a);
   if(na != barsBack + 1) { detail = StringFormat("HISTORY_A_%d_ERR%d", na, GetLastError()); return NEXA_CORR_INSUFFICIENT_DATA; }
   ResetLastError();
   int nb = CopyRates(symB, PERIOD_CURRENT, a[0].time, a[na - 1].time, b);
   if(nb < 2) { detail = StringFormat("HISTORY_B_%d_ERR%d", nb, GetLastError()); return NEXA_CORR_INSUFFICIENT_DATA; }
   datetime tA[], tB[];
   double   cA[], cB[];
   if(ArrayResize(tA, na) != na || ArrayResize(cA, na) != na || ArrayResize(tB, nb) != nb || ArrayResize(cB, nb) != nb)
     { detail = "ALLOC"; return NEXA_CORR_INSUFFICIENT_DATA; }
   for(int i = 0; i < na; i++) { tA[i] = a[i].time; cA[i] = a[i].close; }
   for(int i = 0; i < nb; i++) { tB[i] = b[i].time; cB[i] = b[i].close; }
   return NexaCorrelationFromBars(tA, cA, tB, cB, barsBack, InpMaxCorrelation, NEXA_CORR_MIN_ALIGNED_FRAC,
                                  corr, aligned, detail);
  }

bool CorrelationCapOK(string newSymbol, string &reason)
  {
   int total = PositionsTotal();
   for(int i = 0; i < total; i++)
     {
      string psym = PositionGetSymbol(i);
      if(psym == "") { reason = "CORRELATION_POSITION_UNREADABLE"; return false; }   // fail closed
      if(psym == newSymbol) continue;
      double corr = 0.0; int aligned = 0; string detail = "";
      ENUM_NEXA_CORR_STATE st = NexaCorrelationState(newSymbol, psym, InpCorrelationBars, corr, aligned, detail);
      if(st == NEXA_CORR_INSUFFICIENT_DATA)
        { reason = StringFormat("CORRELATION_DATA_INSUFFICIENT_vs_%s_%s", psym, detail); return false; }
      if(st != NEXA_CORR_OK)
        { reason = StringFormat("CORRELATION_BLOCK_vs_%s_%.2f", psym, corr); return false; }
     }
   reason = "CORRELATION_OK";
   return true;
  }

//==================== PORTFOLIO CURRENCY EXPOSURE ====================
void GetSymbolCurrencies(string sym, string &base, string &quote)
  {
   base  = SymbolInfoString(sym, SYMBOL_CURRENCY_BASE);
   quote = SymbolInfoString(sym, SYMBOL_CURRENCY_PROFIT);
  }

// Net exposure in lots for a currency across ALL open positions on the account,
// positive = net long. All positions count -- another strategy's exposure is still
// real exposure for this account.
// Fail-closed (S11, human-approved 2026-10-03): `ok` is false when any open position
// cannot be read completely (symbol, volume or currency spec). Such a position may be
// real exposure, so the caller must block -- never treat it as zero.
double NetCurrencyExposure(string currency, bool &ok)
  {
   ok = true;
   double net = 0;
   int total = PositionsTotal();
   for(int i = 0; i < total; i++)
     {
      string psym = PositionGetSymbol(i);
      if(psym == "") { ok = false; return 0; }
      double vol = PositionGetDouble(POSITION_VOLUME);
      if(!MathIsValidNumber(vol) || vol <= 0) { ok = false; return 0; }
      long ptype = PositionGetInteger(POSITION_TYPE);
      double dir = (ptype == POSITION_TYPE_BUY) ? 1.0 : -1.0;
      string base, quote;
      GetSymbolCurrencies(psym, base, quote);
      if(base == "" || quote == "") { ok = false; return 0; }
      if(base == currency)  net += dir * vol;
      if(quote == currency) net -= dir * vol;
     }
   return net;
  }

bool ExposureCapOK(string sym, int direction, double candidateLots, string &reason)
  {
   string base, quote;
   GetSymbolCurrencies(sym, base, quote);
   double volMin = SymbolInfoDouble(sym, SYMBOL_VOLUME_MIN);
   if(base == "" || quote == "" || volMin <= 0 || InpMaxSameCurrencyNet <= 0) { reason = "EXPOSURE_CAP_INVALID_SPEC"; return false; }
   double capLots = InpMaxSameCurrencyNet * volMin;

   bool okBase, okQuote;
   double baseNet  = NetCurrencyExposure(base, okBase);
   double quoteNet = NetCurrencyExposure(quote, okQuote);
   if(!okBase || !okQuote) { reason = "EXPOSURE_POSITION_UNREADABLE"; return false; }   // fail closed (S11)
   double baseAfter  = baseNet  + direction * candidateLots;
   double quoteAfter = quoteNet - direction * candidateLots;

   if(MathAbs(baseAfter) > capLots || MathAbs(quoteAfter) > capLots)
     { reason = "PORTFOLIO_CURRENCY_EXPOSURE_CAP"; return false; }
   reason = "EXPOSURE_OK";
   return true;
  }

#endif
