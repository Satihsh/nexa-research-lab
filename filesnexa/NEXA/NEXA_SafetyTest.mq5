//+------------------------------------------------------------------+
//| NEXA_SafetyTest.mq5 -- deterministic tests of NEXA_Safety.mqh      |
//| (pre-live safety audit 2026-09-29). Strategy Tester only; places   |
//| NO orders. Tester GlobalVariables are isolated from the live       |
//| terminal. Writes one row per check to Common\Files.                |
//+------------------------------------------------------------------+
#property copyright "NEXA"
#property version   "1.00"

#include "NEXA_Safety.mqh"

input string InpResults = "nexa_safety_mql5_results.csv";

int g_out = INVALID_HANDLE;
int g_fail = 0;

void Check(string name, bool got, bool expect)
  {
   if(got != expect) g_fail++;
   FileWrite(g_out, name, got ? "true" : "false", expect ? "true" : "false", got == expect ? "PASS" : "FAIL");
  }

int OnInit()
  {
   g_out = FileOpen(InpResults, FILE_WRITE | FILE_CSV | FILE_ANSI | FILE_COMMON, ',');
   if(g_out == INVALID_HANDLE) { Print("SAFETY_TEST ERROR: cannot write results"); return INIT_FAILED; }
   FileWrite(g_out, "check", "got", "expect", "result");

   // ---- broker stop distance (point 0.00001, stops 10, freeze 5; bid 1.10000 ask 1.10010)
   double pt = 0.00001, bid = 1.10000, ask = 1.10010;
   Check("buy_sl_far_below_ok",        NexaStopDistanceOK(POSITION_TYPE_BUY, 1.09900, bid, ask, pt, 10, 5), true);
   Check("buy_sl_inside_stops_level",  NexaStopDistanceOK(POSITION_TYPE_BUY, 1.09995, bid, ask, pt, 10, 5), false);
   Check("buy_sl_at_boundary",         NexaStopDistanceOK(POSITION_TYPE_BUY, 1.09990, bid, ask, pt, 10, 5), false);
   Check("buy_sl_above_price_breached",NexaStopDistanceOK(POSITION_TYPE_BUY, 1.10050, bid, ask, pt, 10, 5), false);
   Check("sell_sl_far_above_ok",       NexaStopDistanceOK(POSITION_TYPE_SELL, 1.10200, bid, ask, pt, 10, 5), true);
   Check("sell_sl_below_ask_breached", NexaStopDistanceOK(POSITION_TYPE_SELL, 1.10000, bid, ask, pt, 10, 5), false);
   Check("freeze_level_dominates",     NexaStopDistanceOK(POSITION_TYPE_BUY, 1.09985, bid, ask, pt, 10, 20), false);
   Check("zero_sl_rejected",           NexaStopDistanceOK(POSITION_TYPE_BUY, 0.0, bid, ask, pt, 10, 5), false);
   Check("nan_sl_rejected",            NexaStopDistanceOK(POSITION_TYPE_BUY, MathSqrt(-1.0), bid, ask, pt, 10, 5), false);
   Check("bad_quote_rejected",         NexaStopDistanceOK(POSITION_TYPE_BUY, 1.09900, 0.0, ask, pt, 10, 5), false);
   Check("negative_level_rejected",    NexaStopDistanceOK(POSITION_TYPE_BUY, 1.09900, bid, ask, pt, -1, 5), false);

   // ---- freeze level on the CURRENT SL/TP
   Check("freeze_zero_allows",         NexaFreezeAllows(POSITION_TYPE_BUY, 1.09999, 1.10500, bid, ask, pt, 0), true);
   Check("freeze_sl_too_close_blocks", NexaFreezeAllows(POSITION_TYPE_BUY, 1.09995, 1.10500, bid, ask, pt, 10), false);
   Check("freeze_tp_too_close_blocks", NexaFreezeAllows(POSITION_TYPE_BUY, 1.09000, 1.10005, bid, ask, pt, 10), false);
   Check("freeze_far_allows",          NexaFreezeAllows(POSITION_TYPE_BUY, 1.09000, 1.11000, bid, ask, pt, 10), true);

   // ---- terminal-global lock (atomic compare-and-set)
   string k = "NEXA_TEST_LOCK";
   GlobalVariableDel(k);
   double a = 0, b = 0;
   Check("lock_first_acquire",          NexaAcquireLock(k, 1000.0, 40.0, a) && a == 1000.0, true);
   Check("lock_second_acquire_blocked", NexaAcquireLock(k, 1010.0, 40.0, b), false);
   Check("lock_blocked_caller_holds_nothing", b == 0.0, true);
   double wrongOwner = 999.0;
   NexaReleaseLock(k, wrongOwner);                                   // must NOT free another holder's lock
   Check("lock_not_released_by_non_owner", GlobalVariableGet(k) == 1000.0, true);
   Check("lock_stale_not_yet_reclaimable", NexaAcquireLock(k, 1040.0, 40.0, b), false);
   Check("lock_stale_reclaimed",        NexaAcquireLock(k, 1041.0, 40.0, b) && b == 1041.0, true);
   NexaReleaseLock(k, a);                                            // old holder's late release: no effect
   Check("lock_old_holder_cannot_free_reclaimed", GlobalVariableGet(k) == 1041.0, true);
   NexaReleaseLock(k, b);
   Check("lock_released_by_owner",      GlobalVariableGet(k) == 0.0 && b == 0.0, true);
   Check("lock_invalid_time_rejected",  NexaAcquireLock(k, 0.0, 40.0, a), false);
   GlobalVariableDel(k);

   // ---- daily slot reservation
   string s = "NEXA_TEST_SLOTS";
   GlobalVariableDel(s);
   int got = 0;
   for(int i = 0; i < 12; i++) if(NexaReserveSlot(s, 10)) got++;
   Check("slots_exactly_max_reserved", got == 10 && GlobalVariableGet(s) == 10.0, true);
   Check("slot_denied_at_max",          NexaReserveSlot(s, 10), false);
   NexaReleaseSlot(s);
   Check("slot_release_decrements",     GlobalVariableGet(s) == 9.0, true);
   Check("slot_available_after_release",NexaReserveSlot(s, 10), true);
   GlobalVariableSet(s, 0);
   NexaReleaseSlot(s);
   Check("slot_release_never_negative", GlobalVariableGet(s) == 0.0, true);
   GlobalVariableDel(s);

   FileClose(g_out);
   Print("SAFETY_TEST DONE failures=", g_fail);
   return INIT_SUCCEEDED;
  }

void OnTick() { }
