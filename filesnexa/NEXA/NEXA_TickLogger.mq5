//+------------------------------------------------------------------+
//| NEXA_TickLogger.mq5                                               |
//|                                                                    |
//| Attach as an EXPERT ADVISOR to ONE chart per symbol                |
//| (4 charts total: EURUSD, GBPUSD, USDJPY, XAUUSD).                  |
//| Enable AlgoTrading in the toolbar for it to run OnTick.            |
//| Places NO orders — pure passive logging, zero balance risk.        |
//|                                                                    |
//| IMPORTANT: SessionTag() below assumes server time already          |
//| roughly matches trading-day hours. Confirm your broker's server    |
//| GMT offset (Market Watch > right-click symbol > Specification,     |
//| or compare TimeCurrent() to TimeGMT()) and adjust the hour         |
//| boundaries below if your server offset differs from the ones       |
//| assumed here (Asia 00-07, London 07-12, Overlap 12-16, NY 16-21,   |
//| server time). Do not trust these boundaries as broker-agnostic.    |
//+------------------------------------------------------------------+
#property strict

int    fileHandle = INVALID_HANDLE;
string fileName;

int OnInit()
  {
   fileName = "NEXA_TickLog_" + _Symbol + "_" + TimeToString(TimeCurrent(), TIME_DATE) + ".csv";
   fileHandle = FileOpen(fileName, FILE_WRITE | FILE_READ | FILE_CSV | FILE_ANSI | FILE_COMMON, ",");
   if(fileHandle == INVALID_HANDLE)
     {
      Print("NEXA_TickLogger: failed to open file, error ", GetLastError());
      return INIT_FAILED;
     }
   FileSeek(fileHandle, 0, SEEK_END);
   if(FileSize(fileHandle) == 0)
      FileWrite(fileHandle, "server_time", "local_time", "symbol", "bid", "ask", "spread_points", "session_tag");
   return INIT_SUCCEEDED;
  }

string SessionTag(datetime t)
  {
   MqlDateTime dt;
   TimeToStruct(t, dt);   // server time -- verify offset per the header note above
   int h = dt.hour;
   if(h >= 0  && h < 7)  return "ASIA";
   if(h >= 7  && h < 12) return "LONDON";
   if(h >= 12 && h < 16) return "LONDON_NY_OVERLAP";
   if(h >= 16 && h < 21) return "NY";
   return "LATE_NY_ASIA_GAP";
  }

void OnTick()
  {
   double bid   = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   double ask   = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   double point = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
   datetime st  = TimeCurrent();
   datetime lt  = TimeLocal();

   FileSeek(fileHandle, 0, SEEK_END);
   FileWrite(fileHandle,
             TimeToString(st, TIME_DATE | TIME_SECONDS),
             TimeToString(lt, TIME_DATE | TIME_SECONDS),
             _Symbol, bid, ask, (ask - bid) / point, SessionTag(st));
  }

void OnDeinit(const int reason)
  {
   if(fileHandle != INVALID_HANDLE)
      FileClose(fileHandle);
  }
