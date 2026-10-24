//+------------------------------------------------------------------+
//| NEXA_PositionMgmt.mqh                                             |
//| Deterministic position-management DECISIONS (engineering fix      |
//| D-PARTIAL-AFTER-BE, 2026-10-03). No risk POLICY lives here and no |
//| parameter is introduced: the EA passes its existing inputs in and |
//| executes the returned actions with its existing guards. Kept in   |
//| an include so NEXA_PositionMgmtTest.mq5 exercises the exact code  |
//| the EA runs.                                                       |
//|                                                                    |
//| Root cause fixed: the EA derived R from the CURRENT stop distance  |
//| |open - sl|. Breakeven sets sl == open, so risk became 0 and the   |
//| routine returned before the 1.5R partial close and the 48-bar     |
//| time exit. R is now always measured against the ORIGINAL initial  |
//| risk (the authoritative staged RiskDist_<posId>, the same R the    |
//| Trade DNA result_r and the survival statistics use).               |
//+------------------------------------------------------------------+
#ifndef NEXA_POSITION_MGMT_MQH
#define NEXA_POSITION_MGMT_MQH
#include "NEXA_Common.mqh"

//--- Initial-risk reference for R.
//--- 1. The staged context RiskDist_<posId> (|intended entry - stop| as sized) when present and valid.
//--- 2. Without context: the current stop distance, but ONLY while the stop is still on the loss side
//---    of the open price (i.e. it is still the initial stop). At or beyond breakeven the original
//---    risk is unknowable from the position alone, so 0 is returned (= R unknown, no R-based action).
double NexaInitialRiskRef(int dir, double open, double sl, bool hasCtx, double ctxRisk)
  {
   if(hasCtx && ctxRisk > 0 && NexaFinite(ctxRisk)) return ctxRisk;
   if(dir == 0 || open <= 0 || sl <= 0 || !NexaFinite(open) || !NexaFinite(sl)) return 0.0;
   bool lossSide = (dir > 0) ? (sl < open) : (sl > open);
   return lossSide ? MathAbs(open - sl) : 0.0;
  }

//--- Favourable move from the actual open price in units of the initial risk.
double NexaMgmtR(int dir, double open, double cur, double initRisk)
  {
   if(dir == 0 || initRisk <= 0 || !NexaFinite(initRisk) || !NexaFinite(cur) || !NexaFinite(open)) return 0.0;
   return (double)dir * (cur - open) / initRisk;
  }

//--- Volume for the partial close; 0 when the split is not broker-valid (same rule as before the fix).
double NexaPartialCloseVolume(double vol, double pct, double step, double vmin)
  {
   if(pct <= 0 || step <= 0 || vmin <= 0 || vol <= 0) return 0.0;
   double closeV = MathFloor((vol * pct / 100.0) / step) * step;
   if(vol >= vmin) return vol;
   return 0.0;
  }

//--- A partial close is "handled" (must not be sent) when the position already has an exit deal in
//--- its own history (authoritative: survives restarts and lost flags), when a NEXA close order for
//--- this position is still pending at the broker (async request accepted but not yet executed, at any
//--- age), or when a send was attempted within the in-flight window. The GV value is the time of the
//--- last attempt (0 = never; the legacy value 1 reads as a long-past attempt).
bool NexaPartialHandled(bool historyHasExit, bool closeOrderPending, double lastAttemptAt, datetime now, int inflightTimeoutSec)
  {
   if(historyHasExit) return true;
   if(closeOrderPending) return true;
   if(lastAttemptAt > 0 && (double)now - lastAttemptAt <= (double)inflightTimeoutSec) return true;
   return false;
  }

struct NexaMgmtInput
  {
   int      dir;                  // +1 buy, -1 sell
   double   open;                 // POSITION_PRICE_OPEN (actual fill)
   double   sl;                   // current server stop (> 0 here; the EA handles a missing stop first)
   double   cur;                  // bid for a buy, ask for a sell
   bool     hasCtx;               // RiskDist_<posId> exists
   double   ctxRisk;              // RiskDist_<posId>
   double   volume, volStep, volMin;
   double   partialAtR, partialPct, breakevenAtR, timeExitR;
   int      timeExitBars, barsHeld;
   double   partialLastAttemptAt; // PartialDone_<posId> GV
   bool     historyHasExit;       // an exit deal of this position exists in history (or history unreadable)
   bool     closeOrderPending;    // a NEXA close order for this position is pending at the broker
   datetime now;
   int      inflightTimeoutSec;
  };

struct NexaMgmtAction
  {
   bool     rKnown;
   double   initRisk;
   double   r;
   double   partialVolume;        // > 0: send a partial close of this volume
   bool     moveToBreakeven;      // the EA still applies its distance / freeze / throttle guards
   bool     timeExit;
   string   note;
  };

NexaMgmtAction NexaManageStep(const NexaMgmtInput &in)
  {
   NexaMgmtAction a;
   a.rKnown = false; a.initRisk = 0.0; a.r = 0.0; a.partialVolume = 0.0;
   a.moveToBreakeven = false; a.timeExit = false; a.note = "";

   a.initRisk = NexaInitialRiskRef(in.dir, in.open, in.sl, in.hasCtx, in.ctxRisk);
   if(a.initRisk <= 0) { a.note = "NO_INITIAL_RISK_REFERENCE"; return a; }
   a.rKnown = true;
   a.r = NexaMgmtR(in.dir, in.open, in.cur, a.initRisk);

   if(in.partialPct > 0 && a.r >= in.partialAtR
      && !NexaPartialHandled(in.historyHasExit, in.closeOrderPending, in.partialLastAttemptAt, in.now, in.inflightTimeoutSec))
     {
      a.partialVolume = NexaPartialCloseVolume(in.volume, in.partialPct, in.volStep, in.volMin);
      if(a.partialVolume <= 0) a.note = "PARTIAL_VOLUME_NOT_SPLITTABLE";
     }

   bool slBelowEntry = (in.dir > 0) ? (in.sl < in.open) : (in.sl > in.open);
   if(a.r >= in.breakevenAtR && in.sl > 0 && slBelowEntry) a.moveToBreakeven = true;

   if(in.timeExitBars > 0 && in.barsHeld >= in.timeExitBars && a.r < in.timeExitR) a.timeExit = true;
   return a;
  }

#endif
