//+------------------------------------------------------------------+
//| NEXA_BarExport.mq5                                                |
//| Research data tap. Run in the STRATEGY TESTER on the same symbol, |
//| period, dates and modelling mode as a NEXA_EA run. It journals the |
//| bars the tester actually served, so Stage 3 parity and Stage 4     |
//| labels use exactly the bar stream NEXA decided on.                 |
//|                                                                    |
//| PLACES NO ORDERS. Includes no NEXA module. Touches no risk state.  |
//|                                                                    |
//| Output (Common\Files):                                             |
//|   NEXA_Bars_<sym>_M1.csv  every CLOSED M1 bar (start_pos = 1)      |
//|   NEXA_Bars_<sym>_D1.csv  every CLOSED D1 bar (start_pos = 1)      |
//|   NEXA_Bars_<sym>_M5/M15/H1.csv  broker's own higher-TF bars, so   |
//|   the parity oracle can rebuild NEXA's MTF caches (300 bars each)  |
//| Columns: time,open,high,low,close,tick_volume,spread,real_volume   |
//| `time` is the bar OPEN time in broker server time, as MT5 reports. |
//| `spread` is in points, as stored in the bar.                       |
//|                                                                    |
//| On init it also writes the WARM-UP history that precedes the test  |
//| window (InpWarmupM1 M1 bars, InpWarmupD1 D1 bars), because NEXA's  |
//| features look back before the first test bar.                      |
//+------------------------------------------------------------------+
#property copyright "NEXA"
#property version   "1.00"
#property description "Tester data tap: journals closed M1/D1 bars. Places no orders."

input int InpWarmupM1  = 7200;  // M1 bars before the test start (5 days)
input int InpWarmupM5  = 1500;  // > NEXA InpMTFCacheBars (300) with margin
input int InpWarmupM15 = 1000;
input int InpWarmupH1  = 700;
input int InpWarmupD1  = 120;   // D1 bars before the test start
input bool InpExportIntraday = true;  // false: write only H1 + D1 (long factory history, small files)

int      g_m1 = INVALID_HANDLE, g_m5 = INVALID_HANDLE, g_m15 = INVALID_HANDLE, g_h1 = INVALID_HANDLE;
int      g_d1 = INVALID_HANDLE;
datetime g_lastM1 = 0, g_lastM5 = 0, g_lastM15 = 0, g_lastH1 = 0;
datetime g_lastD1 = 0;

int OpenOut(const string tf)
  {
   string fn = "NEXA_Bars_" + _Symbol + "_" + tf + ".csv";
   int h = FileOpen(fn, FILE_WRITE | FILE_TXT | FILE_ANSI | FILE_COMMON);
   if(h != INVALID_HANDLE)
      FileWriteString(h, "time,open,high,low,close,tick_volume,spread,real_volume\r\n");
   return h;
  }

void WriteBar(const int h, const MqlRates &r)
  {
   FileWriteString(h, StringFormat("%s,%.*f,%.*f,%.*f,%.*f,%I64d,%d,%I64d\r\n",
                   TimeToString(r.time, TIME_DATE | TIME_SECONDS),
                   _Digits, r.open, _Digits, r.high, _Digits, r.low, _Digits, r.close,
                   r.tick_volume, r.spread, r.real_volume));
  }

//--- write every closed bar of `tf` newer than `last`; returns the newest time written
datetime Drain(const int h, const ENUM_TIMEFRAMES tf, const datetime last, const int warmup)
  {
   MqlRates r[];
   ArraySetAsSeries(r, false);                       // chronological
   int n = (last == 0) ? CopyRates(_Symbol, tf, 1, warmup, r)
                       : CopyRates(_Symbol, tf, last + 1, TimeCurrent(), r);
   if(n <= 0)
      return last;
   datetime newest = last;
   datetime forming = iTime(_Symbol, tf, 0);
   for(int i = 0; i < n; i++)
     {
      if(r[i].time <= last || r[i].time >= forming)  // closed bars only, each once
         continue;
      WriteBar(h, r[i]);
      newest = r[i].time;
     }
   FileFlush(h);
   return newest;
  }

int OnInit()
  {
   if(!MQLInfoInteger(MQL_TESTER))
     {
      Print("NEXA_BarExport: tester-only data tap; refusing to run on a live chart.");
      return INIT_FAILED;
     }
   if(InpExportIntraday)
     {
      g_m1 = OpenOut("M1");
      g_m5 = OpenOut("M5");
      g_m15 = OpenOut("M15");
     }
   g_h1 = OpenOut("H1");
   g_d1 = OpenOut("D1");
   if((InpExportIntraday && (g_m1 == INVALID_HANDLE || g_m5 == INVALID_HANDLE || g_m15 == INVALID_HANDLE)) ||
      g_h1 == INVALID_HANDLE || g_d1 == INVALID_HANDLE)
     {
      PrintFormat("NEXA_BarExport: cannot open output, err %d", GetLastError());
      return INIT_FAILED;
     }
   if(InpExportIntraday)
     {
      g_lastM1  = Drain(g_m1,  PERIOD_M1,  0, InpWarmupM1);
      g_lastM5  = Drain(g_m5,  PERIOD_M5,  0, InpWarmupM5);
      g_lastM15 = Drain(g_m15, PERIOD_M15, 0, InpWarmupM15);
     }
   g_lastH1  = Drain(g_h1,  PERIOD_H1,  0, InpWarmupH1);
   g_lastD1  = Drain(g_d1,  PERIOD_D1,  0, InpWarmupD1);
   PrintFormat("NEXA_BarExport: warm-up written through M1 %s, D1 %s",
               TimeToString(g_lastM1), TimeToString(g_lastD1));
   return INIT_SUCCEEDED;
  }

void OnTick()
  {
   // Lower-timeframe requests are illegal in Open Prices mode on a higher chart
   // ("wrong timeframe request" aborts the test), so they are made ONLY when the
   // intraday export is enabled.
   if(InpExportIntraday)
     {
      datetime m1 = iTime(_Symbol, PERIOD_M1, 0);
      if(m1 != 0 && m1 > g_lastM1 + 60)
         g_lastM1 = Drain(g_m1, PERIOD_M1, g_lastM1, InpWarmupM1);
      datetime m5 = iTime(_Symbol, PERIOD_M5, 0);
      if(m5 != 0 && m5 > g_lastM5 + 300)
         g_lastM5 = Drain(g_m5, PERIOD_M5, g_lastM5, InpWarmupM5);
      datetime m15 = iTime(_Symbol, PERIOD_M15, 0);
      if(m15 != 0 && m15 > g_lastM15 + 900)
         g_lastM15 = Drain(g_m15, PERIOD_M15, g_lastM15, InpWarmupM15);
     }
   datetime h1 = iTime(_Symbol, PERIOD_H1, 0);
   if(h1 != 0 && h1 > g_lastH1 + 3600)
      g_lastH1 = Drain(g_h1, PERIOD_H1, g_lastH1, InpWarmupH1);
   datetime d1 = iTime(_Symbol, PERIOD_D1, 0);
   if(d1 != 0 && d1 > g_lastD1 + 86400)
      g_lastD1 = Drain(g_d1, PERIOD_D1, g_lastD1, InpWarmupD1);
  }

void OnDeinit(const int reason)
  {
   if(g_m1 != INVALID_HANDLE) { FileClose(g_m1); g_m1 = INVALID_HANDLE; }
   if(g_m5 != INVALID_HANDLE)  { FileClose(g_m5);  g_m5 = INVALID_HANDLE; }
   if(g_m15 != INVALID_HANDLE) { FileClose(g_m15); g_m15 = INVALID_HANDLE; }
   if(g_h1 != INVALID_HANDLE)  { FileClose(g_h1);  g_h1 = INVALID_HANDLE; }
   if(g_d1 != INVALID_HANDLE) { FileClose(g_d1); g_d1 = INVALID_HANDLE; }
   PrintFormat("NEXA_BarExport: closed, reason %d, last M1 %s", reason, TimeToString(g_lastM1));
  }
