//+------------------------------------------------------------------+
//| NEXA_MALE5_Bridge.mqh  (OPTIONAL -- not included by NEXA_EA.mq5   |
//| by default)                                                        |
//|                                                                    |
//| This is a second, MT5-native path for item 2 (the AI/meta-label    |
//| layer), as an alternative to the ONNX path already built into      |
//| NEXA_Intelligence.mqh. It uses MegaJoctan/MALE5, a pure-MQL5 ML    |
//| library -- meaning a meta-model can be trained directly inside     |
//| MetaEditor from NEXA's own Trade DNA CSV, with ZERO Python step.   |
//|                                                                    |
//| WHY THIS IS SEPARATE AND OPT-IN, NOT MERGED INTO THE MAIN EA:      |
//| MALE5 is a third-party library that must be installed by you       |
//| first (per its own README: download the release, copy the MALE5   |
//| folder into MQL5/Include). Force-including it in NEXA_EA.mq5       |
//| would break compilation for anyone who hasn't done that. To        |
//| activate this path: install MALE5, uncomment the #include below,  |
//| add #include "NEXA_MALE5_Bridge.mqh" to NEXA_EA.mq5, and call      |
//| GetAIScore_MALE5() from GetAIScore() in NEXA_Intelligence.mqh      |
//| (or wire it in as a second vote alongside the ONNX path).          |
//|                                                                    |
//| TRAINING WORKFLOW (run as a separate MQL5 SCRIPT, not the EA):      |
//| 1. Read NEXA_TradeDNA_<symbol>.csv (Common Files folder) for CLOSE |
//|    rows -- these carry the full feature set plus the R_RESULT.     |
//| 2. Build an X matrix from the feature columns, y = 1 if R_RESULT>0 |
//|    else 0 (or use R_RESULT directly for a regression target).      |
//| 3. StandardizationScaler + TrainTestSplitMatrices (MALE5) for a    |
//|    proper train/test split -- this is a SEPARATE, simpler split    |
//|    than the walk-forward/purged-CV discipline in Part 22 of the    |
//|    research; treat this native path as a fast first-pass model,    |
//|    not a substitute for the full validation battery before any     |
//|    live-influencing deployment.                                    |
//| 4. Fit a MALE5 model (Logistic Regression or Decision Tree          |
//|    recommended first -- interpretable, cheap, and the directive's   |
//|    own criteria: stable, computationally reasonable, validated).    |
//| 5. Persist the fitted model/coefficients to a file the live EA      |
//|    can load at OnInit (MALE5's model classes support this --        |
//|    check the current release's save/load API in MetaEditor's        |
//|    autocomplete, since it is not pinned here to avoid documenting   |
//|    a signature that may have changed since this was written).       |
//+------------------------------------------------------------------+
#ifndef NEXA_MALE5_BRIDGE_MQH
#define NEXA_MALE5_BRIDGE_MQH

// Uncomment once MALE5 is installed in MQL5/Include/MALE5/:
// #include <MALE5\Logistic Regression\logistic_regression.mqh>
// #include <MALE5\preprocessing.mqh>
// #include <MALE5\MatrixExtend.mqh>
// #include <MALE5\metrics.mqh>

#include "NEXA_Common.mqh"

// Returns -1.0 (unavailable) until a MALE5 model has actually been trained and loaded --
// same sentinel convention as GetAIScore() in NEXA_Intelligence.mqh, so callers treat both
// backends identically: never fabricate a score when nothing has been trained yet.
double GetAIScore_MALE5(const NexaSignal &sig)
  {
   // TODO once MALE5 is installed and a model trained per the workflow above:
   // 1. build the same feature vector ordering used in NEXA_Intelligence.mqh's GetAIScore()
   //    (keep ONE frozen feature order shared by both backends so Trade DNA stays comparable)
   // 2. call the loaded model's predict_proba() and return its positive-class probability
   return -1.0;
  }

#endif
