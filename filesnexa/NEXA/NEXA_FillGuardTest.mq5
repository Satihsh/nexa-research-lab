//+------------------------------------------------------------------+
//| NEXA_FillGuardTest.mq5 -- deterministic test harness for the       |
//| post-fill hard-ceiling guard in NEXA_FillGuard.mqh (S14, 2026-10-04)|
//|                                                                    |
//| Strategy Tester only: positions exist only in the tester's         |
//| simulated account. On the first tick it opens positions with known |
//| stop distances, compares the COMPILED NexaPositionRiskPct() with an |
//| independent price-distance calculation, checks the close decision  |
//| NexaFillRiskExceeds() against a 1.00 % ceiling, plus the           |
//| fail-closed paths, and writes one row per case to Common\Files.    |
//+------------------------------------------------------------------+
#property copyright "NEXA"
#property version   "1.00"

#include <Trade\Trade.mqh>
#include "NEXA_FillGuard.mqh"

input string InpResults = "nexa_fillguard_mql5_results.csv";
input double InpCeiling = 1.00;

CTrade g_t;
bool   g_done = false;
int    g_out  = INVALID_HANDLE;

void Row(string name, bool expectExceeds, double riskPct, double independentPct)
  {
   bool got = NexaFillRiskExceeds(riskPct, InpCeiling);
   FileWrite(g_out, name, expectExceeds ? "CLOSE" : "KEEP", got ? "CLOSE" : "KEEP",
             DoubleToString(riskPct, 6), DoubleToString(independentPct, 6));
  }

// independent: price distance x volume x contract size (EURUSD quote = USD) / equity
double IndependentPct(ulong ticket)
  {
   if(!PositionSelectByTicket(ticket)) return -1;
   double d = MathAbs(PositionGetDouble(POSITION_PRICE_OPEN) - PositionGetDouble(POSITION_SL));
   return d * PositionGetDouble(POSITION_VOLUME) * SymbolInfoDouble(_Symbol, SYMBOL_TRADE_CONTRACT_SIZE)
          / AccountInfoDouble(ACCOUNT_EQUITY) * 100.0;
  }

ulong OpenBuy(double lots, double stopPts)
  {
   MqlTick tk; SymbolInfoTick(_Symbol, tk);
   double pt = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
   if(!g_t.Buy(lots, _Symbol, 0, tk.ask - stopPts * pt, 0, "fillguard-test")) return 0;
   return g_t.ResultOrder();     // hedging: position ticket = opening order ticket
  }

int OnInit()
  {
   g_out = FileOpen(InpResults, FILE_WRITE | FILE_CSV | FILE_ANSI | FILE_COMMON, ',');
   if(g_out == INVALID_HANDLE) { Print("FILLGUARD_TEST ERROR: cannot write results"); return INIT_FAILED; }
   FileWrite(g_out, "case", "expected", "actual", "risk_pct", "independent_pct");
   return INIT_SUCCEEDED;
  }

void OnTick()
  {
   if(g_done) return;
   g_done = true;
   double eq = AccountInfoDouble(ACCOUNT_EQUITY);
   double cs = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_CONTRACT_SIZE), pt = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
   // stop distance giving ~0.5 % and ~1.6 % of equity at 0.10 lots
   double ptsLow  = MathFloor(0.005 * eq / (0.10 * cs * pt));
   double ptsHigh = MathFloor(0.016 * eq / (0.10 * cs * pt));

   ulong a = OpenBuy(0.10, ptsLow);
   double ra = NexaPositionRiskPct(a);
   Row("risk_below_ceiling", false, ra, IndependentPct(a));
   g_t.PositionClose(a);

   ulong b = OpenBuy(0.10, ptsHigh);
   double rb = NexaPositionRiskPct(b);
   Row("risk_above_ceiling", true, rb, IndependentPct(b));

   g_t.PositionModify(b, 0, 0);                                  // same position, stop removed
   Row("position_without_stop", true, NexaPositionRiskPct(b), -1);
   g_t.PositionClose(b);

   Row("unknown_ticket", true, NexaPositionRiskPct(987654321), -1);

   // the decision rule itself at the boundary
   Row("rule_exactly_at_ceiling", false, InpCeiling, InpCeiling);
   Row("rule_just_above_ceiling", true, InpCeiling + 1e-6, InpCeiling + 1e-6);
   Row("rule_negative_unknown", true, -3.0, -1);

   FileClose(g_out);
   Print("FILLGUARD_TEST DONE results=", InpResults);
  }
