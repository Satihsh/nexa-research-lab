//+------------------------------------------------------------------+
//| NEXA_TrainingExport.mq5                                           |
//| Builds a supervised training set from NEXA's own Trade DNA.        |
//| Run as a SCRIPT. Places no orders. Reads closed history only.      |
//+------------------------------------------------------------------+
//| LABELLING -- TRIPLE BARRIER ALIGNED TO THE EA'S ACTUAL EXIT LOGIC: |
//| For each OPEN row the SL and TP prices ARE the values the EA sent, |
//| read from the row itself -- never a fixed R assumed here. Walking  |
//| forward over closed M1 bars from the entry bar:                    |
//|   * TP touched first            -> label 1                         |
//|   * SL touched first            -> label 0                         |
//|   * breakeven ratchet: once price reaches +InpBreakevenAtR R the   |
//|     effective SL becomes the entry (mirrors ManageOpenPosition)    |
//|   * conditional time exit: after InpTimeExitBars bars, if progress |
//|     < 0.3R the EA closes at market -> label 0, flagged TIME_EXIT   |
//|   * horizon (InpMaxHoldBars) with nothing hit -> label -1          |
//| These three inputs MUST match the EA's InpBreakevenAtR,            |
//| InpTimeExitBars and the EA's 0.3R progress threshold.              |
//|                                                                    |
//| BAR-ORDER AMBIGUITY: if one M1 bar spans both barriers, OHLC cannot|
//| say which hit first. Resolved to LOSS on purpose and flagged in the |
//| `ambiguous` column so the rate is measured, not assumed.           |
//|                                                                    |
//| EXECUTION REALISM -- WHAT THIS DOES NOT MODEL, STATED PLAINLY:     |
//|   * partial close at InpPartialCloseAtR (position becomes blended) |
//|   * bid/ask on the exit side, slippage, commission, swap           |
//|   * intrabar path (M1 OHLC only)                                   |
//| The `exec_model` column records "M1_OHLC_BE_TIMEEXIT" so a         |
//| downstream researcher knows exactly which simplifications apply.   |
//|                                                                    |
//| ROW PAIRING: an OPEN row is the decision (features + INTENDED      |
//| SL/TP). It becomes a trade only when a FILL row follows it for the |
//| same symbol before any other OPEN or REJECTED row. Unfilled and    |
//| rejected OPENs are dropped -- they are decisions, not trades. The  |
//| label is computed from the FILL row's ACTUAL entry, SL and TP and  |
//| its timestamp; the features come from the OPEN row.                |
//|                                                                    |
//| NO LOOKAHEAD: features come from the OPEN row as journaled live    |
//| (ai_00..ai_47 written by the EA at decision time). Only the        |
//| OUTCOME is read from later bars. The feature vector never sees the |
//| future.                                                             |
//|                                                                    |
//| THIS SCRIPT DOES NOT TRAIN, VALIDATE, CALIBRATE OR SELECT A MODEL. |
//| It emits a dataset and fold boundaries. Purged walk-forward CV,    |
//| embargo, calibration, threshold optimisation and PBO/Deflated-     |
//| Sharpe testing happen outside MT5 and remain unbuilt.              |
//+------------------------------------------------------------------+
#property script_show_inputs

#define NEXA_EXPORT_FEATURES 48

input string InpSourceSymbol     = "EURUSD";
input double InpBreakevenAtR     = 1.00;   // MUST match the EA
input int    InpTimeExitBars     = 48;     // MUST match the EA (entry-TF bars; assumed M1 here)
input double InpTimeExitMinR     = 0.30;   // MUST match the EA's r < 0.3 condition
input int    InpMaxHoldBars      = 480;    // absolute horizon
input int    InpEmbargoBars      = 240;
input int    InpWalkForwardFolds = 5;

//--- header-name -> column index map (robust to column reordering)
int ColIndex(const string &hdr[], string name)
  {
   for(int i = 0; i < ArraySize(hdr); i++) if(hdr[i] == name) return i;
   return -1;
  }

//+------------------------------------------------------------------+
//| Triple barrier with breakeven ratchet and conditional time exit.   |
//| Returns 1 TP, 0 SL/time-exit, -1 horizon. `how` explains the exit. |
//+------------------------------------------------------------------+
int LabelTrade(string sym, datetime entryTime, int dir, double entry, double sl, double tp,
                bool &ambiguous, int &barsToOutcome, string &how)
  {
   ambiguous = false; barsToOutcome = 0; how = "";
   if(dir == 0 || entry <= 0 || sl <= 0 || tp <= 0) { how = "INVALID_ROW"; return -1; }
   double riskDist = MathAbs(entry - sl);
   if(riskDist <= 0) { how = "ZERO_RISK"; return -1; }
   if((dir > 0 && !(sl < entry && tp > entry)) || (dir < 0 && !(sl > entry && tp < entry)))
     { how = "BARRIERS_ON_WRONG_SIDE"; return -1; }

   int startShift = iBarShift(sym, PERIOD_M1, entryTime, false);
   if(startShift < 0) { how = "NO_M1_HISTORY"; return -1; }

   double effSL = sl;
   bool beMoved = false;

   // Entry occurs at the open of the bar containing entryTime (the EA fires on the
   // first tick of a new bar), so that bar's full range is post-entry: include it.
   for(int i = startShift; i >= 0 && barsToOutcome < InpMaxHoldBars; i--)
     {
      double hi = iHigh(sym, PERIOD_M1, i);
      double lo = iLow (sym, PERIOD_M1, i);
      double cl = iClose(sym, PERIOD_M1, i);
      if(hi <= 0 || lo <= 0 || cl <= 0) { how = "BAD_BAR"; return -1; }
      barsToOutcome++;

      bool tpHit = (dir > 0) ? (hi >= tp) : (lo <= tp);
      bool slHit = (dir > 0) ? (lo <= effSL) : (hi >= effSL);

      if(tpHit && slHit) { ambiguous = true; how = "AMBIGUOUS_BAR_RESOLVED_LOSS"; return 0; }
      if(slHit) { how = beMoved ? "BREAKEVEN_STOP" : "SL"; return 0; }
      if(tpHit) { how = "TP"; return 1; }

      // breakeven ratchet mirrors ManageOpenPosition: evaluated on the bar's favourable extreme
      double favorExt = (dir > 0) ? (hi - entry) : (entry - lo);
      if(!beMoved && favorExt / riskDist >= InpBreakevenAtR) { effSL = entry; beMoved = true; }

      // conditional time exit mirrors the EA: after N bars, if progress at close < threshold, flat
      if(barsToOutcome >= InpTimeExitBars)
        {
         double favorClose = (dir > 0) ? (cl - entry) : (entry - cl);
         if(favorClose / riskDist < InpTimeExitMinR) { how = "TIME_EXIT"; return 0; }
        }
     }
   how = "HORIZON";
   return -1;
  }

void OnStart()
  {
   if(InpWalkForwardFolds < 1) { Print("NEXA export: InpWalkForwardFolds must be >= 1"); return; }
   if(InpMaxHoldBars < 1 || InpTimeExitBars < 1) { Print("NEXA export: bar horizons must be >= 1"); return; }
   if(!SymbolSelect(InpSourceSymbol, true)) { Print("NEXA export: symbol not available ", InpSourceSymbol); return; }

   string inFile  = "NEXA_TradeDNA_" + InpSourceSymbol + ".csv";
   string outFile = "NEXA_Training_" + InpSourceSymbol + ".csv";

   // TXT mode: FileReadString returns a full LINE. (In CSV mode it returns one FIELD,
   // which is the defect this replaces.)
   int fin = FileOpen(inFile, FILE_READ | FILE_TXT | FILE_ANSI | FILE_COMMON);
   if(fin == INVALID_HANDLE) { Print("NEXA export: cannot open ", inFile, " err ", GetLastError()); return; }

   string headerLine = "";
   while(!FileIsEnding(fin)) { headerLine = FileReadString(fin); if(StringLen(headerLine) > 5) break; }
   if(StringLen(headerLine) < 5) { FileClose(fin); Print("NEXA export: empty DNA file"); return; }

   string hdr[];
   int hn = StringSplit(headerLine, ',', hdr);
   // Canonical schema v1.0 column names. Resolved BY NAME so column order may
   // change without breaking the exporter; a missing required name is fatal.
   int cSchemaVer = ColIndex(hdr, "schema_version");
   int cDecTs  = ColIndex(hdr, "decision_ts"),  cFillTs = ColIndex(hdr, "fill_ts");
   int cEvent  = ColIndex(hdr, "event"),        cDir    = ColIndex(hdr, "direction");
   int cEntryI = ColIndex(hdr, "entry_intended"), cEntryA = ColIndex(hdr, "entry_actual");
   int cSL     = ColIndex(hdr, "sl_price"),     cTP     = ColIndex(hdr, "tp_price");
   int cTgt    = ColIndex(hdr, "target_r"),     cSetup  = ColIndex(hdr, "liq_setup");
   int cAi0    = ColIndex(hdr, "f00");
   if(cSchemaVer < 0 || cDecTs < 0 || cEvent < 0 || cDir < 0 || cEntryI < 0 || cEntryA < 0
      || cSL < 0 || cTP < 0 || cAi0 < 0)
     { FileClose(fin); Print("NEXA export: header is not canonical schema v1.0 -- refusing to parse"); return; }
   if(cAi0 + NEXA_EXPORT_FEATURES > hn)
     { FileClose(fin); Print("NEXA export: header has fewer than ", NEXA_EXPORT_FEATURES, " ai_ columns"); return; }

   int fout = FileOpen(outFile, FILE_WRITE | FILE_TXT | FILE_ANSI | FILE_COMMON);
   if(fout == INVALID_HANDLE) { FileClose(fin); Print("NEXA export: cannot create ", outFile); return; }

   string aiHdr = "";
   for(int i = 0; i < NEXA_EXPORT_FEATURES; i++) aiHdr += StringFormat(",f%02d", i);
   FileWriteString(fout, "row_time,symbol,dir,entry,sl,tp,target_r,risk_dist,setup,schema,exec_model,label,how,ambiguous,bars_to_outcome" + aiHdr + "\r\n");

   int rows = 0, labelled = 0, ambiguousCount = 0, skipped = 0, unfilled = 0;
   datetime firstTime = 0, lastTime = 0;

   // pending OPEN (decision) awaiting its FILL
   bool   haveOpen = false;
   int    oDir = 0; double oTgtR = 0, oSL = 0, oTP = 0;
   string oSetup = "", oSchema = "", oAi = "", oSchemaVer = "";

   while(!FileIsEnding(fin))
     {
      string line = FileReadString(fin);
      if(StringLen(line) < 5) continue;
      string f[];
      int n = StringSplit(line, ',', f);
      if(n < hn) { skipped++; continue; }
      string ev = f[cEvent];

      if(ev == "OPEN")
        {
         if(haveOpen) unfilled++;                 // previous OPEN never filled: dropped
         haveOpen = false;
         bool featOK = true; string aiBlock = "";
         for(int i = 0; i < NEXA_EXPORT_FEATURES; i++)
           {
            string v = f[cAi0 + i];
            double dv = StringToDouble(v);
            if(v == "NaN" || !MathIsValidNumber(dv)) { featOK = false; break; }
            aiBlock += "," + v;
           }
         if(!featOK) { skipped++; continue; }
         oDir = (int)StringToInteger(f[cDir]);
         oTgtR = (cTgt >= 0) ? StringToDouble(f[cTgt]) : 0;
         oSL = StringToDouble(f[cSL]); oTP = StringToDouble(f[cTP]);   // INTENDED, fallback only
         oSchemaVer = f[cSchemaVer];
         oSetup = (cSetup >= 0) ? f[cSetup] : "";
         oSchema = ColIndex(hdr, "model_schema_version") >= 0 ? f[ColIndex(hdr, "model_schema_version")] : "";
         oAi = aiBlock;
         haveOpen = true;
         continue;
        }
      if(ev == "REJECTED") { if(haveOpen) unfilled++; haveOpen = false; continue; }
      if(ev != "FILL") continue;
      if(!haveOpen) { skipped++; continue; }      // a FILL with no preceding OPEN: not reproducible
      haveOpen = false;

      // Label from the FILL: actual entry price and actual fill time, never the
      // intended values -- the trade that existed is the one to be labelled.
      datetime fillTime = (cFillTs >= 0 && StringLen(f[cFillTs]) > 4)
                          ? StringToTime(f[cFillTs]) : StringToTime(f[cDecTs]);
      int    dir   = (int)StringToInteger(f[cDir]);
      double entry = StringToDouble(f[cEntryA]);
      if(entry <= 0) entry = StringToDouble(f[cEntryI]);
      double sl    = StringToDouble(f[cSL]);
      double tp    = StringToDouble(f[cTP]);
      if(dir == 0) dir = oDir;
      if(dir != oDir) { skipped++; continue; }    // OPEN/FILL disagree on direction: refuse
      // If the FILL row could not read the server SL/TP (position record lagging the
      // deal), use the INTENDED values from the OPEN row -- the EA sent exactly those.
      if(sl <= 0) sl = oSL;
      if(tp <= 0) tp = oTP;

      bool amb; int barsOut; string how;
      int label = LabelTrade(InpSourceSymbol, fillTime, dir, entry, sl, tp, amb, barsOut, how);

      if(firstTime == 0) firstTime = fillTime;
      lastTime = fillTime;
      rows++;
      if(label >= 0) labelled++;
      if(amb) ambiguousCount++;

      FileWriteString(fout, StringFormat("%s,%s,%d,%.5f,%.5f,%.5f,%.3f,%.5f,%s,%s,M1_OHLC_BE_TIMEEXIT,%d,%s,%d,%d%s\r\n",
                      TimeToString(fillTime, TIME_DATE | TIME_SECONDS), InpSourceSymbol, dir, entry, sl, tp, oTgtR,
                      MathAbs(entry - sl), oSetup, oSchema, label, how, (amb ? 1 : 0), barsOut, oAi));
     }
   if(haveOpen) unfilled++;
   FileClose(fin);

   FileWriteString(fout, "\r\nWALK_FORWARD_SPEC\r\n");
   FileWriteString(fout, StringFormat("folds,%d,embargo_bars,%d\r\n", InpWalkForwardFolds, InpEmbargoBars));
   if(rows > 0 && lastTime > firstTime)
     {
      long span = (long)(lastTime - firstTime);
      long foldLen = span / InpWalkForwardFolds;          // folds >= 1 validated above
      for(int i = 0; i < InpWalkForwardFolds; i++)
        {
         datetime fs = firstTime + (datetime)(i * foldLen);
         datetime fe = firstTime + (datetime)((i + 1) * foldLen);
         FileWriteString(fout, StringFormat("fold,%d,%s,%s\r\n", i, TimeToString(fs, TIME_DATE), TimeToString(fe, TIME_DATE)));
        }
     }
   FileClose(fout);

   Print("NEXA export -> ", outFile, " | rows=", rows, " labelled=", labelled, " ambiguous=", ambiguousCount,
         " skipped=", skipped, " unfilled_opens=", unfilled, " (",
         (rows > 0 ? DoubleToString(100.0 * ambiguousCount / rows, 1) : "0"), "% ambiguous)");
   if(labelled < 200)
      Print("WARNING: ", labelled, " labelled rows is far too few to train on. A model fitted to this will memorise it.");
  }
