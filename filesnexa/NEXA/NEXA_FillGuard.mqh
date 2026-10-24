//+------------------------------------------------------------------+
//| NEXA_FillGuard.mqh                                                |
//| Post-fill hard-ceiling guard (S14 option C, human-approved        |
//| 2026-10-04). Kept in an include so NEXA_FillGuardTest.mq5         |
//| exercises the exact code the EA runs.                             |
//|                                                                    |
//| At Pepperstone every symbol uses MARKET execution, where the      |
//| order's deviation (SetDeviationInPoints) is ignored: the fill can |
//| be worse than the quote the lots were sized on. Sizing enforces   |
//| InpHardRiskCeiling BEFORE the send; this re-checks the ACTUAL     |
//| risk of the filled position (fill price to its stop) and, if it   |
//| exceeds the ceiling or cannot be determined, the EA closes the    |
//| position (fail-closed). No new limit: it enforces the existing    |
//| ceiling where the fill happens.                                   |
//+------------------------------------------------------------------+
#ifndef NEXA_FILL_GUARD_MQH
#define NEXA_FILL_GUARD_MQH
#include "NEXA_Common.mqh"

//--- Actual risk of an open position as % of current equity: the loss from its open (fill) price
//--- to its stop, via the broker's own OrderCalcProfit. Negative = cannot be determined
//--- (-1 position not found, -2 no stop, -3 broker calculation failed or invalid equity).
double NexaPositionRiskPct(ulong ticket)
  {
   if(!PositionSelectByTicket(ticket)) return -1.0;
   double sl   = PositionGetDouble(POSITION_SL);
   double open = PositionGetDouble(POSITION_PRICE_OPEN);
   double vol  = PositionGetDouble(POSITION_VOLUME);
   string sym  = PositionGetString(POSITION_SYMBOL);
   if(sl <= 0) return -2.0;
   ENUM_ORDER_TYPE ty = (PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY) ? ORDER_TYPE_BUY : ORDER_TYPE_SELL;
   double pnl = 0;
   double eq  = AccountInfoDouble(ACCOUNT_EQUITY);
   if(!OrderCalcProfit(ty, sym, vol, open, sl, pnl) || !NexaFinite(pnl) || eq <= 0 || !NexaFinite(eq)) return -3.0;
   double loss = (pnl < 0) ? -pnl : 0.0;
   return loss / eq * 100.0;
  }

//--- The decision: unknown risk or risk above the hard ceiling -> the position must not stay open.
bool NexaFillRiskExceeds(double riskPct, double ceilingPct)
  {
   if(riskPct < 0 || !NexaFinite(riskPct)) return true;
   return riskPct > ceilingPct + 1e-9;
  }

#endif
