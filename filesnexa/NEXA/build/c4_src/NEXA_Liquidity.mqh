//+------------------------------------------------------------------+
//| NEXA_Liquidity.mqh                                                |
//| Previous-Day High/Low liquidity sweep engine with EVENT MEMORY.    |
//+------------------------------------------------------------------+
//| WHY A STATE MACHINE AND NOT A FEATURE:                             |
//| Every other feature in NEXA is a property of the current bar. A     |
//| liquidity grab is not. It unfolds across bars:                     |
//|   price exceeds PDH -> holds beyond N bars -> closes back inside   |
//|   -> structure responds -> entry opportunity                       |
//| Each is a separate bar and the decision depends on the sequence,   |
//| so this module carries explicit per-level state forward in time.   |
//|                                                                    |
//| DIRECTION IS NOT ASSUMED. "PDH swept" does not mean SELL. The       |
//| engine observes the structural response after the reclaim and     |
//| labels the event REVERSAL or CONTINUATION accordingly.             |
//|                                                                    |
//| NO LOOKAHEAD: evaluation runs on CLOSED bars only, and the machine |
//| only advances forward. It never re-reads a later bar to            |
//| reinterpret an earlier one.                                        |
//|                                                                    |
//| PERSISTENCE: in-memory state is lost on restart/recompile. It is   |
//| rebuilt by ReconstructLiquidityState(), which replays the machine  |
//| over closed history CAUSALLY: every replayed bar sees only the     |
//| PDH/PDL and session levels that existed AT THAT BAR'S TIME, never  |
//| the final values. Reconstructed events are tagged INFERRED.        |
//+------------------------------------------------------------------+
#ifndef NEXA_LIQUIDITY_MQH
#define NEXA_LIQUIDITY_MQH
#include "NEXA_Common.mqh"

input double InpMinSweepExcursionATR = 0.10;  // minimum excursion past the level to count as a sweep
input double InpMaxSweepExcursionATR = 2.50;  // beyond this it is a breakout, not a grab
input int    InpMaxBarsBeyond        = 6;     // held past the level longer than this -> acceptance
input int    InpResponseWindowBars   = 8;     // bars allowed after reclaim for a structural response
input int    InpEventValidBars       = 12;    // how long a CONFIRMED event stays tradeable
input double InpMinRejectionWickBody = 1.00;  // wick/body on the sweep bar for a clean rejection

NexaLiquidityEvent g_liqEvents[NEXA_LVL_COUNT];
datetime           g_liqLastBarFed = 0;   // time of the last closed bar fed to the machine

// The machine must see each closed bar EXACTLY ONCE. The replay walks through
// index 0 (the newest closed bar); the first live BuildFeatures after init would
// otherwise feed that same bar again and double-count barsBeyond/barsSinceReclaim.
bool Liquidity_ShouldProcessBar(datetime barTime)
  {
   if(barTime <= g_liqLastBarFed) return false;
   g_liqLastBarFed = barTime;
   return true;
  }

void Liquidity_Init()
  {
   g_liqLastBarFed = 0;
   for(int i = 0; i < NEXA_LVL_COUNT; i++)
     {
      g_liqEvents[i].level              = (ENUM_NEXA_LEVEL)i;
      g_liqEvents[i].state              = NEXA_SWEEP_IDLE;
      g_liqEvents[i].resolution         = NEXA_RESOLVE_NONE;
      g_liqEvents[i].levelPrice         = 0;
      g_liqEvents[i].extremeBeyond      = 0;
      g_liqEvents[i].excursionATR       = 0;
      g_liqEvents[i].wickBodyRatio      = 0;
      g_liqEvents[i].barsBeyond         = 0;
      g_liqEvents[i].barsSinceReclaim   = 0;
      g_liqEvents[i].sweepDirection     = 0;
      g_liqEvents[i].responseDirection  = 0;
      g_liqEvents[i].displacementAfter  = false;
      g_liqEvents[i].mssAfter           = false;
      g_liqEvents[i].fvgAfter           = false;
      g_liqEvents[i].sweepBarTime       = 0;
      g_liqEvents[i].setup              = NEXA_SETUP_NONE;
      g_liqEvents[i].origin             = NEXA_ORIGIN_LIVE;
     }
  }

//+------------------------------------------------------------------+
//| NEXA PREVIOUS DAY -- EXPLICIT DEFINITION                          |
//| "Previous day" = the D1 bar that had COMPLETED as of the reference |
//| time, on the execution broker's server clock. Broker-relative by   |
//| construction: two brokers with different daily rollovers produce   |
//| different PDH/PDL for the same calendar date. The source bar's     |
//| timestamp is recorded on every signal so this can be audited.      |
//|                                                                    |
//| The `asOf` parameter makes this CAUSAL for replay: for a bar at    |
//| time T, the previous day is the last D1 bar whose CLOSE precedes   |
//| T's daily boundary -- never today's still-forming D1 bar.          |
//+------------------------------------------------------------------+
bool GetPreviousDayLevelsAsOf(datetime asOf, double &pdh, double &pdl, double &pdc, datetime &srcBarTime)
  {
   pdh = pdl = pdc = 0; srcBarTime = 0;
   // D1 bar containing asOf is index 0 relative to asOf; the completed previous day is index 1.
   int idxNow = iBarShift(_Symbol, PERIOD_D1, asOf, false);
   if(idxNow < 0) return false;
   int idxPrev = idxNow + 1;
   MqlRates d[];
   ArraySetAsSeries(d, true);
   int copied = CopyRates(_Symbol, PERIOD_D1, idxPrev, 1, d);
   if(copied < 1) return false;
   if(ArraySize(d) < 1) return false;
   pdh = d[0].high; pdl = d[0].low; pdc = d[0].close; srcBarTime = d[0].time;
   return (pdh > 0 && pdl > 0 && pdh >= pdl);
  }

//--- Live convenience: previous completed D1 bar relative to now.
bool GetPreviousDayLevels(double &pdh, double &pdl, double &pdc, datetime &srcBarTime)
  {
   return GetPreviousDayLevelsAsOf(TimeCurrent(), pdh, pdl, pdc, srcBarTime);
  }

//--- Map a resolved event onto its explicit setup family.
ENUM_NEXA_SETUP SetupIdentity(ENUM_NEXA_LEVEL lvl, ENUM_NEXA_SWEEP_RESOLUTION res)
  {
   if(res == NEXA_RESOLVE_NONE) return NEXA_SETUP_NONE;
   bool rev = (res == NEXA_RESOLVE_REVERSAL);
   switch(lvl)
     {
      case NEXA_LVL_PDH:       return rev ? NEXA_SETUP_PDH_REVERSAL   : NEXA_SETUP_PDH_CONTINUATION;
      case NEXA_LVL_PDL:       return rev ? NEXA_SETUP_PDL_REVERSAL   : NEXA_SETUP_PDL_CONTINUATION;
      case NEXA_LVL_ASIA_HIGH: return rev ? NEXA_SETUP_ASIAH_REVERSAL : NEXA_SETUP_ASIAH_CONTINUATION;
      case NEXA_LVL_ASIA_LOW:  return rev ? NEXA_SETUP_ASIAL_REVERSAL : NEXA_SETUP_ASIAL_CONTINUATION;
      default: break;
     }
   return NEXA_SETUP_NONE;
  }

//--- Is this level an UPSIDE pool (taken by trading up through it) or downside?
int LevelPolarity(ENUM_NEXA_LEVEL lvl)
  {
   if(lvl == NEXA_LVL_PDH || lvl == NEXA_LVL_ASIA_HIGH) return  1;
   return -1;
  }

//--- Reset one tracker back to idle against a (possibly new) level price.
void ResetEvent(int idx, double newLevelPrice)
  {
   if(idx < 0 || idx >= NEXA_LVL_COUNT) return;
   g_liqEvents[idx].state             = NEXA_SWEEP_IDLE;
   g_liqEvents[idx].resolution        = NEXA_RESOLVE_NONE;
   g_liqEvents[idx].levelPrice        = newLevelPrice;
   g_liqEvents[idx].extremeBeyond     = 0;
   g_liqEvents[idx].excursionATR      = 0;
   g_liqEvents[idx].wickBodyRatio     = 0;
   g_liqEvents[idx].barsBeyond        = 0;
   g_liqEvents[idx].barsSinceReclaim  = 0;
   g_liqEvents[idx].sweepDirection    = 0;
   g_liqEvents[idx].responseDirection = 0;
   g_liqEvents[idx].displacementAfter = false;
   g_liqEvents[idx].mssAfter          = false;
   g_liqEvents[idx].fvgAfter          = false;
   g_liqEvents[idx].sweepBarTime      = 0;
   g_liqEvents[idx].setup             = NEXA_SETUP_NONE;
   g_liqEvents[idx].origin            = NEXA_ORIGIN_LIVE;
  }

//+------------------------------------------------------------------+
//| Advance one level's state machine by exactly one closed bar.       |
//| Structural inputs are supplied by the caller for the SAME bar so   |
//| this module never recomputes structure and the two cannot diverge. |
//+------------------------------------------------------------------+
void AdvanceLevelState(int idx, double levelPrice, double atr,
                        double barHigh, double barLow, double barOpen, double barClose,
                        datetime barTime,
                        bool dispUp, bool dispDown, bool mssUp, bool mssDown,
                        bool fvgBull, bool fvgBear)
  {
   if(idx < 0 || idx >= NEXA_LVL_COUNT) return;
   if(levelPrice <= 0 || atr <= 0) return;
   if(!NexaFinite(levelPrice) || !NexaFinite(atr)) return;

   // A level that moved (new trading day / new session) invalidates any event on
   // the old value: the pool it referenced no longer exists.
   if(g_liqEvents[idx].levelPrice > 0 &&
      MathAbs(g_liqEvents[idx].levelPrice - levelPrice) > _Point)
     {
      ResetEvent(idx, levelPrice);
      return;
     }
   g_liqEvents[idx].levelPrice = levelPrice;

   int polarity = LevelPolarity(g_liqEvents[idx].level);
   bool beyondNow  = (polarity > 0) ? (barHigh > levelPrice) : (barLow  < levelPrice);
   bool closedBack = (polarity > 0) ? (barClose < levelPrice) : (barClose > levelPrice);

   switch(g_liqEvents[idx].state)
     {
      case NEXA_SWEEP_IDLE:
        {
         if(!beyondNow) return;
         double excursion = (polarity > 0) ? (barHigh - levelPrice) : (levelPrice - barLow);
         double excATR = excursion / atr;                  // atr > 0 guaranteed above
         if(excATR < InpMinSweepExcursionATR) return;      // noise, not a probe
         if(excATR > InpMaxSweepExcursionATR)              // decisive break, not a grab
           { ResetEvent(idx, levelPrice); return; }

         g_liqEvents[idx].state          = NEXA_SWEEP_BEYOND;
         g_liqEvents[idx].sweepDirection = polarity;
         g_liqEvents[idx].extremeBeyond  = (polarity > 0) ? barHigh : barLow;
         g_liqEvents[idx].excursionATR   = excATR;
         g_liqEvents[idx].barsBeyond     = 1;
         g_liqEvents[idx].sweepBarTime   = barTime;

         double body = MathAbs(barClose - barOpen);
         double wick = (polarity > 0) ? (barHigh - MathMax(barOpen, barClose))
                                       : (MathMin(barOpen, barClose) - barLow);
         g_liqEvents[idx].wickBodyRatio = (body > 0) ? wick / body : 99.0;

         if(closedBack) g_liqEvents[idx].state = NEXA_SWEEP_RECLAIMED;
         return;
        }

      case NEXA_SWEEP_BEYOND:
        {
         if(beyondNow)
           {
            g_liqEvents[idx].barsBeyond++;
            double newExtreme = (polarity > 0) ? MathMax(g_liqEvents[idx].extremeBeyond, barHigh)
                                                : MathMin(g_liqEvents[idx].extremeBeyond, barLow);
            g_liqEvents[idx].extremeBeyond = newExtreme;
            double excursion = (polarity > 0) ? (newExtreme - levelPrice) : (levelPrice - newExtreme);
            g_liqEvents[idx].excursionATR = excursion / atr;

            if(g_liqEvents[idx].barsBeyond > InpMaxBarsBeyond ||
               g_liqEvents[idx].excursionATR > InpMaxSweepExcursionATR)
               ResetEvent(idx, levelPrice);              // acceptance, not a grab
            return;
           }
         if(closedBack) g_liqEvents[idx].state = NEXA_SWEEP_RECLAIMED;
         return;
        }

      case NEXA_SWEEP_RECLAIMED:
        {
         g_liqEvents[idx].barsSinceReclaim++;

         bool revDisp = (polarity > 0) ? dispDown : dispUp;
         bool revMss  = (polarity > 0) ? mssDown  : mssUp;
         bool revFvg  = (polarity > 0) ? fvgBear  : fvgBull;
         bool contDisp = (polarity > 0) ? dispUp : dispDown;
         bool contMss  = (polarity > 0) ? mssUp  : mssDown;
         bool contFvg  = (polarity > 0) ? fvgBull : fvgBear;

         if(revMss || revDisp)
           {
            g_liqEvents[idx].state             = NEXA_SWEEP_CONFIRMED;
            g_liqEvents[idx].resolution        = NEXA_RESOLVE_REVERSAL;
            g_liqEvents[idx].responseDirection = -polarity;
            g_liqEvents[idx].displacementAfter = revDisp;
            g_liqEvents[idx].mssAfter          = revMss;
            g_liqEvents[idx].fvgAfter          = revFvg;
            g_liqEvents[idx].setup             = SetupIdentity(g_liqEvents[idx].level, NEXA_RESOLVE_REVERSAL);
            g_liqEvents[idx].barsSinceReclaim  = 0;
            return;
           }
         if(contMss || contDisp)
           {
            g_liqEvents[idx].state             = NEXA_SWEEP_CONFIRMED;
            g_liqEvents[idx].resolution        = NEXA_RESOLVE_CONTINUATION;
            g_liqEvents[idx].responseDirection = polarity;
            g_liqEvents[idx].displacementAfter = contDisp;
            g_liqEvents[idx].mssAfter          = contMss;
            g_liqEvents[idx].fvgAfter          = contFvg;
            g_liqEvents[idx].setup             = SetupIdentity(g_liqEvents[idx].level, NEXA_RESOLVE_CONTINUATION);
            g_liqEvents[idx].barsSinceReclaim  = 0;
            return;
           }
         if(g_liqEvents[idx].barsSinceReclaim > InpResponseWindowBars)
            g_liqEvents[idx].state = NEXA_SWEEP_EXPIRED;
         return;
        }

      case NEXA_SWEEP_CONFIRMED:
        {
         g_liqEvents[idx].barsSinceReclaim++;
         if(g_liqEvents[idx].barsSinceReclaim > InpEventValidBars)
            g_liqEvents[idx].state = NEXA_SWEEP_EXPIRED;
         return;
        }

      case NEXA_SWEEP_EXPIRED:
        {
         if(!beyondNow) ResetEvent(idx, levelPrice);
         return;
        }
     }
  }

//+------------------------------------------------------------------+
//| CAUSAL STATE RECONSTRUCTION AFTER RESTART                          |
//|                                                                    |
//| Replays the machine forward over closed bars, oldest to newest.    |
//| CAUSALITY RULE ENFORCED HERE: for each replayed bar, the levels    |
//| used are those that existed AT THAT BAR'S TIMESTAMP:               |
//|   * PDH/PDL come from the D1 bar completed before THAT bar's day   |
//|     (GetPreviousDayLevelsAsOf), not from today's values.           |
//|   * Asia high/low are accumulated INCREMENTALLY as the replay      |
//|     walks through the Asian window, so a bar at 02:00 GMT is       |
//|     evaluated against the Asia range as of 02:00, not the final    |
//|     range known at 09:00. The final Asia range never leaks back.   |
//|                                                                    |
//| HONEST LIMITATION: replay reproduces displacement and FVG exactly  |
//| (local 1-3 bar computations) but approximates MSS with a stricter  |
//| strong-displacement proxy, so it under-reports rather than invents.|
//| Events rebuilt this way are tagged NEXA_ORIGIN_RECONSTRUCTED.      |
//|                                                                    |
//| The returned Asia H/L are the running values AS OF THE LAST        |
//| REPLAYED BAR, which the caller adopts as the live session state so |
//| the transition from replay to live is seamless and still causal.   |
//+------------------------------------------------------------------+
void ReconstructLiquidityState(const MqlRates &rates[], double atr, double dispThresholdATR,
                                int replayBars, double &outAsiaHigh, double &outAsiaLow,
                                bool &outAsiaSeenStart)
  {
   outAsiaHigh = 0; outAsiaLow = 0; outAsiaSeenStart = false;
   int n = ArraySize(rates);
   if(n < 5 || atr <= 0 || !NexaFinite(atr)) return;

   Liquidity_Init();

   int start = MathMin(replayBars, n - 1);
   if(start < 0) return;

   double runAsiaH = 0, runAsiaL = 0;
   int    lastGmtHour = -1;
   double curPdh = 0, curPdl = 0, curPdc = 0; datetime curSrc = 0;

   // rates[] is series-indexed (0 = newest closed); walk DOWN to move forward in time
   for(int i = start; i >= 0; i--)
     {
      datetime bt = rates[i].time;
      if(!Liquidity_ShouldProcessBar(bt)) continue;      // strictly increasing: never re-feed a bar
      MqlDateTime g; TimeToStruct(NexaToGMT(bt), g);
      int gmtHour = g.hour;

      // Previous-day levels AS OF THIS BAR, looked up against the BROKER's D1 bars
      // every bar (not cached on a GMT-day key: the broker day rolls at server
      // midnight, which is InpGMTOffset hours away from the GMT boundary, and a
      // cached value would be stale for exactly that many hours). Identical to the
      // live path, so replay and live cannot disagree on which day was "previous".
      GetPreviousDayLevelsAsOf(bt, curPdh, curPdl, curPdc, curSrc);

      // incremental Asia window: reset at 00:00 GMT boundary, accumulate 00-09.
      // outAsiaSeenStart records whether the replay actually observed that boundary;
      // if it did not, the running range is PARTIAL and must not replace a complete one.
      if(gmtHour == 0 && lastGmtHour != 0) { runAsiaH = rates[i].high; runAsiaL = rates[i].low; outAsiaSeenStart = true; }
      if(gmtHour >= 0 && gmtHour < 9)
        {
         runAsiaH = (runAsiaH == 0) ? rates[i].high : MathMax(runAsiaH, rates[i].high);
         runAsiaL = (runAsiaL == 0) ? rates[i].low  : MathMin(runAsiaL, rates[i].low);
        }
      lastGmtHour = gmtHour;

      double body = MathAbs(rates[i].close - rates[i].open);
      double dispRatio = body / atr;
      bool bull = rates[i].close > rates[i].open;
      bool dispUp   = (dispRatio >= dispThresholdATR &&  bull);
      bool dispDown = (dispRatio >= dispThresholdATR && !bull);

      bool fvgBull = false, fvgBear = false;
      if(i + 2 < n)
        {
         fvgBull = (rates[i + 2].high < rates[i].low);
         fvgBear = (rates[i + 2].low  > rates[i].high);
        }
      bool mssUp   = (dispRatio >= dispThresholdATR * 1.5 &&  bull);
      bool mssDown = (dispRatio >= dispThresholdATR * 1.5 && !bull);

      double lvl[NEXA_LVL_COUNT];
      lvl[NEXA_LVL_PDH] = curPdh; lvl[NEXA_LVL_PDL] = curPdl;
      lvl[NEXA_LVL_ASIA_HIGH] = runAsiaH; lvl[NEXA_LVL_ASIA_LOW] = runAsiaL;

      for(int L = 0; L < NEXA_LVL_COUNT; L++)
         AdvanceLevelState(L, lvl[L], atr,
                           rates[i].high, rates[i].low, rates[i].open, rates[i].close,
                           bt, dispUp, dispDown, mssUp, mssDown, fvgBull, fvgBear);
     }

   outAsiaHigh = runAsiaH; outAsiaLow = runAsiaL;

   int rebuilt = 0;
   for(int L = 0; L < NEXA_LVL_COUNT; L++)
      if(g_liqEvents[L].state != NEXA_SWEEP_IDLE)
        { g_liqEvents[L].origin = NEXA_ORIGIN_RECONSTRUCTED; rebuilt++; }
   Print("NEXA liquidity: causally replayed ", start + 1, " bars, ", rebuilt,
         " active event(s) reconstructed (tagged INFERRED)");
  }

//--- Pick the most actionable event: CONFIRMED beats RECLAIMED; ties broken by recency.
int SelectPrimaryEvent()
  {
   int best = -1; int bestRank = -1;
   for(int i = 0; i < NEXA_LVL_COUNT; i++)
     {
      int rank = -1;
      if(g_liqEvents[i].state == NEXA_SWEEP_CONFIRMED) rank = 2;
      else if(g_liqEvents[i].state == NEXA_SWEEP_RECLAIMED) rank = 1;
      if(rank < 0) continue;
      if(rank > bestRank ||
         (rank == bestRank && best >= 0 &&
          g_liqEvents[i].barsSinceReclaim < g_liqEvents[best].barsSinceReclaim))
        { best = i; bestRank = rank; }
     }
   return best;
  }

bool HasCleanRejection(int idx)
  {
   if(idx < 0 || idx >= NEXA_LVL_COUNT) return false;
   return (g_liqEvents[idx].wickBodyRatio >= InpMinRejectionWickBody);
  }

#endif
