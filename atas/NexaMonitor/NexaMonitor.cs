// NEXA Monitor: ATAS X indicator. READ-ONLY: it never places, modifies or cancels orders.
// Shows Topstep-style practice-rule status on the chart and journals every fill + round trip to CSV
// (default folder ~/Documents/NEXA_ATAS) for Claude to review.
// v2 adds: market context + order book + tape at every entry/exit (context.csv), a per-trade review with
// stop/target, R, MAE/MFE, setup tag and rule flags (trade_review.csv), the original-target-vs-stop follow-up
// after early exits (followup.csv), and "what if" lines on the panel. Facts only, never an entry signal.
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.ComponentModel.DataAnnotations;
using System.Drawing;
using System.IO;
using System.Linq;
using ATAS.DataFeedsCore;
using ATAS.Indicators;
using OFT.Rendering.Context;
using OFT.Rendering.Tools;
using Utils.Common.Logging;

namespace Nexa.Atas
{
    [DisplayName("NEXA Monitor (read-only)")]
    public class NexaMonitor : Indicator
    {
        private readonly object _lock = new();
        private readonly RenderFont _font = new("Arial", 11);
        private readonly RenderFont _bold = new("Arial", 12);
        private Journal _journal;
        private Dictionary<string, MllState> _state = new();
        private bool _timerOn;
        private Level _lastLevel = Level.Ok;
        private string _lastError = "";
        private readonly TapeWindow _tape = new(TimeSpan.FromSeconds(60));
        private readonly BigTrades _big = new(TimeSpan.FromSeconds(60));
        private readonly Dictionary<DateTime, IReadOnlyList<FootLevel>> _levelCache = new();
        private readonly TradeAggregator _agg = new();
        private MarketRecorder _rec;
        private int _lastRecordedBar = -1;
        private long _recBars, _recTrades, _recDom;
        private readonly List<Followup> _followups = new();
        private OpenTrade _open;
        private RangeGuide _range;
        private DateTime _rangeKey, _newsRead;
        private List<NewsEvent> _news;

        [Display(Name = "Max trades per day", GroupName = "Rules", Order = 10)]
        public int MaxTradesPerDay { get; set; } = 2;

        [Display(Name = "Daily loss limit (USD, 0 = off)", GroupName = "Rules", Order = 20)]
        public decimal DailyLossLimitUsd { get; set; } = 1000m;

        [Display(Name = "Maximum Loss Limit (USD, trailing EOD)", GroupName = "Rules", Order = 30)]
        public decimal MaxLossLimitUsd { get; set; } = 2000m;

        [Display(Name = "No new trades after (CT, hh:mm)", GroupName = "Rules", Order = 40)]
        public string LastEntryCt { get; set; } = "15:00";

        [Display(Name = "Must be flat by (CT, hh:mm)", GroupName = "Rules", Order = 50)]
        public string FlatByCt { get; set; } = "15:08";

        [Display(Name = "Risk cap per trade (USD)", GroupName = "What if", Order = 52)]
        public decimal RiskPerTradeUsd { get; set; } = 250m;

        [Display(Name = "Planned stop (ticks) - match your ATAS SL template", GroupName = "What if", Order = 53)]
        public int PlannedStopTicks { get; set; } = 40;

        [Display(Name = "Planned target (ticks) - match your ATAS TP template", GroupName = "What if", Order = 54)]
        public int PlannedTargetTicks { get; set; } = 80;

        [Display(Name = "Commission per contract round trip (USD)", GroupName = "What if", Order = 55)]
        public decimal CommissionRtUsd { get; set; } = 1.22m;

        [Display(Name = "Show what-if lines", GroupName = "What if", Order = 56)]
        public bool ShowWhatIf { get; set; } = true;

        [Display(Name = "Show market context lines", GroupName = "What if", Order = 57)]
        public bool ShowContext { get; set; } = true;

        [Display(Name = "Show indicator lines", GroupName = "What if", Order = 58)]
        public bool ShowIndicators { get; set; } = true;

        [Display(Name = "Big trade = aggregated trade of at least (contracts; Fabio uses 30 on NQ)", GroupName = "What if", Order = 59)]
        public decimal BigTradeMin { get; set; } = 30m;

        [Display(Name = "Record market data (bars + footprint, tape, DOM) continuously", GroupName = "Market recorder", Order = 80)]
        public bool RecordMarket { get; set; } = true;

        [Display(Name = "DOM snapshot every (seconds; re-add indicator after changing)", GroupName = "Market recorder", Order = 81)]
        public int DomSnapshotSeconds { get; set; } = 5;

        [Display(Name = "DOM levels per side to record", GroupName = "Market recorder", Order = 82)]
        public int DomDepth { get; set; } = 20;

        [Display(Name = "Ready: slept, calm, life outside OK (Dhesi)", GroupName = "Trade notes (set BEFORE entry)", Order = 61)]
        public bool ReadyCheck { get; set; }

        [Display(Name = "Setup tag (your name for the setup)", GroupName = "Trade notes (set BEFORE entry)", Order = 62)]
        public string SetupTag { get; set; } = "";

        [Display(Name = "Setup grade (A++ / A / B)", GroupName = "Trade notes (set BEFORE entry)", Order = 63)]
        public string SetupGrade { get; set; } = "";

        [Display(Name = "Why this trade, why now", GroupName = "Trade notes (set BEFORE entry)", Order = 64)]
        public string TradeNotes { get; set; } = "";

        [Display(Name = "Journal folder", GroupName = "Journal", Order = 60)]
        public string JournalFolder { get; set; } =
            Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), "Documents", "NEXA_ATAS");

        [Display(Name = "Show Risk & Range lines (v6: expected range, clock, volatility stop, news)", GroupName = "Risk & Range", Order = 90)]
        public bool ShowRangeGuide { get; set; } = true;

        [Display(Name = "Expected range: previous complete sessions to average", GroupName = "Risk & Range", Order = 91)]
        public int RangeLookbackDays { get; set; } = 10;

        [Display(Name = "Suggested stop = this x typical 5-min range of the current window", GroupName = "Risk & Range", Order = 92)]
        public decimal StopRangeMultiple { get; set; } = 1.5m;

        [Display(Name = "News calendar file (inside the journal folder)", GroupName = "Risk & Range", Order = 93)]
        public string NewsFile { get; set; } = "news_calendar.csv";

        public enum PanelModes { Full, OneLine, Hidden }

        [Display(Name = "Panel on chart (recording and journal keep running in every mode)", GroupName = "Panel", Order = 1)]
        public PanelModes PanelMode { get; set; } = PanelModes.OneLine;

        [Display(Name = "Pop-up alert on rule violation", GroupName = "Alerts", Order = 70)]
        public bool AlertOnViolation { get; set; } = true;

        public NexaMonitor()
        {
            Panel = IndicatorDataProvider.CandlesPanel;
            EnableCustomDrawing = true;
            SubscribeToDrawingEvents(DrawingLayouts.Final);
            if (DataSeries.Count > 0 && DataSeries[0] is ValueDataSeries vs)
                vs.IsHidden = true;
        }

        protected override void OnCalculate(int bar, decimal value)
        {
            if (bar == 0) _lastRecordedBar = -1;
            if (RecordMarket && bar >= 1 && bar - 1 > _lastRecordedBar)
            {
                try { RecordBar(bar - 1); }
                catch (Exception ex) { Fail(ex); }
                _lastRecordedBar = bar - 1;
            }
            if (bar == CurrentBar - 1)
            {
                try { OnPrice(GetCandle(bar).Close, DateTime.UtcNow); }
                catch (Exception ex) { Fail(ex); }
            }
            if (_timerOn) return;
            _timerOn = true;
            SubscribeToTimer(TimeSpan.FromSeconds(5), () => RedrawChart());
            SubscribeToTimer(TimeSpan.FromSeconds(Math.Clamp(DomSnapshotSeconds, 1, 60)), RecorderTick);
        }

        protected override void OnNewMyTrade(MyTrade myTrade)
        {
            base.OnNewMyTrade(myTrade);
            try
            {
                var f = ToFill(myTrade);
                if (f == null) return;
                lock (_lock)
                {
                    EnsureJournal();
                    var isNew = !_journal.Seen(f.Id);
                    _journal.WriteFill(f);
                    var (completed, tracker, started) = RebuildToday();
                    var trip = completed.LastOrDefault(t => t.ExitUtc == f.TimeUtc);
                    if (trip != null) _journal.WriteTrip(trip);
                    if (isNew) PositionEvents(f, completed, tracker, started, trip);
                }
            }
            catch (Exception ex) { Fail(ex); }
            RedrawChart();
        }

        protected override void OnNewOrder(Order order)
        {
            base.OnNewOrder(order);
            LogOrder(order);
        }

        protected override void OnOrderChanged(Order order)
        {
            base.OnOrderChanged(order);
            LogOrder(order);
        }

        private void LogOrder(Order order)
        {
            try
            {
                if (order == null) return;
                var sec = TradingManager?.Security;
                if (sec != null && order.SecurityId != null && sec.SecurityId != null && order.SecurityId != sec.SecurityId) return;
                lock (_lock)
                {
                    EnsureJournal();
                    _journal.WriteOrderEvent(DateTime.UtcNow, order.Id ?? "", order.Security?.Code ?? order.SecurityId ?? "", order.Type.ToString(),
                        order.Direction == OrderDirections.Buy ? 1 : -1, order.Price, order.TriggerPrice, order.QuantityToFill, order.State.ToString(), order.Comment ?? "");
                    CaptureBracket();
                }
            }
            catch (Exception ex) { Fail(ex); }
        }

        protected override void OnNewTrade(MarketDataArg trade)
        {
            base.OnNewTrade(trade);
            try
            {
                if (trade == null) return;
                var side = trade.Direction == ATAS.Indicators.TradeDirection.Buy ? 1 : trade.Direction == ATAS.Indicators.TradeDirection.Sell ? -1 : 0;
                var now = DateTime.UtcNow;                                     // receive time: tape window independent of feed clock
                lock (_lock) _tape.Add(now, trade.Volume, side);
                OnPrice(trade.Price, now);
            }
            catch (Exception ex) { Fail(ex); }
        }

        protected override void OnCumulativeTrade(CumulativeTrade trade)
        {
            base.OnCumulativeTrade(trade);
            BigTrade(trade);
        }

        protected override void OnUpdateCumulativeTrade(CumulativeTrade trade)
        {
            base.OnUpdateCumulativeTrade(trade);
            BigTrade(trade);
        }

        private void BigTrade(CumulativeTrade trade)
        {
            try
            {
                if (trade == null) return;
                var side = trade.Direction == ATAS.Indicators.TradeDirection.Buy ? 1 : trade.Direction == ATAS.Indicators.TradeDirection.Sell ? -1 : 0;
                var now = DateTime.UtcNow;
                lock (_lock)
                {
                    _big.Upsert(trade, now, trade.Volume, side);
                    if (!RecordMarket) return;
                    var snap = new RecTrade(now, trade.Time, side, trade.Volume, trade.FirstPrice, trade.Lastprice,
                        trade.PreviousBid?.Price ?? 0m, trade.PreviousBid?.Volume ?? 0m, trade.PreviousAsk?.Price ?? 0m, trade.PreviousAsk?.Volume ?? 0m,
                        trade.Ticks?.Count ?? 0);
                    var done = _agg.Observe(trade, snap);
                    if (done != null && EnsureRecorder()) { _rec.AddTrade(done); _recTrades++; }
                }
            }
            catch (Exception ex) { Fail(ex); }
        }

        /// <summary>Writes one closed bar + footprint to the recorder (deduplicated by bar time).</summary>
        private void RecordBar(int i)
        {
            var c = GetCandle(i);
            if (c == null) return;
            var levels = (c.GetAllPriceLevels() ?? Enumerable.Empty<PriceVolumeInfo>())
                .Select(p => new RecLevel(p.Price, p.Volume, p.Bid, p.Ask, p.Ticks)).ToList();
            var b = new RecBar(DateTime.SpecifyKind(c.Time, DateTimeKind.Utc), DateTime.SpecifyKind(c.LastTime, DateTimeKind.Utc), c.Open, c.High, c.Low,
                               c.Close, c.Volume, c.Delta, c.Ask, c.Bid, c.Ticks, c.MaxDelta, c.MinDelta, c.OI);
            lock (_lock)
                if (EnsureRecorder() && _rec.WriteBar(b, levels)) _recBars++;
        }

        /// <summary>Timer: order-book snapshot + flush of buffered tape / DOM rows.</summary>
        private void RecorderTick()
        {
            if (!RecordMarket) return;
            try
            {
                var md = MarketDepthInfo;
                var levels = md?.GetMarketDepthSnapshot()?.Select(x => (x.Price, x.Volume, x.IsBid)).ToList();
                lock (_lock)
                {
                    if (!EnsureRecorder()) return;
                    if (levels != null && levels.Count > 0)
                    {
                        if (_rec.AddDom(DateTime.UtcNow, levels, md.CumulativeDomBids, md.CumulativeDomAsks, Math.Clamp(DomDepth, 1, 200))) _recDom++;
                    }
                    _rec.Flush();
                }
            }
            catch (Exception ex) { Fail(ex); }
        }

        private bool EnsureRecorder()
        {
            if (_rec != null) return true;
            var inst = InstrumentInfo?.Instrument;
            if (string.IsNullOrEmpty(inst)) return false;
            EnsureJournal();
            _rec = new MarketRecorder(JournalFolder, inst, ChartInfo?.TimeFrame ?? "chart");
            return true;
        }

        protected override void OnDispose()
        {
            try
            {
                lock (_lock)
                {
                    var last = _agg.TakePending();
                    if (_rec != null)
                    {
                        if (last != null) _rec.AddTrade(last);
                        _rec.Flush();
                    }
                }
            }
            catch (Exception ex) { Fail(ex); }
            base.OnDispose();
        }

        /// <summary>Every price update: MAE/MFE of the open trade, and resolve follow-ups (J5).</summary>
        private void OnPrice(decimal price, DateTime nowUtc)
        {
            if (price <= 0) return;
            lock (_lock)
            {
                _open?.Excursion.Update(price);
                if (_followups.Count == 0) return;
                var ct = SessionClock.ToCt(nowUtc).TimeOfDay;
                var flatBy = ParseCt(FlatByCt, 15, 8);
                foreach (var f in _followups.ToList())
                {
                    var expired = SessionClock.SessionKey(nowUtc) != SessionClock.SessionKey(f.CreatedUtc)
                                  || (ct >= flatBy && ct < new TimeSpan(17, 0, 0));
                    if (expired) f.Expire(nowUtc, "NEITHER_BY_FLAT_TIME");
                    else if (!f.Update(price, nowUtc)) continue;
                    EnsureJournal();
                    _journal.WriteRow("followup.csv", V2Files.FollowupHeader, V2Files.FollowupRow(f));
                    _followups.Remove(f);
                }
            }
        }

        /// <summary>Entry / exit bookkeeping for the v2 journal. Called under _lock for each new fill.</summary>
        private void PositionEvents(Fill f, List<RoundTrip> completed, RoundTripTracker tracker, int started, RoundTrip trip)
        {
            var pos = tracker.Position;
            var prev = pos - f.Side * f.Qty;
            var pv = PointValue();
            if (trip != null)
            {
                var o = _open ?? new OpenTrade { TripKey = Cell.T(trip.EntryUtc), EntryUtc = trip.EntryUtc, Side = trip.Side, Notes = "monitor started mid-trade" };
                var exitCt = SessionClock.ToCt(trip.ExitUtc).TimeOfDay;
                var heldPastFlat = exitCt > ParseCt(FlatByCt, 15, 8) && exitCt < new TimeSpan(17, 0, 0);
                _journal.WriteRow("trade_review.csv", V2Files.ReviewHeader, o.ReviewRow(trip, pv, RiskPerTradeUsd, heldPastFlat));
                WriteContext("EXIT", f.TimeUtc, o.TripKey, trip.Side, trip.AvgExit);
                var tick = InstrumentInfo?.TickSize ?? 0m;
                if (o.InitialStop is decimal st && o.InitialTarget is decimal tg
                    && Math.Abs(trip.AvgExit - st) > tick && Math.Abs(trip.AvgExit - tg) > tick)   // exited early (manual / moved stop)
                    _followups.Add(new Followup(o.TripKey, trip.Side, st, tg, trip.ExitUtc));
                _open = null;
            }
            if (pos != 0 && (prev == 0 || trip != null))
            {
                var side = Math.Sign(pos);
                var entryCt = SessionClock.ToCt(f.TimeUtc).TimeOfDay;
                var lastLoss = completed.LastOrDefault(t => t.NetUsd < 0);
                var inRow = 0;
                for (var i = completed.Count - 1; i >= 0 && completed[i].NetUsd < 0; i--) inRow++;
                _open = new OpenTrade
                {
                    TripKey = Cell.T(f.TimeUtc), EntryUtc = f.TimeUtc, Side = side, TradeNoToday = started,
                    LossesBeforeToday = completed.Count(t => t.NetUsd < 0), LossesInRowBefore = inRow,
                    MinutesSinceLastLoss = lastLoss == null ? null : (f.TimeUtc - lastLoss.ExitUtc).TotalMinutes,
                    DirectionFlip = completed.Count > 0 && completed[^1].Side != side,
                    LateEntry = entryCt < MarketContext.RthOpen || entryCt > ParseCt(LastEntryCt, 15, 0),
                    OverMaxTrades = started > MaxTradesPerDay,
                    SetupTag = SetupTag ?? "", SetupGrade = SetupGrade ?? "", Notes = TradeNotes ?? "", ReadyCheck = ReadyCheck,
                };
                _open.Excursion.Start(side, tracker.AveragePrice);
                CaptureBracket();
                WriteContext("ENTRY", f.TimeUtc, _open.TripKey, side, f.Price);
            }
        }

        /// <summary>First working stop / limit on the exit side after entry = initial stop / target (1R per H-DISC1).</summary>
        private void CaptureBracket()
        {
            if (_open == null) return;
            var (stop, target) = WorkingBracket(_open.Side);
            _open.InitialStop ??= stop;
            _open.InitialTarget ??= target;
        }

        /// <summary>Nearest active stop and limit orders on the exit side of a position with the given side.</summary>
        private (decimal? stop, decimal? target) WorkingBracket(int side)
        {
            var tm = TradingManager;
            if (tm?.Orders == null || side == 0) return (null, null);
            var sec = tm.Security;
            var exitDir = side > 0 ? OrderDirections.Sell : OrderDirections.Buy;
            var mine = tm.Orders.Where(o => o != null && o.State == OrderStates.Active && o.Direction == exitDir
                                            && (sec == null || o.SecurityId == null || sec.SecurityId == null || o.SecurityId == sec.SecurityId)).ToList();
            var last = tm.Position?.AveragePrice ?? 0m;
            decimal? stop = mine.Where(o => o.Type == OrderTypes.Stop || o.Type == OrderTypes.StopLimit)
                .Select(o => o.TriggerPrice > 0 ? o.TriggerPrice : o.Price).OrderBy(p => Math.Abs(p - last)).Cast<decimal?>().FirstOrDefault();
            decimal? target = mine.Where(o => o.Type == OrderTypes.Limit)
                .Select(o => o.Price).OrderBy(p => Math.Abs(p - last)).Cast<decimal?>().FirstOrDefault();
            return (stop, target);
        }

        private void WriteContext(string ev, DateTime utc, string tripKey, int side, decimal price)
        {
            try
            {
                var (bars, levels) = CollectBars(true);
                var ctx = MarketContext.Compute(bars, bars.Count - 1);
                var now = DateTime.UtcNow;
                _journal.WriteRow("context.csv", V2Files.ContextHeader,
                    V2Files.ContextRow(ev, utc, tripKey, side, price, ctx, ReadBook(), _tape.Stats(now), InstrumentInfo?.TickSize ?? 0m));
                var ind = NexaIndicators.Compute(bars, levels, bars.Count - 1, InstrumentInfo?.TickSize ?? 0m);
                _journal.WriteRow("indicators.csv", NexaIndicators.Header, NexaIndicators.Row(ev, utc, tripKey, ind, BigTradeMin, _big.Stats(now, BigTradeMin)));
                var (mtfBars, _) = CollectBars(false, 40, 60000);
                _journal.WriteRow("mtf.csv", Mtf.Header, Mtf.Row(ev, utc, tripKey, Mtf.Snapshot(mtfBars)));
            }
            catch (Exception ex) { Fail(ex); }
        }

        /// <summary>Chart bars of the last few days (default 4 days, max 20,000), oldest first, optionally with footprint levels (closed bars cached).</summary>
        private (List<Bar> bars, List<IReadOnlyList<FootLevel>> levels) CollectBars(bool withLevels, int days = 4, int maxBars = 20000)
        {
            var list = new List<Bar>();
            var lv = withLevels ? new List<IReadOnlyList<FootLevel>>() : null;
            var last = CurrentBar - 1;
            if (last < 0) return (list, lv);
            var lastTime = GetCandle(last).Time;
            var start = last;
            while (start > 0 && last - start < maxBars && (lastTime - GetCandle(start - 1).Time).TotalDays < days) start--;
            for (var i = start; i <= last; i++)
            {
                var c = GetCandle(i);
                list.Add(new Bar(DateTime.SpecifyKind(c.Time, DateTimeKind.Utc), c.Open, c.High, c.Low, c.Close, c.Volume, c.Delta,
                                 c.Ask, c.Bid, c.MaxDelta, c.MinDelta, c.MaxVolumePriceInfo?.Price ?? 0m));
                if (lv == null) continue;
                if (i == last || !_levelCache.TryGetValue(c.Time, out var levels))
                {
                    levels = (c.GetAllPriceLevels() ?? Enumerable.Empty<PriceVolumeInfo>())
                        .Select(p => new FootLevel(p.Price, p.Volume, p.Bid, p.Ask)).ToList();
                    if (i != last) _levelCache[c.Time] = levels;
                }
                lv.Add(levels);
            }
            if (lv != null && _levelCache.Count > 30000) _levelCache.Clear();
            return (list, lv);
        }

        private BookStats ReadBook()
        {
            try
            {
                var md = MarketDepthInfo;
                if (md == null) return null;
                var levels = (md.GetMarketDepthSnapshot() ?? Enumerable.Empty<MarketDataArg>()).Select(x => (x.Price, x.Volume, x.IsBid));
                return BookStats.From(levels, md.CumulativeDomBids, md.CumulativeDomAsks);
            }
            catch (Exception ex) { Fail(ex); return null; }
        }

        protected override void OnPositionChanged(Position position) => RedrawChart();

        protected override void OnPortfolioChanged(Portfolio portfolio) => RedrawChart();

        protected override void OnRender(RenderContext context, DrawingLayouts layout)
        {
            List<string> lines;
            Level level;
            try { (lines, level) = BuildStatus(PanelMode == PanelModes.Full); }
            catch (Exception ex) { Fail(ex); (lines, level) = (new List<string> { "NEXA Monitor error: " + _lastError }, Level.Violation); }

            if (level == Level.Violation && _lastLevel != Level.Violation && AlertOnViolation)
            {
                try { AddAlert("alert1", "NEXA: " + string.Join(" | ", lines.Skip(1).Where(l => l.StartsWith("X ")))); }
                catch (Exception ex) { Fail(ex); }
            }
            _lastLevel = level;
            if (PanelMode == PanelModes.Hidden) return;
            if (PanelMode == PanelModes.OneLine)
            {
                var first = lines.FirstOrDefault(l => l.StartsWith("X ")) ?? lines.FirstOrDefault(l => l.StartsWith("! "));
                var rec = !RecordMarket ? "REC off" : _rec == null ? "REC waiting" : $"REC on ({_recBars} bars, {_recTrades} trades)";
                lines = new List<string> { $"NEXA · {rec} · {(first == null ? "OK" : first.Substring(3))}" };
            }

            var bg = level switch
            {
                Level.Violation => Color.FromArgb(240, 150, 20, 30),
                Level.Warn => Color.FromArgb(240, 150, 100, 0),
                _ => Color.FromArgb(240, 20, 60, 40),
            };
            var one = PanelMode == PanelModes.OneLine;
            var sizes = lines.Select((l, i) => context.MeasureString(l, i == 0 && !one ? _bold : _font)).ToList();
            var gap = 6;
            var width = 24 + sizes.Max(z => z.Width);
            var height = 16 + sizes.Sum(z => z.Height + gap);
            // Price panel only: in classic ATAS ChartArea also spans lower indicator panels (CVD etc.), which hid the panel.
            var area = ChartArea;
            try { var reg = ChartInfo?.PriceChartContainer?.Region; if (reg is Rectangle rr && rr.Width > 0 && rr.Height > 0) area = rr; }
            catch (Exception ex) { Fail(ex); }
            var x = area.Left + 12;
            var y = Math.Max(area.Top + 70, area.Bottom - height - 12);   // bottom-left: clear of ATAS's own top labels
            context.FillRectangle(bg, new Rectangle(x, y, width, height));
            var yy = y + 8;
            for (var i = 0; i < lines.Count; i++)
            {
                context.DrawString(lines[i], i == 0 && !one ? _bold : _font, Color.White, x + 12, yy);
                yy += sizes[i].Height + gap;
            }
        }

        private (List<string>, Level) BuildStatus(bool details)
        {
            var tm = TradingManager;
            var now = DateTime.UtcNow;
            var session = SessionClock.SessionKey(now);
            var ctNow = SessionClock.ToCt(now);
            var lines = new List<string> { $"NEXA Monitor v6 · read-only · facts, not signals · {tm?.Portfolio?.AccountID ?? "no account"} · {tm?.Security?.Code ?? InstrumentInfo?.Instrument}" };

            int tradesToday;
            decimal dayNet, openPnl, pos;
            List<RoundTrip> completed;
            lock (_lock)
            {
                RoundTripTracker tracker;
                int started;
                (completed, tracker, started) = RebuildToday();
                tradesToday = started;
                dayNet = completed.Sum(t => t.NetUsd);
                pos = tm?.Position?.Volume ?? tracker.Position;
                openPnl = tm?.Position?.UnrealizedPnL ?? 0m;
            }

            decimal? buffer = null;
            var portfolio = tm?.Portfolio;
            if (portfolio != null && MaxLossLimitUsd > 0)
            {
                lock (_lock)
                {
                    EnsureJournal();
                    var key = portfolio.AccountID ?? "default";
                    if (!_state.TryGetValue(key, out var st))
                        _state[key] = st = MllState.Create(portfolio.Balance, MaxLossLimitUsd, session);
                    var before = st.LastSession;
                    st.Observe(portfolio.Balance, session, MaxLossLimitUsd);
                    if (before != st.LastSession) _journal.SaveState(_state);
                    buffer = st.Buffer(portfolio.Balance + openPnl);
                }
            }

            var settings = new GuardSettings(MaxTradesPerDay, DailyLossLimitUsd, MaxLossLimitUsd, ParseCt(LastEntryCt, 15, 0), ParseCt(FlatByCt, 15, 8));
            var (level, msgs) = RuleCheck.Evaluate(settings, tradesToday, dayNet, openPnl, pos != 0, now, buffer);

            lines.Add($"Session {session} · CT {ctNow:HH:mm} · trades {tradesToday}/{MaxTradesPerDay} · day P&L {dayNet + openPnl:+0;-0;0} USD");
            lines.Add(pos == 0 ? "Position: flat" : $"Position: {pos:+0;-0} @ {tm?.Position?.AveragePrice:0.##} · open {openPnl:+0;-0;0} USD");
            if (buffer.HasValue) lines.Add($"MLL buffer: {buffer.Value:0} USD (limit {MaxLossLimitUsd:0}, trailing EOD)");
            var extra = new List<(Level, string)>();
            var whatIf = new List<string>();
            if (ShowWhatIf)
                try { WhatIfLines(pos, dayNet, openPnl, buffer, completed, now, whatIf, extra); }
                catch (Exception ex) { Fail(ex); }
            var rangeLines = new List<string>();
            if (ShowRangeGuide)
                try { RangeLines(now, details, rangeLines, extra); }
                catch (Exception ex) { Fail(ex); }
            foreach (var (l, _) in extra) if (l > level) level = l;
            if (msgs.Count == 0 && extra.Count == 0) lines.Add("OK  All rules OK");
            foreach (var m in msgs) lines.Add((level == Level.Violation ? "X  " : "!  ") + m);
            foreach (var (l, m) in extra) lines.Add((l == Level.Violation ? "X  " : "!  ") + m);
            lines.AddRange(whatIf);
            lines.AddRange(rangeLines);
            if (ShowContext && details)
                try { ContextLines(lines); }
                catch (Exception ex) { Fail(ex); }
            if (RecordMarket)
                lines.Add(_rec == null ? "Recorder: waiting for instrument" :
                    $"Recorder ON: {_recBars} bars, {_recTrades} trades, {_recDom} DOM snapshots this run -> {_rec.Folder}");
            lines.Add($"Journal: {JournalFolder}");
            if (_lastError.Length > 0) lines.Add("Last error: " + _lastError);
            return (lines, level);
        }

        /// <summary>"If A happens / if B happens" lines (stop vs target), plus the pre-trade checklist (J1, J3, J9, J10).</summary>
        private void WhatIfLines(decimal pos, decimal dayNet, decimal openPnl, decimal? buffer, List<RoundTrip> completed, DateTime now,
                                 List<string> lines, List<(Level, string)> flags)
        {
            var pv = PointValue();
            var tick = InstrumentInfo?.TickSize ?? 0m;
            if (pv <= 0 || tick <= 0) { lines.Add("What if: waiting for instrument tick size / tick value"); return; }
            string Buf(decimal? b) => b is decimal x ? $"{x:0}" : "n/a";
            var lossesToday = completed.Count(t => t.NetUsd < 0);
            var inRow = 0;
            for (var i = completed.Count - 1; i >= 0 && completed[i].NetUsd < 0; i--) inRow++;

            if (pos != 0)
            {
                var side = Math.Sign(pos);
                var qty = Math.Abs(pos);
                var avg = TradingManager?.Position?.AveragePrice ?? 0m;
                var (stop, target) = WorkingBracket(side);
                var risk = stop is decimal s0 ? WhatIf.RiskUsd(avg, s0, qty, pv) : 0m;
                Outcome a = null, b = null;
                if (stop is decimal st)
                {
                    a = WhatIf.Exit(side, qty, avg, st, pv, CommissionRtUsd, risk, dayNet, openPnl, buffer);
                    lines.Add($"A: if STOP hits @ {st:0.00} -> {a.TradeNetUsd:+0;-0} USD ({a.R:+0.00;-0.00}R) · day {a.DayAfterUsd:+0;-0} · MLL buffer {Buf(a.MllBufferAfterUsd)}");
                    if (RiskPerTradeUsd > 0 && risk > RiskPerTradeUsd)
                        flags.Add((Level.Warn, $"Risk to stop {risk:0} USD > cap {RiskPerTradeUsd:0} USD"));
                }
                else flags.Add((Level.Violation, "No stop order working: H-DISC1 needs a stop on every trade"));
                if (target is decimal tg)
                {
                    b = WhatIf.Exit(side, qty, avg, tg, pv, CommissionRtUsd, risk, dayNet, openPnl, buffer);
                    lines.Add($"B: if TARGET hits @ {tg:0.00} -> {b.TradeNetUsd:+0;-0} USD ({b.R:+0.00;-0.00}R) · day {b.DayAfterUsd:+0;-0} · MLL buffer {Buf(b.MllBufferAfterUsd)}");
                }
                else lines.Add("B: no target order working");
                if (a != null && b != null && WhatIf.BreakEvenWinRate(b.TradeNetUsd, -a.TradeNetUsd) is decimal be)
                    lines.Add($"To break even at this stop/target you must win {be:P0} of trades like this");
                return;
            }

            var n = WhatIf.Contracts(RiskPerTradeUsd, PlannedStopTicks, pv * tick);
            if (n <= 0) { lines.Add($"If you enter now: a {PlannedStopTicks}-tick stop is too wide for the {RiskPerTradeUsd:0} USD cap"); }
            else
            {
                var loss = n * PlannedStopTicks * tick * pv + n * CommissionRtUsd;
                var win = n * PlannedTargetTicks * tick * pv - n * CommissionRtUsd;
                decimal? bufA = buffer is decimal bb ? bb - loss : null;
                lines.Add($"If you enter now: {n} contracts · stop {PlannedStopTicks}t ({PlannedStopTicks * tick:0.##} pts) · target {PlannedTargetTicks}t ({PlannedTargetTicks * tick:0.##} pts)");
                lines.Add($"A: stop -> -{loss:0} USD · day {dayNet - loss:+0;-0} · MLL buffer {Buf(bufA)}   B: target -> +{win:0} USD · day {dayNet + win:+0;-0}");
                if (WhatIf.BreakEvenWinRate(win, loss) is decimal be)
                    lines.Add($"Break-even win rate {be:P0} · 20 losses in a row = -{20 * loss:0} USD (Silfrain: plan for it)");
            }
            var ct = SessionClock.ToCt(now).TimeOfDay;
            var window = ct >= MarketContext.RthOpen && ct <= ParseCt(LastEntryCt, 15, 0);
            lines.Add($"Checklist: ready {(ReadyCheck ? "yes" : "NO")} · setup {(string.IsNullOrWhiteSpace(SetupTag) ? "NOT SET" : SetupTag)} {SetupGrade} · " +
                      $"losses today {lossesToday} (in a row {inRow}) · entry window {(window ? "open" : "closed")}");
            if (inRow >= 2) flags.Add((Level.Warn, $"{inRow} losses in a row today (Dhesi: max 2 losses a day; Fabio cuts early-loss days)"));
            var lastLoss = completed.LastOrDefault(t => t.NetUsd < 0);
            if (lastLoss != null && completed[^1] == lastLoss && (now - lastLoss.ExitUtc).TotalMinutes < 15)
                lines.Add($"Last trade was a loss {(now - lastLoss.ExitUtc).TotalMinutes:0} min ago: is the next one in your plan, or revenge?");
        }

        /// <summary>v6 Risk & Range: expected range, time-of-day window, volatility stop and size, first-hour note, news (plan v6).</summary>
        private void RangeLines(DateTime now, bool details, List<string> lines, List<(Level, string)> flags)
        {
            if (_news == null || (now - _newsRead).TotalMinutes >= 5)
            {
                _newsRead = now;
                var path = Path.Combine(JournalFolder ?? "", NewsFile ?? "");
                _news = File.Exists(path) ? NewsCalendar.Parse(File.ReadAllLines(path)) : new List<NewsEvent>();
            }
            var ev = NewsCalendar.Next(_news, now);
            var nl = NewsCalendar.LevelFor(ev, now);
            if (nl != Level.Ok)
                flags.Add((nl, $"High-impact news {ev.Name} at {NewsCalendar.ToEt(ev.TimeUtc):HH:mm} ET ({(ev.TimeUtc - now).TotalMinutes:+0;-0;0} min): stay flat unless it is in your plan"));
            if (!details) return;

            var key = new DateTime(now.Ticks - now.Ticks % TimeSpan.TicksPerMinute, DateTimeKind.Utc);
            if (_range == null || key != _rangeKey)
            {
                var (bars, _) = CollectBars(false, RangeLookbackDays + 6, 40000);
                _range = RangeGuide.Compute(bars, now, RangeLookbackDays);
                _rangeKey = key;
            }
            var g = _range;
            var tick = InstrumentInfo?.TickSize ?? 0m;
            var pv = PointValue();
            lines.Add(g.ExpectedRange is decimal er
                ? $"Range: expected {er:0.##} pts (avg of last {g.DaysUsed} days) · today {g.TodayRange:0.##} = {g.UsedPct:P0} used"
                : $"Range: needs >= 3 complete sessions on the chart (have {g.DaysUsed}); load more days of history");
            lines.Add($"Clock: {g.Regime} · typical 5-min range in this window {(g.TypicalMove5m is decimal tm ? $"{tm:0.##} pts" : "-")}");
            var st = RangeGuide.StopTicks(g.TypicalMove5m, StopRangeMultiple, tick);
            if (st > 0 && pv > 0)
            {
                var n = WhatIf.Contracts(RiskPerTradeUsd, st, pv * tick);
                lines.Add(n > 0
                    ? $"Volatility stop: {StopRangeMultiple:0.##}x = {st} ticks ({st * tick:0.##} pts) -> {n} contracts for {RiskPerTradeUsd:0} USD risk"
                    : $"Volatility stop: {st} ticks ({st * tick:0.##} pts) is too wide for {RiskPerTradeUsd:0} USD: skip, or wait for a calmer window");
            }
            if (g.TodayIb is decimal ibr && ibr > 0 && g.TodayRange is decimal tr)
                lines.Add($"First hour {ibr:0.##} pts · day so far {tr / ibr:0.0}x it · past days median {(g.MedianDayToIb is decimal md ? $"{md:0.0}x" : "-")}: the first hour is not the day's range");
            lines.Add(ev == null
                ? $"News: no upcoming events in {NewsFile} (journal folder)"
                : $"Next news: {ev.Name} ({ev.Impact}) {NewsCalendar.ToEt(ev.TimeUtc):ddd dd MMM HH:mm} ET · in {FormatSpan(ev.TimeUtc - now)}");
            lines.Add($"Daily stop line: {DailyLossLimitUsd:0} USD (research: about 1/5 of the drawdown = {MaxLossLimitUsd / 5m:0} USD) · max {MaxTradesPerDay} trades");
        }

        private static string FormatSpan(TimeSpan t) =>
            t.TotalMinutes < 0 ? "now" : t.TotalHours >= 24 ? $"{(int)t.TotalDays}d {t.Hours}h" : t.TotalHours >= 1 ? $"{(int)t.TotalHours}h {t.Minutes}m" : $"{(int)t.TotalMinutes} min";

        /// <summary>Candle, location and "backstage" (book + tape) facts for the current bar (J6, J8).</summary>
        private void ContextLines(List<string> lines)
        {
            var (bars, levels) = CollectBars(ShowIndicators);
            var c = MarketContext.Compute(bars, bars.Count - 1);
            if (c == null) return;
            string P(decimal? v) => v is decimal x ? $"{x:0.00}" : "-";
            var b = c.Bar;
            lines.Add($"Bar {SessionClock.ToCt(b.TimeUtc):HH:mm} CT: {c.BarDirection}, body {c.BodyPct:P0}, vol {(c.RelVolume is decimal rv ? $"{rv:0.0}x avg" : "-")}, " +
                      $"delta {b.Delta:+0;-0;0} ({c.DeltaVsBar}) · 5-bar delta {(c.Delta5 is decimal d5 ? $"{d5:+0;-0;0}" : "-")}");
            lines.Add($"Location: {c.VsVwap} VWAP {P(c.Vwap)} ({(c.Vwap is decimal v ? $"{c.Price - v:+0.00;-0.00}" : "-")} pts) · {c.VsPriorRange} · {c.VsIb} · ATR14 {P(c.Atr14)}");
            lines.Add($"Levels: PDH {P(c.PriorHigh)} PDL {P(c.PriorLow)} PDC {P(c.PriorClose)} · ONH {P(c.OnHigh)} ONL {P(c.OnLow)} · IB {P(c.IbLow)}-{P(c.IbHigh)}");
            var book = ReadBook();
            (decimal buy, decimal sell, int trades, decimal maxPrint) tape;
            lock (_lock) tape = _tape.Stats(DateTime.UtcNow);
            var tick = InstrumentInfo?.TickSize ?? 0m;
            var spread = book != null && tick > 0 && book.BestAsk > 0 && book.BestBid > 0 ? $"{(book.BestAsk - book.BestBid) / tick:0}t" : "-";
            lines.Add($"Backstage: spread {spread} · DOM top-10 bid/ask {(book?.Top10Ratio is decimal r ? $"{r:0.00}" : "-")} · " +
                      $"tape 60s buy {tape.buy:0} / sell {tape.sell:0} ({tape.trades} prints, max {tape.maxPrint:0})");
            if (!ShowIndicators) return;
            var s = NexaIndicators.Compute(bars, levels, bars.Count - 1, tick);
            (int buyN, int sellN, decimal buyVol, decimal sellVol, decimal max) big;
            lock (_lock) big = _big.Stats(DateTime.UtcNow, BigTradeMin);
            string N(decimal? v, string f) => v is decimal x ? x.ToString(f) : "-";
            lines.Add($"Indicators: EMA 5/9/13 {s.EmaStack} · MACD(5,13,4) hist {N(s.MacdHist, "+0.00;-0.00;0")} · BB20 %B {N(s.Bb20PctB, "0.00")} · " +
                      $"squeeze {(s.SqueezeOn is bool q ? (q ? "ON" : "off") : "-")} · BB4+BB20 touch {s.Bb4Touch} · RSI14 {N(s.Rsi14, "0")}");
            lines.Add($"Volume: CVD session {N(s.CvdSession, "+0;-0;0")} / RTH {N(s.CvdRth, "+0;-0;0")} · developing VA {P(s.DevVal)}-{P(s.DevVah)} POC {P(s.DevPoc)} · " +
                      $"prior VA {P(s.PriorVal)}-{P(s.PriorVah)} POC {P(s.PriorPoc)} ({s.VsPriorVa})");
            var (mb, _) = CollectBars(false, 40, 60000);
            var mtf = Mtf.Snapshot(mb);
            lines.Add("Timeframes EMA 5/9/13: " + string.Join(" | ", mtf.Select(f => $"{f.Name} {Short(f.EmaStack)}")));
            lines.Add("Timeframes RSI14 / last bar: " + string.Join(" | ", mtf.Select(f => f.Rsi14 is decimal r2 ? $"{f.Name} {r2:0} {f.BarDir}" : $"{f.Name} -")));
            lines.Add($"Footprint bar: imbalances buy {s.BuyImbalances} / sell {s.SellImbalances}, stacks {s.BuyStacks}/{s.SellStacks} · " +
                      $"big trades 60s (>= {BigTradeMin:0}): buy {big.buyN} / sell {big.sellN}, max {big.max:0}");
        }

        private static string Short(string stack) => stack.StartsWith("up") ? "up" : stack.StartsWith("down") ? "down" : stack;

        /// <summary>Replays today's account fills (current Topstep session) through a fresh tracker.</summary>
        private (List<RoundTrip> completed, RoundTripTracker tracker, int started) RebuildToday()
        {
            var tm = TradingManager;
            var tracker = new RoundTripTracker(PointValue());
            var completed = new List<RoundTrip>();
            var started = 0;
            if (tm?.MyTrades == null) return (completed, tracker, 0);
            var session = SessionClock.SessionKey(DateTime.UtcNow);
            foreach (var f in tm.MyTrades.Select(ToFill).Where(f => f != null && SessionClock.SessionKey(f.TimeUtc) == session).OrderBy(f => f.TimeUtc))
            {
                var wasFlat = tracker.Position == 0;
                var rt = tracker.Apply(f);
                if (wasFlat && tracker.Position != 0) started++;
                if (rt != null)
                {
                    completed.Add(rt);
                    if (tracker.Position != 0) started++;          // reversal opens a new trade
                }
            }
            return (completed, tracker, started);
        }

        private Fill ToFill(MyTrade t)
        {
            if (t == null || t.Volume == 0) return null;
            var sec = TradingManager?.Security;
            if (sec != null && t.SecurityId != null && sec.SecurityId != null && t.SecurityId != sec.SecurityId) return null;
            var id = string.IsNullOrEmpty(t.Id) ? $"{t.Time.Ticks}-{t.Price}-{t.Volume}-{t.OrderDirection}" : t.Id;
            return new Fill(id, t.Time, t.Security?.Code ?? t.SecurityId ?? "", t.OrderDirection == OrderDirections.Buy ? 1 : -1,
                            t.Price, Math.Abs(t.Volume), t.Commission ?? 0m);
        }

        private decimal PointValue()
        {
            var sec = TradingManager?.Security;
            if (sec != null && sec.TickSize > 0 && sec.TickCost > 0) return sec.TickCost / sec.TickSize;
            return 0m;
        }

        private void EnsureJournal()
        {
            if (_journal != null) return;
            // v1 default was ~/Documents/Documents/NEXA_ATAS on macOS (SpecialFolder.Personal already = Documents): repair saved settings
            if (JournalFolder != null && JournalFolder.Replace('\\', '/').EndsWith("/Documents/Documents/NEXA_ATAS"))
                JournalFolder = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), "Documents", "NEXA_ATAS");
            _journal = new Journal(JournalFolder);
            _state = _journal.LoadState();
        }

        private static TimeSpan ParseCt(string s, int h, int m) => TimeSpan.TryParse(s, out var t) ? t : new TimeSpan(h, m, 0);

        private void Fail(Exception ex)
        {
            _lastError = ex.GetType().Name + ": " + ex.Message;
            this.LogWarn("NEXA Monitor: " + _lastError);
        }
    }
}
