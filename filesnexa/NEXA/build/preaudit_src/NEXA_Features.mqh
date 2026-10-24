//+------------------------------------------------------------------+
//| NEXA_Features.mqh  -- MTF-explicit, bar-gated, causal              |
//|                                                                    |
//| 1. All structural work runs off CACHED MqlRates arrays refreshed   |
//|    ONCE PER NEW BAR (RefreshMTFCache), never per tick.             |
//| 2. PERIOD_CURRENT appears only as the entry timeframe; M5/M15/H1   |
//|    are cached and analysed independently.                         |
//| 3. Every cache copies from start_pos = 1: the forming bar is never |
//|    present. Swing detection needs `lookback` CLOSED bars on both   |
//|    sides. No future leak by construction.                          |
//| 4. Session levels are attributed by the CLOSED BAR'S timestamp,    |
//|    not by the current clock, and rebuilt causally after restart.   |
//+------------------------------------------------------------------+
#ifndef NEXA_FEATURES_MQH
#define NEXA_FEATURES_MQH
#include "NEXA_Common.mqh"
#include "NEXA_Liquidity.mqh"

input int      InpATRPeriod          = 14;
input int      InpSwingLookback      = 2;
input double   InpDisplacementATRMin = 1.20;
input int      InpSweepLookbackBars  = 20;
input int      InpRegimeATRHistory   = 100;
input double   InpRangeATRRatioMax   = 1.50;
input int      InpMTFCacheBars       = 300;  // bars cached per timeframe
input int      InpReplayBars         = 200;  // bars replayed on init to rebuild event state
input int      InpBreakoutFailWindow = 5;    // bars allowed for a break to fail

//==================== MTF RATE CACHE ====================
MqlRates g_ratesEntry[];
MqlRates g_ratesM5[];
MqlRates g_ratesM15[];
MqlRates g_ratesH1[];

int g_atrHandleEntry = INVALID_HANDLE;
int g_atrHandleM15   = INVALID_HANDLE;

//==================== SESSION STRUCTURE (headless) ====================
double g_asiaHigh=0, g_asiaLow=0, g_londonHigh=0, g_londonLow=0, g_nyHigh=0, g_nyLow=0;
int    g_lastGmtHour = -1;

//==================== BREAKOUT EVENT MEMORY ====================
double   g_brkLevel     = 0;
int      g_brkDirection = 0;      // +1 up, -1 down
int      g_brkBarsAgo   = 0;

//==================== CACHE ====================
// start_pos = 1 everywhere: the forming bar is excluded from every cache.
// Every Copy* return is validated against the count actually needed.
bool RefreshMTFCache()
  {
   int need = InpSwingLookback * 2 + 10;

   int a = CopyRates(_Symbol, PERIOD_CURRENT, 1, InpMTFCacheBars, g_ratesEntry);
   int b = CopyRates(_Symbol, PERIOD_M5,      1, InpMTFCacheBars, g_ratesM5);
   int c = CopyRates(_Symbol, PERIOD_M15,     1, InpMTFCacheBars, g_ratesM15);
   int d = CopyRates(_Symbol, PERIOD_H1,      1, InpMTFCacheBars, g_ratesH1);

   if(a < need || b < need || c < need || d < need) return false;

   // The series flag persists across reallocation but is re-asserted so that a
   // partial init or a future array added without its init line cannot silently
   // invert indexing.
   ArraySetAsSeries(g_ratesEntry, true);
   ArraySetAsSeries(g_ratesM5,    true);
   ArraySetAsSeries(g_ratesM15,   true);
   ArraySetAsSeries(g_ratesH1,    true);

   return (ArraySize(g_ratesEntry) >= need && ArraySize(g_ratesM5) >= need &&
           ArraySize(g_ratesM15) >= need && ArraySize(g_ratesH1) >= need);
  }

//==================== ARRAY-BASED CAUSAL SWING DETECTION ====================
bool IsSwingHighArr(const MqlRates &r[], int idx, int lookback)
  {
   int n = ArraySize(r);
   if(lookback < 1) return false;
   if(idx - lookback < 0 || idx + lookback >= n) return false;
   double h = r[idx].high;
   for(int i = 1; i <= lookback; i++)
     {
      if(r[idx - i].high >= h) return false;
      if(r[idx + i].high >= h) return false;
     }
   return true;
  }

bool IsSwingLowArr(const MqlRates &r[], int idx, int lookback)
  {
   int n = ArraySize(r);
   if(lookback < 1) return false;
   if(idx - lookback < 0 || idx + lookback >= n) return false;
   double l = r[idx].low;
   for(int i = 1; i <= lookback; i++)
     {
      if(r[idx - i].low <= l) return false;
      if(r[idx + i].low <= l) return false;
     }
   return true;
  }

double LastSwingHighArr(const MqlRates &r[], int startIdx, int maxBars, int &foundIdx)
  {
   foundIdx = -1;
   int n = ArraySize(r);
   if(n <= 0 || startIdx < 0) return 0.0;
   int limit = MathMin(startIdx + maxBars, n - InpSwingLookback - 1);
   for(int s = startIdx; s < limit; s++)
      if(IsSwingHighArr(r, s, InpSwingLookback)) { foundIdx = s; return r[s].high; }
   return 0.0;
  }

double LastSwingLowArr(const MqlRates &r[], int startIdx, int maxBars, int &foundIdx)
  {
   foundIdx = -1;
   int n = ArraySize(r);
   if(n <= 0 || startIdx < 0) return 0.0;
   int limit = MathMin(startIdx + maxBars, n - InpSwingLookback - 1);
   for(int s = startIdx; s < limit; s++)
      if(IsSwingLowArr(r, s, InpSwingLookback)) { foundIdx = s; return r[s].low; }
   return 0.0;
  }

//==================== HTF BIAS ====================
ENUM_NEXA_REGIME_TREND SwingTrendArr(const MqlRates &r[])
  {
   int hi1, lo1, hi2, lo2;
   double h1 = LastSwingHighArr(r, InpSwingLookback, 80, hi1);
   double l1 = LastSwingLowArr (r, InpSwingLookback, 80, lo1);
   if(hi1 < 0 || lo1 < 0) return NEXA_TREND_UNKNOWN;
   double h2 = LastSwingHighArr(r, hi1 + 1, 80, hi2);
   double l2 = LastSwingLowArr (r, lo1 + 1, 80, lo2);
   if(hi2 < 0 || lo2 < 0) return NEXA_TREND_UNKNOWN;
   if(h1 > h2 && l1 > l2) return NEXA_TREND_UP;
   if(h1 < h2 && l1 < l2) return NEXA_TREND_DOWN;
   return NEXA_TREND_RANGE;
  }

//==================== SESSION ====================
string SessionTag()
  {
   int g = NexaGMTHourOf(TimeCurrent());
   if(g >= 0  && g < 7)  return "ASIA";
   if(g >= 7  && g < 12) return "LONDON";
   if(g >= 12 && g < 16) return "OVERLAP";
   if(g >= 16 && g < 21) return "NY";
   return "LATE";
  }

//--- Causal session extremes. `barTime` is the CLOSED bar's own timestamp, so the
//--- bar is attributed to the session it actually traded in, not to whatever
//--- session the clock has since moved into.
void UpdateSessionLevels(datetime barTime, double barHigh, double barLow)
  {
   int g = NexaGMTHourOf(barTime);

   if(g == 0  && g_lastGmtHour != 0)  { g_asiaHigh = barHigh;   g_asiaLow = barLow;   }
   if(g == 7  && g_lastGmtHour != 7)  { g_londonHigh = barHigh; g_londonLow = barLow; }
   if(g == 13 && g_lastGmtHour != 13) { g_nyHigh = barHigh;     g_nyLow = barLow;     }

   if(g >= 0  && g < 9)  { g_asiaHigh   = MathMax(g_asiaHigh, barHigh);   g_asiaLow   = (g_asiaLow  ==0)? barLow : MathMin(g_asiaLow,   barLow); }
   if(g >= 7  && g < 16) { g_londonHigh = MathMax(g_londonHigh, barHigh); g_londonLow = (g_londonLow==0)? barLow : MathMin(g_londonLow, barLow); }
   if(g >= 13 && g < 22) { g_nyHigh     = MathMax(g_nyHigh, barHigh);     g_nyLow     = (g_nyLow    ==0)? barLow : MathMin(g_nyLow,     barLow); }

   g_lastGmtHour = g;
  }

//--- Rebuild today's session extremes from closed M1 bars. Running max/min over
//--- completed bars is exact and causal AS OF NOW; it is used only to seed the
//--- live state, never to evaluate an earlier bar (that path is the causal replay
//--- in ReconstructLiquidityState, which accumulates incrementally).
void ReconstructSessionLevels()
  {
   MqlRates m1[];
   ArraySetAsSeries(m1, true);
   int copied = CopyRates(_Symbol, PERIOD_M1, 1, 1500, m1);
   if(copied < 10 || ArraySize(m1) < 10)
     { Print("NEXA session: insufficient M1 history to reconstruct (", copied, ")"); return; }

   g_asiaHigh = 0; g_asiaLow = 0; g_londonHigh = 0; g_londonLow = 0; g_nyHigh = 0; g_nyLow = 0;

   MqlDateTime nowG; TimeToStruct(NexaGMTNow(), nowG);
   int todayKey = nowG.year * 10000 + nowG.mon * 100 + nowG.day;

   int n = MathMin(copied, ArraySize(m1));
   for(int i = n - 1; i >= 0; i--)
     {
      MqlDateTime bg; TimeToStruct(NexaToGMT(m1[i].time), bg);
      int barKey = bg.year * 10000 + bg.mon * 100 + bg.day;
      if(barKey != todayKey) continue;
      int g = bg.hour;

      if(g >= 0 && g < 9)
        { g_asiaHigh = MathMax(g_asiaHigh, m1[i].high);   g_asiaLow   = (g_asiaLow==0)?   m1[i].low : MathMin(g_asiaLow,   m1[i].low); }
      if(g >= 7 && g < 16)
        { g_londonHigh = MathMax(g_londonHigh, m1[i].high); g_londonLow = (g_londonLow==0)? m1[i].low : MathMin(g_londonLow, m1[i].low); }
      if(g >= 13 && g < 22)
        { g_nyHigh = MathMax(g_nyHigh, m1[i].high);       g_nyLow     = (g_nyLow==0)?     m1[i].low : MathMin(g_nyLow,     m1[i].low); }
      g_lastGmtHour = g;
     }
  }

//==================== ATR / REGIME ====================
double GetATR(int handle)
  {
   if(handle == INVALID_HANDLE) return 0.0;
   double buf[];
   int copied = CopyBuffer(handle, 0, 1, 1, buf);
   if(copied < 1 || ArraySize(buf) < 1) return 0.0;
   double v = buf[0];
   return (NexaFinite(v) && v > 0) ? v : 0.0;
  }

ENUM_NEXA_REGIME_VOL VolRegime(int handle, double atrNow)
  {
   if(handle == INVALID_HANDLE || atrNow <= 0 || InpRegimeATRHistory < 1) return NEXA_VOL_NORMAL;
   double buf[];
   int n = CopyBuffer(handle, 0, 1, InpRegimeATRHistory, buf);
   if(n <= 0 || ArraySize(buf) < n) return NEXA_VOL_NORMAL;
   double sum = 0; int cnt = 0;
   for(int i = 0; i < n; i++) { if(NexaFinite(buf[i]) && buf[i] > 0) { sum += buf[i]; cnt++; } }
   if(cnt <= 0) return NEXA_VOL_NORMAL;
   double avg = sum / cnt;
   if(avg <= 0) return NEXA_VOL_NORMAL;
   double ratio = atrNow / avg;
   if(ratio > 1.30) return NEXA_VOL_HIGH;
   if(ratio < 0.70) return NEXA_VOL_LOW;
   return NEXA_VOL_NORMAL;
  }

ENUM_NEXA_REGIME_TREND RangeVsTrendArr(const MqlRates &r[], double atrNow, int lookbackBars)
  {
   int n = ArraySize(r);
   if(atrNow <= 0 || lookbackBars < 2 || n < lookbackBars) return NEXA_TREND_UNKNOWN;
   double hh = r[0].high, ll = r[0].low;
   for(int i = 0; i < lookbackBars; i++)
     {
      if(r[i].high > hh) hh = r[i].high;
      if(r[i].low  < ll) ll = r[i].low;
     }
   if((hh - ll) / atrNow <= InpRangeATRRatioMax) return NEXA_TREND_RANGE;
   return (r[0].close > r[lookbackBars - 1].close) ? NEXA_TREND_UP : NEXA_TREND_DOWN;
  }

//==================== SMC / ICT PRIMITIVES (array-based) ====================
void DetectFVGArr(const MqlRates &r[], bool &bullA, double &bullT, double &bullB,
                   bool &bearA, double &bearT, double &bearB)
  {
   bullA = false; bearA = false; bullT = 0; bullB = 0; bearT = 0; bearB = 0;
   if(ArraySize(r) < 3) return;
   double highA = r[2].high, lowA = r[2].low;
   double highC = r[0].high, lowC = r[0].low;
   bullA = (highA < lowC);
   if(bullA) { bullB = highA; bullT = lowC; }
   bearA = (lowA > highC);
   if(bearA) { bearT = lowA; bearB = highC; }
  }

void DetectOrderBlockArr(const MqlRates &r[], bool brkUp, bool brkDn,
                          bool &obBullA, double &obBullH, double &obBullL,
                          bool &obBearA, double &obBearH, double &obBearL)
  {
   obBullA = false; obBearA = false; obBullH = 0; obBullL = 0; obBearH = 0; obBearL = 0;
   int n = ArraySize(r);
   int lim = MathMin(10, n);
   if(brkUp)
      for(int s = 1; s < lim; s++)
         if(r[s].close < r[s].open) { obBullA = true; obBullH = r[s].high; obBullL = r[s].low; break; }
   if(brkDn)
      for(int s = 1; s < lim; s++)
         if(r[s].close > r[s].open) { obBearA = true; obBearH = r[s].high; obBearL = r[s].low; break; }
  }

void DetectOTEArr(const MqlRates &r[], bool dispUp, bool dispDn, bool &oteUp, bool &oteDn)
  {
   oteUp = false; oteDn = false;
   if(ArraySize(r) < 1) return;
   double cur = r[0].close;
   int idx;
   if(dispUp)
     {
      double legStart = LastSwingLowArr(r, InpSwingLookback, 40, idx);
      double legEnd   = r[0].high;
      if(legStart > 0 && legEnd > legStart)
        {
         double f618 = legEnd - (legEnd - legStart) * 0.618;
         double f79  = legEnd - (legEnd - legStart) * 0.79;
         oteUp = (cur <= f618 && cur >= f79);
        }
     }
   if(dispDn)
     {
      double legStart = LastSwingHighArr(r, InpSwingLookback, 40, idx);
      double legEnd   = r[0].low;
      if(legStart > 0 && legStart > legEnd)
        {
         double f618 = legEnd + (legStart - legEnd) * 0.618;
         double f79  = legEnd + (legStart - legEnd) * 0.79;
         oteDn = (cur >= f618 && cur <= f79);
        }
     }
  }

//--- Camarilla from the previous COMPLETED D1 bar (shift 1) -- never the forming day.
void CalcCamarilla(double &r3, double &r4, double &s3, double &s4)
  {
   r3 = r4 = s3 = s4 = 0;
   MqlRates d[];
   ArraySetAsSeries(d, true);
   int copied = CopyRates(_Symbol, PERIOD_D1, 1, 1, d);
   if(copied < 1 || ArraySize(d) < 1) return;
   double range = d[0].high - d[0].low, C = d[0].close;
   if(range < 0 || C <= 0) return;
   r3 = C + range * 1.1 / 4.0; r4 = C + range * 1.1 / 2.0;
   s3 = C - range * 1.1 / 4.0; s4 = C - range * 1.1 / 2.0;
  }

ENUM_NEXA_BTMM_STAGE ClassifyBTMM(ENUM_NEXA_REGIME_TREND t, ENUM_NEXA_REGIME_VOL v,
                                   bool swU, bool swD, bool dU, bool dD, bool bU, bool bD)
  {
   if(t == NEXA_TREND_RANGE && v == NEXA_VOL_LOW)    return NEXA_BTMM_ACCUMULATION;
   if(t == NEXA_TREND_RANGE && v == NEXA_VOL_NORMAL) return NEXA_BTMM_LIQUIDITY_BUILD;
   if((dU || dD) && (swU || swD))                     return NEXA_BTMM_EXPANSION;
   if(swU || swD)                                      return NEXA_BTMM_SWEEP;
   if((bU || bD) && v == NEXA_VOL_HIGH)                return NEXA_BTMM_DISTRIBUTION;
   return NEXA_BTMM_UNCLEAR;
  }

//==================== BREAKOUT CLASSIFICATION (event-based) ====================
// A false breakout is a two-stage event -- break, THEN close back through the
// level -- so it requires memory of the break bar. `outDirection` reports the
// direction of the break the returned state refers to, so a consumer can tell
// "an UPSIDE break just failed" apart from "a DOWNSIDE break just failed". That
// distinction is what lets a failed upside break confirm a reversal short instead
// of vetoing it.
ENUM_NEXA_BREAKOUT ClassifyBreakout(bool brkUp, bool brkDown,
                                     double swingHigh, double swingLow, double closeNow,
                                     int &outDirection)
  {
   outDirection = 0;
   if(brkUp && swingHigh > 0)
     { g_brkLevel = swingHigh; g_brkDirection =  1; g_brkBarsAgo = 0; outDirection =  1; return NEXA_BREAKOUT_TRUE; }
   if(brkDown && swingLow > 0)
     { g_brkLevel = swingLow;  g_brkDirection = -1; g_brkBarsAgo = 0; outDirection = -1; return NEXA_BREAKOUT_TRUE; }

   if(g_brkDirection != 0 && g_brkLevel > 0)
     {
      g_brkBarsAgo++;
      bool failed = (g_brkDirection > 0) ? (closeNow < g_brkLevel) : (closeNow > g_brkLevel);
      if(failed)
        {
         outDirection = g_brkDirection;
         g_brkDirection = 0; g_brkLevel = 0; g_brkBarsAgo = 0;
         return NEXA_BREAKOUT_FALSE;
        }
      if(g_brkBarsAgo > InpBreakoutFailWindow)
        { g_brkDirection = 0; g_brkLevel = 0; g_brkBarsAgo = 0; }
      else
        { outDirection = g_brkDirection; return NEXA_BREAKOUT_TRUE; }
     }
   return NEXA_BREAKOUT_NONE;
  }

//+------------------------------------------------------------------+
//| BuildFeatures -- CALL ONCE PER NEW BAR ONLY. Never on every tick. |
//+------------------------------------------------------------------+
bool BuildFeatures(NexaSignal &sig)
  {
   if(!RefreshMTFCache()) return false;
   if(ArraySize(g_ratesEntry) < 3) return false;

   double atrNow = GetATR(g_atrHandleEntry);
   double atrM15 = GetATR(g_atrHandleM15);
   if(atrNow <= 0) return false;

   //--- Anchor the decision to the CLOSED bar that produced these features.
   //--- g_ratesEntry is copied from start_pos=1, so index 0 is the newest CLOSED
   //--- bar -- never the forming one.
   sig.decisionBarTime = g_ratesEntry[0].time;
   sig.atrValue    = atrNow;
   sig.atrM15      = atrM15;
   sig.sessionTag  = SessionTag();
   double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   if(ask <= 0 || bid <= 0 || ask < bid) return false;
   sig.bid         = bid;
   sig.ask         = ask;
   sig.spread      = ask - bid;
   sig.spreadATRRatio = sig.spread / atrNow;
   if(!NexaFinite(sig.spreadATRRatio)) return false;

   //--- entry-timeframe structure
   int hiIdx, loIdx;
   double lastSwingHigh = LastSwingHighArr(g_ratesEntry, InpSwingLookback, 60, hiIdx);
   double lastSwingLow  = LastSwingLowArr (g_ratesEntry, InpSwingLookback, 60, loIdx);
   double lastClose     = g_ratesEntry[0].close;

   sig.entrySwingHigh = lastSwingHigh;
   sig.entrySwingLow  = lastSwingLow;

   sig.structureBreakUp   = (lastSwingHigh > 0 && lastClose > lastSwingHigh);
   sig.structureBreakDown = (lastSwingLow  > 0 && lastClose < lastSwingLow);

   ENUM_NEXA_REGIME_TREND priorTrend = SwingTrendArr(g_ratesEntry);
   sig.isBOS_up     = sig.structureBreakUp   && (priorTrend == NEXA_TREND_UP);
   sig.isBOS_down   = sig.structureBreakDown && (priorTrend == NEXA_TREND_DOWN);
   sig.isCHoCH_up   = sig.structureBreakUp   && (priorTrend != NEXA_TREND_UP);
   sig.isCHoCH_down = sig.structureBreakDown && (priorTrend != NEXA_TREND_DOWN);

   double body = MathAbs(g_ratesEntry[0].close - g_ratesEntry[0].open);
   double dispRatio = body / atrNow;
   bool bull = g_ratesEntry[0].close > g_ratesEntry[0].open;
   sig.displacementUp   = (dispRatio >= InpDisplacementATRMin &&  bull);
   sig.displacementDown = (dispRatio >= InpDisplacementATRMin && !bull);
   sig.displacementATR  = dispRatio;

   sig.isMSS_up   = sig.isCHoCH_up   && sig.displacementUp;
   sig.isMSS_down = sig.isCHoCH_down && sig.displacementDown;

   int sIdx;
   double sweepRefHigh = LastSwingHighArr(g_ratesEntry, InpSwingLookback, InpSweepLookbackBars, sIdx);
   double sweepRefLow  = LastSwingLowArr (g_ratesEntry, InpSwingLookback, InpSweepLookbackBars, sIdx);
   sig.sweepDown = (sweepRefHigh > 0 && g_ratesEntry[0].high > sweepRefHigh && lastClose < sweepRefHigh);
   sig.sweepUp   = (sweepRefLow  > 0 && g_ratesEntry[0].low  < sweepRefLow  && lastClose > sweepRefLow);

   DetectFVGArr(g_ratesEntry, sig.fvgBullActive, sig.fvgBullTop, sig.fvgBullBottom,
                 sig.fvgBearActive, sig.fvgBearTop, sig.fvgBearBottom);
   DetectOrderBlockArr(g_ratesEntry, sig.structureBreakUp, sig.structureBreakDown,
                        sig.obBullActive, sig.obBullHigh, sig.obBullLow,
                        sig.obBearActive, sig.obBearHigh, sig.obBearLow);
   DetectOTEArr(g_ratesEntry, sig.displacementUp, sig.displacementDown, sig.inOTE_up, sig.inOTE_down);

   sig.bprActive = sig.fvgBullActive && sig.fvgBearActive &&
                    !(sig.fvgBullTop < sig.fvgBearBottom || sig.fvgBearTop < sig.fvgBullBottom);
   if(sig.bprActive)
     {
      sig.bprTop    = MathMin(sig.fvgBullTop, sig.fvgBearTop);
      sig.bprBottom = MathMax(sig.fvgBullBottom, sig.fvgBearBottom);
     }

   //--- MACRO: completed M5 / M15 / H1 bars only (cache start_pos = 1)
   sig.trendM5  = SwingTrendArr(g_ratesM5);
   sig.trendM15 = SwingTrendArr(g_ratesM15);
   sig.trendH1  = SwingTrendArr(g_ratesH1);

   int m15hi, m15lo, h1hi, h1lo;
   sig.m15SwingHigh = LastSwingHighArr(g_ratesM15, InpSwingLookback, 60, m15hi);
   sig.m15SwingLow  = LastSwingLowArr (g_ratesM15, InpSwingLookback, 60, m15lo);
   sig.h1SwingHigh  = LastSwingHighArr(g_ratesH1,  InpSwingLookback, 60, h1hi);
   sig.h1SwingLow   = LastSwingLowArr (g_ratesH1,  InpSwingLookback, 60, h1lo);

   if(sig.trendH1 == NEXA_TREND_UP   && sig.trendM15 == NEXA_TREND_UP)   sig.htfAlignment =  1;
   else if(sig.trendH1 == NEXA_TREND_DOWN && sig.trendM15 == NEXA_TREND_DOWN) sig.htfAlignment = -1;
   else sig.htfAlignment = 0;

   CalcCamarilla(sig.camR3, sig.camR4, sig.camS3, sig.camS4);

   //--- session levels attributed by the closed bar's own timestamp (causal)
   UpdateSessionLevels(g_ratesEntry[0].time, g_ratesEntry[0].high, g_ratesEntry[0].low);
   sig.asiaHigh = g_asiaHigh; sig.asiaLow = g_asiaLow;
   sig.londonHigh = g_londonHigh; sig.londonLow = g_londonLow;
   sig.nyHigh = g_nyHigh; sig.nyLow = g_nyLow;

   sig.volState   = VolRegime(g_atrHandleEntry, atrNow);
   sig.trendState = (priorTrend == NEXA_TREND_UNKNOWN)
                     ? RangeVsTrendArr(g_ratesEntry, atrNow, 30) : priorTrend;

   sig.breakoutState = ClassifyBreakout(sig.structureBreakUp, sig.structureBreakDown,
                                        lastSwingHigh, lastSwingLow, lastClose, sig.breakoutDirection);

   sig.btmmStage = ClassifyBTMM(sig.trendState, sig.volState, sig.sweepUp, sig.sweepDown,
                                 sig.displacementUp, sig.displacementDown,
                                 sig.structureBreakUp, sig.structureBreakDown);

   //--- LIQUIDITY EVENT ENGINE: advance each pool by this one closed bar, using the
   //--- previous day as it stood AT THIS BAR'S TIME (not at the current clock).
   double pdh, pdl, pdc; datetime pdSrc;
   GetPreviousDayLevelsAsOf(g_ratesEntry[0].time, pdh, pdl, pdc, pdSrc);
   sig.pdh = pdh; sig.pdl = pdl; sig.pdc = pdc; sig.pdSourceBarTime = pdSrc;

   double lvlPrice[NEXA_LVL_COUNT];
   lvlPrice[NEXA_LVL_PDH]        = pdh;
   lvlPrice[NEXA_LVL_PDL]        = pdl;
   lvlPrice[NEXA_LVL_ASIA_HIGH]  = g_asiaHigh;
   lvlPrice[NEXA_LVL_ASIA_LOW]   = g_asiaLow;

   // Feed this closed bar exactly once (the replay may already have consumed it).
   if(Liquidity_ShouldProcessBar(g_ratesEntry[0].time))
      for(int L = 0; L < NEXA_LVL_COUNT; L++)
         AdvanceLevelState(L, lvlPrice[L], atrNow,
                           g_ratesEntry[0].high, g_ratesEntry[0].low,
                           g_ratesEntry[0].open, g_ratesEntry[0].close,
                           g_ratesEntry[0].time,
                           sig.displacementUp, sig.displacementDown,
                           sig.isMSS_up, sig.isMSS_down,
                           sig.fvgBullActive, sig.fvgBearActive);

   int primary = SelectPrimaryEvent();
   if(primary >= 0 && primary < NEXA_LVL_COUNT)
     {
      sig.liqEventActive       = (g_liqEvents[primary].state == NEXA_SWEEP_CONFIRMED);
      sig.liqLevel             = g_liqEvents[primary].level;
      sig.liqState             = g_liqEvents[primary].state;
      sig.liqResolution        = g_liqEvents[primary].resolution;
      sig.liqExcursionATR      = g_liqEvents[primary].excursionATR;
      sig.liqWickBodyRatio     = g_liqEvents[primary].wickBodyRatio;
      sig.liqBarsBeyond        = g_liqEvents[primary].barsBeyond;
      sig.liqBarsSinceReclaim  = g_liqEvents[primary].barsSinceReclaim;
      sig.liqSweepDirection    = g_liqEvents[primary].sweepDirection;
      sig.liqResponseDirection = g_liqEvents[primary].responseDirection;
      sig.liqDisplacementAfter = g_liqEvents[primary].displacementAfter;
      sig.liqMssAfter          = g_liqEvents[primary].mssAfter;
      sig.liqFvgAfter          = g_liqEvents[primary].fvgAfter;
      sig.liqSetup             = g_liqEvents[primary].setup;
      sig.liqOrigin            = g_liqEvents[primary].origin;
     }

   string gvKey = GV("LastTrend_" + _Symbol);
   double lastTrendVal = GlobalVariableCheck(gvKey) ? GlobalVariableGet(gvKey) : -1;
   sig.regimeTransitioning = (lastTrendVal >= 0 && (int)lastTrendVal != (int)sig.trendState);
   GlobalVariableSet(gvKey, (double)sig.trendState);

   return true;
  }

//==================== INIT / DEINIT (defined last: every dependency is above) ====================
bool Features_Init()
  {
   ArraySetAsSeries(g_ratesEntry, true);
   ArraySetAsSeries(g_ratesM5,    true);
   ArraySetAsSeries(g_ratesM15,   true);
   ArraySetAsSeries(g_ratesH1,    true);

   g_atrHandleEntry = iATR(_Symbol, PERIOD_CURRENT, InpATRPeriod);
   g_atrHandleM15   = iATR(_Symbol, PERIOD_M15,     InpATRPeriod);
   if(g_atrHandleEntry == INVALID_HANDLE || g_atrHandleM15 == INVALID_HANDLE) return false;

   g_brkLevel = 0; g_brkDirection = 0; g_brkBarsAgo = 0;

   // Seed London/NY (and a provisional Asia) from closed M1 history as of now.
   ReconstructSessionLevels();

   // Causal replay of the liquidity machine. It computes its OWN incremental Asia
   // range per replayed bar and hands back the running value as of the last bar,
   // which becomes the live Asia state so replay and live agree on the same level.
   if(RefreshMTFCache())
     {
      double atr0 = GetATR(g_atrHandleEntry);
      if(atr0 > 0)
        {
         double replayAsiaH = 0, replayAsiaL = 0; bool asiaComplete = false;
         ReconstructLiquidityState(g_ratesEntry, atr0, InpDisplacementATRMin,
                                    InpReplayBars, replayAsiaH, replayAsiaL, asiaComplete);
         // Adopt the replay's Asia range only if the replay observed the session start.
         // A partial range (replay began mid-Asia) is causal for the bars it covered but
         // must not overwrite the complete M1-derived value used going forward.
         if(asiaComplete && replayAsiaH > 0 && replayAsiaL > 0) { g_asiaHigh = replayAsiaH; g_asiaLow = replayAsiaL; }
        }
     }
   else
     Liquidity_Init();   // no history yet: start clean rather than half-built
   return true;
  }

void Features_Deinit()
  {
   if(g_atrHandleEntry != INVALID_HANDLE) { IndicatorRelease(g_atrHandleEntry); g_atrHandleEntry = INVALID_HANDLE; }
   if(g_atrHandleM15   != INVALID_HANDLE) { IndicatorRelease(g_atrHandleM15);   g_atrHandleM15   = INVALID_HANDLE; }
  }

#endif
