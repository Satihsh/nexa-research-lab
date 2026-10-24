//+------------------------------------------------------------------+
//| NEXA_SpecSnapshot.mq5                                             |
//|                                                                    |
//| Run ONCE as a SCRIPT (drag onto any chart, not an EA).             |
//| Places NO orders. Uses OrderCalcMargin/OrderCalcProfit to compute  |
//| hypothetical margin and monetary tick value directly from the      |
//| broker's own pricing engine — this is what resolves the XAUUSD     |
//| tick-value ambiguity precisely, without a live trade.              |
//|                                                                    |
//| Output: CSV in the Common Files folder (Files > Common in MT5's    |
//| File menu, or terminal_data_folder/../Common/Files).               |
//+------------------------------------------------------------------+
#property script_show_inputs
#property strict

input string InpSymbols     = "EURUSD,GBPUSD,USDJPY,XAUUSD";
input double InpTestVolume  = 0.01;

//--- account-level facts, written once at the top of the file
void WriteAccountInfo(int handle)
  {
   FileWrite(handle, "=== ACCOUNT INFO ===");
   FileWrite(handle, "Field", "Value");
   FileWrite(handle, "Leverage",        AccountInfoInteger(ACCOUNT_LEVERAGE));
   FileWrite(handle, "MarginMode",      EnumToString((ENUM_ACCOUNT_MARGIN_MODE)AccountInfoInteger(ACCOUNT_MARGIN_MODE)));
   FileWrite(handle, "Balance",         AccountInfoDouble(ACCOUNT_BALANCE));
   FileWrite(handle, "Currency",        AccountInfoString(ACCOUNT_CURRENCY));
   // 0 = stop-out/call expressed as a PERCENT of margin, 1 = expressed in account CURRENCY
   FileWrite(handle, "MarginSO_Mode",   AccountInfoInteger(ACCOUNT_MARGIN_SO_MODE));
   FileWrite(handle, "MarginCallLevel", AccountInfoDouble(ACCOUNT_MARGIN_SO_CALL));
   FileWrite(handle, "StopOutLevel",    AccountInfoDouble(ACCOUNT_MARGIN_SO_SO));
   FileWrite(handle, "");
   FileWrite(handle, "=== SYMBOL SPECS ===");
   FileWrite(handle,
             "Symbol","Bid","Ask","Spread_points","Point","TickSize",
             "TickValue","TickValueProfit","TickValueLoss","ContractSize",
             "StopsLevel_pts","FreezeLevel_pts","ExecMode","FillModeBitmask",
             "MarginInitial","MarginMaintenance",
             "HypMargin_Buy","HypMargin_Sell",
             "SwapLong_pts","SwapShort_pts",
             "TestMove_price","HypProfit_for_TestMove");
  }

//--- per-symbol facts, including hypothetical (no-order) margin/profit calcs
void WriteSymbolInfo(int handle, string sym)
  {
   if(!SymbolSelect(sym, true))
     {
      FileWrite(handle, sym, "NOT AVAILABLE ON THIS SERVER");
      return;
     }

   double bid          = SymbolInfoDouble(sym, SYMBOL_BID);
   double ask          = SymbolInfoDouble(sym, SYMBOL_ASK);
   double point        = SymbolInfoDouble(sym, SYMBOL_POINT);
   double tickSize     = SymbolInfoDouble(sym, SYMBOL_TRADE_TICK_SIZE);
   double tickValue    = SymbolInfoDouble(sym, SYMBOL_TRADE_TICK_VALUE);
   double tickValueP   = SymbolInfoDouble(sym, SYMBOL_TRADE_TICK_VALUE_PROFIT);
   double tickValueL   = SymbolInfoDouble(sym, SYMBOL_TRADE_TICK_VALUE_LOSS);
   double contractSize = SymbolInfoDouble(sym, SYMBOL_TRADE_CONTRACT_SIZE);
   int    stopsLevel   = (int)SymbolInfoInteger(sym, SYMBOL_TRADE_STOPS_LEVEL);
   int    freezeLevel  = (int)SymbolInfoInteger(sym, SYMBOL_TRADE_FREEZE_LEVEL);
   int    execMode     = (int)SymbolInfoInteger(sym, SYMBOL_TRADE_EXEMODE);
   int    fillMode     = (int)SymbolInfoInteger(sym, SYMBOL_FILLING_MODE);
   double marginInit   = SymbolInfoDouble(sym, SYMBOL_MARGIN_INITIAL);
   double marginMaint  = SymbolInfoDouble(sym, SYMBOL_MARGIN_MAINTENANCE);
   double swapLong     = SymbolInfoDouble(sym, SYMBOL_SWAP_LONG);
   double swapShort    = SymbolInfoDouble(sym, SYMBOL_SWAP_SHORT);

   //--- hypothetical margin for a BUY/SELL of InpTestVolume, no order sent
   //--- a failed broker calculation is written as -1 (unavailable), never as a
   //--- plausible-looking 0 that downstream sizing research could mistake for data
   double marginBuy = 0.0, marginSell = 0.0;
   if(!OrderCalcMargin(ORDER_TYPE_BUY, sym, InpTestVolume, ask, marginBuy))
     { PrintFormat("SpecSnapshot %s: OrderCalcMargin BUY failed, err %d", sym, GetLastError()); marginBuy = -1.0; }
   if(!OrderCalcMargin(ORDER_TYPE_SELL, sym, InpTestVolume, bid, marginSell))
     { PrintFormat("SpecSnapshot %s: OrderCalcMargin SELL failed, err %d", sym, GetLastError()); marginSell = -1.0; }

   //--- hypothetical profit for a defined price move -> exact $ tick/pip value,
   //--- this is the number that resolves the XAUUSD ambiguity definitively
   double testMove = 0.0010;                 // default: 10 pips for 4/5-digit FX
   if(sym == "USDJPY") testMove = 0.10;       // ~10 pips for JPY pairs (2-digit pip)
   if(sym == "XAUUSD") testMove = 1.00;       // $1.00 gold move

   double profitUp = 0.0;
   if(!OrderCalcProfit(ORDER_TYPE_BUY, sym, InpTestVolume, ask, ask + testMove, profitUp))
     { PrintFormat("SpecSnapshot %s: OrderCalcProfit failed, err %d", sym, GetLastError()); profitUp = -1.0; }

   FileWrite(handle, sym, bid, ask, (ask - bid) / point, point, tickSize,
             tickValue, tickValueP, tickValueL, contractSize,
             stopsLevel, freezeLevel, execMode, fillMode,
             marginInit, marginMaint,
             marginBuy, marginSell,
             swapLong, swapShort,
             testMove, profitUp);
  }

void OnStart()
  {
   string fileName = "NEXA_SpecSnapshot_" + TimeToString(TimeCurrent(), TIME_DATE) + ".csv";
   int handle = FileOpen(fileName, FILE_WRITE | FILE_CSV | FILE_ANSI | FILE_COMMON, ",");
   if(handle == INVALID_HANDLE)
     {
      Print("NEXA_SpecSnapshot: failed to open file, error ", GetLastError());
      return;
     }

   WriteAccountInfo(handle);

   string symbols[];
   int count = StringSplit(InpSymbols, ',', symbols);
   for(int i = 0; i < count; i++)
      WriteSymbolInfo(handle, symbols[i]);

   FileClose(handle);
   Print("NEXA spec snapshot written: ", fileName, " (Common Files folder)");
  }
