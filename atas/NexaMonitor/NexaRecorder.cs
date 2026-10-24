// NEXA Market Recorder: raw market data from the chart, written continuously so every ATAS indicator on the user's list
// (Big Trades, Cluster Search/Statistics, DOM levels/heatmap, Volume Profile/TPO, CVD/CVD Pro/Market Power, Spread Volume,
// VWAP/TWAP, OHLC+, VSA-WSD, Speed of Tape, Max/Dynamic Levels, OI) can be rebuilt exactly afterwards from ATAS's own
// open-source formulas (github.com/AtasPlatform/Indicators). Pure C#, no ATAS dependency (unit-tested). Read-only.
//
// Files, one set per Topstep session (17:00 CT → 17:00 CT), under <journal>/recorder/<instrument>_<timeframe>/:
//   bars_<session>.csv    one row per CLOSED chart bar (deduplicated by bar time, so history reloads are safe)
//   levels_<session>.csv  the bar's footprint: volume / bid / ask / ticks at every price
//   tape_<session>.csv    every aggregated trade with the best bid/ask (and their sizes) just before it
//   dom_<session>.csv     order-book snapshot (top N levels per side) every few seconds
using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;

namespace Nexa.Atas
{
    /// <summary>One closed bar as the recorder stores it.</summary>
    public sealed record RecBar(DateTime TimeUtc, DateTime LastTimeUtc, decimal Open, decimal High, decimal Low, decimal Close,
                                decimal Volume, decimal Delta, decimal AskVolume, decimal BidVolume, decimal Ticks,
                                decimal MaxDelta, decimal MinDelta, decimal OpenInterest);

    /// <summary>One footprint level of a bar, with its trade count.</summary>
    public readonly record struct RecLevel(decimal Price, decimal Volume, decimal Bid, decimal Ask, decimal Ticks);

    /// <summary>One aggregated (ATAS cumulative) trade and the quote just before it.</summary>
    public sealed record RecTrade(DateTime ReceivedUtc, DateTime TradeTime, int Side, decimal Volume, decimal FirstPrice, decimal LastPrice,
                                  decimal PrevBid, decimal PrevBidSize, decimal PrevAsk, decimal PrevAskSize, int Prints);

    public sealed class MarketRecorder
    {
        public const string BarsHeader = "bar_time_utc,bar_time_ct,last_time_utc,duration_sec,open,high,low,close,volume,delta,ask_volume,bid_volume,ticks,max_delta,min_delta,open_interest";
        public const string LevelsHeader = "bar_time_utc,price,volume,bid,ask,ticks";
        public const string TapeHeader = "received_utc,trade_time,side,volume,first_price,last_price,prev_bid,prev_bid_size,prev_ask,prev_ask_size,prints";
        public const string DomHeader = "time_utc,best_bid,best_ask,cum_bids,cum_asks,bids_price_size,asks_price_size";

        private readonly string _dir;
        private readonly Dictionary<string, HashSet<DateTime>> _barsSeen = new();
        private readonly Dictionary<string, StringBuilder> _buffers = new();
        private string _lastDom = "";

        public MarketRecorder(string journalDir, string instrument, string timeframe)
        {
            _dir = Path.Combine(journalDir, "recorder", Safe(instrument) + "_" + Safe(timeframe));
            Directory.CreateDirectory(_dir);
        }

        public string Folder => _dir;

        /// <summary>Writes a closed bar and its footprint once; returns false if this bar time was already recorded.</summary>
        public bool WriteBar(RecBar b, IReadOnlyList<RecLevel> levels)
        {
            var session = SessionClock.SessionKey(b.TimeUtc);
            var bars = Path.Combine(_dir, $"bars_{session}.csv");
            if (!_barsSeen.TryGetValue(bars, out var seen))
            {
                seen = new HashSet<DateTime>();
                if (File.Exists(bars))
                    foreach (var line in File.ReadLines(bars).Skip(1))
                        if (DateTime.TryParseExact(line.Split(',')[0], "yyyy-MM-dd HH:mm:ss.fff", CultureInfo.InvariantCulture,
                                                   DateTimeStyles.AdjustToUniversal | DateTimeStyles.AssumeUniversal, out var t))
                            seen.Add(DateTime.SpecifyKind(t, DateTimeKind.Utc));
                _barsSeen[bars] = seen;
            }
            if (!seen.Add(b.TimeUtc)) return false;

            Append(bars, BarsHeader, string.Join(",", Cell.T(b.TimeUtc), Cell.T(SessionClock.ToCt(b.TimeUtc)), Cell.T(b.LastTimeUtc),
                Cell.N((decimal)Math.Max(0, (b.LastTimeUtc - b.TimeUtc).TotalSeconds), 3), N(b.Open), N(b.High), N(b.Low), N(b.Close), N(b.Volume),
                N(b.Delta), N(b.AskVolume), N(b.BidVolume), N(b.Ticks), N(b.MaxDelta), N(b.MinDelta), N(b.OpenInterest)) + "\n");
            if (levels != null && levels.Count > 0)
            {
                var sb = new StringBuilder();
                var t = Cell.T(b.TimeUtc);
                foreach (var l in levels.OrderBy(x => x.Price))
                    sb.Append(t).Append(',').Append(N(l.Price)).Append(',').Append(N(l.Volume)).Append(',').Append(N(l.Bid)).Append(',')
                      .Append(N(l.Ask)).Append(',').Append(N(l.Ticks)).Append('\n');
                Append(Path.Combine(_dir, $"levels_{session}.csv"), LevelsHeader, sb.ToString());
            }
            return true;
        }

        /// <summary>Buffers one aggregated trade (flushed by <see cref="Flush"/>).</summary>
        public void AddTrade(RecTrade x) =>
            Buffer($"tape_{SessionClock.SessionKey(x.ReceivedUtc)}.csv", TapeHeader, string.Join(",", Cell.T(x.ReceivedUtc), Cell.T(x.TradeTime),
                x.Side > 0 ? "BUY" : x.Side < 0 ? "SELL" : "BETWEEN", N(x.Volume), N(x.FirstPrice), N(x.LastPrice),
                N(x.PrevBid), N(x.PrevBidSize), N(x.PrevAsk), N(x.PrevAskSize), x.Prints.ToString(CultureInfo.InvariantCulture)));

        /// <summary>Buffers one order-book snapshot: top <paramref name="depth"/> levels per side as price:size;price:size.</summary>
        public bool AddDom(DateTime utc, IEnumerable<(decimal price, decimal volume, bool isBid)> levels, decimal cumBids, decimal cumAsks, int depth)
        {
            var l = (levels ?? Enumerable.Empty<(decimal, decimal, bool)>()).Where(x => x.volume > 0).ToList();
            var bids = l.Where(x => x.isBid).OrderByDescending(x => x.price).Take(depth).ToList();
            var asks = l.Where(x => !x.isBid).OrderBy(x => x.price).Take(depth).ToList();
            if (bids.Count == 0 && asks.Count == 0) return false;
            string Side(List<(decimal price, decimal volume, bool isBid)> s) => string.Join(";", s.Select(x => N(x.price) + ":" + N(x.volume)));
            var book = string.Join(",", bids.Count > 0 ? N(bids[0].price) : "", asks.Count > 0 ? N(asks[0].price) : "", N(cumBids), N(cumAsks), Side(bids), Side(asks));
            if (book == _lastDom) return false;                                   // unchanged book (e.g. market closed): not repeated
            _lastDom = book;
            Buffer($"dom_{SessionClock.SessionKey(utc)}.csv", DomHeader, Cell.T(utc) + "," + book);
            return true;
        }

        /// <summary>Writes buffered tape / DOM rows to disk.</summary>
        public void Flush()
        {
            foreach (var kv in _buffers.Where(kv => kv.Value.Length > 0).ToList())
            {
                var parts = kv.Key.Split('|');
                Append(Path.Combine(_dir, parts[0]), parts[1], kv.Value.ToString());
                kv.Value.Clear();
            }
        }

        private void Buffer(string file, string header, string line)
        {
            var key = file + "|" + header;
            if (!_buffers.TryGetValue(key, out var sb)) _buffers[key] = sb = new StringBuilder();
            sb.Append(line).Append('\n');
            if (sb.Length > 1_000_000) Flush();
        }

        private static void Append(string path, string header, string text)
        {
            if (!File.Exists(path)) text = header + "\n" + text;
            File.AppendAllText(path, text);
        }

        private static string N(decimal d) => d.ToString(CultureInfo.InvariantCulture);
        private static string Safe(string s) => string.Concat((s ?? "unknown").Select(c => char.IsLetterOrDigit(c) || c == '-' ? c : '_'));
    }

    /// <summary>ATAS updates an aggregated trade while it grows; it is final when the next one starts.</summary>
    public sealed class TradeAggregator
    {
        private object _key;
        private RecTrade _pending;

        /// <summary>Returns the previous trade when a new one starts (it is then final), otherwise null.</summary>
        public RecTrade Observe(object key, RecTrade snapshot)
        {
            if (key == null || snapshot == null) return null;
            if (ReferenceEquals(key, _key)) { _pending = snapshot with { ReceivedUtc = _pending.ReceivedUtc }; return null; }
            var done = _pending;
            _key = key;
            _pending = snapshot;
            return done;
        }

        public RecTrade TakePending()
        {
            var p = _pending;
            _pending = null; _key = null;
            return p;
        }
    }
}
