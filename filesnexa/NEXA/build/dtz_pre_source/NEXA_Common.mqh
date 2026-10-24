//+------------------------------------------------------------------+
//| NEXA_Common.mqh                                                   |
//| Shared enums, the NexaSignal feature/decision record, and helpers.|
//+------------------------------------------------------------------+
#ifndef NEXA_COMMON_MQH
#define NEXA_COMMON_MQH

string GV(string key) { return "NEXA_" + key; }

//--- Trade DNA schema version. This is a CONTRACT with the research tier: the
//--- Python side refuses to load a journal whose schema_version it does not know.
//--- Bump on ANY column add/remove/rename, and treat older files as legacy.
#define NEXA_DNA_SCHEMA_VERSION "1.0"

//--- Broker server clock offset from GMT, in hours. This is the ONE explicit
//--- timezone assumption in the system. It is NOT inferred: TimeGMT() is not
//--- reliable inside the Strategy Tester, so every session, FOMC and hard-close
//--- decision derives GMT from server time through this single helper. Verify the
//--- value against your broker before trusting any session-dependent behaviour.
input int InpGMTOffset = 2;

datetime NexaGMTNow()              { return TimeCurrent() - (datetime)(InpGMTOffset * 3600); }
datetime NexaToGMT(datetime srv)   { return srv - (datetime)(InpGMTOffset * 3600); }
int      NexaGMTHourOf(datetime srv)
  {
   MqlDateTime dt; TimeToStruct(NexaToGMT(srv), dt);
   return dt.hour;
  }

//--- Finite-number guard for every double that can reach a trading decision.
bool NexaFinite(double v) { return MathIsValidNumber(v); }

enum ENUM_NEXA_REGIME_TREND { NEXA_TREND_UP, NEXA_TREND_DOWN, NEXA_TREND_RANGE, NEXA_TREND_UNKNOWN };
enum ENUM_NEXA_REGIME_VOL   { NEXA_VOL_HIGH, NEXA_VOL_NORMAL, NEXA_VOL_LOW };
enum ENUM_NEXA_BREAKOUT     { NEXA_BREAKOUT_NONE, NEXA_BREAKOUT_TRUE, NEXA_BREAKOUT_FALSE };
enum ENUM_NEXA_BTMM_STAGE   { NEXA_BTMM_ACCUMULATION, NEXA_BTMM_LIQUIDITY_BUILD, NEXA_BTMM_SWEEP,
                               NEXA_BTMM_EXPANSION, NEXA_BTMM_DISTRIBUTION, NEXA_BTMM_UNCLEAR };

// Data-provenance taxonomy. Every stored feature traces to exactly one of these.
// OBSERVED = measured from broker feed/own fills. INFERRED = deterministic derivation.
// MODELLED = output of a model with its own error term. ASSUMED = working premise only.
enum ENUM_NEXA_PROVENANCE { NEXA_OBSERVED, NEXA_INFERRED, NEXA_MODELLED, NEXA_ASSUMED };

//--- Liquidity pool identity. Extendable without touching the state machine.
enum ENUM_NEXA_LEVEL { NEXA_LVL_PDH, NEXA_LVL_PDL, NEXA_LVL_ASIA_HIGH, NEXA_LVL_ASIA_LOW, NEXA_LVL_COUNT };

//--- Sweep lifecycle. A liquidity grab is a MULTI-BAR EVENT, not a bar property.
enum ENUM_NEXA_SWEEP_STATE
  {
   NEXA_SWEEP_IDLE,        // price has not taken the level
   NEXA_SWEEP_BEYOND,      // price is currently trading past the level
   NEXA_SWEEP_RECLAIMED,   // closed back inside -- grab confirmed, awaiting response
   NEXA_SWEEP_CONFIRMED,   // structural response observed (direction now known)
   NEXA_SWEEP_EXPIRED      // no response within the response window
  };

//--- Which way the market resolved AFTER the grab. Never assumed from sweep direction.
enum ENUM_NEXA_SWEEP_RESOLUTION
  {
   NEXA_RESOLVE_NONE,
   NEXA_RESOLVE_REVERSAL,      // structure shifted against the sweep direction
   NEXA_RESOLVE_CONTINUATION   // price pushed on through in the sweep direction
  };

//--- Setup identity: reversal and continuation are different FAMILIES, journaled apart.
enum ENUM_NEXA_SETUP
  {
   NEXA_SETUP_NONE,
   NEXA_SETUP_PDH_REVERSAL,      NEXA_SETUP_PDH_CONTINUATION,
   NEXA_SETUP_PDL_REVERSAL,      NEXA_SETUP_PDL_CONTINUATION,
   NEXA_SETUP_ASIAH_REVERSAL,    NEXA_SETUP_ASIAH_CONTINUATION,
   NEXA_SETUP_ASIAL_REVERSAL,    NEXA_SETUP_ASIAL_CONTINUATION
  };

//--- Live (observed as it happened) vs reconstructed (replayed from history after restart).
enum ENUM_NEXA_STATE_ORIGIN { NEXA_ORIGIN_LIVE, NEXA_ORIGIN_RECONSTRUCTED };

//--- One tracked liquidity pool with its full event history.
struct NexaLiquidityEvent
  {
   ENUM_NEXA_LEVEL          level;
   ENUM_NEXA_SWEEP_STATE    state;
   ENUM_NEXA_SWEEP_RESOLUTION resolution;
   double   levelPrice;
   double   extremeBeyond;      // furthest excursion past the level
   double   excursionATR;       // that excursion, ATR-normalised
   double   wickBodyRatio;      // rejection quality on the sweep bar
   int      barsBeyond;         // how long price held past the level
   int      barsSinceReclaim;   // age of the grab
   int      sweepDirection;     // +1 = took highs (upside liquidity), -1 = took lows
   int      responseDirection;  // +1 bullish structural response, -1 bearish, 0 none
   bool     displacementAfter;
   bool     mssAfter;
   bool     fvgAfter;
   datetime sweepBarTime;
   ENUM_NEXA_SETUP        setup;
   ENUM_NEXA_STATE_ORIGIN origin;
  };

struct NexaSignal
  {
   //--- entry-timeframe structure
   bool     structureBreakUp, structureBreakDown;
   bool     isBOS_up, isBOS_down, isCHoCH_up, isCHoCH_down, isMSS_up, isMSS_down;
   bool     displacementUp, displacementDown;
   double   displacementATR;
   bool     sweepUp, sweepDown;
   bool     fvgBullActive, fvgBearActive;
   double   fvgBullTop, fvgBullBottom, fvgBearTop, fvgBearBottom;
   bool     obBullActive, obBearActive;
   double   obBullHigh, obBullLow, obBearHigh, obBearLow;
   bool     inOTE_up, inOTE_down;
   bool     bprActive;
   double   bprTop, bprBottom;
   double   entrySwingHigh, entrySwingLow;

   //--- MACRO timeframes, read explicitly from completed HTF bars
   ENUM_NEXA_REGIME_TREND trendM5, trendM15, trendH1;
   double   m15SwingHigh, m15SwingLow, h1SwingHigh, h1SwingLow;
   int      htfAlignment;      // +1 H1&M15 up, -1 both down, 0 conflicted

   //--- location / cycle / regime
   double   camR3, camR4, camS3, camS4;
   ENUM_NEXA_BTMM_STAGE   btmmStage;
   ENUM_NEXA_REGIME_TREND trendState;
   ENUM_NEXA_REGIME_VOL   volState;
   ENUM_NEXA_BREAKOUT     breakoutState;
   int      breakoutDirection;  // direction of the break that breakoutState refers to (+1/-1/0)
   bool     regimeTransitioning;
   string   sessionTag;
   double   atrValue, atrM15;

   //--- session structural liquidity (headless -- no chart objects)
   double   asiaHigh, asiaLow, londonHigh, londonLow, nyHigh, nyLow;

   //--- execution context
   double   bid, ask;                  // quote at decision time
   double   spread, spreadATRRatio;

   //--- DECISION TIMESTAMP (schema v1.0, normative).
   //--- The OPEN TIME OF THE CLOSED BAR whose features produced this decision.
   //--- Not wall-clock, not the forming bar. Every causality claim in the dataset
   //--- is anchored here: a feature is legitimate only if computable from data at
   //--- or before this instant.
   datetime decisionBarTime;

   //--- microstructure PROXIES: tick-flow imbalances, INFERRED, never real LOB depth
   double   obiProxy;   // -1..+1 signed tick-flow imbalance over rolling window
   double   cvdProxy;   // cumulative signed tick delta, resets daily

   //--- conditioning
   bool     newsRiskActive;
   int      usdCompositeDirection;   // INFERRED from traded symbols, not DXY

   //--- liquidity event engine (multi-bar state, see NEXA_Liquidity.mqh)
   double   pdh, pdl, pdc;
   bool     liqEventActive;
   ENUM_NEXA_LEVEL          liqLevel;
   ENUM_NEXA_SWEEP_STATE    liqState;
   ENUM_NEXA_SWEEP_RESOLUTION liqResolution;
   double   liqExcursionATR;
   double   liqWickBodyRatio;
   int      liqBarsBeyond;
   int      liqBarsSinceReclaim;
   int      liqSweepDirection;
   int      liqResponseDirection;
   bool     liqDisplacementAfter;
   bool     liqMssAfter;
   bool     liqFvgAfter;
   ENUM_NEXA_SETUP          liqSetup;
   ENUM_NEXA_STATE_ORIGIN   liqOrigin;
   datetime pdSourceBarTime;

   //--- decision outputs
   int      compositeScore;
   int      qualityScore;             // Tier-4 points earned (0..10), journaled
   double   aiScore;          // -1 = model unavailable; never treat as a low score
   double   dynamicTargetR;
   bool     adversarialPass;
   string   adversarialReason;
  };

// NexaSignal holds string members. ZeroMemory() on a struct containing strings or
// dynamic arrays is unsafe in MQL5. Use this instead, everywhere.
void ResetSignal(NexaSignal &s)
  {
   s.structureBreakUp=false; s.structureBreakDown=false;
   s.isBOS_up=false; s.isBOS_down=false; s.isCHoCH_up=false; s.isCHoCH_down=false;
   s.isMSS_up=false; s.isMSS_down=false;
   s.displacementUp=false; s.displacementDown=false; s.displacementATR=0;
   s.sweepUp=false; s.sweepDown=false;
   s.fvgBullActive=false; s.fvgBearActive=false;
   s.fvgBullTop=0; s.fvgBullBottom=0; s.fvgBearTop=0; s.fvgBearBottom=0;
   s.obBullActive=false; s.obBearActive=false;
   s.obBullHigh=0; s.obBullLow=0; s.obBearHigh=0; s.obBearLow=0;
   s.inOTE_up=false; s.inOTE_down=false;
   s.bprActive=false; s.bprTop=0; s.bprBottom=0;
   s.entrySwingHigh=0; s.entrySwingLow=0;
   s.trendM5=NEXA_TREND_UNKNOWN; s.trendM15=NEXA_TREND_UNKNOWN; s.trendH1=NEXA_TREND_UNKNOWN;
   s.m15SwingHigh=0; s.m15SwingLow=0; s.h1SwingHigh=0; s.h1SwingLow=0;
   s.htfAlignment=0;
   s.camR3=0; s.camR4=0; s.camS3=0; s.camS4=0;
   s.btmmStage=NEXA_BTMM_UNCLEAR;
   s.trendState=NEXA_TREND_UNKNOWN;
   s.volState=NEXA_VOL_NORMAL;
   s.breakoutState=NEXA_BREAKOUT_NONE;
   s.breakoutDirection=0;
   s.regimeTransitioning=false;
   s.sessionTag="";
   s.atrValue=0; s.atrM15=0;
   s.asiaHigh=0; s.asiaLow=0; s.londonHigh=0; s.londonLow=0; s.nyHigh=0; s.nyLow=0;
   s.bid=0; s.ask=0; s.spread=0; s.spreadATRRatio=0;
   s.decisionBarTime=0;
   s.obiProxy=0; s.cvdProxy=0;
   s.newsRiskActive=false;
   s.usdCompositeDirection=0;
   s.pdh=0; s.pdl=0; s.pdc=0;
   s.liqEventActive=false;
   s.liqLevel=NEXA_LVL_PDH;
   s.liqState=NEXA_SWEEP_IDLE;
   s.liqResolution=NEXA_RESOLVE_NONE;
   s.liqExcursionATR=0; s.liqWickBodyRatio=0;
   s.liqBarsBeyond=0; s.liqBarsSinceReclaim=0;
   s.liqSweepDirection=0; s.liqResponseDirection=0;
   s.liqDisplacementAfter=false; s.liqMssAfter=false; s.liqFvgAfter=false;
   s.liqSetup=NEXA_SETUP_NONE; s.liqOrigin=NEXA_ORIGIN_LIVE; s.pdSourceBarTime=0;
   s.compositeScore=0;
   s.qualityScore=0;
   s.aiScore=-1;
   s.dynamicTargetR=0;
   s.adversarialPass=false;
   s.adversarialReason="";
  }

#endif
