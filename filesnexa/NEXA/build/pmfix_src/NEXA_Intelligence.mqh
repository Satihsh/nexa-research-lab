//+------------------------------------------------------------------+
//| NEXA_Intelligence.mqh                                             |
//| AI/meta-label hook (real ONNX integration), adversarial validation,|
//| rolling expectancy / strategy-survival, native economic-calendar   |
//| news filter, synthetic USD-composite (INFERRED, not DXY).          |
//|                                                                    |
//| THE AI LAYER IS NOT TRAINED MERELY BECAUSE THIS CODE EXISTS. No    |
//| model ships with this codebase. GetAIScore() returns -1 until a    |
//| model file whose declared shape matches the frozen schema loads   |
//| cleanly. When AI confirmation is required and no valid model is    |
//| available, the EA fails CLOSED (no trade).                          |
//+------------------------------------------------------------------+
#ifndef NEXA_INTELLIGENCE_MQH
#define NEXA_INTELLIGENCE_MQH
#include "NEXA_Common.mqh"

// Width of the AI feature vector. MUST match the packing block in PackFeatures()
// and the trained model's input dimension. Append-only; bump the version on change.
#define NEXA_AI_FEATURE_COUNT   48
#define NEXA_AI_SCHEMA_VERSION  "1.0"

input string   InpOnnxModelFile         = "NEXA_MetaModel.onnx";
input int      InpNewsBufferMinutes     = 30;
input int      InpMinSampleForSurvival  = 20;
input double   InpExpectancyPauseR      = -0.10;
input double   InpStressSpreadMultiplier = 3.0;

//==================== AI / META-LABEL HOOK ====================
long g_onnxHandle = INVALID_HANDLE;
bool g_onnxLoggedUnavailable = false;

//+------------------------------------------------------------------+
//| NEXA AI FEATURE SCHEMA v1.0 -- FROZEN, 48 ELEMENTS                 |
//| This ordering is a CONTRACT with any trained model. APPEND ONLY.   |
//| Every packed value is also journaled to Trade DNA as ai_00..ai_47, |
//| so the training set reproduces exactly what the live model saw.    |
//|                                                                    |
//| [ 0- 7] structure: breaks, BOS, CHoCH, MSS                          |
//| [ 8-10] displacement (2 bool + ATR ratio)                           |
//| [11-12] bar-local sweep flags                                       |
//| [13-19] SMC objects: FVG, OB, OTE, BPR                              |
//| [20-23] regime: trend, volatility, breakout, transition             |
//| [24-27] MTF: M5/M15/H1 trend + alignment                            |
//| [28-29] spread/ATR; USD composite (INFERRED from traded symbols)    |
//| [30-31] microstructure proxies OBI, CVD (INFERRED, not real LOB)    |
//| [32-39] liquidity event state machine                               |
//| [40-47] liquidity detail, setup identity, provenance, news          |
//| Returns false if any value is non-finite -- caller must not infer.  |
//+------------------------------------------------------------------+
bool PackFeatures(const NexaSignal &sig, float &out[])
  {
   if(ArrayResize(out, NEXA_AI_FEATURE_COUNT) != NEXA_AI_FEATURE_COUNT) return false;
   int k = 0;
   out[k++] = (float)sig.structureBreakUp;
   out[k++] = (float)sig.structureBreakDown;
   out[k++] = (float)sig.isBOS_up;
   out[k++] = (float)sig.isBOS_down;
   out[k++] = (float)sig.isCHoCH_up;
   out[k++] = (float)sig.isCHoCH_down;
   out[k++] = (float)sig.isMSS_up;
   out[k++] = (float)sig.isMSS_down;
   out[k++] = (float)sig.displacementUp;
   out[k++] = (float)sig.displacementDown;
   out[k++] = (float)sig.displacementATR;
   out[k++] = (float)sig.sweepUp;
   out[k++] = (float)sig.sweepDown;
   out[k++] = (float)sig.fvgBullActive;
   out[k++] = (float)sig.fvgBearActive;
   out[k++] = (float)sig.obBullActive;
   out[k++] = (float)sig.obBearActive;
   out[k++] = (float)sig.inOTE_up;
   out[k++] = (float)sig.inOTE_down;
   out[k++] = (float)sig.bprActive;
   out[k++] = (float)sig.trendState;
   out[k++] = (float)sig.volState;
   out[k++] = (float)sig.breakoutState;
   out[k++] = (float)sig.regimeTransitioning;
   out[k++] = (float)sig.trendM5;
   out[k++] = (float)sig.trendM15;
   out[k++] = (float)sig.trendH1;
   out[k++] = (float)sig.htfAlignment;
   out[k++] = (float)sig.spreadATRRatio;
   out[k++] = (float)sig.usdCompositeDirection;
   out[k++] = (float)sig.obiProxy;
   out[k++] = (float)sig.cvdProxy;
   out[k++] = (float)sig.liqState;
   out[k++] = (float)sig.liqResolution;
   out[k++] = (float)sig.liqExcursionATR;
   out[k++] = (float)sig.liqWickBodyRatio;
   out[k++] = (float)sig.liqBarsBeyond;
   out[k++] = (float)sig.liqBarsSinceReclaim;
   out[k++] = (float)sig.liqSweepDirection;
   out[k++] = (float)sig.liqResponseDirection;
   out[k++] = (float)sig.liqMssAfter;
   out[k++] = (float)sig.liqDisplacementAfter;
   out[k++] = (float)sig.liqFvgAfter;
   out[k++] = (float)sig.liqEventActive;
   out[k++] = (float)sig.liqLevel;
   out[k++] = (float)sig.liqSetup;
   out[k++] = (float)sig.liqOrigin;
   out[k++] = (float)(sig.newsRiskActive ? 1 : 0);

   if(k != NEXA_AI_FEATURE_COUNT) return false;
   for(int i = 0; i < NEXA_AI_FEATURE_COUNT; i++)
      if(!MathIsValidNumber((double)out[i])) return false;
   return true;
  }

//--- Load the model and pin its tensor shapes to the frozen schema. If the model
//--- cannot accept exactly [1,48] -> [1,1], it is not a NEXA model: release it.
bool AI_Init()
  {
   g_onnxHandle = INVALID_HANDLE;
   g_onnxLoggedUnavailable = false;

   if(!FileIsExist(InpOnnxModelFile, 0))
     {
      Print("NEXA AI: no model file (", InpOnnxModelFile, "). AI layer INACTIVE. ",
            "If InpRequireAIConfirmation=true the EA will not trade.");
      return false;
     }

   long h = OnnxCreate(InpOnnxModelFile, ONNX_DEFAULT);
   if(h == INVALID_HANDLE)
     {
      Print("NEXA AI: model file present but OnnxCreate failed, error ", GetLastError());
      return false;
     }

   ulong inShape[2]  = {1, NEXA_AI_FEATURE_COUNT};
   ulong outShape[2] = {1, 1};
   bool okIn  = OnnxSetInputShape (h, 0, inShape);
   bool okOut = OnnxSetOutputShape(h, 0, outShape);
   if(!okIn || !okOut)
     {
      Print("NEXA AI: model rejected shape [1,", NEXA_AI_FEATURE_COUNT, "] -> [1,1] (in=", okIn,
            " out=", okOut, ", err ", GetLastError(), "). Not a schema-v", NEXA_AI_SCHEMA_VERSION,
            " model -- released. AI layer INACTIVE.");
      OnnxRelease(h);
      return false;
     }

   g_onnxHandle = h;
   Print("NEXA AI: model loaded and shape-validated (schema v", NEXA_AI_SCHEMA_VERSION, ", ",
         NEXA_AI_FEATURE_COUNT, " features).");
   return true;
  }

void AI_Deinit()
  {
   if(g_onnxHandle != INVALID_HANDLE) { OnnxRelease(g_onnxHandle); g_onnxHandle = INVALID_HANDLE; }
  }

bool AI_ModelAvailable() { return (g_onnxHandle != INVALID_HANDLE); }

//--- PROVENANCE (schema v1.0). Identifies WHICH model produced a probability, so a
//--- journal row can be attributed to a model version during drift analysis.
//--- "NONE" is a truthful value: it means no model participated in this decision.
string AI_ModelId()
  {
   if(g_onnxHandle == INVALID_HANDLE) return "NONE";
   return InpOnnxModelFile + "@schema" + NEXA_AI_SCHEMA_VERSION;
  }

//--- Calibration is seam L1 (a later stage). Until it exists this is truthfully
//--- "NONE": probabilities written to the journal are RAW model output, not
//--- calibrated, and must not be read as empirical frequencies.
string AI_CalibrationId() { return "NONE"; }

//--- Returns -1.0 when no valid model is loaded or inference fails validation.
//--- Returns a probability in [0,1] only from a real, shape-validated model.
double GetAIScore(const NexaSignal &sig)
  {
   if(g_onnxHandle == INVALID_HANDLE)
     {
      if(!g_onnxLoggedUnavailable)
        { Print("NEXA AI: GetAIScore() with no model -> UNAVAILABLE(-1)."); g_onnxLoggedUnavailable = true; }
      return -1.0;
     }

   float inputs[];
   if(!PackFeatures(sig, inputs))
     { Print("NEXA AI: feature packing failed validation (count/finite). No inference."); return -1.0; }

   float output[1];
   output[0] = 0.0f;
   if(!OnnxRun(g_onnxHandle, ONNX_DEFAULT, inputs, output))
     { Print("NEXA AI: OnnxRun failed, error ", GetLastError()); return -1.0; }

   double p = (double)output[0];
   if(!MathIsValidNumber(p) || p < 0.0 || p > 1.0)
     { Print("NEXA AI: model produced an invalid probability (", p, "). Treated as UNAVAILABLE."); return -1.0; }
   return p;
  }

//==================== ADVERSARIAL VALIDATION ====================
bool AdversarialCheck(const NexaSignal &sig, int direction, double stopDistance, string &reason)
  {
   if(stopDistance <= 0 || !NexaFinite(stopDistance)) { reason = "ADV_FAIL_INVALID_STOP_DISTANCE"; return false; }

   // 1. stressed spread must not dominate the stop
   double stressedSpread = sig.spread * InpStressSpreadMultiplier;
   if(stressedSpread / stopDistance > 0.40)
     { reason = "ADV_FAIL_STRESSED_SPREAD_TOO_LARGE_VS_STOP"; return false; }

   // 2. contradictory structure on the same bar
   if((sig.structureBreakUp && sig.structureBreakDown) || (sig.displacementUp && sig.displacementDown))
     { reason = "ADV_FAIL_CONTRADICTORY_SIGNALS"; return false; }

   // 3. historical analog base rate for this (trend, vol) bucket -- neutral until enough samples
   string bucketKey = GV("BucketWin_" + _Symbol + "_" + IntegerToString((int)sig.trendState) + "_" + IntegerToString((int)sig.volState));
   string bucketCountKey = bucketKey + "_n";
   if(GlobalVariableCheck(bucketCountKey))
     {
      double n = GlobalVariableGet(bucketCountKey);
      if(n > 0 && n >= InpMinSampleForSurvival)
        {
         double wins = GlobalVariableCheck(bucketKey) ? GlobalVariableGet(bucketKey) : 0;
         double winRate = wins / n;
         if(winRate < 0.25) { reason = "ADV_FAIL_HISTORICAL_BUCKET_POOR"; return false; }
        }
     }

   // 4. worst-plausible-path proxy vs stop
   if(sig.atrValue > 0 && stopDistance < sig.atrValue * 0.5)
     { reason = "ADV_FAIL_STOP_TOO_TIGHT_VS_ATR"; return false; }

   reason = "ADV_PASS";
   return true;
  }

//==================== EXPECTANCY / STRATEGY SURVIVAL ====================
void UpdateExpectancyStats(double rResult, ENUM_NEXA_REGIME_TREND trendState, ENUM_NEXA_REGIME_VOL volState)
  {
   if(!NexaFinite(rResult)) return;
   string sumKey = GV("RSum_" + _Symbol), cntKey = GV("RCount_" + _Symbol);
   double sum = GlobalVariableCheck(sumKey) ? GlobalVariableGet(sumKey) : 0;
   double cnt = GlobalVariableCheck(cntKey) ? GlobalVariableGet(cntKey) : 0;
   GlobalVariableSet(sumKey, sum + rResult);
   GlobalVariableSet(cntKey, cnt + 1);

   string bucketKey = GV("BucketWin_" + _Symbol + "_" + IntegerToString((int)trendState) + "_" + IntegerToString((int)volState));
   string bucketCountKey = bucketKey + "_n";
   double bwins = GlobalVariableCheck(bucketKey) ? GlobalVariableGet(bucketKey) : 0;
   double bn = GlobalVariableCheck(bucketCountKey) ? GlobalVariableGet(bucketCountKey) : 0;
   GlobalVariableSet(bucketKey, bwins + (rResult > 0 ? 1 : 0));
   GlobalVariableSet(bucketCountKey, bn + 1);
  }

double RollingExpectancyR()
  {
   string sumKey = GV("RSum_" + _Symbol), cntKey = GV("RCount_" + _Symbol);
   double sum = GlobalVariableCheck(sumKey) ? GlobalVariableGet(sumKey) : 0;
   double cnt = GlobalVariableCheck(cntKey) ? GlobalVariableGet(cntKey) : 0;
   return (cnt > 0) ? sum / cnt : 0;
  }

bool StrategySurvivalOK(string &reason)
  {
   string cntKey = GV("RCount_" + _Symbol);
   double cnt = GlobalVariableCheck(cntKey) ? GlobalVariableGet(cntKey) : 0;
   if(cnt < InpMinSampleForSurvival) { reason = "SURVIVAL_INSUFFICIENT_SAMPLE_" + DoubleToString(cnt, 0); return true; }
   double expR = RollingExpectancyR();
   if(expR < InpExpectancyPauseR)
     { reason = StringFormat("SURVIVAL_PAUSED_EXPECTANCY_%.3fR_OVER_%d_TRADES", expR, (int)cnt); return false; }
   reason = StringFormat("SURVIVAL_OK_EXPECTANCY_%.3fR", expR);
   return true;
  }

//==================== NEWS FILTER -- native MT5 economic calendar ====================
// FAIL-CLOSED: if the calendar cannot be queried (error, unavailable), the function
// reports a risk window. "No events" (a clean zero) is the only fail-open path.
bool g_newsTesterNoticeShown = false;

bool IsNewsRiskWindow(string sym)
  {
   // The economic calendar is not available inside the Strategy Tester. Failing
   // closed there would block every backtest trade, which is not a test of anything.
   // The filter is declared INACTIVE in the tester and said so once, loudly, so
   // backtest results are read knowing news gating was absent.
   if(MQLInfoInteger(MQL_TESTER))
     {
      if(!g_newsTesterNoticeShown)
        { Print("NEXA news: economic calendar unavailable in Strategy Tester -- generic news filter INACTIVE for this run. FOMC gate still active."); g_newsTesterNoticeShown = true; }
      return false;
     }

   string base  = SymbolInfoString(sym, SYMBOL_CURRENCY_BASE);
   string quote = SymbolInfoString(sym, SYMBOL_CURRENCY_PROFIT);

   datetime from = TimeCurrent() - (datetime)(InpNewsBufferMinutes * 60);
   datetime to   = TimeCurrent() + (datetime)(InpNewsBufferMinutes * 60);

   MqlCalendarValue values[];
   ResetLastError();
   int n = CalendarValueHistory(values, from, to, NULL, NULL);
   int err = GetLastError();
   if(n < 0 || err != 0)
     {
      Print("NEXA news: calendar query failed (err ", err, ") -- treating as RISK WINDOW (fail-closed).");
      return true;
     }
   if(n == 0) return false;

   int total = MathMin(n, ArraySize(values));
   for(int i = 0; i < total; i++)
     {
      // Safety audit 2026-09-29: an event that cannot be resolved cannot be classified, so it is
      // treated as a risk window (fail closed) instead of being silently skipped.
      MqlCalendarEvent evt;
      if(!CalendarEventById(values[i].event_id, evt))
        { Print("NEXA news: event ", values[i].event_id, " unresolvable -- treating as RISK WINDOW (fail-closed)."); return true; }
      if(evt.importance != CALENDAR_IMPORTANCE_HIGH) continue;
      MqlCalendarCountry country;
      if(!CalendarCountryById(evt.country_id, country))
        { Print("NEXA news: country ", evt.country_id, " unresolvable -- treating as RISK WINDOW (fail-closed)."); return true; }
      if(country.currency == base || country.currency == quote) return true;
     }
   return false;
  }

//==================== SYNTHETIC USD COMPOSITE (INFERRED) ====================
// Built from the direction of the four traded symbols -- NOT DXY, not external.
// Journaled and fed to the model; never scored as independent macro evidence.
int UsdCompositeDirection()
  {
   string basket[4] = {"EURUSD", "GBPUSD", "USDJPY", "XAUUSD"};
   int usdStrongVotes = 0, usdWeakVotes = 0, counted = 0;
   for(int i = 0; i < 4; i++)
     {
      if(!SymbolSelect(basket[i], true)) continue;
      double c0  = iClose(basket[i], PERIOD_CURRENT, 1);
      double c10 = iClose(basket[i], PERIOD_CURRENT, 11);
      if(c0 <= 0 || c10 <= 0) continue;
      bool up = c0 > c10;
      counted++;
      if(basket[i] == "USDJPY") { if(up) usdStrongVotes++; else usdWeakVotes++; }
      else                       { if(up) usdWeakVotes++;   else usdStrongVotes++; }
     }
   if(counted < 2) return 0;
   if(usdStrongVotes >= counted - 1) return 1;
   if(usdWeakVotes   >= counted - 1) return -1;
   return 0;
  }

#endif
