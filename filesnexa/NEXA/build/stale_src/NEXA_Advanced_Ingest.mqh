//+------------------------------------------------------------------+
//| NEXA_Advanced_Ingest.mqh                                          |
//| Pre-flight execution validation + DIAGNOSTIC-ONLY shadow ledger.   |
//+------------------------------------------------------------------+
//| DESIGN RULE: nothing here may EVER gate a risk decision using a    |
//| simulated, derived or reconstructed balance. Every hard check uses |
//| live broker state (AccountInfoDouble / OrderCalcMargin). The       |
//| shadow ledger is instrumentation: it answers "what would a clean   |
//| R-compounding path have produced?" for comparison against the real |
//| account. Any code that reads it to decide whether a trade may      |
//| proceed is a bug. REAL BROKER STATE WINS, ALWAYS.                  |
//+------------------------------------------------------------------+
#ifndef NEXA_ADVANCED_INGEST_MQH
#define NEXA_ADVANCED_INGEST_MQH
#include "NEXA_Common.mqh"

input double InpPreflightMaxMarginPct = 40.0;  // pre-flight ceiling vs REAL free margin
input bool   InpShadowLedgerEnabled   = true;  // diagnostic only; cannot affect execution

//==================== SHADOW LEDGER (DIAGNOSTIC ONLY) ====================
struct NexaShadowLedger
  {
   double   startBalance;
   double   modelledBalance;   // clean R-compounding path -- NOT the account
   double   modelledPeak;
   double   modelledMaxDDPct;
   int      tradesCounted;
   double   sumR;
  };

NexaShadowLedger g_shadow;

void AdvancedIngest_Init()
  {
   g_shadow.startBalance    = AccountInfoDouble(ACCOUNT_BALANCE);
   g_shadow.modelledBalance = g_shadow.startBalance;
   g_shadow.modelledPeak    = g_shadow.startBalance;
   g_shadow.modelledMaxDDPct = 0.0;
   g_shadow.tradesCounted   = 0;
   g_shadow.sumR            = 0.0;
   Print("NEXA shadow ledger initialized at ", DoubleToString(g_shadow.startBalance, 2),
         " (diagnostic only -- does not gate execution)");
  }

void SyncShadowLedger(double tradeResultR, double riskPctUsed)
  {
   if(!InpShadowLedgerEnabled) return;
   if(!NexaFinite(tradeResultR) || !NexaFinite(riskPctUsed)) return;
   double riskUnit = g_shadow.modelledBalance * (riskPctUsed / 100.0);
   g_shadow.modelledBalance += tradeResultR * riskUnit;
   g_shadow.tradesCounted++;
   g_shadow.sumR += tradeResultR;
   if(g_shadow.modelledBalance > g_shadow.modelledPeak) g_shadow.modelledPeak = g_shadow.modelledBalance;
   if(g_shadow.modelledPeak > 0)
     {
      double dd = (g_shadow.modelledPeak - g_shadow.modelledBalance) / g_shadow.modelledPeak * 100.0;
      if(dd > g_shadow.modelledMaxDDPct) g_shadow.modelledMaxDDPct = dd;
     }
  }

double ShadowVsRealGap() { return g_shadow.modelledBalance - AccountInfoDouble(ACCOUNT_BALANCE); }

string ShadowLedgerReport()
  {
   double avgR = (g_shadow.tradesCounted > 0) ? g_shadow.sumR / g_shadow.tradesCounted : 0.0;
   return StringFormat("SHADOW n=%d avgR=%.3f modelled=%.2f real=%.2f gap=%.2f maxDD=%.2f%%",
                        g_shadow.tradesCounted, avgR, g_shadow.modelledBalance,
                        AccountInfoDouble(ACCOUNT_BALANCE), ShadowVsRealGap(), g_shadow.modelledMaxDDPct);
  }

//==================== PRE-FLIGHT VALIDATION (REAL STATE ONLY) ====================
// Runs BEFORE dispatch. Every value is queried live. Can only reject, never permit.
bool PreflightExecutionCheck(int direction, double lots, double price, string &reason)
  {
   if(direction == 0 || lots <= 0 || price <= 0 || !NexaFinite(lots) || !NexaFinite(price))
     { reason = "PREFLIGHT_INVALID_ARGS"; return false; }

   double realEquity     = AccountInfoDouble(ACCOUNT_EQUITY);
   double realFreeMargin = AccountInfoDouble(ACCOUNT_MARGIN_FREE);
   if(realEquity <= 0 || realFreeMargin <= 0) { reason = "PREFLIGHT_NO_FREE_MARGIN"; return false; }

   if(!TerminalInfoInteger(TERMINAL_CONNECTED))   { reason = "PREFLIGHT_TERMINAL_DISCONNECTED"; return false; }
   if(!TerminalInfoInteger(TERMINAL_TRADE_ALLOWED)) { reason = "PREFLIGHT_TERMINAL_ALGO_DISABLED"; return false; }
   if(!MQLInfoInteger(MQL_TRADE_ALLOWED))         { reason = "PREFLIGHT_EA_TRADE_NOT_ALLOWED"; return false; }
   if(!AccountInfoInteger(ACCOUNT_TRADE_ALLOWED)) { reason = "PREFLIGHT_ACCOUNT_TRADE_NOT_ALLOWED"; return false; }
   if(!AccountInfoInteger(ACCOUNT_TRADE_EXPERT))  { reason = "PREFLIGHT_ACCOUNT_EA_NOT_ALLOWED"; return false; }

   // Direction-aware symbol trade mode. CLOSEONLY/LONGONLY/SHORTONLY are real states.
   ENUM_SYMBOL_TRADE_MODE mode = (ENUM_SYMBOL_TRADE_MODE)SymbolInfoInteger(_Symbol, SYMBOL_TRADE_MODE);
   bool modeOK = (mode == SYMBOL_TRADE_MODE_FULL) ||
                 (mode == SYMBOL_TRADE_MODE_LONGONLY  && direction > 0) ||
                 (mode == SYMBOL_TRADE_MODE_SHORTONLY && direction < 0);
   if(!modeOK) { reason = StringFormat("PREFLIGHT_SYMBOL_TRADE_MODE_%d", (int)mode); return false; }

   ENUM_ORDER_TYPE oType = (direction > 0) ? ORDER_TYPE_BUY : ORDER_TYPE_SELL;
   double requiredMargin = 0.0;
   if(!OrderCalcMargin(oType, _Symbol, lots, price, requiredMargin))
     { reason = "PREFLIGHT_MARGIN_CALC_FAILED"; return false; }
   if(!NexaFinite(requiredMargin) || requiredMargin < 0)
     { reason = "PREFLIGHT_MARGIN_INVALID"; return false; }

   if(requiredMargin > realFreeMargin * (InpPreflightMaxMarginPct / 100.0))
     { reason = StringFormat("PREFLIGHT_MARGIN_%.1fPCT_OF_FREE", requiredMargin / realFreeMargin * 100.0); return false; }

   reason = "PREFLIGHT_PASS";
   return true;
  }

#endif
