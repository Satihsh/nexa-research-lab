// NEXA Monitor v3 indicator snapshot: the indicators (and settings) that traders in the user's sources actually use,
// computed from chart bars and footprint levels. Pure C#, no ATAS dependency (unit-tested). Facts only, never a signal.
// Sources per field: research/intelligence/JOURNAL_SOURCES_DECODE.md §"Indicators".
using System;
using System.Collections.Generic;
using System.Linq;

namespace Nexa.Atas
{
    /// <summary>One footprint price level of a bar: total volume, volume at bid (sell aggressor), volume at ask (buy aggressor).</summary>
    public readonly record struct FootLevel(decimal Price, decimal Volume, decimal Bid, decimal Ask);

    public sealed class IndicatorSnapshot
    {
        public decimal? Ema5, Ema9, Ema13, MacdLine, MacdSignal, MacdHist, Bb20Mid, Bb20Up, Bb20Low, Bb20PctB, Bb20WidthPct,
                        Bb4Up, Bb4Low, Kc20Up, Kc20Low, Rsi14, CvdSession, CvdRth;
        public bool? SqueezeOn;
        public string EmaStack = "n/a", Bb4Touch = "none";
        public decimal? DevPoc, DevVah, DevVal, PriorPoc, PriorVah, PriorVal;
        public int BuyImbalances, SellImbalances, BuyStacks, SellStacks;
        public string VsPriorVa = "n/a", VsDevVa = "n/a";
    }

    public static class NexaIndicators
    {
        /// <summary>Indicators for bars[idx] using bars[0..idx] only (no look-ahead). levels[i] may be null when footprint is unavailable.</summary>
        public static IndicatorSnapshot Compute(IReadOnlyList<Bar> bars, IReadOnlyList<IReadOnlyList<FootLevel>> levels, int idx, decimal tickSize)
        {
            var s = new IndicatorSnapshot();
            if (bars == null || idx < 0 || idx >= bars.Count) return s;
            var close = bars.Take(idx + 1).Select(b => b.Close).ToArray();
            var price = close[idx];

            // EMA 5 / 9 / 13 (TG Capital SRC-YT-085; EMA 5/13 = BTMM S07)
            s.Ema5 = Ema(close, 5); s.Ema9 = Ema(close, 9); s.Ema13 = Ema(close, 13);
            if (s.Ema5 is decimal e5 && s.Ema9 is decimal e9 && s.Ema13 is decimal e13)
                s.EmaStack = e5 > e9 && e9 > e13 ? "up (5>9>13)" : e5 < e9 && e9 < e13 ? "down (5<9<13)" : "mixed";

            // MACD(5, 13, 4) (NEXA 8E momentum engine, BTMM S07)
            if (close.Length >= 13 + 4)
            {
                var line = EmaSeries(close, 5).Zip(EmaSeries(close, 13), (a, b) => a - b).Skip(12).ToArray();
                s.MacdLine = line[^1];
                s.MacdSignal = Ema(line, 4);
                s.MacdHist = s.MacdLine - s.MacdSignal;
            }

            // Bollinger(20, 2σ) (Silfrain; Straight Kim -FCNwoQ_ARs; Carter S19) and Bollinger(4, 4σ) on opens (Straight Kim)
            if (close.Length >= 20)
            {
                var w = close[^20..];
                var mid = w.Average();
                var sd = StdDev(w, mid);
                s.Bb20Mid = mid; s.Bb20Up = mid + 2 * sd; s.Bb20Low = mid - 2 * sd;
                if (sd > 0) s.Bb20PctB = (price - s.Bb20Low) / (4 * sd);
                if (mid != 0) s.Bb20WidthPct = 4 * sd / mid * 100m;
                // Keltner(20, 1.5 × ATR20) around the same 20-bar mean; squeeze ON when BB(20,2) sits inside it (Carter TTM, S19 / 8E)
                if (idx >= 20)
                {
                    decimal tr = 0;
                    for (var i = idx - 19; i <= idx; i++)
                        tr += Math.Max(bars[i].High, bars[i - 1].Close) - Math.Min(bars[i].Low, bars[i - 1].Close);
                    var atr = tr / 20m;
                    s.Kc20Up = mid + 1.5m * atr; s.Kc20Low = mid - 1.5m * atr;
                    s.SqueezeOn = s.Bb20Up < s.Kc20Up && s.Bb20Low > s.Kc20Low;
                }
            }
            if (idx >= 3)
            {
                var opens = Enumerable.Range(idx - 3, 4).Select(i => bars[i].Open).ToArray();
                var m4 = opens.Average();
                var sd4 = StdDev(opens, m4);
                s.Bb4Up = m4 + 4 * sd4; s.Bb4Low = m4 - 4 * sd4;
                var b = bars[idx];
                var up = s.Bb20Up is decimal u20 && b.High >= s.Bb4Up && b.High >= u20;
                var dn = s.Bb20Low is decimal l20 && b.Low <= s.Bb4Low && b.Low <= l20;
                s.Bb4Touch = up && dn ? "both" : up ? "upper (both bands)" : dn ? "lower (both bands)" : "none";
            }

            // RSI 14, Wilder smoothing (ATAS default period; no source gives an intraday RSI setting)
            s.Rsi14 = Rsi(close, 14);

            // Cumulative delta since the Topstep session start (17:00 CT) and since the RTH open (ATAS CVD)
            var session = SessionClock.SessionKey(bars[idx].TimeUtc);
            var today = SessionClock.ToCt(bars[idx].TimeUtc).Date;
            decimal cs = 0, cr = 0;
            var anyRth = false;
            for (var i = idx; i >= 0 && SessionClock.SessionKey(bars[i].TimeUtc) == session; i--)
            {
                cs += bars[i].Delta;
                var ct = SessionClock.ToCt(bars[i].TimeUtc);
                if (ct.Date == today && ct.TimeOfDay >= MarketContext.RthOpen && ct.TimeOfDay < MarketContext.RthClose) { cr += bars[i].Delta; anyRth = true; }
            }
            s.CvdSession = cs;
            if (anyRth) s.CvdRth = cr;

            // Volume profile (Fabio's value area; OFC1 EQ-014 greedy 70 %, two ticks at a time, ties upward)
            if (levels != null && tickSize > 0)
            {
                var nowCt = SessionClock.ToCt(bars[idx].TimeUtc);
                var inRth = nowCt.TimeOfDay >= MarketContext.RthOpen && nowCt.TimeOfDay < MarketContext.RthClose;
                var priorCutoff = nowCt.TimeOfDay >= MarketContext.RthClose ? today.AddDays(1) : today;
                DateTime? priorDate = null;
                var dev = new List<int>(); var prior = new List<int>();
                for (var i = idx; i >= 0; i--)
                {
                    var ct = SessionClock.ToCt(bars[i].TimeUtc);
                    var rth = ct.TimeOfDay >= MarketContext.RthOpen && ct.TimeOfDay < MarketContext.RthClose;
                    if (!rth) continue;
                    if (inRth && ct.Date == today) dev.Add(i);
                    else if (ct.Date < priorCutoff)
                    {
                        priorDate ??= ct.Date;
                        if (ct.Date != priorDate) break;
                        prior.Add(i);
                    }
                }
                (s.DevPoc, s.DevVal, s.DevVah) = Profile(dev.Select(i => i < levels.Count ? levels[i] : null), tickSize);
                (s.PriorPoc, s.PriorVal, s.PriorVah) = Profile(prior.Select(i => i < levels.Count ? levels[i] : null), tickSize);
                s.VsPriorVa = Where(price, s.PriorVal, s.PriorVah, "prior VA");
                s.VsDevVa = Where(price, s.DevVal, s.DevVah, "developing VA");

                // Footprint imbalances in this bar (OFC1 E4: 3×, ≥ 10 contracts, diagonal; stack = ≥ 3 consecutive ticks)
                if (idx < levels.Count && levels[idx] != null)
                    (s.BuyImbalances, s.SellImbalances, s.BuyStacks, s.SellStacks) = Imbalances(levels[idx], tickSize);
            }
            return s;
        }

        public static decimal? Ema(IReadOnlyList<decimal> x, int n) => x.Count >= n ? EmaSeries(x, n)[^1] : null;

        /// <summary>EMA seeded with the first value, alpha = 2 / (n + 1).</summary>
        public static decimal[] EmaSeries(IReadOnlyList<decimal> x, int n)
        {
            var r = new decimal[x.Count];
            if (x.Count == 0) return r;
            var a = 2m / (n + 1);
            r[0] = x[0];
            for (var i = 1; i < x.Count; i++) r[i] = a * x[i] + (1 - a) * r[i - 1];
            return r;
        }

        public static decimal? Rsi(IReadOnlyList<decimal> c, int n)
        {
            if (c.Count < n + 1) return null;
            decimal g = 0, l = 0;
            for (var i = 1; i <= n; i++) { var d = c[i] - c[i - 1]; if (d > 0) g += d; else l -= d; }
            g /= n; l /= n;
            for (var i = n + 1; i < c.Count; i++)
            {
                var d = c[i] - c[i - 1];
                g = (g * (n - 1) + Math.Max(d, 0)) / n;
                l = (l * (n - 1) + Math.Max(-d, 0)) / n;
            }
            return l == 0 ? (g == 0 ? 50m : 100m) : 100m - 100m / (1 + g / l);
        }

        private static decimal StdDev(IReadOnlyList<decimal> w, decimal mean) =>
            (decimal)Math.Sqrt((double)(w.Sum(v => (v - mean) * (v - mean)) / w.Count));

        /// <summary>POC / VAL / VAH from footprint levels of a set of bars (70 % value area).</summary>
        public static (decimal? poc, decimal? val, decimal? vah) Profile(IEnumerable<IReadOnlyList<FootLevel>> barLevels, decimal tick)
        {
            var vol = new Dictionary<long, decimal>();
            foreach (var lv in barLevels)
                if (lv != null)
                    foreach (var x in lv)
                    {
                        var k = (long)Math.Round(x.Price / tick);
                        vol[k] = (vol.TryGetValue(k, out var v) ? v : 0) + x.Volume;
                    }
            if (vol.Count == 0 || vol.Values.Sum() <= 0) return (null, null, null);
            var k0 = vol.Keys.Min();
            var n = (int)(vol.Keys.Max() - k0 + 1);
            if (n > 200000) return (null, null, null);
            var a = new decimal[n];
            foreach (var kv in vol) a[kv.Key - k0] = kv.Value;
            var (poc, lo, hi) = VaGreedy(a, 0.70m);
            return ((k0 + poc) * tick, (k0 + lo) * tick, (k0 + hi) * tick);
        }

        /// <summary>Same algorithm as of_common.va_greedy: POC = first max; add the larger 2-bin side (ties up) until ≥ alpha.</summary>
        public static (int poc, int lo, int hi) VaGreedy(decimal[] v, decimal alpha)
        {
            var poc = 0;
            for (var i = 1; i < v.Length; i++) if (v[i] > v[poc]) poc = i;
            int lo = poc, hi = poc, n = v.Length;
            var tot = v.Sum();
            var acc = v[poc];
            while (acc < alpha * tot && (lo > 0 || hi < n - 1))
            {
                var up = hi < n - 1 ? v.Skip(hi + 1).Take(2).Sum() : -1m;
                var dn = lo > 0 ? v.Skip(Math.Max(lo - 2, 0)).Take(lo - Math.Max(lo - 2, 0)).Sum() : -1m;
                if (up >= dn) { var k = Math.Min(2, n - 1 - hi); acc += v.Skip(hi + 1).Take(k).Sum(); hi += k; }
                else { var k = Math.Min(2, lo); acc += v.Skip(lo - k).Take(k).Sum(); lo -= k; }
            }
            return (poc, lo, hi);
        }

        public static (int buy, int sell, int buyStacks, int sellStacks) Imbalances(IReadOnlyList<FootLevel> lv, decimal tick)
        {
            var map = lv.GroupBy(x => (long)Math.Round(x.Price / tick)).ToDictionary(g => g.Key, g => (bid: g.Sum(x => x.Bid), ask: g.Sum(x => x.Ask)));
            if (map.Count == 0) return (0, 0, 0, 0);
            long lo = map.Keys.Min(), hi = map.Keys.Max();
            (decimal bid, decimal ask) At(long k) => map.TryGetValue(k, out var v) ? v : (0m, 0m);
            int buy = 0, sell = 0, bs = 0, ss = 0, runB = 0, runS = 0;
            for (var k = lo; k <= hi; k++)
            {
                var isBuy = At(k).ask >= 10 && At(k - 1).bid >= 1 && At(k).ask >= 3 * At(k - 1).bid;
                var isSell = At(k).bid >= 10 && At(k + 1).ask >= 1 && At(k).bid >= 3 * At(k + 1).ask;
                if (isBuy) { buy++; runB++; if (runB == 3) bs++; } else runB = 0;
                if (isSell) { sell++; runS++; if (runS == 3) ss++; } else runS = 0;
            }
            return (buy, sell, bs, ss);
        }

        public const string Header =
            "event,time_utc,trip_key,ema5,ema9,ema13,ema_stack,macd_5_13,macd_signal_4,macd_hist,bb20_mid,bb20_up,bb20_low,bb20_pctb,bb20_width_pct," +
            "bb4_open_up,bb4_open_low,bb4_touch,kc20_up,kc20_low,squeeze_on,rsi14,cvd_session,cvd_rth,dev_poc,dev_val,dev_vah,vs_dev_va," +
            "prior_poc,prior_val,prior_vah,vs_prior_va,buy_imbalances,sell_imbalances,buy_stacks,sell_stacks," +
            "big_trade_min,big_buy_count,big_sell_count,big_buy_vol,big_sell_vol,big_max";

        public static string Row(string ev, DateTime utc, string tripKey, IndicatorSnapshot s, decimal bigMin,
                                 (int buyN, int sellN, decimal buyVol, decimal sellVol, decimal max) big) =>
            string.Join(",", ev, Cell.T(utc), Cell.S(tripKey), Cell.N(s.Ema5), Cell.N(s.Ema9), Cell.N(s.Ema13), Cell.S(s.EmaStack),
                Cell.N(s.MacdLine, 3), Cell.N(s.MacdSignal, 3), Cell.N(s.MacdHist, 3), Cell.N(s.Bb20Mid), Cell.N(s.Bb20Up), Cell.N(s.Bb20Low),
                Cell.N(s.Bb20PctB, 3), Cell.N(s.Bb20WidthPct, 4), Cell.N(s.Bb4Up), Cell.N(s.Bb4Low), Cell.S(s.Bb4Touch), Cell.N(s.Kc20Up), Cell.N(s.Kc20Low),
                s.SqueezeOn is bool q ? (q ? "on" : "off") : "", Cell.N(s.Rsi14, 1), Cell.N(s.CvdSession, 0), Cell.N(s.CvdRth, 0),
                Cell.N(s.DevPoc), Cell.N(s.DevVal), Cell.N(s.DevVah), Cell.S(s.VsDevVa), Cell.N(s.PriorPoc), Cell.N(s.PriorVal), Cell.N(s.PriorVah), Cell.S(s.VsPriorVa),
                s.BuyImbalances, s.SellImbalances, s.BuyStacks, s.SellStacks,
                Cell.N(bigMin, 0), big.buyN, big.sellN, Cell.N(big.buyVol, 0), Cell.N(big.sellVol, 0), Cell.N(big.max, 0));

        private static string Where(decimal p, decimal? lo, decimal? hi, string name) =>
            lo is decimal l && hi is decimal h ? (p > h ? $"above {name}" : p < l ? $"below {name}" : $"inside {name}") : "n/a";
    }

    /// <summary>Multi-timeframe view built from the chart's bars (exact aggregation of 1-minute bars).</summary>
    public static class Mtf
    {
        /// <summary>Frames in minutes; H4 aligned to the 17:00 CT session start (17, 21, 01, 05, 09, 13 CT); D = Topstep session.</summary>
        public static readonly (string Name, int Minutes)[] Frames =
            { ("M1", 1), ("M5", 5), ("M10", 10), ("M15", 15), ("M30", 30), ("H1", 60), ("H4", 240), ("D", 1440) };

        /// <summary>Chart bar length in minutes (median spacing of the last bars); 0 if unknown.</summary>
        public static int ChartMinutes(IReadOnlyList<Bar> bars)
        {
            if (bars == null || bars.Count < 3) return 0;
            var d = Enumerable.Range(Math.Max(1, bars.Count - 50), Math.Min(50, bars.Count - 1))
                .Select(i => (bars[i].TimeUtc - bars[i - 1].TimeUtc).TotalMinutes).Where(x => x > 0).OrderBy(x => x).ToList();
            return d.Count == 0 ? 0 : (int)Math.Round(d[d.Count / 2]);
        }

        public static string Key(DateTime utc, int minutes)
        {
            if (minutes >= 1440) return SessionClock.SessionKey(utc);
            if (minutes == 240)
            {
                var ct = SessionClock.ToCt(utc);
                var start = (ct.TimeOfDay >= new TimeSpan(17, 0, 0) ? ct.Date : ct.Date.AddDays(-1)).AddHours(17);
                return SessionClock.SessionKey(utc) + "#" + (int)Math.Floor((ct - start).TotalHours / 4);
            }
            return (utc.Ticks / TimeSpan.FromMinutes(minutes).Ticks).ToString();
        }

        /// <summary>Aggregates bars into a larger frame. MaxDelta/MinDelta follow the running delta (exact from the parts).</summary>
        public static List<Bar> Aggregate(IReadOnlyList<Bar> bars, int minutes)
        {
            var r = new List<Bar>();
            if (bars == null) return r;
            string key = null;
            Bar cur = null;
            decimal run = 0;
            foreach (var b in bars)
            {
                var k = Key(b.TimeUtc, minutes);
                if (k != key)
                {
                    if (cur != null) r.Add(cur);
                    key = k; run = 0;
                    cur = b with { MaxDelta = b.MaxDelta, MinDelta = b.MinDelta, Poc = 0m };
                    run = b.Delta;
                    continue;
                }
                cur = cur with
                {
                    High = Math.Max(cur.High, b.High), Low = Math.Min(cur.Low, b.Low), Close = b.Close, Volume = cur.Volume + b.Volume,
                    Delta = cur.Delta + b.Delta, AskVolume = cur.AskVolume + b.AskVolume, BidVolume = cur.BidVolume + b.BidVolume,
                    MaxDelta = Math.Max(cur.MaxDelta, run + b.MaxDelta), MinDelta = Math.Min(cur.MinDelta, run + b.MinDelta),
                };
                run += b.Delta;
            }
            if (cur != null) r.Add(cur);
            return r;
        }

        public sealed record FrameState(string Name, int Bars, string EmaStack, decimal? Rsi14, decimal? Bb20PctB, decimal? MacdHist, string BarDir, decimal? BarDelta);

        /// <summary>State of every frame at the last bar; frames smaller than the chart's bar are skipped (n/a).</summary>
        public static List<FrameState> Snapshot(IReadOnlyList<Bar> bars)
        {
            var chart = ChartMinutes(bars);
            var r = new List<FrameState>();
            foreach (var (name, m) in Frames)
            {
                if (chart == 0 || m < chart || (m % chart != 0 && m < 1440)) { r.Add(new FrameState(name, 0, "n/a", null, null, null, "n/a", null)); continue; }
                var agg = m == chart ? bars.ToList() : Aggregate(bars, m);
                var s = NexaIndicators.Compute(agg, null, agg.Count - 1, 0m);
                var last = agg[^1];
                r.Add(new FrameState(name, agg.Count, s.EmaStack, s.Rsi14, s.Bb20PctB, s.MacdHist,
                    last.Close > last.Open ? "up" : last.Close < last.Open ? "down" : "flat", last.Delta));
            }
            return r;
        }

        public static string Header => "event,time_utc,trip_key," + string.Join(",", Frames.SelectMany(f => new[]
            { $"{f.Name}_bars", $"{f.Name}_ema_stack", $"{f.Name}_rsi14", $"{f.Name}_bb20_pctb", $"{f.Name}_macd_hist", $"{f.Name}_bar_dir", $"{f.Name}_bar_delta" }));

        public static string Row(string ev, DateTime utc, string tripKey, List<FrameState> st) =>
            string.Join(",", new[] { ev, Cell.T(utc), Cell.S(tripKey) }.Concat(st.SelectMany(f => new[]
            { f.Bars.ToString(), Cell.S(f.EmaStack), Cell.N(f.Rsi14, 1), Cell.N(f.Bb20PctB, 3), Cell.N(f.MacdHist, 3), f.BarDir, Cell.N(f.BarDelta, 0) })));
    }
}
