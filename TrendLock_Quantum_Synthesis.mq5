//+------------------------------------------------------------------+
//| TrendLock_Quantum_Synthesis.mq5                                  |
//|                                                                  |
//| Synthesis of two TradingView strategies into one MT5 EA:         |
//|   * TrendLock "Supertrend Donchian Breakout" (STDB)              |
//|       -> trend regime (Supertrend), HTF Supertrend agreement,    |
//|          Donchian breakout trigger, volume confirmation,         |
//|          exit on trend flip                                      |
//|   * CleanTradeQuantum v7.2 OB/FVG                                |
//|       -> EMA trend filter, candle-body filter, ATR expansion     |
//|          filter, chop/regime guard (ADX + EMA slope), optional   |
//|          FVG confluence, ATR/structure/combined stop modes,      |
//|          adaptive loss-cooldown ("error guard"), prop-style      |
//|          daily-loss and max-drawdown limits                      |
//|                                                                  |
//| DELIBERATELY NOT PORTED (see audit notes in the delivery):       |
//|   * "Quantum" up/down bar counting    - redundant trend proxy    |
//|   * bar_index "WFO" parameter routing - in-sample curve fitting  |
//|   * 12-vote correlated signal cluster - counts one idea N times  |
//|   * STDB long-side bug `close > lower_channel` - FIXED here to   |
//|     `close > upper channel` (a real breakout)                    |
//|                                                                  |
//| CAUSALITY: every signal is computed on CLOSED bars only          |
//| (CopyRates start_pos = 1). The higher-timeframe Supertrend uses  |
//| the last CLOSED higher-timeframe bar, never the forming one.     |
//|                                                                  |
//| NO MARTINGALE, NO GRID, NO LOT MULTIPLIERS. One position per     |
//| symbol+magic. Volume is derived from equity risk only, and a     |
//| losing streak can only REDUCE trading (cooldown), never size up. |
//+------------------------------------------------------------------+
#property copyright   "TrendLock x CleanTradeQuantum synthesis"
#property version     "1.00"
#property description "Supertrend + HTF + Donchian breakout with regime/SMC filters,"
#property description "equity-risk sizing and 3-tier TP (1R/2R/3R) with breakeven."

#include <Trade\Trade.mqh>

//--- stop-loss construction modes (from CleanTradeQuantum "Stop-loss mode")
enum ENUM_STOP_MODE
  {
   STOP_ATR       = 0,   // ATR multiple from entry
   STOP_STRUCTURE = 1,   // beyond last confirmed swing (+ ATR buffer)
   STOP_COMBINED  = 2    // the CLOSER of the two valid stops
  };

//==================================================================//
//                              INPUTS                              //
//==================================================================//
input group "=== Identity ==="
input long   InpMagic              = 72020260;   // Magic number (isolates this EA's positions)
input string InpComment            = "TLQ";      // Order comment
input bool   InpVerbose            = false;      // Log every rejected signal reason

input group "=== Risk & Sizing ==="
input double InpRiskPercent        = 1.0;        // Risk per trade, % of equity
input double InpMaxRiskPercent     = 2.0;        // Hard ceiling if broker min lot forces more risk
input double InpMaxMarginPercent   = 50.0;       // Max % of free margin one trade may consume
input int    InpDeviationPoints    = 20;         // Max slippage, points
input double InpMaxSpreadPoints    = 0.0;        // Max spread in points (0 = off)
input double InpMaxSpreadAtrFrac   = 0.20;       // Max spread as fraction of ATR (0 = off)

input group "=== Account Guards (prop-style) ==="
input double InpDailyLossPct       = 5.0;        // Stop new entries after this daily equity loss %
input double InpMaxDrawdownPct     = 10.0;       // Permanent halt at this drawdown from equity peak %
input int    InpMaxTradesPerDay    = 6;          // Max new entries per server day
input bool   InpFlattenOnLimit     = false;      // Also close the open position when a limit hits

input group "=== Trend: Supertrend (STDB) ==="
input double InpStFactor           = 3.0;        // Supertrend factor
input int    InpStAtrLen           = 10;         // Supertrend ATR length (Wilder)
input bool   InpUseHtfFilter       = true;       // Require higher-timeframe Supertrend agreement
input ENUM_TIMEFRAMES InpHtf       = PERIOD_H4;  // Higher timeframe (must exceed chart TF)
input int    InpCalcBars           = 500;        // Bars used to compute indicators

input group "=== Breakout: Donchian (STDB) ==="
input int    InpDonchianLen        = 20;         // Donchian lookback (excludes signal bar)

input group "=== Confirmation Filters ==="
input bool   InpUseVolFilter       = true;       // Require tick-volume spike (STDB)
input int    InpVolMaLen           = 20;         // Volume SMA length
input double InpVolMult            = 1.5;        // Volume spike multiplier
input bool   InpUseEmaFilter       = true;       // Price above rising EMA for longs (CTQ)
input int    InpEmaLen             = 34;         // Trend EMA length
input bool   InpUseBodyFilter      = true;       // Signal candle body filter (CTQ)
input double InpBodyRatioMin       = 0.35;       // Min body / range
input bool   InpUseAtrExpansion    = true;       // ATR must not be contracting (CTQ)
input int    InpAtrMaLen           = 21;         // ATR SMA length
input double InpAtrExpansionMult   = 0.95;       // ATR >= ATR-SMA x this
input bool   InpUseChopFilter      = true;       // Block entries in chop regime (CTQ)
input int    InpAdxLen             = 14;         // ADX (Wilder) length
input double InpChopAdxMax         = 18.0;       // Chop if ADX <= this ...
input double InpChopSlopeAtrMax    = 0.035;      // ... AND |EMA slope| <= ATR x this
input bool   InpRequireFvg         = false;      // Require same-direction fair value gap (CTQ)

input group "=== Direction ==="
input bool   InpAllowLong          = true;       // Allow long trades
input bool   InpAllowShort         = true;       // Allow short trades

input group "=== Stops & 3-Tier Targets ==="
input ENUM_STOP_MODE InpStopMode   = STOP_ATR;   // Stop-loss construction
input int    InpRiskAtrLen         = 14;         // ATR length for stops (Wilder)
input double InpSlAtrMult          = 2.0;        // ATR stop multiple
input int    InpSwingLen           = 6;          // Swing pivot strength (bars each side)
input double InpSwingBufferAtr     = 0.20;       // Buffer beyond swing, ATR multiple
input double InpMinStopAtr         = 0.5;        // Stop never tighter than ATR x this
input double InpTp1R               = 1.0;        // TP1 in R (partial + breakeven)
input double InpTp2R               = 2.0;        // TP2 in R (partial)
input double InpTp3R               = 3.0;        // TP3 in R (server-side final target)
input double InpTp1ClosePct        = 50.0;       // % of ORIGINAL volume closed at TP1
input double InpTp2ClosePct        = 25.0;       // % of ORIGINAL volume closed at TP2
input bool   InpExitOnTrendFlip    = true;       // Close if chart Supertrend flips against (STDB)

input group "=== Adaptive Error Guard (CTQ) ==="
input bool   InpUseErrorGuard      = true;       // Cooldown same direction after losses
input int    InpErrorCooldownBars  = 8;          // Base cooldown, bars
input int    InpMaxErrorMultiplier = 4;          // Max cooldown multiplier for loss streaks
input int    InpErrorLookbackBars  = 40;         // Losses within this window count as a streak

input group "=== Session (broker server time) ==="
input bool   InpUseSession         = false;      // Restrict new entries to a server-time window
input int    InpStartHour          = 7;          // Start hour (inclusive)
input int    InpEndHour            = 20;         // End hour (exclusive; wraps past midnight)

//==================================================================//
//                              GLOBALS                             //
//==================================================================//
CTrade   g_trade;
int      g_hEma        = INVALID_HANDLE;   // chart-TF EMA (MODE_EMA == Pine ta.ema)
int      g_hAdx        = INVALID_HANDLE;   // Wilder ADX (matches Pine ta.dmi smoothing)
datetime g_lastBar     = 0;                // new-bar gate
int      g_needBars    = 0;                // minimum bars for a valid context
double   g_lastAtr     = 0.0;              // last closed-bar ATR (for emergency re-protection)
datetime g_lastMgmtTry = 0;                // throttles management retries after a failed request
string   g_pfx         = "";               // GlobalVariable namespace for this EA instance

//--- Everything a closed bar tells us. Plain numeric struct.
struct SignalCtx
  {
   int    stDir;       // chart-TF Supertrend direction on bar 1: -1 up, +1 down (Pine convention)
   int    htfDir;      // HTF Supertrend direction on last closed HTF bar
   double atr;         // Wilder ATR (risk length) on bar 1
   double atrSma;      // SMA of that ATR
   double open1, high1, low1, close1;
   double donHigh;     // highest high of the N bars BEFORE bar 1
   double donLow;      // lowest low of the N bars BEFORE bar 1
   double vol1;        // tick volume of bar 1
   double volSma;      // SMA of tick volume ending at bar 1
   double ema1, ema2;  // EMA on bar 1 and bar 2
   double adx1;        // ADX on bar 1
   bool   fvgBull;     // 3-candle bullish gap ending at bar 1
   bool   fvgBear;     // 3-candle bearish gap ending at bar 1
   double swingLow;    // last CONFIRMED swing low  (0 = none)
   double swingHigh;   // last CONFIRMED swing high (0 = none)
  };

//==================================================================//
//                    GLOBAL-VARIABLE PERSISTENCE                   //
//  Terminal GlobalVariables survive restarts, so tier state,       //
//  cooldowns and account guards are not lost if MT5 reloads.       //
//==================================================================//
double GVGet(const string key, const double def)
  {
   string name = g_pfx + key;
   return GlobalVariableCheck(name) ? GlobalVariableGet(name) : def;
  }

void GVSet(const string key, const double value)
  {
   GlobalVariableSet(g_pfx + key, value);
  }

void GVDel(const string key)
  {
   string name = g_pfx + key;
   if(GlobalVariableCheck(name))
      GlobalVariableDel(name);
  }

string PosKey(const long positionId)
  {
   return "P" + IntegerToString(positionId) + "_";
  }

//==================================================================//
//                 BROKER-SAFE PRICE / VOLUME HELPERS               //
//==================================================================//
//--- Round a price to the symbol's tick size, then to _Digits.
//--- Works for 5-digit, 4-digit, 3-digit (JPY) and 2-digit (metals/indices)
//--- quotes because it never assumes a pip size: it uses the broker's own
//--- tick size and digits.
double NormalizePrice(const double price)
  {
   double tickSize = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   double p = price;
   if(tickSize > 0.0)
      p = MathRound(p / tickSize) * tickSize;
   return NormalizeDouble(p, _Digits);
  }

//--- Decimal places implied by the volume step (0.01 -> 2, 0.1 -> 1, 1 -> 0).
int VolumeDigits()
  {
   double step = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   int    d    = 0;
   double s    = step;
   while(d < 8 && MathAbs(s - MathRound(s)) > 1e-9)
     {
      s *= 10.0;
      d++;
     }
   return d;
  }

//--- Round volume DOWN to the step and clamp to the broker maximum.
//--- Rounding down means rounding can only reduce risk, never raise it.
double NormalizeVolumeDown(const double volume)
  {
   double step = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   double vmax = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   if(step <= 0.0 || volume <= 0.0)
      return 0.0;
   double v = MathFloor(volume / step + 1e-9) * step;     // epsilon: 0.03/0.01 must be 3, not 2.999
   if(vmax > 0.0 && v > vmax)
      v = MathFloor(vmax / step + 1e-9) * step;
   return NormalizeDouble(v, VolumeDigits());
  }

//--- Broker minimum distance for SL/TP from the current price.
double MinStopsDist()
  {
   return (double)SymbolInfoInteger(_Symbol, SYMBOL_TRADE_STOPS_LEVEL) * _Point;
  }

//--- Broker freeze distance: inside it, SL/TP cannot be modified.
double FreezeDist()
  {
   return (double)SymbolInfoInteger(_Symbol, SYMBOL_TRADE_FREEZE_LEVEL) * _Point;
  }

//==================================================================//
//                         POSITION OWNERSHIP                       //
//==================================================================//
//--- Select this EA's position (symbol + magic). Iterating by ticket is
//--- correct under both netting and hedging, and never touches positions
//--- opened manually or by another EA.
bool SelectOurPosition(ulong &ticket)
  {
   ticket = 0;
   int total = PositionsTotal();
   for(int i = 0; i < total; i++)
     {
      ulong t = PositionGetTicket(i);
      if(t == 0)
         continue;
      if(PositionGetString(POSITION_SYMBOL) != _Symbol)
         continue;
      if(PositionGetInteger(POSITION_MAGIC) != InpMagic)
         continue;
      ticket = t;
      return true;
     }
   return false;
  }

//==================================================================//
//                    INDICATOR MATH (closed bars)                  //
//  Arrays are CHRONOLOGICAL: r[0] oldest, r[n-1] = bar 1 (last      //
//  closed bar). CopyRates starts at position 1, so the forming bar  //
//  is never present.                                                //
//==================================================================//
//--- True range, Pine ta.tr(true) semantics (first bar = high - low).
double TrueRange(const MqlRates &r[], const int i)
  {
   double hl = r[i].high - r[i].low;
   if(i == 0)
      return hl;
   double pc = r[i - 1].close;
   return MathMax(hl, MathMax(MathAbs(r[i].high - pc), MathAbs(r[i].low - pc)));
  }

//--- Wilder ATR (Pine ta.atr == ta.rma(tr)). MT5's built-in iATR is a SIMPLE
//--- average of TR, so it is computed here to match the Pine originals.
//--- Seeded with the SMA of the first `len` true ranges; 0 = not yet valid.
bool WilderATR(const MqlRates &r[], const int n, const int len, double &atr[])
  {
   if(len < 1 || n < len + 1)
      return false;
   if(ArrayResize(atr, n) != n)
      return false;
   ArrayInitialize(atr, 0.0);
   double sum = 0.0;
   for(int i = 0; i < len; i++)
      sum += TrueRange(r, i);
   atr[len - 1] = sum / (double)len;
   for(int i = len; i < n; i++)
      atr[i] = (atr[i - 1] * (double)(len - 1) + TrueRange(r, i)) / (double)len;
   return true;
  }

//--- Supertrend, Pine ta.supertrend(factor, atrPeriod) semantics.
//--- Returns the direction on the last bar: -1 = uptrend, +1 = downtrend.
bool SuperTrendDir(const MqlRates &r[], const int n, const double factor,
                   const int len, int &dirLast)
  {
   dirLast = 0;
   double atr[];
   if(!WilderATR(r, n, len, atr))
      return false;

   double upper[], lower[];
   if(ArrayResize(upper, n) != n || ArrayResize(lower, n) != n)
      return false;
   ArrayInitialize(upper, 0.0);
   ArrayInitialize(lower, 0.0);

   int start   = len - 1;
   int prevDir = 1;
   int dir     = 1;
   for(int i = start; i < n; i++)
     {
      double src = (r[i].high + r[i].low) / 2.0;
      double ub  = src + factor * atr[i];
      double lb  = src - factor * atr[i];
      if(i == start)
         dir = 1;                                   // Pine: na(atr[1]) -> direction := 1
      else
        {
         double prevLb = lower[i - 1];
         double prevUb = upper[i - 1];
         // bands only ratchet in the trend's favour unless price closed through them
         if(!(lb > prevLb || r[i - 1].close < prevLb))
            lb = prevLb;
         if(!(ub < prevUb || r[i - 1].close > prevUb))
            ub = prevUb;
         // Pine compares prevSuperTrend == prevUpperBand; tracking the previous
         // direction is equivalent and avoids floating-point equality.
         if(prevDir == 1)
            dir = (r[i].close > ub) ? -1 : 1;
         else
            dir = (r[i].close < lb) ? 1 : -1;
        }
      lower[i] = lb;
      upper[i] = ub;
      prevDir  = dir;
     }
   dirLast = dir;
   return true;
  }

//--- Most recent CONFIRMED swing low: `len` higher lows on BOTH sides.
//--- The right-hand bars must already be closed, so no future data is used.
double FindSwingLow(const MqlRates &r[], const int n, const int len)
  {
   for(int k = n - 1 - len; k >= len; k--)
     {
      bool pivot = true;
      for(int j = 1; j <= len; j++)
        {
         if(!(r[k].low < r[k - j].low && r[k].low < r[k + j].low))
           {
            pivot = false;
            break;
           }
        }
      if(pivot)
         return r[k].low;
     }
   return 0.0;
  }

double FindSwingHigh(const MqlRates &r[], const int n, const int len)
  {
   for(int k = n - 1 - len; k >= len; k--)
     {
      bool pivot = true;
      for(int j = 1; j <= len; j++)
        {
         if(!(r[k].high > r[k - j].high && r[k].high > r[k + j].high))
           {
            pivot = false;
            break;
           }
        }
      if(pivot)
         return r[k].high;
     }
   return 0.0;
  }

//==================================================================//
//                  BUILD THE CLOSED-BAR SIGNAL CONTEXT             //
//==================================================================//
bool BuildContext(SignalCtx &c)
  {
   ZeroMemory(c);

   MqlRates r[];
   ArraySetAsSeries(r, false);
   int n = CopyRates(_Symbol, _Period, 1, InpCalcBars, r);
   if(n < g_needBars || ArraySize(r) < n)
      return false;
   int last = n - 1;                                        // bar 1

   //--- chart-TF Supertrend
   if(!SuperTrendDir(r, n, InpStFactor, InpStAtrLen, c.stDir))
      return false;

   //--- HTF Supertrend on the last CLOSED higher-timeframe bar (strictly causal)
   if(InpUseHtfFilter)
     {
      MqlRates h[];
      ArraySetAsSeries(h, false);
      int nh = CopyRates(_Symbol, InpHtf, 1, InpCalcBars, h);
      if(nh < InpStAtrLen + 10 || ArraySize(h) < nh)
         return false;
      if(!SuperTrendDir(h, nh, InpStFactor, InpStAtrLen, c.htfDir))
         return false;
     }

   //--- risk ATR and its SMA
   double atr[];
   if(!WilderATR(r, n, InpRiskAtrLen, atr))
      return false;
   c.atr = atr[last];
   if(c.atr <= 0.0)
      return false;
   int from = last - InpAtrMaLen + 1;
   if(from < InpRiskAtrLen - 1)
      return false;                                         // SMA would include unseeded values
   double s = 0.0;
   for(int i = from; i <= last; i++)
      s += atr[i];
   c.atrSma = s / (double)InpAtrMaLen;

   //--- signal bar
   c.open1  = r[last].open;
   c.high1  = r[last].high;
   c.low1   = r[last].low;
   c.close1 = r[last].close;

   //--- Donchian channel of the N bars BEFORE the signal bar (Pine: ta.highest(high,len)[1])
   from = last - InpDonchianLen;
   if(from < 0)
      return false;
   double hh = -DBL_MAX, ll = DBL_MAX;
   for(int i = from; i <= last - 1; i++)
     {
      if(r[i].high > hh)
         hh = r[i].high;
      if(r[i].low < ll)
         ll = r[i].low;
     }
   c.donHigh = hh;
   c.donLow  = ll;

   //--- tick-volume SMA including the signal bar (Pine: ta.sma(volume,len))
   from = last - InpVolMaLen + 1;
   if(from < 0)
      return false;
   double vs = 0.0;
   for(int i = from; i <= last; i++)
      vs += (double)r[i].tick_volume;
   c.volSma = vs / (double)InpVolMaLen;
   c.vol1   = (double)r[last].tick_volume;

   //--- 3-candle fair value gap ending at bar 1 (CTQ definition: middle candle
   //--- in the gap's direction, bar-1 low above bar-3 high for a bullish gap)
   if(last >= 2)
     {
      c.fvgBull = (r[last].low  > r[last - 2].high) && (r[last - 1].close > r[last - 1].open);
      c.fvgBear = (r[last].high < r[last - 2].low)  && (r[last - 1].close < r[last - 1].open);
     }

   //--- structure stops
   c.swingLow  = FindSwingLow(r, n, InpSwingLen);
   c.swingHigh = FindSwingHigh(r, n, InpSwingLen);

   //--- EMA on bars 1 and 2
   double e[];
   ArraySetAsSeries(e, true);
   if(CopyBuffer(g_hEma, 0, 1, 2, e) < 2 || ArraySize(e) < 2)
      return false;
   c.ema1 = e[0];
   c.ema2 = e[1];

   //--- ADX main line on bar 1
   double a[];
   ArraySetAsSeries(a, true);
   if(CopyBuffer(g_hAdx, 0, 1, 1, a) < 1 || ArraySize(a) < 1)
      return false;
   c.adx1 = a[0];

   return true;
  }

//==================================================================//
//                     ACCOUNT GUARDS (live equity)                 //
//==================================================================//
//--- Roll the server day: reset daily start equity and trade count.
void RollDay()
  {
   MqlDateTime dt;
   TimeToStruct(TimeCurrent(), dt);
   double key = (double)(dt.year * 10000 + dt.mon * 100 + dt.day);
   double eq  = AccountInfoDouble(ACCOUNT_EQUITY);
   if(GVGet("DAY", 0.0) != key)
     {
      GVSet("DAY", key);
      GVSet("DSE", eq);                 // day-start equity
      GVSet("TD", 0.0);                 // trades today
     }
   double peak = GVGet("PEAK", 0.0);
   if(eq > peak)
      GVSet("PEAK", eq);
  }

bool DailyLimitHit()
  {
   double start = GVGet("DSE", 0.0);
   double eq    = AccountInfoDouble(ACCOUNT_EQUITY);
   if(start <= 0.0)
      return false;
   return ((start - eq) / start * 100.0) >= InpDailyLossPct;
  }

//--- Max drawdown is a PERMANENT halt (prop-firm style). To resume, delete
//--- the GlobalVariable "<prefix>HALT" in MT5 (F3) after reviewing the account.
bool MaxDrawdownHit()
  {
   if(GVGet("HALT", 0.0) >= 1.0)
      return true;
   double peak = GVGet("PEAK", 0.0);
   double eq   = AccountInfoDouble(ACCOUNT_EQUITY);
   if(peak <= 0.0)
      return false;
   if(((peak - eq) / peak * 100.0) >= InpMaxDrawdownPct)
     {
      GVSet("HALT", 1.0);
      PrintFormat("TLQ HALT: drawdown from equity peak reached %.2f%%. Delete GV %sHALT to resume.",
                  InpMaxDrawdownPct, g_pfx);
      return true;
     }
   return false;
  }

bool InSession()
  {
   if(!InpUseSession)
      return true;
   MqlDateTime dt;
   TimeToStruct(TimeCurrent(), dt);
   if(InpStartHour <= InpEndHour)
      return (dt.hour >= InpStartHour && dt.hour < InpEndHour);
   return (dt.hour >= InpStartHour || dt.hour < InpEndHour);   // window wraps midnight
  }

//--- Adaptive error guard: a direction that just lost is locked for a while.
//--- The lock only ever REDUCES trading. It never changes position size.
bool ErrorGuardOK(const int dir)
  {
   if(!InpUseErrorGuard)
      return true;
   datetime until = (datetime)(long)GVGet(dir > 0 ? "LOCKL" : "LOCKS", 0.0);
   return TimeCurrent() > until;
  }

void RecordOutcome(const int dir, const double pnl)
  {
   if(!InpUseErrorGuard)
      return;
   if(pnl < 0.0)
     {
      int      lastDir = (int)GVGet("LLDIR", 0.0);
      datetime lastT   = (datetime)(long)GVGet("LLTIME", 0.0);
      int      cnt     = (int)GVGet("LLCNT", 0.0);
      long     window  = (long)InpErrorLookbackBars * (long)PeriodSeconds();
      bool     streak  = (lastDir == dir && lastT > 0 &&
                          ((long)TimeCurrent() - (long)lastT) <= window);
      if(streak)
         cnt = (cnt + 1 > InpMaxErrorMultiplier) ? InpMaxErrorMultiplier : cnt + 1;
      else
         cnt = 1;
      long     lockSecs = (long)InpErrorCooldownBars * (long)cnt * (long)PeriodSeconds();
      datetime until    = (datetime)((long)TimeCurrent() + lockSecs);
      GVSet(dir > 0 ? "LOCKL" : "LOCKS", (double)(long)until);
      GVSet("LLDIR", (double)dir);
      GVSet("LLTIME", (double)(long)TimeCurrent());
      GVSet("LLCNT", (double)cnt);
      PrintFormat("TLQ error guard: %s loss (%.2f), streak x%d, direction locked until %s",
                  dir > 0 ? "LONG" : "SHORT", pnl, cnt, TimeToString(until, TIME_DATE | TIME_MINUTES));
     }
   else if(pnl > 0.0)
     {
      GVSet("LLCNT", 0.0);                              // a win resets the streak
      GVSet("LLDIR", 0.0);
     }
  }

//--- Every permission and guard that must hold before ANY new entry.
bool EntryGuardsOK(const int dir, string &why)
  {
   why = "";
   if(!TerminalInfoInteger(TERMINAL_TRADE_ALLOWED)) { why = "TERMINAL_ALGO_DISABLED";  return false; }
   if(!MQLInfoInteger(MQL_TRADE_ALLOWED))           { why = "EA_TRADE_NOT_ALLOWED";    return false; }
   if(!AccountInfoInteger(ACCOUNT_TRADE_ALLOWED))   { why = "ACCOUNT_TRADE_DISABLED";  return false; }
   if(!AccountInfoInteger(ACCOUNT_TRADE_EXPERT))    { why = "ACCOUNT_EA_DISABLED";     return false; }

   ENUM_SYMBOL_TRADE_MODE mode = (ENUM_SYMBOL_TRADE_MODE)SymbolInfoInteger(_Symbol, SYMBOL_TRADE_MODE);
   bool modeOK = (mode == SYMBOL_TRADE_MODE_FULL) ||
                 (mode == SYMBOL_TRADE_MODE_LONGONLY  && dir > 0) ||
                 (mode == SYMBOL_TRADE_MODE_SHORTONLY && dir < 0);
   if(!modeOK)                                     { why = "SYMBOL_TRADE_MODE";       return false; }

   if(MaxDrawdownHit())                            { why = "MAX_DRAWDOWN_HALT";       return false; }
   if(DailyLimitHit())                             { why = "DAILY_LOSS_LIMIT";        return false; }
   if((int)GVGet("TD", 0.0) >= InpMaxTradesPerDay) { why = "MAX_TRADES_PER_DAY";      return false; }
   if(!InSession())                                { why = "OUTSIDE_SESSION";         return false; }
   if(!ErrorGuardOK(dir))                          { why = "ERROR_GUARD_COOLDOWN";    return false; }
   return true;
  }

//==================================================================//
//                          POSITION SIZING                         //
//==================================================================//
//--- Lots such that a stop-out loses InpRiskPercent of equity.
//--- Loss per lot = (stop distance / tick size) x tick value, queried
//--- natively from the broker. TICK_VALUE_LOSS is used where the broker
//--- publishes it (more exact for cross-currency symbols), else TICK_VALUE.
double CalcLots(const double stopDist, string &why)
  {
   why = "";
   double equity   = AccountInfoDouble(ACCOUNT_EQUITY);
   double tickSize = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   double tickVal  = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE_LOSS);
   if(tickVal <= 0.0)
      tickVal = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
   double vmin     = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);

   if(equity <= 0.0)                      { why = "INVALID_EQUITY";          return 0.0; }
   if(tickSize <= 0.0 || tickVal <= 0.0)  { why = "INVALID_TICK_SPEC";       return 0.0; }
   if(stopDist <= 0.0)                    { why = "ZERO_STOP_DISTANCE";      return 0.0; }
   if(vmin <= 0.0)                        { why = "INVALID_VOLUME_SPEC";     return 0.0; }

   double lossPerLot = (stopDist / tickSize) * tickVal;
   if(lossPerLot <= 0.0)                  { why = "ZERO_LOSS_PER_LOT";       return 0.0; }

   double riskMoney = equity * InpRiskPercent / 100.0;
   double lots      = NormalizeVolumeDown(riskMoney / lossPerLot);

   if(lots < vmin)
     {
      // Target risk is below the broker's smallest lot. Taking the minimum lot
      // is allowed ONLY if it still fits under the hard ceiling. Risk is never
      // raised merely because the broker's minimum is larger.
      double minLotRisk = lossPerLot * vmin / equity * 100.0;
      if(minLotRisk > InpMaxRiskPercent)
        {
         why = StringFormat("MIN_LOT_RISK_%.2fPCT_EXCEEDS_CEILING", minLotRisk);
         return 0.0;
        }
      lots = NormalizeVolumeDown(vmin);
     }

   // final re-check after every normalisation
   double actualRisk = lossPerLot * lots / equity * 100.0;
   if(actualRisk > InpMaxRiskPercent + 1e-9)
     {
      why = StringFormat("ACTUAL_RISK_%.2fPCT_EXCEEDS_CEILING", actualRisk);
      return 0.0;
     }
   return lots;
  }

//==================================================================//
//                              ENTRY                               //
//==================================================================//
void TryOpen(const int dir, const SignalCtx &c)
  {
   string why;
   if(!EntryGuardsOK(dir, why))
     {
      if(InpVerbose)
         PrintFormat("TLQ %s signal rejected: %s", dir > 0 ? "LONG" : "SHORT", why);
      return;
     }

   double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   if(ask <= 0.0 || bid <= 0.0 || ask < bid)
      return;
   double spread = ask - bid;

   //--- spread guards
   if(InpMaxSpreadPoints > 0.0 && spread / _Point > InpMaxSpreadPoints)
     {
      if(InpVerbose)
         PrintFormat("TLQ reject: spread %.1f pts > %.1f", spread / _Point, InpMaxSpreadPoints);
      return;
     }
   if(InpMaxSpreadAtrFrac > 0.0 && spread > c.atr * InpMaxSpreadAtrFrac)
     {
      if(InpVerbose)
         PrintFormat("TLQ reject: spread %.5f > ATR x %.2f", spread, InpMaxSpreadAtrFrac);
      return;
     }

   double entry = (dir > 0) ? ask : bid;

   //--- stop construction
   double atrStop = (dir > 0) ? entry - c.atr * InpSlAtrMult : entry + c.atr * InpSlAtrMult;
   double structStop  = 0.0;
   bool   structValid = false;
   if(dir > 0 && c.swingLow > 0.0)
     {
      structStop  = c.swingLow - c.atr * InpSwingBufferAtr;
      structValid = (structStop < entry);
     }
   if(dir < 0 && c.swingHigh > 0.0)
     {
      structStop  = c.swingHigh + c.atr * InpSwingBufferAtr;
      structValid = (structStop > entry);
     }

   double stop = atrStop;
   if(InpStopMode == STOP_STRUCTURE && structValid)
      stop = structStop;
   else if(InpStopMode == STOP_COMBINED && structValid)
      stop = (dir > 0) ? MathMax(atrStop, structStop) : MathMin(atrStop, structStop);

   //--- floor: never tighter than ATR x InpMinStopAtr, never inside the broker
   //--- stops level. The stop is measured from the side it triggers on (bid for
   //--- longs, ask for shorts), hence + spread. Widening BEFORE entry is safe:
   //--- sizing below uses the final distance, so money at risk is unchanged.
   double minDist = MathMax(c.atr * InpMinStopAtr, MinStopsDist() + spread);
   if(dir > 0 && entry - stop < minDist)
      stop = entry - minDist;
   if(dir < 0 && stop - entry < minDist)
      stop = entry + minDist;
   stop = NormalizePrice(stop);

   double dist = MathAbs(entry - stop);
   if(dist <= 0.0)
      return;

   //--- server-side final target = TP3. It protects the trade even if the EA
   //--- stops running. TP1/TP2 partials are managed by the EA on ticks.
   double tp = NormalizePrice((dir > 0) ? entry + InpTp3R * dist : entry - InpTp3R * dist);
   if(MathAbs(tp - entry) < MinStopsDist() + spread)
      return;

   //--- sizing
   double lots = CalcLots(dist, why);
   if(lots <= 0.0)
     {
      PrintFormat("TLQ %s NO TRADE: %s", dir > 0 ? "LONG" : "SHORT", why);
      return;
     }

   //--- margin check with the broker's own calculator
   double margin = 0.0;
   ENUM_ORDER_TYPE otype = (dir > 0) ? ORDER_TYPE_BUY : ORDER_TYPE_SELL;
   if(!OrderCalcMargin(otype, _Symbol, lots, entry, margin))
     {
      PrintFormat("TLQ NO TRADE: OrderCalcMargin failed, err %d", GetLastError());
      return;
     }
   double freeMargin = AccountInfoDouble(ACCOUNT_MARGIN_FREE);
   if(freeMargin <= 0.0 || margin / freeMargin * 100.0 > InpMaxMarginPercent)
     {
      PrintFormat("TLQ NO TRADE: margin %.2f vs free %.2f exceeds %.0f%% cap",
                  margin, freeMargin, InpMaxMarginPercent);
      return;
     }

   //--- send
   bool ok = (dir > 0) ? g_trade.Buy(lots, _Symbol, ask, stop, tp, InpComment)
                       : g_trade.Sell(lots, _Symbol, bid, stop, tp, InpComment);
   uint rc = g_trade.ResultRetcode();
   if(!ok || (rc != TRADE_RETCODE_DONE && rc != TRADE_RETCODE_PLACED && rc != TRADE_RETCODE_DONE_PARTIAL))
     {
      PrintFormat("TLQ %s order FAILED rc=%u (%s)", dir > 0 ? "BUY" : "SELL", rc,
                  g_trade.ResultRetcodeDescription());
      return;
     }
   PrintFormat("TLQ %s %.2f lots @%.5f SL %.5f TP3 %.5f (R=%.5f)",
               dir > 0 ? "BUY" : "SELL", lots, entry, stop, tp, dist);
  }

//==================================================================//
//                 POSITION MANAGEMENT (every tick, O(1))           //
//==================================================================//
//--- Move the stop to the entry price. Stops only ever move closer to
//--- price; a request that would widen risk is never sent.
bool MoveToBreakeven(const ulong ticket)
  {
   if(!PositionSelectByTicket(ticket))
      return false;
   long   type = PositionGetInteger(POSITION_TYPE);
   double open = PositionGetDouble(POSITION_PRICE_OPEN);
   double sl   = PositionGetDouble(POSITION_SL);
   double tp   = PositionGetDouble(POSITION_TP);
   double be   = NormalizePrice(open);
   double bid  = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   double ask  = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   double stops  = MinStopsDist();
   double freeze = FreezeDist();

   if(type == POSITION_TYPE_BUY)
     {
      if(sl > 0.0 && sl >= be)
         return true;                                   // already at or beyond breakeven
      if(bid - be < stops)
         return false;                                  // too close to price right now
      if(sl > 0.0 && freeze > 0.0 && bid - sl <= freeze)
         return false;
      if(tp > 0.0 && freeze > 0.0 && tp - bid <= freeze)
         return false;
     }
   else
     {
      if(sl > 0.0 && sl <= be)
         return true;
      if(be - ask < stops)
         return false;
      if(sl > 0.0 && freeze > 0.0 && sl - ask <= freeze)
         return false;
      if(tp > 0.0 && freeze > 0.0 && ask - tp <= freeze)
         return false;
     }
   if(!g_trade.PositionModify(ticket, be, tp))
      return false;
   return (g_trade.ResultRetcode() == TRADE_RETCODE_DONE);
  }

//--- Close part of the position.
//--- Returns 1 = closed, 0 = split not possible at this volume (skip tier),
//--- -1 = request failed (retry later).
int TryPartial(const ulong ticket, const double wantVolume)
  {
   if(!PositionSelectByTicket(ticket))
      return -1;
   double cur  = PositionGetDouble(POSITION_VOLUME);
   double vmin = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double v    = NormalizeVolumeDown(wantVolume);
   // Both the closed slice and the remainder must be valid broker volumes.
   if(v < vmin - 1e-12 || cur - v < vmin - 1e-12)
      return 0;
   if(!g_trade.PositionClosePartial(ticket, v))
     {
      PrintFormat("TLQ partial close failed rc=%u (%s)", g_trade.ResultRetcode(),
                  g_trade.ResultRetcodeDescription());
      return -1;
     }
   uint rc = g_trade.ResultRetcode();
   if(rc == TRADE_RETCODE_DONE || rc == TRADE_RETCODE_DONE_PARTIAL || rc == TRADE_RETCODE_PLACED)
      return 1;
   return -1;
  }

//--- First sight of a new position: store its ORIGINAL risk distance and
//--- volume. After breakeven the stop sits at entry, so R could no longer be
//--- derived from the live stop; it has to be remembered.
bool RegisterPosition(const ulong ticket, const string key)
  {
   if(!PositionSelectByTicket(ticket))
      return false;
   long   type   = PositionGetInteger(POSITION_TYPE);
   double open   = PositionGetDouble(POSITION_PRICE_OPEN);
   double sl     = PositionGetDouble(POSITION_SL);
   double tp     = PositionGetDouble(POSITION_TP);
   double vol    = PositionGetDouble(POSITION_VOLUME);
   bool   isLong = (type == POSITION_TYPE_BUY);

   //--- a position without a server-side stop is never left unprotected
   if(sl <= 0.0)
     {
      if(g_lastAtr <= 0.0)
        {
         Print("TLQ CRITICAL: position has no stop and no ATR is available yet. Retrying.");
         return false;
        }
      double reSL = NormalizePrice(isLong ? open - g_lastAtr * InpSlAtrMult
                                          : open + g_lastAtr * InpSlAtrMult);
      if(!g_trade.PositionModify(ticket, reSL, tp) || g_trade.ResultRetcode() != TRADE_RETCODE_DONE)
        {
         PrintFormat("TLQ CRITICAL: could not re-protect position %I64u (rc=%u)", ticket,
                     g_trade.ResultRetcode());
         return false;
        }
      sl = reSL;
      PrintFormat("TLQ WARNING: position %I64u had no stop; re-protected at %.5f", ticket, reSL);
     }

   double R = MathAbs(open - sl);
   if(R <= 0.0)
     {
      Print("TLQ WARNING: zero risk distance (stop already at entry); tier management disabled.");
      return false;
     }

   //--- align the server TP to exactly TP3 x R of the ACTUAL fill
   double tp3      = NormalizePrice(isLong ? open + InpTp3R * R : open - InpTp3R * R);
   double tickSize = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   if(tickSize > 0.0 && MathAbs(tp - tp3) > tickSize)
     {
      if(!g_trade.PositionModify(ticket, sl, tp3) || g_trade.ResultRetcode() != TRADE_RETCODE_DONE)
         PrintFormat("TLQ note: TP3 re-alignment refused (rc=%u); keeping TP %.5f",
                     g_trade.ResultRetcode(), tp);
     }

   GVSet(key + "R",  R);
   GVSet(key + "V0", vol);
   GVSet(key + "S",  0.0);     // tier stage: 0 none, 1 after TP1, 2 after TP2
   GVSet(key + "B",  0.0);     // breakeven applied
   return true;
  }

//--- 3-tier scaling, evaluated on every tick:
//---   TP1 (1R): close InpTp1ClosePct of ORIGINAL volume, stop -> breakeven
//---   TP2 (2R): close InpTp2ClosePct of ORIGINAL volume
//---   TP3 (3R): server-side take-profit closes the remainder
void ManagePosition()
  {
   ulong ticket;
   if(!SelectOurPosition(ticket))
      return;

   long   type   = PositionGetInteger(POSITION_TYPE);
   double open   = PositionGetDouble(POSITION_PRICE_OPEN);
   double tp     = PositionGetDouble(POSITION_TP);
   long   posId  = PositionGetInteger(POSITION_IDENTIFIER);
   bool   isLong = (type == POSITION_TYPE_BUY);
   string key    = PosKey(posId);

   //--- a failed request is retried at most every 5 seconds, not every tick
   if(g_lastMgmtTry > 0 && TimeCurrent() - g_lastMgmtTry < 5)
      return;

   if(!GlobalVariableCheck(g_pfx + key + "R"))
     {
      if(!RegisterPosition(ticket, key))
        {
         g_lastMgmtTry = TimeCurrent();
         return;
        }
     }

   double R     = GVGet(key + "R", 0.0);
   double v0    = GVGet(key + "V0", 0.0);
   int    stage = (int)GVGet(key + "S", 0.0);
   int    beSet = (int)GVGet(key + "B", 0.0);
   if(R <= 0.0 || v0 <= 0.0)
      return;

   double bid   = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   double ask   = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   double favor = isLong ? bid - open : open - ask;      // measured on the closing side

   //--- breakeven is retried until it succeeds (stops/freeze levels can delay it)
   if(stage >= 1 && beSet == 0)
     {
      if(MoveToBreakeven(ticket))
         GVSet(key + "B", 1.0);
      else
         g_lastMgmtTry = TimeCurrent();
     }

   //--- TP1
   if(stage == 0 && favor >= InpTp1R * R)
     {
      int res = TryPartial(ticket, v0 * InpTp1ClosePct / 100.0);
      if(res < 0)
        {
         g_lastMgmtTry = TimeCurrent();
         return;
        }
      if(res == 0)
         Print("TLQ TP1: volume too small to split; full volume rides to TP3 with breakeven.");
      GVSet(key + "S", 1.0);
      if(MoveToBreakeven(ticket))
         GVSet(key + "B", 1.0);
      return;
     }

   //--- TP2
   if(stage == 1 && favor >= InpTp2R * R)
     {
      int res = TryPartial(ticket, v0 * InpTp2ClosePct / 100.0);
      if(res < 0)
        {
         g_lastMgmtTry = TimeCurrent();
         return;
        }
      if(res == 0)
         Print("TLQ TP2: volume too small to split; remainder rides to TP3.");
      GVSet(key + "S", 2.0);
      return;
     }

   //--- TP3 fallback: only if the server TP is missing (e.g. broker rejected it)
   if(tp <= 0.0 && favor >= InpTp3R * R)
     {
      if(!g_trade.PositionClose(ticket))
         g_lastMgmtTry = TimeCurrent();
     }
  }

//--- Remove tier state left behind by positions that no longer exist.
void SweepPositionGVs(const long keepId)
  {
   string pfx   = g_pfx + "P";
   string keep  = g_pfx + PosKey(keepId);
   int    total = GlobalVariablesTotal();
   for(int i = total - 1; i >= 0; i--)
     {
      string name = GlobalVariableName(i);
      if(StringFind(name, pfx) != 0)
         continue;
      if(keepId > 0 && StringFind(name, keep) == 0)
         continue;
      GlobalVariableDel(name);
     }
  }

//==================================================================//
//                         NEW-BAR PIPELINE                         //
//==================================================================//
void OnNewBar()
  {
   RollDay();

   SignalCtx c;
   if(!BuildContext(c))
      return;
   g_lastAtr = c.atr;

   ulong ticket;
   bool  hasPos = SelectOurPosition(ticket);
   long  posId  = hasPos ? PositionGetInteger(POSITION_IDENTIFIER) : 0;
   SweepPositionGVs(posId);

   //--- account limits may also flatten, if configured
   if(hasPos && InpFlattenOnLimit && (DailyLimitHit() || MaxDrawdownHit()))
     {
      if(g_trade.PositionClose(ticket))
         Print("TLQ: position closed because an account limit was hit.");
      return;
     }

   //--- STDB exit: close when the chart Supertrend turns against the position
   if(hasPos)
     {
      if(InpExitOnTrendFlip && PositionSelectByTicket(ticket))
        {
         long type = PositionGetInteger(POSITION_TYPE);
         bool flip = (type == POSITION_TYPE_BUY && c.stDir > 0) ||
                     (type == POSITION_TYPE_SELL && c.stDir < 0);
         if(flip && g_trade.PositionClose(ticket))
            Print("TLQ: closed on Supertrend flip.");
        }
      return;                                   // one position at a time; no same-bar re-entry
     }

   //--- shared filters
   double range     = c.high1 - c.low1;
   double bodyRatio = (range > 0.0) ? MathAbs(c.close1 - c.open1) / range : 0.0;
   bool volOK  = !InpUseVolFilter    || (c.volSma > 0.0 && c.vol1 > c.volSma * InpVolMult);
   bool atrOK  = !InpUseAtrExpansion || (c.atrSma > 0.0 && c.atr >= c.atrSma * InpAtrExpansionMult);
   bool chop   = InpUseChopFilter && c.adx1 <= InpChopAdxMax &&
                 MathAbs(c.ema1 - c.ema2) <= c.atr * InpChopSlopeAtrMax;

   //--- LONG: trend up (chart + HTF), real Donchian breakout of the upper band
   bool longSig = InpAllowLong
                  && c.stDir < 0
                  && (!InpUseHtfFilter || c.htfDir < 0)
                  && c.close1 > c.donHigh
                  && volOK && atrOK && !chop
                  && (!InpUseEmaFilter  || (c.close1 > c.ema1 && c.ema1 > c.ema2))
                  && (!InpUseBodyFilter || (c.close1 > c.open1 && bodyRatio >= InpBodyRatioMin))
                  && (!InpRequireFvg    || c.fvgBull);

   //--- SHORT: mirror image, breakdown of the lower band
   bool shortSig = InpAllowShort
                   && c.stDir > 0
                   && (!InpUseHtfFilter || c.htfDir > 0)
                   && c.close1 < c.donLow
                   && volOK && atrOK && !chop
                   && (!InpUseEmaFilter  || (c.close1 < c.ema1 && c.ema1 < c.ema2))
                   && (!InpUseBodyFilter || (c.close1 < c.open1 && bodyRatio >= InpBodyRatioMin))
                   && (!InpRequireFvg    || c.fvgBear);

   // Supertrend direction is exclusive, so both cannot be true together.
   if(longSig)
      TryOpen(1, c);
   else if(shortSig)
      TryOpen(-1, c);
  }

//==================================================================//
//                        INPUT VALIDATION                          //
//==================================================================//
bool ValidateInputs(string &why)
  {
   why = "";
   if(InpRiskPercent <= 0.0 || InpRiskPercent > InpMaxRiskPercent) { why = "InpRiskPercent must be in (0, InpMaxRiskPercent]"; return false; }
   if(InpMaxRiskPercent <= 0.0 || InpMaxRiskPercent > 5.0)         { why = "InpMaxRiskPercent must be in (0, 5]"; return false; }
   if(InpMaxMarginPercent <= 0.0 || InpMaxMarginPercent > 100.0)   { why = "InpMaxMarginPercent must be in (0, 100]"; return false; }
   if(InpDailyLossPct <= 0.0 || InpMaxDrawdownPct <= 0.0)          { why = "loss limits must be positive"; return false; }
   if(InpMaxTradesPerDay < 1)                                       { why = "InpMaxTradesPerDay must be >= 1"; return false; }
   if(InpDeviationPoints < 0 || InpMaxSpreadPoints < 0.0 || InpMaxSpreadAtrFrac < 0.0) { why = "spread/deviation inputs must be >= 0"; return false; }
   if(InpStFactor <= 0.0 || InpStAtrLen < 1)                       { why = "Supertrend inputs invalid"; return false; }
   if(InpDonchianLen < 2 || InpVolMaLen < 1 || InpEmaLen < 2)      { why = "lookback lengths too small"; return false; }
   if(InpRiskAtrLen < 1 || InpAtrMaLen < 1 || InpAdxLen < 2)       { why = "ATR/ADX lengths invalid"; return false; }
   if(InpSwingLen < 1)                                              { why = "InpSwingLen must be >= 1"; return false; }
   if(InpSlAtrMult <= 0.0 || InpMinStopAtr < 0.0 || InpSwingBufferAtr < 0.0) { why = "stop inputs invalid"; return false; }
   if(!(InpTp1R > 0.0 && InpTp1R < InpTp2R && InpTp2R < InpTp3R))  { why = "targets must satisfy 0 < TP1 < TP2 < TP3"; return false; }
   if(InpTp1ClosePct <= 0.0 || InpTp2ClosePct <= 0.0 ||
      InpTp1ClosePct + InpTp2ClosePct >= 100.0)                    { why = "TP1% + TP2% must be positive and < 100"; return false; }
   if(InpErrorCooldownBars < 0 || InpMaxErrorMultiplier < 1 || InpErrorLookbackBars < 1) { why = "error-guard inputs invalid"; return false; }
   if(InpStartHour < 0 || InpStartHour > 23 || InpEndHour < 0 || InpEndHour > 23) { why = "session hours must be 0..23"; return false; }
   if(InpUseHtfFilter && PeriodSeconds(InpHtf) <= PeriodSeconds(_Period)) { why = "InpHtf must be a HIGHER timeframe than the chart"; return false; }
   if(InpCalcBars < g_needBars)                                     { why = StringFormat("InpCalcBars must be >= %d", g_needBars); return false; }
   return true;
  }

//==================================================================//
//                          EVENT HANDLERS                          //
//==================================================================//
int OnInit()
  {
   g_pfx = "TLQ_" + IntegerToString(InpMagic) + "_" + _Symbol + "_";

   // bars needed for every lookback to be valid on bar 1
   int longest = MathMax(InpStAtrLen, InpRiskAtrLen);
   g_needBars  = longest + InpAtrMaLen + InpDonchianLen + InpVolMaLen + 2 * InpSwingLen + 20;

   string why;
   if(!ValidateInputs(why))
     {
      Print("TLQ INIT FAILED: ", why);
      return INIT_PARAMETERS_INCORRECT;
     }

   if(!SymbolSelect(_Symbol, true) || SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE) <= 0.0 ||
      SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP) <= 0.0)
     {
      Print("TLQ INIT FAILED: invalid symbol specification");
      return INIT_FAILED;
     }

   g_hEma = iMA(_Symbol, _Period, InpEmaLen, 0, MODE_EMA, PRICE_CLOSE);
   g_hAdx = iADXWilder(_Symbol, _Period, InpAdxLen);
   if(g_hEma == INVALID_HANDLE || g_hAdx == INVALID_HANDLE)
     {
      Print("TLQ INIT FAILED: indicator handle creation, err ", GetLastError());
      return INIT_FAILED;
     }

   g_trade.SetExpertMagicNumber((ulong)InpMagic);
   g_trade.SetDeviationInPoints((ulong)InpDeviationPoints);
   g_trade.SetTypeFillingBySymbol(_Symbol);
   g_trade.SetAsyncMode(false);           // synchronous: every retcode is checked before continuing

   ENUM_ACCOUNT_MARGIN_MODE mm = (ENUM_ACCOUNT_MARGIN_MODE)AccountInfoInteger(ACCOUNT_MARGIN_MODE);
   PrintFormat("TLQ init %s %s | margin mode %s | risk %.2f%% (ceiling %.2f%%) | TP %.1fR/%.1fR/%.1fR",
               _Symbol, EnumToString(_Period), EnumToString(mm), InpRiskPercent, InpMaxRiskPercent,
               InpTp1R, InpTp2R, InpTp3R);
   if(mm == ACCOUNT_MARGIN_MODE_RETAIL_NETTING)
      Print("TLQ note: NETTING account. Do not trade this symbol manually or with another EA "
            "at the same time; netting merges all trades on a symbol into one position.");

   RollDay();
   return INIT_SUCCEEDED;
  }

void OnDeinit(const int reason)
  {
   // Release every indicator handle so the terminal frees its buffers.
   if(g_hEma != INVALID_HANDLE)
     {
      IndicatorRelease(g_hEma);
      g_hEma = INVALID_HANDLE;
     }
   if(g_hAdx != INVALID_HANDLE)
     {
      IndicatorRelease(g_hAdx);
      g_hAdx = INVALID_HANDLE;
     }
   PrintFormat("TLQ deinit, reason %d", reason);
  }

void OnTick()
  {
   // Tier 1: every tick, cheap. Tiered exits and breakeven need tick precision.
   ManagePosition();

   // Tier 2: once per new bar. All signal math runs on closed bars only.
   datetime bt = iTime(_Symbol, _Period, 0);
   if(bt == 0 || bt == g_lastBar)
      return;
   g_lastBar = bt;
   OnNewBar();
  }

//--- Broker deal history is authoritative for counting trades and for the
//--- outcome that feeds the error guard.
void OnTradeTransaction(const MqlTradeTransaction &trans,
                        const MqlTradeRequest &request,
                        const MqlTradeResult &result)
  {
   if(trans.type != TRADE_TRANSACTION_DEAL_ADD)
      return;
   if(!HistoryDealSelect(trans.deal))
      return;
   if(HistoryDealGetString(trans.deal, DEAL_SYMBOL) != _Symbol)
      return;
   if(HistoryDealGetInteger(trans.deal, DEAL_MAGIC) != InpMagic)
      return;

   RollDay();
   ENUM_DEAL_ENTRY entry = (ENUM_DEAL_ENTRY)HistoryDealGetInteger(trans.deal, DEAL_ENTRY);

   if(entry == DEAL_ENTRY_IN)
     {
      GVSet("TD", GVGet("TD", 0.0) + 1.0);      // counted at the confirmed fill
      return;
     }
   if(entry != DEAL_ENTRY_OUT && entry != DEAL_ENTRY_OUT_BY)
      return;

   long posId = HistoryDealGetInteger(trans.deal, DEAL_POSITION_ID);
   if(PositionSelectByTicket((ulong)posId))
      return;                                   // partial close: the trade is still open

   // A closing SELL deal ends a LONG position, and vice versa.
   ENUM_DEAL_TYPE dtype = (ENUM_DEAL_TYPE)HistoryDealGetInteger(trans.deal, DEAL_TYPE);
   int dir = (dtype == DEAL_TYPE_SELL) ? 1 : -1;

   // Net result of the whole position, including partials, costs and swap.
   double pnl = 0.0;
   if(HistorySelectByPosition(posId))
     {
      int n = HistoryDealsTotal();
      for(int i = 0; i < n; i++)
        {
         ulong d = HistoryDealGetTicket(i);
         if(d == 0)
            continue;
         pnl += HistoryDealGetDouble(d, DEAL_PROFIT)
              + HistoryDealGetDouble(d, DEAL_SWAP)
              + HistoryDealGetDouble(d, DEAL_COMMISSION)
              + HistoryDealGetDouble(d, DEAL_FEE);
        }
     }
   RecordOutcome(dir, pnl);

   string key = PosKey(posId);
   GVDel(key + "R");
   GVDel(key + "V0");
   GVDel(key + "S");
   GVDel(key + "B");
  }
//+------------------------------------------------------------------+
