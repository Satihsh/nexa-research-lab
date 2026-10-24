//+------------------------------------------------------------------+
//| NEXA_ClockTest.mq5 -- deterministic test harness for the          |
//| DST-aware server clock in NEXA_Common.mqh (D-TZ, 2026-10-03).      |
//|                                                                    |
//| Strategy Tester only. Places NO orders. OnInit walks every server  |
//| hour from 2000-01-01 to 2031-01-01 through the COMPILED            |
//| NexaServerGMTOffsetHours() / NexaGMTHourOf() and writes one row    |
//| per hour to Common\Files, so research/test_nexa_dtz_clock.py can   |
//| compare it with research/nexa_time.py hour by hour.                |
//+------------------------------------------------------------------+
#property copyright "NEXA"
#property version   "1.00"

#include "NEXA_Common.mqh"

input string InpResults = "nexa_clock_mql5_results.csv";

int OnInit()
  {
   int out = FileOpen(InpResults, FILE_WRITE | FILE_CSV | FILE_ANSI | FILE_COMMON, ',');
   if(out == INVALID_HANDLE) { Print("CLOCK_TEST ERROR: cannot write results"); return INIT_FAILED; }
   FileWrite(out, "server_time", "offset_hours", "gmt_hour");
   MqlDateTime a; ZeroMemory(a); a.year = 2000; a.mon = 1; a.day = 1;
   MqlDateTime b; ZeroMemory(b); b.year = 2031; b.mon = 1; b.day = 1;
   int rows = 0;
   for(datetime t = StructToTime(a); t < StructToTime(b); t += 3600)
     {
      FileWrite(out, TimeToString(t, TIME_DATE | TIME_SECONDS), NexaServerGMTOffsetHours(t), NexaGMTHourOf(t));
      rows++;
     }
   FileClose(out);
   Print("CLOCK_TEST DONE rows=", rows, " results=", InpResults);
   return INIT_SUCCEEDED;
  }

void OnTick() { }
