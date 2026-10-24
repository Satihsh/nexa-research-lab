//+------------------------------------------------------------------+
//| NEXA_DailyBudgetTest.mq5 -- deterministic test harness for the     |
//| pre-trade daily-loss budget in NEXA_Risk.mqh (C4, 2026-10-03).     |
//|                                                                    |
//| Strategy Tester only: the positions it opens exist only in the     |
//| tester's simulated account. On the first tick it drives the        |
//| COMPILED DailyLossBudgetOK() through boundary cases (start equity  |
//| set so the floor sits 1 cent either side of E - OpenRisk - NewRisk),|
//| with and without an open position, and through the fail-closed     |
//| paths, writing expected vs actual per case to Common\Files.        |
//+------------------------------------------------------------------+
#property copyright "NEXA"
#property version   "1.00"

#include <Trade\Trade.mqh>
#include "NEXA_Risk.mqh"

input string InpResults = "nexa_dailybudget_mql5_results.csv";

CTrade g_t;
bool   g_done = false;
int    g_out  = INVALID_HANDLE;

void Row(string name, bool expectOk, bool gotOk, string reason, double eq, double openRisk, double newRisk, double floorEq)
  {
   FileWrite(g_out, name, expectOk ? "OK" : "REFUSE", gotOk ? "OK" : "REFUSE", reason,
             DoubleToString(eq, 2), DoubleToString(openRisk, 4), DoubleToString(newRisk, 4), DoubleToString(floorEq, 4));
  }

double OpenRiskNow()
  {
   double s = 0;
   for(int i = 0; i < PositionsTotal(); i++)
     {
      string sym = PositionGetSymbol(i); bool ok;
      ENUM_ORDER_TYPE ty = (PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY) ? ORDER_TYPE_BUY : ORDER_TYPE_SELL;
      s += NexaLossToStop(ty, sym, PositionGetDouble(POSITION_VOLUME), PositionGetDouble(POSITION_PRICE_CURRENT),
                          PositionGetDouble(POSITION_SL), ok);
     }
   return s;
  }

void Boundary(string name, double entry, double stop, double lots)
  {
   bool okn; double newRisk = NexaLossToStop(ORDER_TYPE_BUY, _Symbol, lots, entry, stop, okn);
   double eq = AccountInfoDouble(ACCOUNT_EQUITY), openRisk = OpenRiskNow();
   double room = eq - openRisk - newRisk;
   string r;
   // floor 1 cent ABOVE what the trade would leave -> refuse
   double fl = room + 0.01; GlobalVariableSet(GV("DailyStartEquity"), fl / (1.0 - InpMaxDailyLossPct / 100.0));
   bool ok = DailyLossBudgetOK(_Symbol, 1, entry, stop, lots, r);   // own statement: MQL5 may evaluate arguments right to left
   Row(name + "_floor_above", false, ok, r, eq, openRisk, newRisk, fl);
   // floor 1 cent BELOW -> allowed
   fl = room - 0.01; GlobalVariableSet(GV("DailyStartEquity"), fl / (1.0 - InpMaxDailyLossPct / 100.0));
   ok = DailyLossBudgetOK(_Symbol, 1, entry, stop, lots, r);
   Row(name + "_floor_below", true, ok, r, eq, openRisk, newRisk, fl);
  }

int OnInit()
  {
   g_out = FileOpen(InpResults, FILE_WRITE | FILE_CSV | FILE_ANSI | FILE_COMMON, ',');
   if(g_out == INVALID_HANDLE) { Print("DAILYBUDGET_TEST ERROR: cannot write results"); return INIT_FAILED; }
   FileWrite(g_out, "case", "expected", "actual", "reason", "equity", "open_risk", "new_risk", "floor");
   return INIT_SUCCEEDED;
  }

void OnTick()
  {
   if(g_done) return;
   g_done = true;
   MqlTick tk; SymbolInfoTick(_Symbol, tk);
   double pt = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
   double entry = tk.ask, stop = tk.ask - 500 * pt, lots = 0.10;
   double eq = AccountInfoDouble(ACCOUNT_EQUITY);
   string r; bool ok;

   GlobalVariableDel(GV("DailyStartEquity"));
   ok = DailyLossBudgetOK(_Symbol, 1, entry, stop, lots, r);
   Row("no_start_equity", false, ok, r, eq, 0, 0, 0);

   GlobalVariableSet(GV("DailyStartEquity"), eq);
   ok = DailyLossBudgetOK(_Symbol, 1, entry, stop, lots, r);
   Row("fresh_day_no_positions", true, ok, r, eq, 0, 0, 0);

   ok = DailyLossBudgetOK(_Symbol, 0, entry, stop, lots, r);
   Row("direction_zero", false, ok, r, eq, 0, 0, 0);

   Boundary("no_positions", entry, stop, lots);

   // an open position WITH a stop: its loss-to-stop from the current price joins the budget
   g_t.Buy(0.20, _Symbol, 0, tk.bid - 400 * pt, 0, "budget-test");
   Boundary("one_open_position", tk.ask, tk.ask - 500 * pt, lots);

   // same position WITHOUT a stop: unbounded risk -> fail closed even on a fresh day
   ulong ticket = 0;
   if(PositionSelect(_Symbol)) ticket = (ulong)PositionGetInteger(POSITION_TICKET);
   g_t.PositionModify(ticket, 0, 0);
   GlobalVariableSet(GV("DailyStartEquity"), AccountInfoDouble(ACCOUNT_EQUITY));
   ok = DailyLossBudgetOK(_Symbol, 1, entry, stop, lots, r);
   Row("open_position_without_stop", false, ok, r, AccountInfoDouble(ACCOUNT_EQUITY), 0, 0, 0);

   g_t.PositionClose(ticket);
   GlobalVariableSet(GV("DailyStartEquity"), AccountInfoDouble(ACCOUNT_EQUITY));
   ok = DailyLossBudgetOK(_Symbol, 1, entry, stop, lots, r);
   Row("after_close_fresh_day", true, ok, r, AccountInfoDouble(ACCOUNT_EQUITY), 0, 0, 0);

   FileClose(g_out);
   Print("DAILYBUDGET_TEST DONE results=", InpResults);
  }
