//+------------------------------------------------------------------+
//| NEXA_TickProbe.mq5 -- which tick fields does Pepperstone supply?  |
//| Strategy Tester ONLY (real-tick model); places NO orders.         |
//| Writes Common\Files\nexa_tick_probe.csv: per symbol, counts of     |
//| non-zero last / volume / volume_real, every flag bit, bookdepth,   |
//| and whether a market-depth subscription is accepted.              |
//+------------------------------------------------------------------+
#property copyright "NEXA"
#property version   "1.00"

input string InpSymbols = "XAUUSD,NAS100,EURUSD";
input int    InpTicks   = 200000;
bool g_done = false;

void OnTick()
  {
   if(g_done) return;
   g_done = true;
   string syms[]; StringSplit(InpSymbols, ',', syms);
   int h = FileOpen("nexa_tick_probe.csv", FILE_WRITE | FILE_CSV | FILE_ANSI | FILE_COMMON, ',');
   FileWrite(h, "symbol","ticks","last_nonzero","volume_nonzero","volume_real_nonzero","bid_bit","ask_bit","last_bit",
             "volume_bit","buy_bit","sell_bit","bookdepth","market_book_add","first_time","last_time",
             "sample_bid","sample_ask","sample_last","sample_volume","sample_volume_real","sample_flags");
   for(int s = 0; s < ArraySize(syms); s++)
     {
      string sym = syms[s];
      SymbolSelect(sym, true);
      MqlTick t[];
      ulong to = (ulong)TimeCurrent() * 1000;
      int n = CopyTicksRange(sym, t, COPY_TICKS_ALL, to - 86400000 * 3, to);
      if(n > InpTicks) n = InpTicks;
      long ln = 0, vn = 0, vrn = 0, fb[6] = {0,0,0,0,0,0};
      int bits[6] = {TICK_FLAG_BID, TICK_FLAG_ASK, TICK_FLAG_LAST, TICK_FLAG_VOLUME, TICK_FLAG_BUY, TICK_FLAG_SELL};
      for(int i = 0; i < n; i++)
        {
         if(t[i].last != 0) ln++;
         if(t[i].volume != 0) vn++;
         if(t[i].volume_real != 0) vrn++;
         for(int b = 0; b < 6; b++) if((t[i].flags & bits[b]) != 0) fb[b]++;
        }
      bool book = MarketBookAdd(sym);
      if(book) MarketBookRelease(sym);
      int k = n > 0 ? n - 1 : 0;
      FileWrite(h, sym, n, ln, vn, vrn, fb[0], fb[1], fb[2], fb[3], fb[4], fb[5],
                SymbolInfoInteger(sym, SYMBOL_TICKS_BOOKDEPTH), book ? "true" : "false",
                n > 0 ? TimeToString((datetime)(t[0].time_msc / 1000), TIME_DATE | TIME_SECONDS) : "",
                n > 0 ? TimeToString((datetime)(t[k].time_msc / 1000), TIME_DATE | TIME_SECONDS) : "",
                n > 0 ? DoubleToString(t[k].bid, 5) : "", n > 0 ? DoubleToString(t[k].ask, 5) : "",
                n > 0 ? DoubleToString(t[k].last, 5) : "", n > 0 ? IntegerToString((long)t[k].volume) : "",
                n > 0 ? DoubleToString(t[k].volume_real, 5) : "", n > 0 ? IntegerToString(t[k].flags) : "");
     }
   FileClose(h);
   Print("TICK_PROBE DONE");
  }
