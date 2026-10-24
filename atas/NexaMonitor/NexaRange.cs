// NEXA Monitor v6 "Risk & Range": only things the research shows ARE predictable (how much and when the market moves,
// known news times, the right size). Never a direction call. Plan: atas/PLAN_RISK_PANEL_v6.md.
// Pure C#, no ATAS dependency (unit-tested in NexaMonitor.Tests). Times: RTH = 08:30–15:00 CT, as MarketContext.
using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;

namespace Nexa.Atas
{
    public sealed class RangeGuide
    {
        public int DaysUsed;
        public decimal? ExpectedRange, TodayRange, MedianDayToIb, TodayIb;
        public string Regime = "closed";
        public decimal? TypicalMove5m;             // mean high–low of 5-minute blocks in the current window, previous days
        public decimal? UsedPct => ExpectedRange is decimal e && e > 0 && TodayRange is decimal t ? t / e : null;

        // Windows from the recorder decode (U-shaped activity): CT start of each window.
        public static readonly (TimeSpan From, TimeSpan To, string Name)[] Windows =
        {
            (new(8, 30, 0), new(9, 0, 0), "OPEN SURGE"),
            (new(9, 0, 0), new(10, 30, 0), "MORNING"),
            (new(10, 30, 0), new(14, 0, 0), "LUNCH LULL"),
            (new(14, 0, 0), new(15, 0, 0), "CLOSE"),
        };

        public static string RegimeAt(TimeSpan ct) =>
            Windows.FirstOrDefault(w => ct >= w.From && ct < w.To).Name ?? "closed";

        /// <summary>Range facts for "now" from chart bars (oldest first). Only previous complete RTH days feed the averages.</summary>
        public static RangeGuide Compute(IReadOnlyList<Bar> bars, DateTime nowUtc, int lookbackDays = 10)
        {
            var g = new RangeGuide();
            var nowCt = SessionClock.ToCt(nowUtc);
            g.Regime = RegimeAt(nowCt.TimeOfDay);
            var win = Windows.FirstOrDefault(w => w.Name == g.Regime);
            var days = new SortedDictionary<DateTime, List<(TimeSpan t, Bar b)>>();
            foreach (var b in bars ?? Array.Empty<Bar>())
            {
                var ct = SessionClock.ToCt(b.TimeUtc);
                if (ct.TimeOfDay < MarketContext.RthOpen || ct.TimeOfDay >= MarketContext.RthClose) continue;
                if (!days.TryGetValue(ct.Date, out var l)) days[ct.Date] = l = new List<(TimeSpan, Bar)>();
                l.Add((ct.TimeOfDay, b));
            }
            var ib = MarketContext.RthOpen.Add(TimeSpan.FromHours(1));
            if (days.TryGetValue(nowCt.Date, out var today) && today.Count > 0)
            {
                g.TodayRange = today.Max(x => x.b.High) - today.Min(x => x.b.Low);
                if (nowCt.TimeOfDay >= ib)
                {
                    var f = today.Where(x => x.t < ib).ToList();
                    if (f.Count > 0) g.TodayIb = f.Max(x => x.b.High) - f.Min(x => x.b.Low);
                }
            }
            // complete = bars from the first 5 minutes to the last 5 minutes of RTH
            var prev = days.Where(d => d.Key < nowCt.Date && d.Value.Min(x => x.t) <= MarketContext.RthOpen.Add(TimeSpan.FromMinutes(5))
                                       && d.Value.Max(x => x.t) >= MarketContext.RthClose.Subtract(TimeSpan.FromMinutes(5)))
                           .Select(d => d.Value).ToList();
            prev = prev.Skip(Math.Max(0, prev.Count - lookbackDays)).ToList();
            g.DaysUsed = prev.Count;
            if (prev.Count < 3) return g;
            g.ExpectedRange = prev.Average(d => d.Max(x => x.b.High) - d.Min(x => x.b.Low));
            var ratios = prev.Select(d =>
            {
                var f = d.Where(x => x.t < ib).ToList();
                var r = f.Count == 0 ? 0 : f.Max(x => x.b.High) - f.Min(x => x.b.Low);
                return r > 0 ? (d.Max(x => x.b.High) - d.Min(x => x.b.Low)) / r : (decimal?)null;
            }).Where(r => r.HasValue).Select(r => r.Value).OrderBy(r => r).ToList();
            if (ratios.Count > 0) g.MedianDayToIb = ratios[ratios.Count / 2];
            if (win.Name != null)
            {
                var blocks = prev.SelectMany(d => d.Where(x => x.t >= win.From && x.t < win.To)
                                 .GroupBy(x => (int)(x.t - win.From).TotalMinutes / 5)
                                 .Select(k => k.Max(x => x.b.High) - k.Min(x => x.b.Low))).ToList();
                if (blocks.Count > 0) g.TypicalMove5m = blocks.Average();
            }
            return g;
        }

        /// <summary>Suggested stop in ticks = multiple × typical 5-minute range, rounded up, at least 4 ticks.</summary>
        public static int StopTicks(decimal? typical5m, decimal multiple, decimal tick) =>
            typical5m is decimal m && tick > 0 && multiple > 0 ? Math.Max(4, (int)Math.Ceiling(m * multiple / tick)) : 0;
    }

    public sealed record NewsEvent(DateTime TimeUtc, string Name, string Impact);

    /// <summary>news_calendar.csv: date,time_et,event,impact (header row; '#' comments). ET converted with US DST rules.</summary>
    public static class NewsCalendar
    {
        private static readonly TimeZoneInfo Et = TimeZoneInfo.FindSystemTimeZoneById("America/New_York");

        public static DateTime ToEt(DateTime utc) => TimeZoneInfo.ConvertTimeFromUtc(DateTime.SpecifyKind(utc, DateTimeKind.Utc), Et);

        public static List<NewsEvent> Parse(IEnumerable<string> lines)
        {
            var list = new List<NewsEvent>();
            foreach (var raw in lines ?? Array.Empty<string>())
            {
                var line = raw?.Trim() ?? "";
                if (line.Length == 0 || line.StartsWith("#") || line.StartsWith("date", StringComparison.OrdinalIgnoreCase)) continue;
                var p = line.Split(',');
                if (p.Length < 3) continue;
                if (!DateTime.TryParseExact(p[0].Trim() + " " + p[1].Trim(), "yyyy-MM-dd HH:mm", CultureInfo.InvariantCulture,
                                            DateTimeStyles.None, out var et)) continue;
                var utc = TimeZoneInfo.ConvertTimeToUtc(DateTime.SpecifyKind(et, DateTimeKind.Unspecified), Et);
                list.Add(new NewsEvent(utc, p[2].Trim(), p.Length > 3 ? p[3].Trim().ToLowerInvariant() : "high"));
            }
            return list.OrderBy(e => e.TimeUtc).ToList();
        }

        /// <summary>Next event that is not more than 2 minutes in the past (so a just-released number still shows).</summary>
        public static NewsEvent Next(IReadOnlyList<NewsEvent> events, DateTime nowUtc) =>
            events?.FirstOrDefault(e => e.TimeUtc >= nowUtc.AddMinutes(-2));

        /// <summary>Warn 15 min before a high-impact event, violation-level from 2 min before to 2 min after.</summary>
        public static Level LevelFor(NewsEvent e, DateTime nowUtc)
        {
            if (e == null || e.Impact != "high") return Level.Ok;
            var mins = (e.TimeUtc - nowUtc).TotalMinutes;
            return mins <= 2 && mins >= -2 ? Level.Violation : mins <= 15 && mins > 2 ? Level.Warn : Level.Ok;
        }
    }
}
