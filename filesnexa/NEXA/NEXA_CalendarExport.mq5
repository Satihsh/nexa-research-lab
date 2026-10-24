//+------------------------------------------------------------------+
//| NEXA_CalendarExport.mq5                                           |
//| READ-ONLY research export of the MT5 Economic Calendar.            |
//| Run as a SCRIPT in a LIVE, connected terminal (the calendar is      |
//| unavailable in the Strategy Tester). Places no orders.              |
//|                                                                    |
//| Output (Common\Files):                                             |
//|   NEXA_Cal_countries.csv   id,name,code,currency,currency_symbol,url_name
//|   NEXA_Cal_events.csv      id,type,sector,frequency,time_mode,country_id,unit,
//|                            importance,multiplier,digits,event_code,name,source_url
//|   NEXA_Cal_values.csv      id,event_id,time_server,time_server_int,period,revision,
//|                            actual,prev,revised_prev,forecast,impact_type
//|   NEXA_Cal_provenance.txt  who/when/where, row counts, time semantics
//|                                                                    |
//| TIME: MqlCalendarValue.time is TRADE-SERVER time. It is written     |
//| verbatim (text + integer); conversion to UTC happens only in        |
//| research/nexa_time.py. Values are stored by MT5 as long x 1e6; the  |
//| LONG_MIN sentinel means "no value" and is written EMPTY, never 0.   |
//+------------------------------------------------------------------+
#property script_show_inputs
#property copyright "NEXA"
#property version   "1.00"
#property description "Read-only MT5 economic-calendar export with provenance. Places no orders."

input datetime InpFrom = D'2017.01.01 00:00';
input int      InpChunkDays = 92;          // CalendarValueHistory is queried in chunks

string V(const long v)
  {
   if(v == LONG_MIN)
      return "";
   return DoubleToString((double)v / 1e6, 6);
  }

string Q(string s)                         // CSV-quote free text
  {
   StringReplace(s, "\"", "\"\"");
   return "\"" + s + "\"";
  }

int OpenOut(const string name)
  {
   return FileOpen(name, FILE_WRITE | FILE_TXT | FILE_ANSI | FILE_COMMON);
  }

void OnStart()
  {
   datetime to = TimeTradeServer();
   MqlCalendarCountry countries[];
   int nc = CalendarCountries(countries);
   if(nc <= 0)
     {
      PrintFormat("NEXA_CalendarExport: CalendarCountries failed (%d), err %d. Is the terminal connected?", nc, GetLastError());
      return;
     }

   int hc = OpenOut("NEXA_Cal_countries.csv");
   int he = OpenOut("NEXA_Cal_events.csv");
   int hv = OpenOut("NEXA_Cal_values.csv");
   if(hc == INVALID_HANDLE || he == INVALID_HANDLE || hv == INVALID_HANDLE)
     {
      PrintFormat("NEXA_CalendarExport: cannot open outputs, err %d", GetLastError());
      return;
     }
   FileWriteString(hc, "id,name,code,currency,currency_symbol,url_name\r\n");
   FileWriteString(he, "id,type,sector,frequency,time_mode,country_id,unit,importance,multiplier,digits,event_code,name,source_url\r\n");
   FileWriteString(hv, "id,event_id,time_server,time_server_int,period,revision,actual,prev,revised_prev,forecast,impact_type\r\n");

   long n_events = 0, n_values = 0;
   for(int i = 0; i < nc; i++)
     {
      FileWriteString(hc, StringFormat("%I64u,%s,%s,%s,%s,%s\r\n", countries[i].id, Q(countries[i].name),
                      countries[i].code, countries[i].currency, Q(countries[i].currency_symbol), countries[i].url_name));
      MqlCalendarEvent ev[];
      int ne = CalendarEventByCountry(countries[i].code, ev);
      for(int k = 0; k < ne; k++)
        {
         FileWriteString(he, StringFormat("%I64u,%d,%d,%d,%d,%I64u,%d,%d,%d,%d,%s,%s,%s\r\n",
                         ev[k].id, (int)ev[k].type, (int)ev[k].sector, (int)ev[k].frequency, (int)ev[k].time_mode,
                         ev[k].country_id, (int)ev[k].unit, (int)ev[k].importance, (int)ev[k].multiplier,
                         (int)ev[k].digits, Q(ev[k].event_code), Q(ev[k].name), Q(ev[k].source_url)));
         n_events++;
        }
     }

   for(datetime a = InpFrom; a < to; a += (datetime)InpChunkDays * 86400)
     {
      datetime b = MathMin(to, a + (datetime)InpChunkDays * 86400);
      MqlCalendarValue vals[];
      int nv = CalendarValueHistory(vals, a, b, NULL, NULL);
      if(nv < 0)
        {
         PrintFormat("NEXA_CalendarExport: CalendarValueHistory %s..%s failed, err %d",
                     TimeToString(a), TimeToString(b), GetLastError());
         continue;
        }
      for(int k = 0; k < nv; k++)
        {
         if(vals[k].time < a || vals[k].time >= b)
            continue;                     // chunk edges: each value written exactly once
         FileWriteString(hv, StringFormat("%I64u,%I64u,%s,%I64d,%s,%d,%s,%s,%s,%s,%d\r\n",
                         vals[k].id, vals[k].event_id, TimeToString(vals[k].time, TIME_DATE | TIME_SECONDS),
                         (long)vals[k].time, TimeToString(vals[k].period, TIME_DATE), vals[k].revision,
                         V(vals[k].actual_value), V(vals[k].prev_value), V(vals[k].revised_prev_value),
                         V(vals[k].forecast_value), (int)vals[k].impact_type));
         n_values++;
        }
     }
   FileClose(hc);
   FileClose(he);
   FileClose(hv);

   int hp = OpenOut("NEXA_Cal_provenance.txt");
   if(hp != INVALID_HANDLE)
     {
      FileWriteString(hp, "source=MT5 Economic Calendar via terminal (CalendarCountries/CalendarEventByCountry/CalendarValueHistory)\r\n");
      FileWriteString(hp, StringFormat("terminal_build=%d\r\ncompany=%s\r\nserver=%s\r\naccount_login=%I64d\r\n",
                      (int)TerminalInfoInteger(TERMINAL_BUILD), AccountInfoString(ACCOUNT_COMPANY),
                      AccountInfoString(ACCOUNT_SERVER), AccountInfoInteger(ACCOUNT_LOGIN)));
      FileWriteString(hp, StringFormat("export_time_trade_server=%s\r\nexport_time_gmt=%s\r\nexport_time_local=%s\r\ntime_gmt_offset_s=%d\r\n",
                      TimeToString(TimeTradeServer(), TIME_DATE | TIME_SECONDS), TimeToString(TimeGMT(), TIME_DATE | TIME_SECONDS),
                      TimeToString(TimeLocal(), TIME_DATE | TIME_SECONDS), TimeGMTOffset()));
      FileWriteString(hp, StringFormat("range_from_server=%s\r\nrange_to_server=%s\r\n",
                      TimeToString(InpFrom, TIME_DATE | TIME_SECONDS), TimeToString(to, TIME_DATE | TIME_SECONDS)));
      FileWriteString(hp, StringFormat("countries=%d\r\nevents=%I64d\r\nvalues=%I64d\r\n", nc, n_events, n_values));
      FileWriteString(hp, "time_semantics=MqlCalendarValue.time is trade-server time; written verbatim\r\n");
      FileWriteString(hp, "value_semantics=long/1e6; LONG_MIN written empty (no value)\r\n");
      FileWriteString(hp, "revision_semantics=values reflect the calendar state at export time; forecast/prev revision history is NOT reconstructable from this export\r\n");
      FileClose(hp);
     }
   PrintFormat("NEXA_CalendarExport: %d countries, %I64d events, %I64d values written", nc, n_events, n_values);
  }
