//+------------------------------------------------------------------+
//| NEXA_Microstructure.mqh                                           |
//| Tick-flow imbalance PROXIES on MQL5's native vector type.          |
//|                                                                    |
//| HONEST LABELING: spot FX through MT5 has no centralized limit      |
//| order book. "OBI" and "CVD" here are TICK-DIRECTION PROXIES from   |
//| the broker's own feed, not real depth or aggressor volume. Where   |
//| the tick carries TICK_FLAG_BUY/SELL that is used; otherwise price  |
//| direction is the fallback. Both are INFERRED, never OBSERVED.      |
//|                                                                    |
//| VOLUME: most FX feeds report tick.volume == 0. The documented      |
//| semantic of this module is a TICK-COUNT proxy, so a tick without   |
//| volume counts as one unit. Without this the proxy would be zero    |
//| forever on FX -- silently useless rather than honestly approximate.|
//+------------------------------------------------------------------+
#ifndef NEXA_MICROSTRUCTURE_MQH
#define NEXA_MICROSTRUCTURE_MQH
#include "NEXA_Common.mqh"

input int InpTickFlowWindow = 50;   // rolling window size for the OBI proxy (>= 2)

vector   g_tickDeltaBuf;
int      g_tickBufIndex = 0;
bool     g_tickBufFilled = false;
double   g_lastTickPrice = 0;
long     g_lastTickMsc = 0;
double   g_cvdCumulative = 0;
double   g_cvdDayStamp = -1;
int      g_tickWindow = 0;

void Microstructure_Init()
  {
   g_tickWindow = (InpTickFlowWindow >= 2) ? InpTickFlowWindow : 50;
   g_tickDeltaBuf = vector::Zeros(g_tickWindow);
   g_tickBufIndex = 0;
   g_tickBufFilled = false;
   g_lastTickPrice = 0;
   g_lastTickMsc = 0;
   g_cvdCumulative = 0;
   g_cvdDayStamp = -1;
  }

void ResetCVDIfNewDay()
  {
   MqlDateTime dt; TimeToStruct(TimeCurrent(), dt);
   double today = dt.year * 10000 + dt.mon * 100 + dt.day;
   if(g_cvdDayStamp != today) { g_cvdDayStamp = today; g_cvdCumulative = 0; }
  }

// Call on EVERY tick. O(1). Never touches history.
void UpdateTickFlow()
  {
   if(g_tickWindow < 2 || (int)g_tickDeltaBuf.Size() != g_tickWindow) return;   // not initialised: fail safe

   ResetCVDIfNewDay();

   MqlTick tick;
   if(!SymbolInfoTick(_Symbol, tick)) return;
   if(tick.time_msc == g_lastTickMsc) return;      // same tick re-delivered: do not double count
   g_lastTickMsc = tick.time_msc;

   double price = (tick.last > 0) ? tick.last : tick.bid;
   if(price <= 0 || !NexaFinite(price)) return;

   double vol = (tick.volume > 0) ? (double)tick.volume : 1.0;   // tick-count proxy when volume absent

   double signedDelta = 0;
   bool haveFlags = (tick.flags & (TICK_FLAG_BUY | TICK_FLAG_SELL)) != 0;
   if(haveFlags)
     {
      if((tick.flags & TICK_FLAG_BUY) != 0)  signedDelta =  vol;
      if((tick.flags & TICK_FLAG_SELL) != 0) signedDelta = -vol;
     }
   else if(g_lastTickPrice > 0)
     {
      if(price > g_lastTickPrice)      signedDelta =  vol;
      else if(price < g_lastTickPrice) signedDelta = -vol;
     }
   g_lastTickPrice = price;

   if(g_tickBufIndex < 0 || g_tickBufIndex >= g_tickWindow) g_tickBufIndex = 0;
   g_tickDeltaBuf[g_tickBufIndex] = signedDelta;
   g_tickBufIndex = (g_tickBufIndex + 1) % g_tickWindow;
   if(g_tickBufIndex == 0) g_tickBufFilled = true;

   g_cvdCumulative += signedDelta;
  }

// -1..+1 tick-flow imbalance over the rolling window. 0 until the buffer has filled once.
double GetOBIProxy()
  {
   if(!g_tickBufFilled) return 0;
   int n = (int)g_tickDeltaBuf.Size();
   if(n <= 0) return 0;
   double sumPos = 0, sumAbs = 0;
   for(int i = 0; i < n; i++)
     {
      double v = g_tickDeltaBuf[i];
      if(!NexaFinite(v)) return 0;
      sumPos += v;
      sumAbs += MathAbs(v);
     }
   if(sumAbs <= 0) return 0;
   double r = sumPos / sumAbs;
   return NexaFinite(r) ? r : 0;
  }

double GetCVDProxy()
  {
   return NexaFinite(g_cvdCumulative) ? g_cvdCumulative : 0;
  }

#endif
