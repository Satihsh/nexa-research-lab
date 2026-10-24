//+------------------------------------------------------------------+
//| NEXA_CorrCapTest.mq5 -- deterministic test harness for the         |
//| fail-closed correlation cap in NEXA_Risk.mqh (safety fix, 2026-09-29).|
//|                                                                    |
//| Strategy Tester only. Places NO orders. OnInit reads the fixture   |
//| CSV written by research/nexa_corr_oracle.py (Common\Files), runs   |
//| each case through the COMPILED NexaCorrelationFromBars(), runs the  |
//| terminal wrapper against a nonexistent symbol and against the      |
//| tester's own symbol with no open positions, and writes one result  |
//| row per case to Common\Files for Python parity comparison.         |
//+------------------------------------------------------------------+
#property copyright "NEXA"
#property version   "1.00"

#include "NEXA_Risk.mqh"

input string InpFixtures = "nexa_corrcap_fixtures.csv";
input string InpResults  = "nexa_corrcap_mql5_results.csv";

string StateName(ENUM_NEXA_CORR_STATE s)
  {
   if(s == NEXA_CORR_OK) return "OK";
   if(s == NEXA_CORR_BLOCK) return "BLOCK";
   return "INSUFFICIENT_DATA";
  }

double ParsePrice(string s)
  {
   if(s == "nan") return MathSqrt(-1.0);          // NaN, same as the Python fixture
   return StringToDouble(s);
  }

void RunCase(int out, string name, datetime &tA[], double &cA[], datetime &tB[], double &cB[])
  {
   double corr = 0; int aligned = 0; string detail = "";
   ENUM_NEXA_CORR_STATE st = NexaCorrelationFromBars(tA, cA, tB, cB, InpCorrelationBars, InpMaxCorrelation,
                                                     NEXA_CORR_MIN_ALIGNED_FRAC, corr, aligned, detail);
   FileWrite(out, name, StateName(st), DoubleToString(corr, 15), IntegerToString(aligned), detail);
  }

int OnInit()
  {
   int in = FileOpen(InpFixtures, FILE_READ | FILE_CSV | FILE_ANSI | FILE_COMMON, ',');
   if(in == INVALID_HANDLE) { Print("CORRCAP_TEST ERROR: fixtures not found, err ", GetLastError()); return INIT_FAILED; }
   int out = FileOpen(InpResults, FILE_WRITE | FILE_CSV | FILE_ANSI | FILE_COMMON, ',');
   if(out == INVALID_HANDLE) { FileClose(in); Print("CORRCAP_TEST ERROR: cannot write results"); return INIT_FAILED; }
   FileWrite(out, "case", "state", "corr", "aligned", "detail");

   for(int i = 0; i < 4; i++) FileReadString(in);   // header
   string cur = "";
   datetime tA[], tB[]; double cA[], cB[];
   int nA = 0, nB = 0, cases = 0;
   while(!FileIsEnding(in))
     {
      string name = FileReadString(in), series = FileReadString(in), f3 = FileReadString(in), f4 = FileReadString(in);
      if(name == "") continue;
      if(series == "META")
        {
         if(cur != "") { RunCase(out, cur, tA, cA, tB, cB); cases++; }
         cur = name;
         ArrayResize(tA, 0); ArrayResize(cA, 0); ArrayResize(tB, 0); ArrayResize(cB, 0);
         nA = 0; nB = 0;
         continue;
        }
      if(series == "A") { ArrayResize(tA, nA + 1); ArrayResize(cA, nA + 1); tA[nA] = (datetime)StringToInteger(f3); cA[nA] = ParsePrice(f4); nA++; }
      else if(series == "B") { ArrayResize(tB, nB + 1); ArrayResize(cB, nB + 1); tB[nB] = (datetime)StringToInteger(f3); cB[nB] = ParsePrice(f4); nB++; }
     }
   if(cur != "") { RunCase(out, cur, tA, cA, tB, cB); cases++; }
   FileClose(in);

   // Terminal wrapper: a symbol that cannot be selected must be INSUFFICIENT_DATA (-> block).
   double corr = 0; int aligned = 0; string detail = "";
   ENUM_NEXA_CORR_STATE st = NexaCorrelationState(_Symbol, "NEXA_NO_SUCH_SYMBOL_XYZ", InpCorrelationBars, corr, aligned, detail);
   FileWrite(out, "wrapper_unreadable_symbol", StateName(st), DoubleToString(corr, 15), IntegerToString(aligned), detail);
   // Wrapper argument validation: empty symbol name.
   st = NexaCorrelationState(_Symbol, "", InpCorrelationBars, corr, aligned, detail);
   FileWrite(out, "wrapper_empty_symbol", StateName(st), DoubleToString(corr, 15), IntegerToString(aligned), detail);
   // Cap with no open positions in the tester account: nothing to correlate against -> OK.
   string reason = "";
   bool ok = CorrelationCapOK(_Symbol, reason);
   FileWrite(out, "cap_no_positions", ok ? "OK" : "BLOCK", "0", "0", reason);
   FileClose(out);
   Print("CORRCAP_TEST DONE cases=", cases, " results=", InpResults);
   return INIT_SUCCEEDED;
  }

void OnTick() { }
