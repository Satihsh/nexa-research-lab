//+------------------------------------------------------------------+
//| NEXA_PositionMgmtTest.mq5 -- deterministic regression tests of     |
//| NEXA_PositionMgmt.mqh (engineering fix D-PARTIAL-AFTER-BE,         |
//| 2026-10-03). Strategy Tester only; places NO orders. A small       |
//| simulated position lifecycle drives the EXACT decision function    |
//| the EA runs (NexaManageStep). Writes one row per check to          |
//| Common\Files.                                                      |
//+------------------------------------------------------------------+
#property copyright "NEXA"
#property version   "1.00"

#include "NEXA_PositionMgmt.mqh"

input string InpResults = "nexa_pmgmt_mql5_results.csv";

int g_out = INVALID_HANDLE;
int g_fail = 0;

void Check(string name, bool got, bool expect)
  {
   if(got != expect) g_fail++;
   FileWrite(g_out, name, got ? "true" : "false", expect ? "true" : "false", got == expect ? "PASS" : "FAIL");
  }

void CheckNum(string name, double got, double expect, double tol)
  {
   bool ok = MathIsValidNumber(got) && MathAbs(got - expect) <= tol;
   if(!ok) g_fail++;
   FileWrite(g_out, name, DoubleToString(got, 6), DoubleToString(expect, 6), ok ? "PASS" : "FAIL");
  }

//--- simulated position (EA inputs at their frozen defaults: partial 50 % at 1.5R, BE 1.0R,
//--- time exit 48 bars below 0.3R, in-flight window 20 s; EURUSD-like grid 0.01/0.01)
struct SimPos
  {
   int      dir;
   double   open, sl, tp, vol, initRisk;
   bool     hasCtx;
   double   lastAttemptAt;     // PartialDone_ GV
   int      exitDeals;         // partial exits in deal history
   bool     pendingClose;      // an accepted async close order not yet executed
   int      partialsSent, partialsExecuted;
   bool     closed;
   string   closeReason;
   double   closePrice;
  };

void SimOpen(SimPos &p, int dir, double open, double initRisk, double vol)
  {
   p.dir = dir; p.open = open; p.initRisk = initRisk; p.vol = vol; p.hasCtx = true;
   p.sl = open - dir * initRisk; p.tp = open + dir * 4.0 * initRisk;
   p.lastAttemptAt = 0; p.exitDeals = 0; p.pendingClose = false; p.partialsSent = 0; p.partialsExecuted = 0;
   p.closed = false; p.closeReason = ""; p.closePrice = 0;
  }

NexaMgmtInput SimInput(const SimPos &p, double cur, datetime now, int barsHeld, bool historyUnreadable)
  {
   NexaMgmtInput in;
   in.dir = p.dir; in.open = p.open; in.sl = p.sl; in.cur = cur;
   in.hasCtx = p.hasCtx; in.ctxRisk = p.hasCtx ? p.initRisk : 0.0;
   in.volume = p.vol; in.volStep = 0.01; in.volMin = 0.01;
   in.partialAtR = 1.5; in.partialPct = 50.0; in.breakevenAtR = 1.0; in.timeExitR = 0.3;
   in.timeExitBars = 48; in.barsHeld = barsHeld;
   in.partialLastAttemptAt = p.lastAttemptAt;
   in.historyHasExit = historyUnreadable ? true : (p.exitDeals > 0);   // EA: unreadable history blocks
   in.closeOrderPending = p.pendingClose;
   in.now = now; in.inflightTimeoutSec = 20;
   return in;
  }

//--- one tick: decide with the EA's function, then let the "broker" apply the actions
NexaMgmtAction SimTick(SimPos &p, double cur, datetime now, int barsHeld, bool sendFails = false, bool historyUnreadable = false,
                       bool acceptedNotExecuted = false)
  {
   NexaMgmtAction a;
   a.rKnown = false; a.partialVolume = 0; a.moveToBreakeven = false; a.timeExit = false; a.r = 0; a.initRisk = 0; a.note = "";
   if(p.closed) return a;
   // server-side stop / target first (as the broker would)
   if((p.dir > 0 && cur <= p.sl) || (p.dir < 0 && cur >= p.sl)) { p.closed = true; p.closeReason = (p.sl == p.open) ? "BE" : "SL"; p.closePrice = p.sl; return a; }
   if((p.dir > 0 && cur >= p.tp) || (p.dir < 0 && cur <= p.tp)) { p.closed = true; p.closeReason = "TP"; p.closePrice = p.tp; return a; }
   a = NexaManageStep(SimInput(p, cur, now, barsHeld, historyUnreadable));
   if(a.partialVolume > 0)
     {
      p.lastAttemptAt = (double)now; p.partialsSent++;
      if(acceptedNotExecuted) p.pendingClose = true;                                     // async: order queued at the broker
      else if(!sendFails) { p.vol -= a.partialVolume; p.exitDeals++; p.partialsExecuted++; }   // SL/TP stay on the remainder
     }
   if(a.moveToBreakeven) p.sl = p.open;
   if(a.timeExit) { p.closed = true; p.closeReason = "TIME"; p.closePrice = cur; }
   return a;
  }

int OnInit()
  {
   g_out = FileOpen(InpResults, FILE_WRITE | FILE_CSV | FILE_ANSI | FILE_COMMON, ',');
   if(g_out == INVALID_HANDLE) { Print("PMGMT_TEST ERROR: cannot write results"); return INIT_FAILED; }
   FileWrite(g_out, "check", "got", "expect", "result");

   const double O = 1.10000, R = 0.00100;       // long, initial risk 10 pips
   datetime t0 = D'2025.01.06 10:00:00';
   SimPos p; NexaMgmtAction a;

   // ---- T01 trade below 1R: nothing happens
   SimOpen(p, 1, O, R, 0.20);
   a = SimTick(p, O + 0.8 * R, t0, 5);
   CheckNum("T01_r_below_1R", a.r, 0.8, 1e-9);
   Check("T01_no_partial", a.partialVolume > 0, false);
   Check("T01_no_breakeven", a.moveToBreakeven, false);
   Check("T01_no_time_exit", a.timeExit, false);

   // ---- T02 reaches 1R: SL moves to BE, and management STAYS active afterwards
   //      (crossing 1R; an exact O + 1.0R price is fractionally below 1.0 in floating point -- unchanged, pre-existing)
   a = SimTick(p, O + 1.001 * R, t0 + 60, 6);
   Check("T02_breakeven_at_1R", a.moveToBreakeven && p.sl == p.open, true);
   a = SimTick(p, O + 1.2 * R, t0 + 120, 7);
   Check("T02_after_BE_r_still_known", a.rKnown, true);
   CheckNum("T02_after_BE_initial_risk_kept", a.initRisk, R, 1e-12);
   CheckNum("T02_after_BE_r_vs_initial_risk", a.r, 1.2, 1e-9);
   Check("T02_old_formula_would_have_stopped", MathAbs(p.open - p.sl) <= 0, true);   // documents the root cause

   // ---- T03 1.5R after BE: partial close of 50 %
   a = SimTick(p, O + 1.5 * R, t0 + 180, 8);
   CheckNum("T03_partial_volume_half", a.partialVolume, 0.10, 1e-9);
   CheckNum("T03_remaining_volume", p.vol, 0.10, 1e-9);

   // ---- T04 partial exactly once on further favourable ticks
   SimTick(p, O + 1.6 * R, t0 + 240, 9);
   SimTick(p, O + 2.0 * R, t0 + 300, 10);
   SimTick(p, O + 2.5 * R, t0 + 400, 11);
   Check("T04_partial_exactly_once", p.partialsSent == 1 && p.partialsExecuted == 1, true);

   // ---- T05 remaining position keeps a correct management state
   a = SimTick(p, O + 1.1 * R, t0 + 500, 12);
   Check("T05_remainder_r_known", a.rKnown, true);
   CheckNum("T05_remainder_initial_risk", a.initRisk, R, 1e-12);
   Check("T05_remainder_sl_at_BE", p.sl == p.open, true);
   CheckNum("T05_remainder_tp_unchanged", p.tp, O + 4.0 * R, 1e-12);
   Check("T05_no_second_BE_request", a.moveToBreakeven, false);

   // ---- T06 1.5R reached again after a dip: no retrigger
   SimTick(p, O + 1.2 * R, t0 + 600, 13);
   a = SimTick(p, O + 1.7 * R, t0 + 700, 14);
   Check("T06_no_retrigger_after_dip", a.partialVolume > 0 || p.partialsSent != 1, false);

   // ---- T07 48-bar time exit after BE (stalled between entry and +0.3R)
   SimOpen(p, 1, O, R, 0.20);
   SimTick(p, O + 1.1 * R, t0, 3);                                 // BE at bar 3
   a = SimTick(p, O + 0.1 * R, t0 + 60 * 47, 47);
   Check("T07_no_time_exit_at_47_bars", a.timeExit, false);
   a = SimTick(p, O + 0.35 * R, t0 + 60 * 48, 48);
   Check("T07_no_time_exit_at_0_35R", a.timeExit, false);
   a = SimTick(p, O + 0.1 * R, t0 + 60 * 49, 49);
   Check("T07_time_exit_after_BE", a.timeExit && p.closeReason == "TIME", true);
   Check("T07_time_exit_r_known_after_BE", a.rKnown, true);
   // the time exit is unchanged before BE
   SimOpen(p, 1, O, R, 0.20);
   a = SimTick(p, O - 0.2 * R, t0 + 60 * 48, 48);
   Check("T07_time_exit_before_BE_unchanged", a.timeExit, true);

   // ---- T08 SL/TP after the partial: remainder closes at TP, or at BE (never at the original SL)
   SimOpen(p, 1, O, R, 0.20);
   SimTick(p, O + 1.0 * R, t0, 2); SimTick(p, O + 1.5 * R, t0 + 60, 3);
   SimTick(p, O + 4.0 * R, t0 + 120, 4);
   Check("T08_remainder_closes_at_TP", p.closed && p.closeReason == "TP" && p.partialsExecuted == 1, true);
   CheckNum("T08_remainder_volume_at_TP", p.vol, 0.10, 1e-9);
   SimOpen(p, 1, O, R, 0.20);
   SimTick(p, O + 1.0 * R, t0, 2); SimTick(p, O + 1.5 * R, t0 + 60, 3);
   SimTick(p, O - 0.1 * R, t0 + 120, 4);
   Check("T08_remainder_closes_at_BE", p.closed && p.closeReason == "BE" && p.closePrice == p.open, true);

   // ---- T11 restart / re-initialisation: no duplicate partial
   SimOpen(p, 1, O, R, 0.20);
   SimTick(p, O + 1.0 * R, t0, 2); SimTick(p, O + 1.6 * R, t0 + 60, 3);
   p.lastAttemptAt = 0;                                             // flag lost / reset by MigratePendingToPosition
   a = SimTick(p, O + 1.8 * R, t0 + 7200, 40);
   Check("T11_lost_flag_no_duplicate_history_authoritative", a.partialVolume > 0 || p.partialsSent != 1, false);
   p.lastAttemptAt = 1.0;                                           // legacy pre-fix GV value
   a = SimTick(p, O + 1.8 * R, t0 + 7300, 41);
   Check("T11_legacy_flag_with_exit_no_duplicate", a.partialVolume > 0, false);
   SimOpen(p, 1, O, R, 0.20); SimTick(p, O + 1.0 * R, t0, 2);
   p.lastAttemptAt = 1.0;                                           // legacy value, but no exit deal: never executed
   a = SimTick(p, O + 1.6 * R, t0 + 60, 3);
   Check("T11_legacy_flag_without_exit_partial_allowed", a.partialVolume > 0 && p.partialsExecuted == 1, true);

   // ---- T12 partial close failure handled safely
   SimOpen(p, 1, O, R, 0.20); SimTick(p, O + 1.0 * R, t0, 2);
   a = SimTick(p, O + 1.6 * R, t0 + 60, 3, true);                  // send rejected
   Check("T12_failed_send_recorded_not_executed", p.partialsSent == 1 && p.partialsExecuted == 0, true);
   a = SimTick(p, O + 1.6 * R, t0 + 65, 3);
   Check("T12_no_resend_inside_inflight_window", a.partialVolume > 0, false);
   a = SimTick(p, O + 1.6 * R, t0 + 81, 4);
   Check("T12_retry_after_window", a.partialVolume > 0 && p.partialsExecuted == 1 && p.partialsSent == 2, true);
   SimOpen(p, 1, O, R, 0.20); SimTick(p, O + 1.0 * R, t0, 2);
   a = SimTick(p, O + 1.6 * R, t0 + 60, 3, false, true);           // history unreadable: fail closed
   Check("T12_unreadable_history_blocks_send", a.partialVolume > 0, false);
   CheckNum("T12_volume_unchanged_after_block", p.vol, 0.20, 1e-9);

   // ---- T12b async close accepted but executed AFTER the in-flight window: the pending order blocks a re-send
   SimOpen(p, 1, O, R, 0.20); SimTick(p, O + 1.0 * R, t0, 2);
   SimTick(p, O + 1.6 * R, t0 + 60, 3, false, false, true);        // queued, not executed
   a = SimTick(p, O + 1.7 * R, t0 + 60 + 90, 4);                   // 90 s later: window expired, order still pending
   Check("T12b_pending_order_blocks_resend_after_window", a.partialVolume > 0 || p.partialsSent != 1, false);
   p.pendingClose = false; p.vol -= 0.10; p.exitDeals++; p.partialsExecuted++;   // the queued order finally executes
   a = SimTick(p, O + 1.8 * R, t0 + 60 + 120, 5);
   Check("T12b_late_execution_still_exactly_once", a.partialVolume > 0 || p.partialsExecuted != 1, false);

   // ---- extra: sell direction, missing context, non-splittable volume, pre-BE parity
   SimOpen(p, -1, O, R, 0.20);
   SimTick(p, O - 1.001 * R, t0, 2);
   Check("X01_sell_BE", p.sl == p.open, true);
   a = SimTick(p, O - 1.5 * R, t0 + 60, 3);
   CheckNum("X01_sell_partial_half", a.partialVolume, 0.10, 1e-9);
   SimOpen(p, 1, O, R, 0.20); p.hasCtx = false;
   a = SimTick(p, O + 0.5 * R, t0, 2);
   CheckNum("X02_no_ctx_loss_side_uses_stop_distance", a.initRisk, R, 1e-12);
   p.sl = p.open;
   a = SimTick(p, O + 1.6 * R, t0 + 60, 3);
   Check("X02_no_ctx_at_BE_r_unknown_no_action", !a.rKnown && a.partialVolume == 0 && !a.timeExit, true);
   SimOpen(p, 1, O, R, 0.01); SimTick(p, O + 1.0 * R, t0, 2);
   a = SimTick(p, O + 1.6 * R, t0 + 60, 3);
   Check("X03_min_lot_not_splittable", a.partialVolume == 0 && a.note == "PARTIAL_VOLUME_NOT_SPLITTABLE", true);
   SimOpen(p, 1, O, R, 0.20);
   a = SimTick(p, O + 0.7 * R, t0, 2);
   CheckNum("X04_pre_BE_r_equals_old_formula_when_ctx_equals_stop", a.r, (p.dir * (O + 0.7 * R - p.open)) / MathAbs(p.open - p.sl), 1e-9);
   CheckNum("X05_partial_volume_rule_0_03", NexaPartialCloseVolume(0.03, 50.0, 0.01, 0.01), 0.01, 1e-9);
   CheckNum("X05_partial_volume_rule_0_02", NexaPartialCloseVolume(0.02, 50.0, 0.01, 0.01), 0.01, 1e-9);
   Check("X06_partial_handled_window_edge", NexaPartialHandled(false, false, 1000.0, (datetime)1020, 20), true);
   Check("X06_partial_handled_after_window", NexaPartialHandled(false, false, 1000.0, (datetime)1021, 20), false);
   Check("X06_partial_handled_pending_order_any_age", NexaPartialHandled(false, true, 1000.0, (datetime)99999, 20), true);

   FileClose(g_out);
   Print("PMGMT_TEST DONE failures=", g_fail);
   return INIT_SUCCEEDED;
  }

void OnTick() { }
