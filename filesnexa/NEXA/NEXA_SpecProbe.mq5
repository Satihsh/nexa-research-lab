//+------------------------------------------------------------------+
//| NEXA_SpecProbe.mq5 -- broker symbol-specification probe (research)|
//| Strategy Tester ONLY: the tester syncs the broker's live symbol   |
//| specification and trades a SIMULATED account. Nothing here can    |
//| touch the real/demo account. Writes Common\Files\nexa_spec_probe.csv|
//| One simulated min-lot round trip per symbol measures the broker's |
//| actual commission (DEAL_COMMISSION) and realised spread cost.     |
//+------------------------------------------------------------------+
#property copyright "NEXA"
#property version   "1.00"
#include <Trade\Trade.mqh>

input string InpSymbols = "XAUUSD,NAS100,US100,USTEC,EURUSD,GBPUSD";
input string InpOut     = "nexa_spec_probe.csv";

CTrade trade;
string g_syms[];
bool   g_done = false;

string D(double v) { return DoubleToString(v, 10); }

void WriteSpec(int h, string s)
  {
   double bid = SymbolInfoDouble(s, SYMBOL_BID), ask = SymbolInfoDouble(s, SYMBOL_ASK);
   double vmin = SymbolInfoDouble(s, SYMBOL_VOLUME_MIN);
   double mBuy = 0, mSell = 0, pTick = 0, lTick = 0;
   double ts = SymbolInfoDouble(s, SYMBOL_TRADE_TICK_SIZE);
   bool okM1 = OrderCalcMargin(ORDER_TYPE_BUY, s, vmin, ask, mBuy);
   bool okM2 = OrderCalcMargin(ORDER_TYPE_SELL, s, vmin, bid, mSell);
   bool okP1 = OrderCalcProfit(ORDER_TYPE_BUY, s, 1.0, ask, ask + ts, pTick);     // per 1 lot, +1 tick
   bool okP2 = OrderCalcProfit(ORDER_TYPE_BUY, s, 1.0, ask, ask - ts, lTick);     // per 1 lot, -1 tick
   FileWrite(h, s, TimeToString(TimeCurrent(), TIME_DATE | TIME_SECONDS), D(bid), D(ask),
             SymbolInfoInteger(s, SYMBOL_SPREAD), SymbolInfoInteger(s, SYMBOL_DIGITS), D(SymbolInfoDouble(s, SYMBOL_POINT)),
             D(SymbolInfoDouble(s, SYMBOL_TRADE_CONTRACT_SIZE)), D(ts),
             D(SymbolInfoDouble(s, SYMBOL_TRADE_TICK_VALUE)), D(SymbolInfoDouble(s, SYMBOL_TRADE_TICK_VALUE_PROFIT)),
             D(SymbolInfoDouble(s, SYMBOL_TRADE_TICK_VALUE_LOSS)),
             D(vmin), D(SymbolInfoDouble(s, SYMBOL_VOLUME_MAX)), D(SymbolInfoDouble(s, SYMBOL_VOLUME_STEP)),
             SymbolInfoInteger(s, SYMBOL_TRADE_STOPS_LEVEL), SymbolInfoInteger(s, SYMBOL_TRADE_FREEZE_LEVEL),
             EnumToString((ENUM_SYMBOL_TRADE_MODE)SymbolInfoInteger(s, SYMBOL_TRADE_MODE)),
             SymbolInfoInteger(s, SYMBOL_FILLING_MODE),
             D(SymbolInfoDouble(s, SYMBOL_SWAP_LONG)), D(SymbolInfoDouble(s, SYMBOL_SWAP_SHORT)),
             EnumToString((ENUM_SYMBOL_SWAP_MODE)SymbolInfoInteger(s, SYMBOL_SWAP_MODE)),
             EnumToString((ENUM_SYMBOL_CALC_MODE)SymbolInfoInteger(s, SYMBOL_TRADE_CALC_MODE)),
             SymbolInfoString(s, SYMBOL_CURRENCY_BASE), SymbolInfoString(s, SYMBOL_CURRENCY_PROFIT),
             SymbolInfoString(s, SYMBOL_CURRENCY_MARGIN),
             okM1 ? D(mBuy) : "ERR", okM2 ? D(mSell) : "ERR", okP1 ? D(pTick) : "ERR", okP2 ? D(lTick) : "ERR",
             SymbolInfoString(s, SYMBOL_PATH), AccountInfoInteger(ACCOUNT_LEVERAGE));
  }

int OnInit()
  {
   StringSplit(InpSymbols, ',', g_syms);
   return INIT_SUCCEEDED;
  }

void OnTick()
  {
   if(g_done) return;
   g_done = true;
   int h = FileOpen(InpOut, FILE_WRITE | FILE_CSV | FILE_ANSI | FILE_COMMON, ',');
   if(h == INVALID_HANDLE) { Print("SPEC_PROBE cannot write"); return; }
   FileWrite(h, "symbol","time","bid","ask","spread_pts","digits","point","contract_size","tick_size","tick_value",
             "tick_value_profit","tick_value_loss","volume_min","volume_max","volume_step","stops_level","freeze_level",
             "trade_mode","filling_mode","swap_long","swap_short","swap_mode","calc_mode","ccy_base","ccy_profit",
             "ccy_margin","margin_buy_minlot","margin_sell_minlot","profit_1lot_plus1tick","profit_1lot_minus1tick",
             "path","account_leverage");
   for(int i = 0; i < ArraySize(g_syms); i++)
     {
      string s = g_syms[i];
      if(!SymbolSelect(s, true)) { FileWrite(h, s, "NOT_AVAILABLE"); continue; }
      WriteSpec(h, s);
     }
   FileWrite(h, "");
   FileWrite(h, "ROUND_TRIP", "symbol", "volume", "entry", "exit", "commission_in", "commission_out", "swap", "profit");
   for(int i = 0; i < ArraySize(g_syms); i++)
     {
      string s = g_syms[i];
      if(!SymbolSelect(s, true)) continue;
      double v = SymbolInfoDouble(s, SYMBOL_VOLUME_MIN);
      if(!trade.Buy(v, s)) { FileWrite(h, "ROUND_TRIP", s, D(v), "BUY_FAILED", IntegerToString(trade.ResultRetcode())); continue; }
      ulong inDeal = trade.ResultDeal();
      ulong pos = 0;
      for(int p = PositionsTotal() - 1; p >= 0; p--) { ulong t = PositionGetTicket(p); if(PositionGetString(POSITION_SYMBOL) == s) { pos = t; break; } }
      if(pos == 0 || !trade.PositionClose(pos)) { FileWrite(h, "ROUND_TRIP", s, D(v), "CLOSE_FAILED"); continue; }
      ulong outDeal = trade.ResultDeal();
      HistorySelect(0, TimeCurrent() + 86400);
      FileWrite(h, "ROUND_TRIP", s, D(v), D(HistoryDealGetDouble(inDeal, DEAL_PRICE)), D(HistoryDealGetDouble(outDeal, DEAL_PRICE)),
                D(HistoryDealGetDouble(inDeal, DEAL_COMMISSION)), D(HistoryDealGetDouble(outDeal, DEAL_COMMISSION)),
                D(HistoryDealGetDouble(outDeal, DEAL_SWAP)), D(HistoryDealGetDouble(outDeal, DEAL_PROFIT)));
     }
   FileClose(h);
   Print("SPEC_PROBE DONE");
  }
