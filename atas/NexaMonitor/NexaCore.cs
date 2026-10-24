// NEXA Monitor core logic: pure C#, no ATAS dependency (unit-tested in NexaMonitor.Tests).
// Read-only by design: nothing in this file (or the indicator) places, modifies or cancels orders.
using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.Json;

namespace Nexa.Atas
{
    /// <summary>One execution (fill) on the account.</summary>
    public sealed record Fill(string Id, DateTime TimeUtc, string Security, int Side, decimal Price, decimal Qty, decimal Commission);

    /// <summary>A completed trade: from flat back to flat.</summary>
    public sealed record RoundTrip(string Session, DateTime EntryUtc, DateTime ExitUtc, string Security, int Side, decimal MaxQty,
                                   decimal AvgEntry, decimal AvgExit, decimal Points, decimal GrossUsd, decimal CommissionUsd, decimal NetUsd);

    /// <summary>Topstep trading day: 17:00 CT → 15:10 CT next day. Session key = CT date of (time + 7 h).</summary>
    public static class SessionClock
    {
        public static readonly TimeZoneInfo Ct = TimeZoneInfo.FindSystemTimeZoneById("America/Chicago");

        public static DateTime ToCt(DateTime utc) =>
            TimeZoneInfo.ConvertTimeFromUtc(DateTime.SpecifyKind(utc, DateTimeKind.Utc), Ct);

        public static string SessionKey(DateTime utc) =>
            ToCt(utc).AddHours(7).ToString("yyyy-MM-dd", CultureInfo.InvariantCulture);
    }

    /// <summary>Turns a time-ordered fill stream into round trips (flat → flat), with average-price accounting.</summary>
    public sealed class RoundTripTracker
    {
        private readonly decimal _pointValue;        // USD per 1.0 price point per contract
        private decimal _pos, _avg, _maxQty, _realized, _comm, _exitQty, _exitVal;
        private DateTime _entryUtc;
        private int _side;
        private string _security = "";

        public RoundTripTracker(decimal pointValue) => _pointValue = pointValue;

        public decimal Position => _pos;
        public decimal AveragePrice => _avg;

        public decimal OpenPnlUsd(decimal lastPrice) => _pos == 0 ? 0 : (lastPrice - _avg) * _pos * _pointValue;

        /// <summary>Applies a fill; returns the round trip it completed, if any.</summary>
        public RoundTrip Apply(Fill f)
        {
            var q = f.Side * f.Qty;
            if (q == 0) return null;
            if (_pos == 0)
            {
                Start(f, q, f.Commission);
                return null;
            }
            if (Math.Sign(q) == Math.Sign(_pos))
            {
                _avg = (_avg * Math.Abs(_pos) + f.Price * Math.Abs(q)) / (Math.Abs(_pos) + Math.Abs(q));
                _pos += q;
                _maxQty = Math.Max(_maxQty, Math.Abs(_pos));
                _comm += f.Commission;
                return null;
            }
            var closeQty = Math.Min(Math.Abs(q), Math.Abs(_pos));
            var share = Math.Abs(q) > 0 ? closeQty / Math.Abs(q) : 1m;
            _realized += closeQty * (f.Price - _avg) * Math.Sign(_pos) * _pointValue;
            _exitQty += closeQty;
            _exitVal += closeQty * f.Price;
            _comm += f.Commission * share;
            _pos += Math.Sign(q) * closeQty;
            if (_pos != 0) return null;

            var avgExit = _exitVal / _exitQty;
            var rt = new RoundTrip(SessionClock.SessionKey(_entryUtc), _entryUtc, f.TimeUtc, _security, _side, _maxQty,
                                   _avg, avgExit, (avgExit - _avg) * _side, _realized, _comm, _realized - _comm);
            var remaining = Math.Abs(q) - closeQty;
            if (remaining > 0)
                Start(f with { Qty = remaining }, Math.Sign(q) * remaining, f.Commission * (1 - share));
            else
                Reset();
            return rt;
        }

        private void Start(Fill f, decimal q, decimal commission)
        {
            Reset();
            _pos = q;
            _avg = f.Price;
            _side = Math.Sign(q);
            _maxQty = Math.Abs(q);
            _entryUtc = f.TimeUtc;
            _security = f.Security;
            _comm = commission;
        }

        private void Reset()
        {
            _pos = _avg = _maxQty = _realized = _comm = _exitQty = _exitVal = 0;
            _side = 0;
        }
    }

    public sealed record GuardSettings(int MaxTradesPerDay, decimal DailyLossLimitUsd, decimal MaxLossLimitUsd,
                                       TimeSpan LastEntryCt, TimeSpan FlatByCt);

    public enum Level { Ok = 0, Warn = 1, Violation = 2 }

    /// <summary>Checks the Topstep-style practice rules. Pure function of the current state.</summary>
    public static class RuleCheck
    {
        public static (Level level, List<string> messages) Evaluate(GuardSettings s, int tradesToday, decimal dayNetUsd,
            decimal openPnlUsd, bool inPosition, DateTime nowUtc, decimal? mllBufferUsd)
        {
            var msgs = new List<string>();
            var level = Level.Ok;
            void Add(Level l, string m) { msgs.Add(m); if (l > level) level = l; }

            if (tradesToday > s.MaxTradesPerDay)
                Add(Level.Violation, $"Trades today {tradesToday} > max {s.MaxTradesPerDay}");
            else if (tradesToday == s.MaxTradesPerDay && !inPosition)
                Add(Level.Warn, $"Max {s.MaxTradesPerDay} trades reached: done for today");

            var dayTotal = dayNetUsd + openPnlUsd;
            if (s.DailyLossLimitUsd > 0)
            {
                if (dayTotal <= -s.DailyLossLimitUsd)
                    Add(Level.Violation, $"Daily loss {dayTotal:0} <= -{s.DailyLossLimitUsd:0}: stop trading today");
                else if (dayTotal <= -0.8m * s.DailyLossLimitUsd)
                    Add(Level.Warn, $"Daily loss {dayTotal:0} near limit -{s.DailyLossLimitUsd:0}");
            }

            var ct = SessionClock.ToCt(nowUtc).TimeOfDay;
            var inEvening = ct >= new TimeSpan(17, 0, 0);          // new Topstep day starts 17:00 CT
            if (!inEvening && ct >= s.FlatByCt && inPosition)
                Add(Level.Violation, $"Position open after {s.FlatByCt:hh\\:mm} CT: must be flat");
            else if (!inEvening && ct >= s.LastEntryCt && !inPosition)
                Add(Level.Warn, $"After {s.LastEntryCt:hh\\:mm} CT: no new trades");

            if (mllBufferUsd.HasValue)
            {
                if (mllBufferUsd.Value <= 0)
                    Add(Level.Violation, "Maximum Loss Limit breached");
                else if (mllBufferUsd.Value <= 0.25m * s.MaxLossLimitUsd)
                    Add(Level.Warn, $"Only {mllBufferUsd.Value:0} USD above the Maximum Loss Limit");
            }
            return (level, msgs);
        }
    }

    /// <summary>Topstep-style trailing MLL on end-of-day balance, locking at the starting balance.</summary>
    public sealed class MllState
    {
        public decimal StartBalance { get; set; }
        public decimal PeakEod { get; set; }
        public decimal Mll { get; set; }
        public string LastSession { get; set; } = "";
        public decimal LastBalance { get; set; }

        public static MllState Create(decimal startBalance, decimal maxLoss, string session) => new()
        {
            StartBalance = startBalance, PeakEod = startBalance, Mll = startBalance - maxLoss,
            LastSession = session, LastBalance = startBalance,
        };

        /// <summary>Call with every balance observation; closes the previous day when the session key changes.</summary>
        public void Observe(decimal balance, string session, decimal maxLoss)
        {
            if (session != LastSession && !string.IsNullOrEmpty(LastSession))
            {
                PeakEod = Math.Max(PeakEod, LastBalance);                       // previous session's last balance = its EOD
                Mll = Math.Max(Mll, Math.Min(PeakEod - maxLoss, StartBalance));
            }
            LastSession = session;
            LastBalance = balance;
        }

        public decimal Buffer(decimal equity) => equity - Mll;
    }

    /// <summary>CSV journal (fills, round trips, orders, v2 context/review/follow-up) and persisted MLL state, in one folder.</summary>
    public sealed class Journal
    {
        private readonly string _dir;
        private readonly HashSet<string> _seen = new();
        public const string FillsHeader = "fill_id,time_utc,time_ct,session,security,side,price,qty,commission";
        public const string TripsHeader = "session,entry_utc,exit_utc,entry_ct,exit_ct,security,side,max_qty,avg_entry,avg_exit,points,gross_usd,commission_usd,net_usd";

        public Journal(string dir)
        {
            _dir = dir;
            Directory.CreateDirectory(dir);
            var fills = Path.Combine(dir, "fills.csv");
            if (File.Exists(fills))
                foreach (var line in File.ReadLines(fills).Skip(1))
                {
                    var id = line.Split(',')[0];
                    if (id.Length > 0) _seen.Add(id);
                }
        }

        public bool Seen(string id) => _seen.Contains(id);

        public void WriteFill(Fill f)
        {
            if (!_seen.Add(f.Id)) return;
            Append("fills.csv", FillsHeader, string.Join(",", Csv(f.Id), Iso(f.TimeUtc), Iso(SessionClock.ToCt(f.TimeUtc)),
                SessionClock.SessionKey(f.TimeUtc), Csv(f.Security), f.Side > 0 ? "BUY" : "SELL", Num(f.Price), Num(f.Qty), Num(f.Commission)));
        }

        public void WriteTrip(RoundTrip t) =>
            Append("roundtrips.csv", TripsHeader, string.Join(",", t.Session, Iso(t.EntryUtc), Iso(t.ExitUtc),
                Iso(SessionClock.ToCt(t.EntryUtc)), Iso(SessionClock.ToCt(t.ExitUtc)), Csv(t.Security), t.Side > 0 ? "LONG" : "SHORT",
                Num(t.MaxQty), Num(t.AvgEntry), Num(t.AvgExit), Num(t.Points), Num(t.GrossUsd), Num(t.CommissionUsd), Num(t.NetUsd)));

        public const string OrdersHeader = "event_utc,event_ct,session,order_id,security,type,side,price,trigger_price,qty,state,comment";

        /// <summary>Logs every order event (new / changed) so each trade's initial stop (= 1R) can be reconstructed.</summary>
        public void WriteOrderEvent(DateTime eventUtc, string orderId, string security, string type, int side, decimal price,
                                    decimal triggerPrice, decimal qty, string state, string comment) =>
            Append("orders.csv", OrdersHeader, string.Join(",", Iso(eventUtc), Iso(SessionClock.ToCt(eventUtc)), SessionClock.SessionKey(eventUtc),
                Csv(orderId), Csv(security), Csv(type), side > 0 ? "BUY" : "SELL", Num(price), Num(triggerPrice), Num(qty), Csv(state), Csv(comment)));

        /// <summary>v2 journal files (context.csv, trade_review.csv, followup.csv): one CSV line, header written on first use.</summary>
        public void WriteRow(string file, string header, string line) => Append(file, header, line);

        public Dictionary<string, MllState> LoadState()
        {
            var p = Path.Combine(_dir, "state.json");
            if (!File.Exists(p)) return new();
            try { return JsonSerializer.Deserialize<Dictionary<string, MllState>>(File.ReadAllText(p)) ?? new(); }
            catch (JsonException) { return new(); }
        }

        public void SaveState(Dictionary<string, MllState> state) =>
            File.WriteAllText(Path.Combine(_dir, "state.json"), JsonSerializer.Serialize(state, new JsonSerializerOptions { WriteIndented = true }));

        private void Append(string file, string header, string line)
        {
            var p = Path.Combine(_dir, file);
            var sb = new StringBuilder();
            if (!File.Exists(p)) sb.AppendLine(header);
            sb.AppendLine(line);
            File.AppendAllText(p, sb.ToString());
        }

        private static string Iso(DateTime t) => t.ToString("yyyy-MM-dd HH:mm:ss.fff", CultureInfo.InvariantCulture);
        private static string Num(decimal d) => d.ToString(CultureInfo.InvariantCulture);
        private static string Csv(string s) => (s ?? "").Replace(",", ";");
    }
}
