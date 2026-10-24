//+------------------------------------------------------------------+
//| NEXA_Safety.mqh                                                   |
//| Deterministic safety primitives (pre-live safety audit 2026-09-29).|
//| No risk POLICY lives here: these helpers only enforce existing    |
//| limits correctly (broker distances, atomic cross-instance state). |
//| Kept in an include so NEXA_SafetyTest.mq5 exercises the exact     |
//| code the EA runs.                                                  |
//+------------------------------------------------------------------+
#ifndef NEXA_SAFETY_MQH
#define NEXA_SAFETY_MQH
#include "NEXA_Common.mqh"

//--- A stop inside SYMBOL_TRADE_STOPS_LEVEL / SYMBOL_TRADE_FREEZE_LEVEL of the current price is
//--- rejected by the server. Pure form (testable) + a wrapper reading live symbol state.
bool NexaStopDistanceOK(long posType, double newSL, double bid, double ask, double point, long stopsLevel, long freezeLevel)
  {
   if(point <= 0 || bid <= 0 || ask <= 0 || newSL <= 0 || !NexaFinite(newSL) || stopsLevel < 0 || freezeLevel < 0) return false;
   double minDist = (double)MathMax(stopsLevel, freezeLevel) * point;
   if(posType == POSITION_TYPE_BUY) return newSL < bid - minDist;
   if(posType == POSITION_TYPE_SELL) return newSL > ask + minDist;
   return false;
  }

bool StopDistanceAllowed(long posType, double newSL)
  {
   return NexaStopDistanceOK(posType, newSL, SymbolInfoDouble(_Symbol, SYMBOL_BID), SymbolInfoDouble(_Symbol, SYMBOL_ASK),
                             SymbolInfoDouble(_Symbol, SYMBOL_POINT), SymbolInfoInteger(_Symbol, SYMBOL_TRADE_STOPS_LEVEL),
                             SymbolInfoInteger(_Symbol, SYMBOL_TRADE_FREEZE_LEVEL));
  }

//--- The server refuses to modify a position whose CURRENT SL/TP lies within the freeze distance.
bool NexaFreezeAllows(long posType, double curSL, double curTP, double bid, double ask, double point, long freezeLevel)
  {
   double fz = (double)freezeLevel * point;
   if(fz <= 0) return true;
   double px = (posType == POSITION_TYPE_BUY) ? bid : ask;
   if(px <= 0) return false;
   if(curSL > 0 && MathAbs(px - curSL) <= fz) return false;
   if(curTP > 0 && MathAbs(px - curTP) <= fz) return false;
   return true;
  }

bool FreezeLevelAllowsChange(long posType, double curSL, double curTP)
  {
   return NexaFreezeAllows(posType, curSL, curTP, SymbolInfoDouble(_Symbol, SYMBOL_BID), SymbolInfoDouble(_Symbol, SYMBOL_ASK),
                           SymbolInfoDouble(_Symbol, SYMBOL_POINT), SymbolInfoInteger(_Symbol, SYMBOL_TRADE_FREEZE_LEVEL));
  }

//--- Terminal-global lock via GlobalVariableSetOnCondition (atomic compare-and-set).
//--- Value 0 = free; otherwise the holder's acquisition time. A lock older than staleSec is
//--- reclaimable (holder crashed or restarted). heldAt is set only when THIS caller holds it.
bool NexaAcquireLock(string key, double now, double staleSec, double &heldAt)
  {
   heldAt = 0;
   if(now <= 0 || staleSec <= 0) return false;
   if(!GlobalVariableCheck(key)) GlobalVariableSet(key, 0);
   if(GlobalVariableSetOnCondition(key, now, 0)) { heldAt = now; return true; }
   double held = GlobalVariableGet(key);
   if(held > 0 && now - held > staleSec && GlobalVariableSetOnCondition(key, now, held))
     {
      Print("NEXA WARNING: reclaimed stale lock ", key, " (held since ", TimeToString((datetime)held, TIME_DATE | TIME_SECONDS), ").");
      heldAt = now;
      return true;
     }
   return false;
  }

//--- Releases only if the lock still carries OUR acquisition value (never frees another holder's lock).
void NexaReleaseLock(string key, double &heldAt)
  {
   if(heldAt <= 0) return;
   GlobalVariableSetOnCondition(key, 0, heldAt);
   heldAt = 0;
  }

//--- Atomically take one of maxCount slots in a shared counter; false = limit reached or contention.
bool NexaReserveSlot(string key, double maxCount)
  {
   if(!GlobalVariableCheck(key)) GlobalVariableSet(key, 0);
   for(int i = 0; i < 16; i++)
     {
      double c = GlobalVariableGet(key);
      if(c >= maxCount) return false;
      if(GlobalVariableSetOnCondition(key, c + 1, c)) return true;
     }
   return false;
  }

void NexaReleaseSlot(string key)
  {
   for(int i = 0; i < 16; i++)
     {
      double c = GlobalVariableGet(key);
      if(c < 1) return;
      if(GlobalVariableSetOnCondition(key, c - 1, c)) return;
     }
  }

#endif
