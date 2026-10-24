// NEXA Monitor v2 journal logic: market context, "what if" outcomes, excursions and follow-ups.
// Pure C#, no ATAS dependency (unit-tested in NexaMonitor.Tests). Facts only: nothing here is an entry signal.
// Field sources: research/intelligence/JOURNAL_SOURCES_DECODE.md (J1–J11).
using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;

namespace Nexa.Atas
{
    /// <summary>One chart bar (ATAS IndicatorCandle copied out). Times are UTC.</summary>
    public sealed record Bar(DateTime TimeUtc, decimal Open, decimal High, decimal Low, decimal Close, decimal Volume,
                             decimal Delta, decimal AskVolume, decimal BidVolume, decimal MaxDelta, decimal MinDelta, decimal Poc);

    /// <summary>Price levels and location of one bar, from the bars up to and including it (no look-ahead).</summary>
    public sealed class MarketContext
    {
        public static readonly TimeSpan RthOpen = new(8, 30, 0), RthClose = new(15, 0, 0);

        public Bar Bar, PrevBar;
        public decimal? VwapRth, VwapEth, RthOpenPrice, RthHigh, RthLow, Or30High, Or30Low, IbHigh, IbLow;
        public decimal? PriorHigh, PriorLow, PriorClose, OnHigh, OnLow, Atr14, RelVolume, Change5, Delta5;
        public bool InRth, IbComplete, RthClosed;

        public decimal Price => Bar.Close;
        public decimal BodyPct => Range(Bar) == 0 ? 0 : Math.Abs(Bar.Close - Bar.Open) / Range(Bar);
        public decimal UpperWickPct => Range(Bar) == 0 ? 0 : (Bar.High - Math.Max(Bar.Open, Bar.Close)) / Range(Bar);
        public decimal LowerWickPct => Range(Bar) == 0 ? 0 : (Math.Min(Bar.Open, Bar.Close) - Bar.Low) / Range(Bar);
        public string BarDirection => Bar.Close > Bar.Open ? "up" : Bar.Close < Bar.Open ? "down" : "flat";
        /// <summary>Does the bar's delta point the same way as its body? (descriptive only)</summary>
        public string DeltaVsBar => Bar.Delta == 0 || BarDirection == "flat" ? "n/a"
            : (Bar.Delta > 0) == (Bar.Close > Bar.Open) ? "agrees" : "disagrees";
        public decimal? Vwap => InRth ? VwapRth : VwapEth;
        public string VsVwap => Vwap is decimal v ? (Price > v ? "above" : Price < v ? "below" : "at") : "n/a";
        public string VsPriorRange => PriorHigh is decimal h && PriorLow is decimal l
            ? (Price > h ? "above prior-day high" : Price < l ? "below prior-day low" : "inside prior-day range") : "no prior day";
        public string VsIb => RthClosed ? "RTH closed" : !InRth ? "pre-open" : !IbComplete ? "IB forming"
            : Price > IbHigh ? "above IB" : Price < IbLow ? "below IB" : "inside IB";

        private static decimal Range(Bar b) => b.High - b.Low;

        /// <summary>Context for bars[idx]. RTH = 08:30–15:00 CT; overnight = Topstep session (17:00 CT) before 08:30 CT.</summary>
        public static MarketContext Compute(IReadOnlyList<Bar> bars, int idx)
        {
            if (bars == null || idx < 0 || idx >= bars.Count) return null;
            var c = new MarketContext { Bar = bars[idx], PrevBar = idx > 0 ? bars[idx - 1] : null };
            var nowCt = SessionClock.ToCt(c.Bar.TimeUtc);
            var session = SessionClock.SessionKey(c.Bar.TimeUtc);
            var today = nowCt.Date;
            c.InRth = nowCt.TimeOfDay >= RthOpen && nowCt.TimeOfDay < RthClose;
            c.RthClosed = nowCt.TimeOfDay >= RthClose && nowCt.TimeOfDay < new TimeSpan(17, 0, 0);

            decimal pvR = 0, vR = 0, pvE = 0, vE = 0;
            DateTime? priorDate = null;
            var priorCutoff = nowCt.TimeOfDay >= RthClose ? today.AddDays(1) : today;   // after 15:00 CT today's RTH is the prior day
            for (var i = idx; i >= 0; i--)
            {
                var b = bars[i];
                var ct = SessionClock.ToCt(b.TimeUtc);
                var rth = ct.TimeOfDay >= RthOpen && ct.TimeOfDay < RthClose;
                var tp = (b.High + b.Low + b.Close) / 3m;
                if (SessionClock.SessionKey(b.TimeUtc) == session)
                {
                    pvE += tp * b.Volume; vE += b.Volume;
                    if (ct.TimeOfDay < RthOpen || ct.TimeOfDay >= new TimeSpan(17, 0, 0))
                    {
                        c.OnHigh = Max(c.OnHigh, b.High); c.OnLow = Min(c.OnLow, b.Low);
                    }
                }
                if (rth && ct.Date == today && c.InRth)
                {
                    pvR += tp * b.Volume; vR += b.Volume;
                    c.RthHigh = Max(c.RthHigh, b.High); c.RthLow = Min(c.RthLow, b.Low);
                    c.RthOpenPrice = b.Open;                                   // last assignment = earliest RTH bar
                    var mins = (ct.TimeOfDay - RthOpen).TotalMinutes;
                    if (mins < 30) { c.Or30High = Max(c.Or30High, b.High); c.Or30Low = Min(c.Or30Low, b.Low); }
                    if (mins < 60) { c.IbHigh = Max(c.IbHigh, b.High); c.IbLow = Min(c.IbLow, b.Low); }
                }
                if (rth && ct.Date < priorCutoff)
                {
                    priorDate ??= ct.Date;
                    if (ct.Date != priorDate) break;                          // only the most recent completed RTH day
                    if (c.PriorClose == null) c.PriorClose = b.Close;         // first seen walking back = last bar of that day
                    c.PriorHigh = Max(c.PriorHigh, b.High); c.PriorLow = Min(c.PriorLow, b.Low);
                }
            }
            if (vR > 0) c.VwapRth = pvR / vR;
            if (vE > 0) c.VwapEth = pvE / vE;
            c.IbComplete = c.InRth && (nowCt.TimeOfDay - RthOpen).TotalMinutes >= 60;

            if (idx >= 14)
            {
                decimal tr = 0;
                for (var i = idx - 13; i <= idx; i++)
                    tr += Math.Max(bars[i].High, bars[i - 1].Close) - Math.Min(bars[i].Low, bars[i - 1].Close);
                c.Atr14 = tr / 14m;
            }
            if (idx >= 20)
            {
                var avg = Enumerable.Range(idx - 20, 20).Average(i => bars[i].Volume);
                if (avg > 0) c.RelVolume = c.Bar.Volume / avg;
            }
            if (idx >= 5)
            {
                c.Change5 = c.Bar.Close - bars[idx - 5].Close;
                c.Delta5 = Enumerable.Range(idx - 4, 5).Sum(i => bars[i].Delta);
            }
            return c;
        }

        private static decimal? Max(decimal? a, decimal b) => a is decimal x ? Math.Max(x, b) : b;
        private static decimal? Min(decimal? a, decimal b) => a is decimal x ? Math.Min(x, b) : b;
    }

    /// <summary>Rolling window of tape prints (time and sales).</summary>
    public sealed class TapeWindow
    {
        private readonly Queue<(DateTime t, decimal vol, int side)> _q = new();
        private readonly TimeSpan _window;
        public TapeWindow(TimeSpan window) => _window = window;

        public void Add(DateTime timeUtc, decimal volume, int aggressorSide)
        {
            _q.Enqueue((timeUtc, volume, aggressorSide));
            Prune(timeUtc);
        }

        public (decimal buy, decimal sell, int trades, decimal maxPrint) Stats(DateTime nowUtc)
        {
            Prune(nowUtc);
            decimal b = 0, s = 0, m = 0;
            foreach (var x in _q)
            {
                if (x.side > 0) b += x.vol; else if (x.side < 0) s += x.vol;
                m = Math.Max(m, x.vol);
            }
            return (b, s, _q.Count, m);
        }

        private void Prune(DateTime nowUtc)
        {
            while (_q.Count > 0 && nowUtc - _q.Peek().t > _window) _q.Dequeue();
        }
    }

    /// <summary>Aggregated (ATAS cumulative) trades of the last window; an aggregate can grow after it first appears, so it is upserted.</summary>
    public sealed class BigTrades
    {
        private readonly Dictionary<object, (DateTime t, decimal vol, int side)> _d = new(ReferenceEqualityComparer.Instance);
        private readonly TimeSpan _window;
        public BigTrades(TimeSpan window) => _window = window;

        public void Upsert(object key, DateTime timeUtc, decimal volume, int aggressorSide)
        {
            if (key == null) return;
            var t = _d.TryGetValue(key, out var x) ? x.t : timeUtc;
            _d[key] = (t, volume, aggressorSide);
            Prune(timeUtc);
        }

        /// <summary>Aggregates with volume ≥ min inside the window: counts and volumes per side, and the largest.</summary>
        public (int buyN, int sellN, decimal buyVol, decimal sellVol, decimal max) Stats(DateTime nowUtc, decimal min)
        {
            Prune(nowUtc);
            int bn = 0, sn = 0; decimal bv = 0, sv = 0, m = 0;
            foreach (var x in _d.Values.Where(v => v.vol >= min))
            {
                if (x.side > 0) { bn++; bv += x.vol; } else if (x.side < 0) { sn++; sv += x.vol; }
                m = Math.Max(m, x.vol);
            }
            return (bn, sn, bv, sv, m);
        }

        private void Prune(DateTime nowUtc)
        {
            foreach (var k in _d.Where(kv => nowUtc - kv.Value.t > _window).Select(kv => kv.Key).ToList()) _d.Remove(k);
        }
    }

    /// <summary>Order-book (DOM) summary at one moment.</summary>
    public sealed record BookStats(decimal BestBid, decimal BestAsk, decimal Top10Bids, decimal Top10Asks, decimal CumBids, decimal CumAsks)
    {
        public decimal? Top10Ratio => Top10Asks > 0 ? Top10Bids / Top10Asks : null;

        /// <summary>Levels as (price, volume, isBid). Best bid = highest bid; best ask = lowest ask.</summary>
        public static BookStats From(IEnumerable<(decimal price, decimal volume, bool isBid)> levels, decimal cumBids, decimal cumAsks)
        {
            var l = (levels ?? Enumerable.Empty<(decimal, decimal, bool)>()).Where(x => x.volume > 0).ToList();
            var bids = l.Where(x => x.isBid).OrderByDescending(x => x.price).ToList();
            var asks = l.Where(x => !x.isBid).OrderBy(x => x.price).ToList();
            return new BookStats(bids.FirstOrDefault().price, asks.FirstOrDefault().price,
                bids.Take(10).Sum(x => x.volume), asks.Take(10).Sum(x => x.volume), cumBids, cumAsks);
        }
    }

    /// <summary>Result of one hypothetical exit.</summary>
    public sealed record Outcome(decimal Price, decimal TradeNetUsd, decimal? R, decimal DayAfterUsd, decimal? MllBufferAfterUsd);

    /// <summary>"If A happens / if B happens" arithmetic. Costs: commission per contract round trip (no slippage in the panel).</summary>
    public static class WhatIf
    {
        public static Outcome Exit(int side, decimal qty, decimal avgEntry, decimal exitPrice, decimal pointValue, decimal commRt,
                                   decimal riskUsd, decimal dayNetUsd, decimal openPnlUsd, decimal? mllBufferUsd)
        {
            var net = (exitPrice - avgEntry) * side * qty * pointValue - commRt * qty;
            decimal? r = riskUsd > 0 ? net / riskUsd : null;
            decimal? buf = mllBufferUsd is decimal b ? b - openPnlUsd + net : null;
            return new Outcome(exitPrice, net, r, dayNetUsd + net, buf);
        }

        /// <summary>Gross $ risk to the stop (H-DISC1 1R definition: |entry − stop| × contracts × point value).</summary>
        public static decimal RiskUsd(decimal avgEntry, decimal stop, decimal qty, decimal pointValue) =>
            Math.Abs(avgEntry - stop) * qty * pointValue;

        /// <summary>Contracts so that stopTicks × tick value × contracts ≤ risk cap.</summary>
        public static int Contracts(decimal riskCapUsd, int stopTicks, decimal tickValue) =>
            stopTicks <= 0 || tickValue <= 0 ? 0 : (int)Math.Floor(riskCapUsd / (stopTicks * tickValue));

        /// <summary>Win rate needed to break even when a win nets +win and a loss nets −loss (both positive numbers).</summary>
        public static decimal? BreakEvenWinRate(decimal winUsd, decimal lossUsd) =>
            winUsd > 0 && lossUsd > 0 ? lossUsd / (winUsd + lossUsd) : null;
    }

    /// <summary>Maximum adverse / favourable excursion of an open trade, in points.</summary>
    public sealed class Excursion
    {
        public int Side { get; private set; }
        public decimal Entry { get; private set; }
        public decimal MaePoints { get; private set; }
        public decimal MfePoints { get; private set; }

        public void Start(int side, decimal entry) { Side = side; Entry = entry; MaePoints = MfePoints = 0; }

        public void Update(decimal price)
        {
            if (Side == 0) return;
            var move = (price - Entry) * Side;
            if (move > MfePoints) MfePoints = move;
            if (-move > MaePoints) MaePoints = -move;
        }
    }

    /// <summary>After an exit: which would have come first, the original target or the original stop? (MBB Omar, J5)</summary>
    public sealed class Followup
    {
        public string TripKey { get; }
        public int Side { get; }
        public decimal Stop { get; }
        public decimal Target { get; }
        public DateTime CreatedUtc { get; }
        public string Result { get; private set; } = "";
        public DateTime ResolvedUtc { get; private set; }

        public Followup(string tripKey, int side, decimal stop, decimal target, DateTime createdUtc)
        {
            TripKey = tripKey; Side = side; Stop = stop; Target = target; CreatedUtc = createdUtc;
        }

        /// <summary>Returns true once resolved. A print touching the level counts.</summary>
        public bool Update(decimal price, DateTime timeUtc)
        {
            if (Result.Length > 0) return true;
            if ((price - Target) * Side >= 0) Result = "TARGET_FIRST";
            else if ((price - Stop) * Side <= 0) Result = "STOP_FIRST";
            else return false;
            ResolvedUtc = timeUtc;
            return true;
        }

        public void Expire(DateTime timeUtc, string why)
        {
            if (Result.Length > 0) return;
            Result = why;
            ResolvedUtc = timeUtc;
        }
    }

    /// <summary>Formatting helpers for CSV cells.</summary>
    public static class Cell
    {
        public static string N(decimal? d, int dp = 2) => d is decimal x ? Math.Round(x, dp).ToString(CultureInfo.InvariantCulture) : "";
        public static string S(string s) => (s ?? "").Replace(",", ";").Replace("\n", " ").Replace("\r", " ");
        public static string T(DateTime t) => t.ToString("yyyy-MM-dd HH:mm:ss.fff", CultureInfo.InvariantCulture);
    }

    /// <summary>CSV layouts for the v2 journal files.</summary>
    public static class V2Files
    {
        public const string ContextHeader =
            "event,time_utc,time_ct,session,weekday,trip_key,side,price,bar_time_ct,bar_open,bar_high,bar_low,bar_close,bar_volume,bar_delta," +
            "bar_ask_vol,bar_bid_vol,bar_max_delta,bar_min_delta,bar_poc,bar_dir,body_pct,upper_wick_pct,lower_wick_pct,delta_vs_bar," +
            "rel_volume,change_5bars,delta_5bars,atr14,vwap,vs_vwap,dist_vwap,rth_open,rth_high,rth_low,or30_high,or30_low,ib_high,ib_low,vs_ib," +
            "prior_high,prior_low,prior_close,vs_prior_range,on_high,on_low,best_bid,best_ask,spread_ticks,dom_top10_bids,dom_top10_asks," +
            "dom_top10_ratio,dom_cum_bids,dom_cum_asks,tape60_buy,tape60_sell,tape60_trades,tape60_max_print";

        public static string ContextRow(string ev, DateTime utc, string tripKey, int side, decimal price, MarketContext c, BookStats book,
                                        (decimal buy, decimal sell, int trades, decimal maxPrint) tape, decimal tickSize)
        {
            var ct = SessionClock.ToCt(utc);
            var cells = new List<string> { ev, Cell.T(utc), Cell.T(ct), SessionClock.SessionKey(utc), ct.DayOfWeek.ToString(), Cell.S(tripKey),
                side > 0 ? "LONG" : side < 0 ? "SHORT" : "", Cell.N(price) };
            if (c != null)
            {
                var b = c.Bar;
                cells.AddRange(new[] { Cell.T(SessionClock.ToCt(b.TimeUtc)), Cell.N(b.Open), Cell.N(b.High), Cell.N(b.Low), Cell.N(b.Close), Cell.N(b.Volume), Cell.N(b.Delta),
                    Cell.N(b.AskVolume), Cell.N(b.BidVolume), Cell.N(b.MaxDelta), Cell.N(b.MinDelta), Cell.N(b.Poc), c.BarDirection,
                    Cell.N(c.BodyPct, 3), Cell.N(c.UpperWickPct, 3), Cell.N(c.LowerWickPct, 3), c.DeltaVsBar,
                    Cell.N(c.RelVolume, 3), Cell.N(c.Change5), Cell.N(c.Delta5), Cell.N(c.Atr14), Cell.N(c.Vwap), c.VsVwap,
                    Cell.N(c.Vwap is decimal v ? price - v : null), Cell.N(c.RthOpenPrice), Cell.N(c.RthHigh), Cell.N(c.RthLow), Cell.N(c.Or30High), Cell.N(c.Or30Low),
                    Cell.N(c.IbHigh), Cell.N(c.IbLow), Cell.S(c.VsIb), Cell.N(c.PriorHigh), Cell.N(c.PriorLow), Cell.N(c.PriorClose), Cell.S(c.VsPriorRange),
                    Cell.N(c.OnHigh), Cell.N(c.OnLow) });
            }
            else cells.AddRange(Enumerable.Repeat("", 38));
            if (book != null)
                cells.AddRange(new[] { Cell.N(book.BestBid), Cell.N(book.BestAsk),
                    Cell.N(tickSize > 0 && book.BestAsk > 0 && book.BestBid > 0 ? (book.BestAsk - book.BestBid) / tickSize : null, 1),
                    Cell.N(book.Top10Bids), Cell.N(book.Top10Asks), Cell.N(book.Top10Ratio, 3), Cell.N(book.CumBids), Cell.N(book.CumAsks) });
            else cells.AddRange(Enumerable.Repeat("", 8));
            cells.AddRange(new[] { Cell.N(tape.buy), Cell.N(tape.sell), tape.trades.ToString(CultureInfo.InvariantCulture), Cell.N(tape.maxPrint) });
            return string.Join(",", cells);
        }

        public const string ReviewHeader =
            "trip_key,session,weekday,entry_ct,exit_ct,side,max_qty,avg_entry,avg_exit,net_usd,initial_stop,initial_target,risk_usd,result_r," +
            "planned_rr,mae_points,mfe_points,mae_r,mfe_r,minutes_in_trade,trade_no_today,losses_before_today,losses_in_row_before," +
            "minutes_since_last_loss,direction_flip,setup_tag,setup_grade,ready_check,notes,rule_flags";

        public const string FollowupHeader = "trip_key,side,initial_stop,initial_target,result,resolved_utc,resolved_ct";

        public static string FollowupRow(Followup f) => string.Join(",", Cell.S(f.TripKey), f.Side > 0 ? "LONG" : "SHORT", Cell.N(f.Stop), Cell.N(f.Target),
            f.Result, Cell.T(f.ResolvedUtc), Cell.T(SessionClock.ToCt(f.ResolvedUtc)));
    }

    /// <summary>Everything known about a trade while it is open; turned into a review row at exit.</summary>
    public sealed class OpenTrade
    {
        public string TripKey;
        public DateTime EntryUtc;
        public int Side;
        public decimal? InitialStop, InitialTarget;
        public int TradeNoToday, LossesBeforeToday, LossesInRowBefore;
        public double? MinutesSinceLastLoss;
        public bool DirectionFlip, LateEntry, OverMaxTrades;
        public string SetupTag = "", SetupGrade = "", Notes = "";
        public bool ReadyCheck;
        public readonly Excursion Excursion = new();

        /// <summary>Rule flags kept even on winners (McCormick, J4).</summary>
        public List<string> Flags(decimal riskUsd, decimal riskCapUsd, bool heldPastFlat)
        {
            var f = new List<string>();
            if (InitialStop == null) f.Add("NO_STOP");
            if (OverMaxTrades) f.Add("OVER_MAX_TRADES");
            if (LateEntry) f.Add("OUTSIDE_ENTRY_WINDOW");
            if (InitialStop != null && riskCapUsd > 0 && riskUsd > riskCapUsd) f.Add("RISK_OVER_CAP");
            if (heldPastFlat) f.Add("HELD_PAST_FLAT_TIME");
            if (!ReadyCheck) f.Add("READY_CHECK_NOT_TICKED");
            if (string.IsNullOrWhiteSpace(SetupTag)) f.Add("NO_SETUP_TAG");
            return f;
        }

        public string ReviewRow(RoundTrip t, decimal pointValue, decimal riskCapUsd, bool heldPastFlat)
        {
            var risk = InitialStop is decimal s ? WhatIf.RiskUsd(t.AvgEntry, s, t.MaxQty, pointValue) : 0m;
            decimal? r = risk > 0 ? t.NetUsd / risk : null;
            decimal? rr = InitialStop is decimal s2 && InitialTarget is decimal tg && t.AvgEntry != s2
                ? Math.Abs(tg - t.AvgEntry) / Math.Abs(t.AvgEntry - s2) : null;
            decimal? stopPts = InitialStop is decimal s3 ? Math.Abs(t.AvgEntry - s3) : null;
            var ct = SessionClock.ToCt(t.EntryUtc);
            return string.Join(",", Cell.S(TripKey), t.Session, ct.DayOfWeek, Cell.T(ct), Cell.T(SessionClock.ToCt(t.ExitUtc)),
                t.Side > 0 ? "LONG" : "SHORT", Cell.N(t.MaxQty), Cell.N(t.AvgEntry), Cell.N(t.AvgExit), Cell.N(t.NetUsd),
                Cell.N(InitialStop), Cell.N(InitialTarget), Cell.N(risk), Cell.N(r, 3), Cell.N(rr, 2),
                Cell.N(Excursion.MaePoints), Cell.N(Excursion.MfePoints),
                Cell.N(stopPts > 0 ? Excursion.MaePoints / stopPts : null, 3), Cell.N(stopPts > 0 ? Excursion.MfePoints / stopPts : null, 3),
                Cell.N((decimal)(t.ExitUtc - t.EntryUtc).TotalMinutes, 1), TradeNoToday, LossesBeforeToday, LossesInRowBefore,
                Cell.N(MinutesSinceLastLoss is double m ? (decimal)m : null, 1), DirectionFlip ? "yes" : "no",
                Cell.S(SetupTag), Cell.S(SetupGrade), ReadyCheck ? "yes" : "no", Cell.S(Notes), string.Join(";", Flags(risk, riskCapUsd, heldPastFlat)));
        }
    }
}
