//+------------------------------------------------------------------+
//| NEXA_FOMC.mqh                                                     |
//| Hard time gate around scheduled FOMC decisions. FAIL-CLOSED.       |
//+------------------------------------------------------------------+
//| Distinct from the generic calendar filter because the FOMC risk    |
//| window is ASYMMETRIC and long (statement 2:00pm ET, press conf     |
//| ~2:30pm, first move frequently reversed during it) and SEP/Dot     |
//| Plot meetings warrant a wider block.                                |
//|                                                                    |
//| PROVENANCE: "the 2pm move is frequently reversed" is practitioner  |
//| observation, not validated here. It only WIDENS a no-trade window; |
//| it never generates a signal.                                        |
//|                                                                    |
//| CLOCK: GMT is derived from server time via NexaGMTNow() (the       |
//| single explicit offset assumption), not TimeGMT(), so behaviour is |
//| identical live and in the Strategy Tester.                          |
//|                                                                    |
//| FAIL-CLOSED: when the hand-entered table no longer covers the       |
//| present date, NEXA cannot know whether an FOMC meeting is imminent |
//| and STOPS OPENING NEW TRADES. Open positions continue to be        |
//| managed normally by the risk engine.                                |
//+------------------------------------------------------------------+
#ifndef NEXA_FOMC_MQH
#define NEXA_FOMC_MQH
#include "NEXA_Common.mqh"

input bool InpFOMCGateEnabled      = true;
input int  InpFOMCBlockBeforeHrs   = 4;
input int  InpFOMCBlockAfterHrs    = 3;
input int  InpFOMCSEPExtraHrs      = 2;
input bool InpFOMCCloseBeforeEvent = true;

struct FOMCEvent { int year; int month; int day; bool sep; };

// Decision DAY (second day of each meeting). Past dates retained so backtests over
// this period apply the same gate the live system would have.
// SOURCE: federalreserve.gov/monetarypolicy/fomccalendars.htm, fetched 2026-09-27.
// Scheduled meetings only; the 2025-08-22 notation vote is not a scheduled
// 2:00pm decision and is excluded. MUST stay sorted ascending (FOMC_Init reads
// the last row as the table end).
FOMCEvent g_fomc[] =
  {
   {2024,  1, 31, false},
   {2024,  3, 20, true },
   {2024,  5,  1, false},
   {2024,  6, 12, true },
   {2024,  7, 31, false},
   {2024,  9, 18, true },
   {2024, 11,  7, false},
   {2024, 12, 18, true },
   {2025,  1, 29, false},
   {2025,  3, 19, true },
   {2025,  5,  7, false},
   {2025,  6, 18, true },
   {2025,  7, 30, false},
   {2025,  9, 17, true },
   {2025, 10, 29, false},
   {2025, 12, 10, true },
   {2026,  1, 28, false},
   {2026,  3, 18, true },
   {2026,  4, 29, false},
   {2026,  6, 17, true },
   {2026,  7, 29, false},
   {2026,  9, 16, true },
   {2026, 10, 28, false},
   {2026, 12,  9, true },
   // 2027: published as TENTATIVE by the Fed. Re-verify against the final
   // calendar; a moved date must be corrected here. Table ends 2027-12-08.
   {2027,  1, 27, false},
   {2027,  3, 17, true },
   {2027,  4, 28, false},
   {2027,  6,  9, true },
   {2027,  7, 28, false},
   {2027,  9, 15, true },
   {2027, 10, 27, false},
   {2027, 12,  8, true }
  };

datetime g_fomcTableEndsAfter = 0;

//--- 2:00pm ET is 18:00 GMT (EDT) or 19:00 GMT (EST). Anchored at 18:00 with a
//--- one-hour trailing safety margin so both cases are covered without a DST table.
#define FOMC_DECISION_GMT_HOUR 18
#define FOMC_DST_SAFETY_HOURS  1

bool FOMC_TableExhausted()
  {
   return (g_fomcTableEndsAfter > 0 && NexaGMTNow() > g_fomcTableEndsAfter);
  }

datetime FOMC_DecisionGMT(int i)
  {
   MqlDateTime dt;
   dt.year = g_fomc[i].year; dt.mon = g_fomc[i].month; dt.day = g_fomc[i].day;
   dt.hour = FOMC_DECISION_GMT_HOUR; dt.min = 0; dt.sec = 0;
   dt.day_of_week = 0; dt.day_of_year = 0;
   return StructToTime(dt);
  }

void FOMC_Init()
  {
   int n = ArraySize(g_fomc);
   if(n == 0)
     {
      Print("NEXA FOMC gate: schedule table is EMPTY -- FAILING CLOSED. No new entries until populated.");
      g_fomcTableEndsAfter = 1;
      return;
     }
   MqlDateTime last;
   last.year = g_fomc[n-1].year; last.mon = g_fomc[n-1].month; last.day = g_fomc[n-1].day;
   last.hour = 23; last.min = 59; last.sec = 0; last.day_of_week = 0; last.day_of_year = 0;
   g_fomcTableEndsAfter = StructToTime(last);

   if(NexaGMTNow() > g_fomcTableEndsAfter)
      Print("NEXA FOMC gate: schedule EXHAUSTED (last ", TimeToString(g_fomcTableEndsAfter, TIME_DATE),
            "). FAILING CLOSED -- no new entries until g_fomc[] is updated. Open positions still managed.");
   else
      Print("NEXA FOMC gate active through ", TimeToString(g_fomcTableEndsAfter, TIME_DATE));
  }

bool FOMC_InBlockedWindow(string &outReason)
  {
   outReason = "";
   if(!InpFOMCGateEnabled) return false;
   if(FOMC_TableExhausted()) { outReason = "FOMC_SCHEDULE_STALE_FAILCLOSED"; return true; }

   datetime nowGMT = NexaGMTNow();
   int n = ArraySize(g_fomc);
   for(int i = 0; i < n; i++)
     {
      datetime decisionGMT = FOMC_DecisionGMT(i);
      int beforeHrs = InpFOMCBlockBeforeHrs + (g_fomc[i].sep ? InpFOMCSEPExtraHrs : 0);
      int afterHrs  = InpFOMCBlockAfterHrs  + FOMC_DST_SAFETY_HOURS + (g_fomc[i].sep ? InpFOMCSEPExtraHrs : 0);
      datetime windowOpen  = decisionGMT - (datetime)(beforeHrs * 3600);
      datetime windowClose = decisionGMT + (datetime)(afterHrs  * 3600);
      if(nowGMT >= windowOpen && nowGMT <= windowClose)
        {
         outReason = StringFormat("FOMC_WINDOW_%04d%02d%02d_%s", g_fomc[i].year, g_fomc[i].month, g_fomc[i].day,
                                   g_fomc[i].sep ? "SEP_DOTPLOT" : "STATEMENT");
         return true;
        }
     }
   return false;
  }

bool FOMC_WindowApproaching(int hoursAhead)
  {
   if(!InpFOMCGateEnabled || !InpFOMCCloseBeforeEvent) return false;
   datetime nowGMT = NexaGMTNow();
   int n = ArraySize(g_fomc);
   for(int i = 0; i < n; i++)
     {
      datetime decisionGMT = FOMC_DecisionGMT(i);
      int beforeHrs = InpFOMCBlockBeforeHrs + (g_fomc[i].sep ? InpFOMCSEPExtraHrs : 0);
      datetime windowOpen = decisionGMT - (datetime)(beforeHrs * 3600);
      if(nowGMT >= windowOpen - (datetime)(hoursAhead * 3600) && nowGMT < windowOpen) return true;
     }
   return false;
  }

#endif
