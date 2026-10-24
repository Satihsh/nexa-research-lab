//+------------------------------------------------------------------+
//| NEXA_DealAudit.mq5                                                |
//|                                                                    |
//| Run as a SCRIPT AFTER you've manually opened and closed a small   |
//| batch of 0.01-lot test trades (the slippage-sampling step from    |
//| the data collection plan). Reads back what MT5 actually recorded  |
//| for each deal: commission, swap, realized price, profit.          |
//|                                                                    |
//| This is the only reliable way to get real commission -- it is     |
//| not exposed by OrderCalcMargin/Profit, only by closed deal        |
//| history. Places NO new orders.                                    |
//+------------------------------------------------------------------+
#property script_show_inputs
#property strict

input int InpLookbackDays = 7;

void OnStart()
  {
   datetime from = TimeCurrent() - InpLookbackDays * 24 * 3600;
   datetime to   = TimeCurrent();

   if(!HistorySelect(from, to))
     {
      Print("NEXA_DealAudit: HistorySelect failed, error ", GetLastError());
      return;
     }

   int total = HistoryDealsTotal();
   string fileName = "NEXA_DealAudit_" + TimeToString(TimeCurrent(), TIME_DATE) + ".csv";
   int handle = FileOpen(fileName, FILE_WRITE | FILE_CSV | FILE_ANSI | FILE_COMMON, ",");
   if(handle == INVALID_HANDLE)
     {
      Print("NEXA_DealAudit: failed to open output file, error ", GetLastError());
      return;
     }

   FileWrite(handle, "ticket", "time", "symbol", "deal_type", "volume",
             "price", "commission", "swap", "profit");

   int written = 0;
   for(int i = 0; i < total; i++)
     {
      ulong ticket = HistoryDealGetTicket(i);
      if(ticket == 0)
         continue;

      string   sym    = HistoryDealGetString(ticket, DEAL_SYMBOL);
      double   vol    = HistoryDealGetDouble(ticket, DEAL_VOLUME);
      double   price  = HistoryDealGetDouble(ticket, DEAL_PRICE);
      double   comm   = HistoryDealGetDouble(ticket, DEAL_COMMISSION);
      double   swap   = HistoryDealGetDouble(ticket, DEAL_SWAP);
      double   profit = HistoryDealGetDouble(ticket, DEAL_PROFIT);
      long     dtype  = HistoryDealGetInteger(ticket, DEAL_TYPE);
      datetime dtime  = (datetime)HistoryDealGetInteger(ticket, DEAL_TIME);

      // skip non-trade deals (balance/credit operations etc.)
      if(dtype != DEAL_TYPE_BUY && dtype != DEAL_TYPE_SELL)
         continue;

      FileWrite(handle, ticket, TimeToString(dtime, TIME_DATE | TIME_SECONDS),
                sym, EnumToString((ENUM_DEAL_TYPE)dtype), vol, price, comm, swap, profit);
      written++;
     }

   FileClose(handle);
   Print("NEXA_DealAudit: wrote ", written, " trade deals to ", fileName, " (Common Files folder)");
  }
