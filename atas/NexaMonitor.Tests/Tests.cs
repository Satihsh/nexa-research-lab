using System;
using System.IO;
using System.Linq;
using Nexa.Atas;

int pass = 0, fail = 0;
void Check(string name, bool ok) { if (ok) pass++; else { fail++; Console.WriteLine("FAIL " + name); } }
bool Near(decimal a, decimal b) => Math.Abs(a - b) < 0.0001m;
DateTime U(int y, int mo, int d, int h, int mi) => new DateTime(y, mo, d, h, mi, 0, DateTimeKind.Utc);
var s = new GuardSettings(2, 1000m, 2000m, new TimeSpan(15, 0, 0), new TimeSpan(15, 8, 0));

// 1. Session key: Topstep day rolls at 17:00 CT (CDT = UTC-5 in October, CST = UTC-6 in January)
Check("session 16:59 CDT", SessionClock.SessionKey(U(2026, 10, 19, 21, 59)) == "2026-10-19");
Check("session 17:00 CDT", SessionClock.SessionKey(U(2026, 10, 19, 22, 0)) == "2026-10-20");
Check("session 17:00 CST", SessionClock.SessionKey(U(2027, 1, 12, 23, 0)) == "2027-01-13");
Check("session 16:59 CST", SessionClock.SessionKey(U(2027, 1, 12, 22, 59)) == "2027-01-12");
Check("CT conversion", SessionClock.ToCt(U(2026, 10, 19, 14, 30)).Hour == 9);

// 2. Simple long, NQ-like point value 20
var t = new RoundTripTracker(20m);
Check("open", t.Apply(new Fill("a", U(2026, 10, 19, 14, 31), "NQ", 1, 100m, 1m, 2m)) == null && t.Position == 1);
var rt = t.Apply(new Fill("b", U(2026, 10, 19, 14, 40), "NQ", -1, 102m, 1m, 2m));
Check("simple long", rt != null && Near(rt.GrossUsd, 40m) && Near(rt.Points, 2m) && Near(rt.NetUsd, 36m) && rt.Side == 1 && t.Position == 0);

// 3. Scale in + partial exits
t = new RoundTripTracker(20m);
t.Apply(new Fill("1", U(2026, 10, 19, 15, 0), "NQ", 1, 100m, 1m, 0m));
t.Apply(new Fill("2", U(2026, 10, 19, 15, 1), "NQ", 1, 104m, 1m, 0m));
Check("avg after scale-in", Near(t.AveragePrice, 102m));
Check("partial exit no trip", t.Apply(new Fill("3", U(2026, 10, 19, 15, 2), "NQ", -1, 106m, 1m, 0m)) == null && t.Position == 1);
rt = t.Apply(new Fill("4", U(2026, 10, 19, 15, 3), "NQ", -1, 101m, 1m, 0m));
Check("scale trip", rt != null && Near(rt.GrossUsd, 60m) && Near(rt.AvgExit, 103.5m) && Near(rt.Points, 1.5m) && rt.MaxQty == 2);

// 4. Reversal with commission split
t = new RoundTripTracker(20m);
t.Apply(new Fill("r1", U(2026, 10, 19, 15, 10), "NQ", 1, 100m, 2m, 2m));
rt = t.Apply(new Fill("r2", U(2026, 10, 19, 15, 11), "NQ", -1, 99m, 3m, 3m));
Check("reversal closes long", rt != null && Near(rt.GrossUsd, -40m) && Near(rt.CommissionUsd, 4m) && t.Position == -1 && Near(t.AveragePrice, 99m));
rt = t.Apply(new Fill("r3", U(2026, 10, 19, 15, 12), "NQ", 1, 97m, 1m, 1m));
Check("reversed short trip", rt != null && rt.Side == -1 && Near(rt.GrossUsd, 40m) && Near(rt.CommissionUsd, 2m));
Check("open pnl", Near(new RoundTripTracker(20m).OpenPnlUsd(100m), 0m));

// 5. Rule checks (14:30 UTC = 09:30 CDT)
var morning = U(2026, 10, 19, 14, 30);
Check("ok", RuleCheck.Evaluate(s, 1, 0m, 0m, false, morning, 1500m).level == Level.Ok);
Check("trades > max", RuleCheck.Evaluate(s, 3, 0m, 0m, false, morning, null).level == Level.Violation);
Check("max reached flat", RuleCheck.Evaluate(s, 2, 0m, 0m, false, morning, null).level == Level.Warn);
Check("max reached in position ok", RuleCheck.Evaluate(s, 2, 0m, 0m, true, morning, null).level == Level.Ok);
Check("daily loss hit", RuleCheck.Evaluate(s, 1, -900m, -100m, true, morning, null).level == Level.Violation);
Check("daily loss near", RuleCheck.Evaluate(s, 1, -850m, 0m, false, morning, null).level == Level.Warn);
Check("daily limit off", RuleCheck.Evaluate(s with { DailyLossLimitUsd = 0 }, 1, -5000m, 0m, false, morning, null).level == Level.Ok);
Check("position after 15:08 CT", RuleCheck.Evaluate(s, 1, 0m, 0m, true, U(2026, 10, 19, 20, 9), null).level == Level.Violation);
Check("flat after 15:00 CT warns", RuleCheck.Evaluate(s, 0, 0m, 0m, false, U(2026, 10, 19, 20, 1), null).level == Level.Warn);
Check("evening 17:30 CT position ok", RuleCheck.Evaluate(s, 0, 0m, 0m, true, U(2026, 10, 19, 22, 30), null).level == Level.Ok);
Check("mll breached", RuleCheck.Evaluate(s, 0, 0m, 0m, false, morning, 0m).level == Level.Violation);
Check("mll near", RuleCheck.Evaluate(s, 0, 0m, 0m, false, morning, 400m).level == Level.Warn);

// 6. MLL: Topstep's own example (start 50,000, MLL 48,000; +500 day -> 48,500; -500 day stays; locks at 50,000)
var m = MllState.Create(50000m, 2000m, "2026-10-19");
m.Observe(50500m, "2026-10-19", 2000m);
m.Observe(50000m, "2026-10-20", 2000m);
Check("mll trails to 48500", m.Mll == 48500m);
m.Observe(53000m, "2026-10-21", 2000m);
Check("mll stays after loss day", m.Mll == 48500m);
m.Observe(56000m, "2026-10-22", 2000m);
Check("mll locks at start", m.Mll == 50000m);
m.Observe(56000m, "2026-10-23", 2000m);
Check("mll stays locked", m.Mll == 50000m && m.Buffer(51000m) == 1000m);

// 7. Journal: fills de-duplicated across restarts, state round-trips
var dir = Path.Combine(Path.GetTempPath(), "nexa_journal_test_" + Guid.NewGuid().ToString("N"));
var j = new Journal(dir);
var f1 = new Fill("x1", U(2026, 10, 19, 14, 31), "NQ", 1, 100m, 1m, 1.22m);
j.WriteFill(f1); j.WriteFill(f1);
var j2 = new Journal(dir);
Check("reload seen", j2.Seen("x1"));
j2.WriteFill(f1);
Check("one fill line", File.ReadAllLines(Path.Combine(dir, "fills.csv")).Length == 2);
j2.WriteTrip(rt);
Check("trip written", File.ReadAllLines(Path.Combine(dir, "roundtrips.csv")).Length == 2);
j2.WriteOrderEvent(U(2026, 10, 19, 14, 31), "o1", "MNQ", "Stop", -1, 0m, 21450.25m, 2m, "Active", "SL");
var ol = File.ReadAllLines(Path.Combine(dir, "orders.csv"));
Check("order event written", ol.Length == 2 && ol[0] == Journal.OrdersHeader && ol[1].Contains(",Stop,SELL,0,21450.25,2,Active,SL"));
j2.SaveState(new() { ["acc"] = m });
Check("state round trip", new Journal(dir).LoadState()["acc"].Mll == 50000m);
Directory.Delete(dir, true);

// 8. v2 market context: Mon 2026-10-19 RTH (prior day), Mon evening + Tue 07:00 (overnight), Tue RTH 08:30-09:30 (CDT = UTC-5)
Bar B(int d, int h, int mi, decimal o, decimal hi, decimal lo, decimal c, decimal v = 100m, decimal delta = 0m) =>
    new Bar(new DateTime(2026, 10, d, h, mi, 0, DateTimeKind.Utc).AddHours(5), o, hi, lo, c, v, delta, 0m, 0m, 0m, 0m, c);
var bars = new System.Collections.Generic.List<Bar>();
for (var k = 0; k < 13; k++)
{
    var mi = 8 * 60 + 30 + 30 * k;
    bars.Add(B(19, mi / 60, mi % 60, 100m, k == 3 ? 110m : 105m, k == 7 ? 90m : 95m, k == 12 ? 102m : 100m));
}
bars.Add(B(19, 17, 0, 102m, 104m, 99m, 101m));
bars.Add(B(19, 20, 0, 101m, 103m, 100m, 102m));
bars.Add(B(20, 7, 0, 102m, 115m, 98m, 103m));
bars.Add(B(20, 8, 30, 103m, 106m, 101m, 105m, 100m));
bars.Add(B(20, 9, 0, 105m, 108m, 104m, 107m, 200m));
bars.Add(B(20, 9, 30, 107m, 112m, 106m, 111m, 300m, -50m));
var cx = MarketContext.Compute(bars, bars.Count - 1);
Check("ctx in RTH", cx.InRth && cx.IbComplete);
Check("ctx prior day", cx.PriorHigh == 110m && cx.PriorLow == 90m && cx.PriorClose == 102m);
Check("ctx overnight", cx.OnHigh == 115m && cx.OnLow == 98m);
Check("ctx IB + OR30", cx.IbHigh == 108m && cx.IbLow == 101m && cx.Or30High == 106m && cx.Or30Low == 101m && cx.VsIb == "above IB");
Check("ctx RTH open/high/low", cx.RthOpenPrice == 103m && cx.RthHigh == 112m && cx.RthLow == 101m);
Check("ctx vwap", cx.VwapRth is decimal vw && Math.Abs(vw - 107.6111m) < 0.001m && cx.VsVwap == "above");
Check("ctx labels", cx.VsPriorRange == "above prior-day high" && cx.DeltaVsBar == "disagrees" && cx.BarDirection == "up");
Check("ctx atr + change5", cx.Atr14 != null && cx.Change5 == 111m - 101m && cx.RelVolume == null);
var ev = MarketContext.Compute(bars, 13);                                   // Mon 17:00 CT: Monday RTH is now the prior day
Check("ctx evening prior day", !ev.InRth && ev.PriorHigh == 110m && ev.PriorClose == 102m && ev.VsIb == "pre-open");
Check("ctx no look-ahead", MarketContext.Compute(bars, 16).RthHigh == 106m);
Check("ctx bad index", MarketContext.Compute(bars, 99) == null);

// 9. Tape window, order book
var t0 = U(2026, 10, 20, 14, 30);
var tape = new TapeWindow(TimeSpan.FromSeconds(60));
tape.Add(t0, 5m, 1); tape.Add(t0.AddSeconds(30), 3m, -1); tape.Add(t0.AddSeconds(70), 2m, 1);
var ts = tape.Stats(t0.AddSeconds(70));
Check("tape prune + stats", ts.buy == 2m && ts.sell == 3m && ts.trades == 2 && ts.maxPrint == 3m);
var book = BookStats.From(new[] { (100m, 10m, true), (99.75m, 5m, true), (100.25m, 4m, false), (100.5m, 6m, false), (101m, 0m, false) }, 500m, 400m);
Check("book", book.BestBid == 100m && book.BestAsk == 100.25m && book.Top10Bids == 15m && book.Top10Asks == 10m && book.Top10Ratio == 1.5m);
Check("book empty", BookStats.From(null, 0m, 0m).Top10Ratio == null);

// 10. What if (MNQ: $2 per point), excursion, follow-up
var risk = WhatIf.RiskUsd(21000m, 20990m, 2m, 2m);
var wa = WhatIf.Exit(1, 2m, 21000m, 20990m, 2m, 1.22m, risk, 100m, 10m, 1500m);
var wb = WhatIf.Exit(1, 2m, 21000m, 21020m, 2m, 1.22m, risk, 100m, 10m, 1500m);
Check("whatif risk", risk == 40m);
Check("whatif stop", Near(wa.TradeNetUsd, -42.44m) && Near(wa.R.Value, -1.061m) && Near(wa.DayAfterUsd, 57.56m) && Near(wa.MllBufferAfterUsd.Value, 1447.56m));
Check("whatif target", Near(wb.TradeNetUsd, 77.56m) && wb.MllBufferAfterUsd == 1567.56m);
Check("whatif short", Near(WhatIf.Exit(-1, 1m, 100m, 98m, 20m, 0m, 0m, 0m, 0m, null).TradeNetUsd, 40m) && WhatIf.Exit(-1, 1m, 100m, 98m, 20m, 0m, 0m, 0m, 0m, null).R == null);
Check("break-even win rate", Math.Abs(WhatIf.BreakEvenWinRate(77.56m, 42.44m).Value - 0.35367m) < 0.0001m && WhatIf.BreakEvenWinRate(0m, 1m) == null);
Check("contracts", WhatIf.Contracts(250m, 40, 0.5m) == 12 && WhatIf.Contracts(250m, 0, 0.5m) == 0 && WhatIf.Contracts(250m, 1000, 0.5m) == 0);
var ex = new Excursion(); ex.Start(1, 100m); ex.Update(98m); ex.Update(103m); ex.Update(99m);
Check("excursion long", ex.MaePoints == 2m && ex.MfePoints == 3m);
ex.Start(-1, 100m); ex.Update(101m); ex.Update(97m);
Check("excursion short", ex.MaePoints == 1m && ex.MfePoints == 3m);
var fu = new Followup("k", 1, 95m, 110m, t0);
Check("followup pending", !fu.Update(105m, t0) && fu.Result == "");
Check("followup target", fu.Update(110m, t0.AddMinutes(3)) && fu.Result == "TARGET_FIRST");
var fs = new Followup("k2", -1, 105m, 95m, t0);
Check("followup short stop", fs.Update(105.25m, t0) && fs.Result == "STOP_FIRST");
var fe = new Followup("k3", 1, 95m, 110m, t0); fe.Expire(t0, "NEITHER_BY_FLAT_TIME"); fe.Update(120m, t0);
Check("followup expire sticks", fe.Result == "NEITHER_BY_FLAT_TIME");
Check("followup row", V2Files.FollowupRow(fu).Split(',').Length == V2Files.FollowupHeader.Split(',').Length);

// 11. v2 rows: column counts match headers; rule flags kept on winners
string Cols(string row) => row.Split(',').Length.ToString();
var hdr = V2Files.ContextHeader.Split(',').Length.ToString();
Check("context row cols", Cols(V2Files.ContextRow("ENTRY", t0, "k", 1, 111m, cx, book, ts, 0.25m)) == hdr);
Check("context row cols (no data)", Cols(V2Files.ContextRow("EXIT", t0, "k", -1, 111m, null, null, (0m, 0m, 0, 0m), 0m)) == hdr);
var ot = new OpenTrade { TripKey = "k", Side = 1, EntryUtc = t0, TradeNoToday = 3, OverMaxTrades = true };
var win = new RoundTrip("2026-10-20", t0, t0.AddMinutes(12), "MNQ", 1, 2m, 21000m, 21020m, 20m, 80m, 2.44m, 77.56m);
var row = ot.ReviewRow(win, 2m, 250m, false);
Check("review cols", Cols(row) == V2Files.ReviewHeader.Split(',').Length.ToString());
Check("review flags on a winner", row.EndsWith("NO_STOP;OVER_MAX_TRADES;READY_CHECK_NOT_TICKED;NO_SETUP_TAG"));
ot.InitialStop = 20990m; ot.InitialTarget = 21020m; ot.ReadyCheck = true; ot.SetupTag = "VWAP reclaim, A"; ot.Excursion.Start(1, 21000m); ot.Excursion.Update(20995m);
row = ot.ReviewRow(win, 2m, 250m, true);
var rc = row.Split(',');
Check("review R + rr + mae", rc[12] == "40" && rc[13] == "1.939" && rc[14] == "2" && rc[17] == "0.5" && rc[25] == "VWAP reclaim; A");
Check("review flags held past flat", row.EndsWith("OVER_MAX_TRADES;HELD_PAST_FLAT_TIME"));
Check("risk over cap flag", ot.Flags(300m, 250m, false).Contains("RISK_OVER_CAP"));
var dir2 = Path.Combine(Path.GetTempPath(), "nexa_journal_test_" + Guid.NewGuid().ToString("N"));
var j3 = new Journal(dir2);
j3.WriteRow("trade_review.csv", V2Files.ReviewHeader, row); j3.WriteRow("trade_review.csv", V2Files.ReviewHeader, row);
Check("v2 file header once", File.ReadAllLines(Path.Combine(dir2, "trade_review.csv")).Length == 3);
Directory.Delete(dir2, true);

// 12. v3 indicators
var closedBar = new System.Collections.Generic.List<Bar>(bars) { B(20, 15, 30, 111m, 112m, 110m, 111m) };
Check("ctx 15:30 CT = RTH closed", MarketContext.Compute(closedBar, closedBar.Count - 1).VsIb == "RTH closed");
Check("ema seed + value", NexaIndicators.Ema(new[] { 10m, 10m, 10m, 10m, 10m }, 5) == 10m && NexaIndicators.Ema(new[] { 1m, 2m }, 5) == null);
var es = NexaIndicators.EmaSeries(new[] { 10m, 13m }, 2);                     // alpha 2/3: 2/3*13 + 1/3*10 = 12
Check("ema alpha", Near(es[1], 12m));
Check("rsi all up = 100, flat = 50", NexaIndicators.Rsi(Enumerable.Range(0, 20).Select(i => (decimal)i).ToList(), 14) == 100m
      && NexaIndicators.Rsi(Enumerable.Repeat(5m, 20).ToList(), 14) == 50m);
var rsiMix = NexaIndicators.Rsi(new[] { 1m, 2m, 1m, 2m, 1m, 2m, 1m, 2m, 1m, 2m, 1m, 2m, 1m, 2m, 1m }, 14);  // 7 up, 7 down, equal size
Check("rsi balanced = 50", rsiMix == 50m);
Check("va greedy (python parity)", NexaIndicators.VaGreedy(new[] { 1m, 2m, 10m, 3m, 1m }, 0.70m) == (2, 2, 4)
      && NexaIndicators.VaGreedy(new[] { 5m, 5m, 1m }, 0.70m) == (0, 0, 2));
var prof = NexaIndicators.Profile(new[] { (System.Collections.Generic.IReadOnlyList<FootLevel>)new[] { new FootLevel(100m, 10m, 5m, 5m), new FootLevel(100.25m, 50m, 25m, 25m) },
                                           new[] { new FootLevel(100.25m, 20m, 10m, 10m), new FootLevel(100.5m, 5m, 2m, 3m) } }, 0.25m);
// 100: 10, 100.25: 70, 100.5: 5 -> POC alone holds 82 % >= 70 %
Check("profile poc/va", prof.poc == 100.25m && prof.val == 100.25m && prof.vah == 100.25m);
var imb = NexaIndicators.Imbalances(new[] { new FootLevel(100m, 5m, 5m, 0m), new FootLevel(100.25m, 41m, 1m, 40m), new FootLevel(100.5m, 31m, 1m, 30m),
                                           new FootLevel(100.75m, 30m, 0m, 30m), new FootLevel(101m, 12m, 2m, 10m) }, 0.25m);
// ask(100.25)=40 vs bid(100)=5 -> 8x buy; 30 vs 1 buy; 30 vs bid(100.5)=1 buy; 10 vs bid(100.75)=0 -> not (needs >= 1)
Check("imbalances + stack", imb.buy == 3 && imb.buyStacks == 1 && imb.sell == 0 && imb.sellStacks == 0);
var bt = new BigTrades(TimeSpan.FromSeconds(60));
var k1 = new object(); var k2 = new object();
bt.Upsert(k1, t0, 10m, 1); bt.Upsert(k1, t0.AddSeconds(1), 35m, 1); bt.Upsert(k2, t0.AddSeconds(2), 40m, -1);
var bst = bt.Stats(t0.AddSeconds(5), 30m);
Check("big trades upsert", bst.buyN == 1 && bst.buyVol == 35m && bst.sellN == 1 && bst.max == 40m);
Check("big trades window", bt.Stats(t0.AddSeconds(61), 30m).buyN == 0 && bt.Stats(t0.AddSeconds(61), 30m).sellN == 1);
// indicators on the synthetic bars: no footprint -> profile n/a; CVD = sum of deltas in session
var lvNull = bars.Select(_ => (System.Collections.Generic.IReadOnlyList<FootLevel>)null).ToList();
var snap = NexaIndicators.Compute(bars, lvNull, bars.Count - 1, 0.25m);
Check("snapshot basics", snap.Ema13 != null && snap.MacdHist != null && snap.Bb20PctB == null && snap.CvdRth == -50m && snap.CvdSession == -50m && snap.VsPriorVa == "n/a");
var longBars = Enumerable.Range(0, 40).Select(i => new Bar(t0.AddMinutes(i), 100m + i, 101m + i, 99m + i, 100.5m + i, 10m, 1m, 0m, 0m, 0m, 0m, 100m + i)).ToList();
var snap2 = NexaIndicators.Compute(longBars, null, 39, 0.25m);
Check("uptrend snapshot", snap2.EmaStack == "up (5>9>13)" && snap2.MacdHist is decimal mh && snap2.Bb20PctB is decimal pb && pb > 0.5m && snap2.Rsi14 == 100m && snap2.SqueezeOn != null);
Check("indicator row cols", NexaIndicators.Row("ENTRY", t0, "k", snap2, 30m, bst).Split(',').Length == NexaIndicators.Header.Split(',').Length);

// 13. Market recorder: bars deduplicated across restarts, footprint rows, tape aggregation, DOM snapshot, session files
var rdir = Path.Combine(Path.GetTempPath(), "nexa_rec_test_" + Guid.NewGuid().ToString("N"));
var rec = new MarketRecorder(rdir, "MNQZ6", "M1");
var rb = new RecBar(U(2026, 10, 20, 14, 30), U(2026, 10, 20, 14, 30).AddSeconds(59.5), 100m, 101m, 99m, 100.5m, 50m, 4m, 27m, 23m, 31m, 6m, -3m, 0m);
var rl = new[] { new RecLevel(100.25m, 20m, 10m, 10m, 7m), new RecLevel(100m, 30m, 13m, 17m, 9m) };
Check("rec bar written", rec.WriteBar(rb, rl));
Check("rec bar dedupe same run", !rec.WriteBar(rb, rl));
Check("rec bar dedupe after restart", !new MarketRecorder(rdir, "MNQZ6", "M1").WriteBar(rb, rl));
var bfile = Path.Combine(rec.Folder, "bars_2026-10-20.csv");
var bl = File.ReadAllLines(bfile);
Check("rec bars file", bl.Length == 2 && bl[0] == MarketRecorder.BarsHeader && bl[1].StartsWith("2026-10-20 14:30:00.000,2026-10-20 09:30:00.000,") && bl[1].Contains(",59.5,100,101,99,100.5,50,4,27,23,31,6,-3,0"));
var ll = File.ReadAllLines(Path.Combine(rec.Folder, "levels_2026-10-20.csv"));
Check("rec levels sorted", ll.Length == 3 && ll[1].EndsWith(",100,30,13,17,9") && ll[2].EndsWith(",100.25,20,10,10,7"));
Check("rec evening bar -> next session file", rec.WriteBar(rb with { TimeUtc = U(2026, 10, 20, 22, 5) }, null) && File.Exists(Path.Combine(rec.Folder, "bars_2026-10-21.csv")));
var agg = new TradeAggregator();
var ka = new object(); var kb = new object();
var tr1 = new RecTrade(t0, t0, 1, 3m, 100m, 100m, 99.75m, 12m, 100m, 4m, 2);
Check("agg first", agg.Observe(ka, tr1) == null);
Check("agg grows", agg.Observe(ka, tr1 with { Volume = 9m, LastPrice = 100.25m, ReceivedUtc = t0.AddSeconds(1) }) == null);
var fin = agg.Observe(kb, tr1 with { Side = -1, Volume = 1m });
Check("agg final on next", fin != null && fin.Volume == 9m && fin.LastPrice == 100.25m && fin.ReceivedUtc == t0);
rec.AddTrade(fin);
rec.AddDom(t0, new[] { (100m, 15m, true), (99.75m, 30m, true), (100.25m, 8m, false), (100.5m, 0m, false) }, 900m, 800m, 1);
Check("rec buffered until flush", !File.Exists(Path.Combine(rec.Folder, "tape_2026-10-20.csv")));
rec.Flush();
var tl = File.ReadAllLines(Path.Combine(rec.Folder, "tape_2026-10-20.csv"));
var dl = File.ReadAllLines(Path.Combine(rec.Folder, "dom_2026-10-20.csv"));
Check("rec tape row", tl.Length == 2 && tl[1].EndsWith(",BUY,9,100,100.25,99.75,12,100,4,2"));
Check("rec dom row (depth 1)", dl.Length == 2 && dl[1].EndsWith(",100,100.25,900,800,100:15,100.25:8"));
Check("agg take pending", agg.TakePending()?.Side == -1 && agg.TakePending() == null);
Directory.Delete(rdir, true);

// 14. Multi-timeframe aggregation and DOM de-duplication
var m1 = new System.Collections.Generic.List<Bar>
{
    new Bar(U(2026, 10, 20, 14, 30), 100m, 102m, 99m, 101m, 10m, 5m, 0m, 0m, 6m, -1m, 0m),
    new Bar(U(2026, 10, 20, 14, 31), 101m, 103m, 100m, 102m, 20m, -8m, 0m, 0m, 2m, -9m, 0m),
    new Bar(U(2026, 10, 20, 14, 32), 102m, 102m, 98m, 99m, 30m, 4m, 0m, 0m, 4m, -2m, 0m),
    new Bar(U(2026, 10, 20, 14, 35), 99m, 100m, 97m, 98m, 5m, -1m, 0m, 0m, 1m, -1m, 0m),
};
var m5 = Mtf.Aggregate(m1, 5);
// running delta: bar1 max 6, min -1; bar2 starts at 5: 5+2=7, 5-9=-4; bar3 starts at -3: -3+4=1, -3-2=-5
Check("mtf aggregate ohlcv", m5.Count == 2 && m5[0].Open == 100m && m5[0].High == 103m && m5[0].Low == 98m && m5[0].Close == 99m && m5[0].Volume == 60m && m5[0].Delta == 1m);
Check("mtf exact max/min delta", m5[0].MaxDelta == 7m && m5[0].MinDelta == -5m && m5[1].Open == 99m);
Check("mtf H4 key aligned to 17:00 CT", Mtf.Key(U(2026, 10, 20, 22, 0), 240) == "2026-10-21#0" && Mtf.Key(U(2026, 10, 21, 1, 59), 240) == "2026-10-21#0"
      && Mtf.Key(U(2026, 10, 21, 2, 0), 240) == "2026-10-21#1" && Mtf.Key(U(2026, 10, 21, 14, 0), 240) == "2026-10-21#4");
Check("mtf D key = session", Mtf.Key(U(2026, 10, 20, 21, 59), 1440) == "2026-10-20" && Mtf.Key(U(2026, 10, 20, 22, 0), 1440) == "2026-10-21");
var mlong = Enumerable.Range(0, 600).Select(i => new Bar(U(2026, 10, 20, 13, 0).AddMinutes(i), 100m + i * 0.1m, 100.5m + i * 0.1m, 99.5m + i * 0.1m, 100.2m + i * 0.1m, 10m, 1m, 0m, 0m, 1m, 0m, 0m)).ToList();
Check("mtf chart minutes", Mtf.ChartMinutes(m1) == 1 && Mtf.ChartMinutes(Mtf.Aggregate(mlong, 5)) == 5 && Mtf.ChartMinutes(m1.Take(2).ToList()) == 0);
var snapM = Mtf.Snapshot(mlong);
Check("mtf snapshot frames", snapM.Count == 8 && snapM[0].Name == "M1" && snapM[0].EmaStack.StartsWith("up") && snapM[5].Name == "H1" && snapM[5].Bars == 10 && snapM[7].Name == "D");
var snap5 = Mtf.Snapshot(Mtf.Aggregate(mlong, 5));
Check("mtf smaller frames n/a on M5 chart", snap5[0].EmaStack == "n/a" && snap5[1].Bars == 120 && snap5[2].Bars == 60);
Check("mtf row cols", Mtf.Row("ENTRY", t0, "k", snapM).Split(',').Length == Mtf.Header.Split(',').Length);
var rdir2 = Path.Combine(Path.GetTempPath(), "nexa_rec_test_" + Guid.NewGuid().ToString("N"));
var rec2 = new MarketRecorder(rdir2, "NQ", "M1");
var book1 = new[] { (100m, 15m, true), (100.25m, 8m, false) };
Check("dom dedupe", rec2.AddDom(t0, book1, 1m, 1m, 5) && !rec2.AddDom(t0.AddSeconds(5), book1, 1m, 1m, 5)
      && rec2.AddDom(t0.AddSeconds(10), new[] { (100m, 16m, true), (100.25m, 8m, false) }, 1m, 1m, 5));
Directory.Delete(rdir2, true);

// v6 Risk & Range (NexaRange.cs)
{
    // synthetic 1-min RTH bars, 08:30-14:59 CT (13:30-19:59 UTC in October), range R per day
    var rbars = new System.Collections.Generic.List<Bar>();
    void AddDay(int d, decimal low, decimal high, decimal ibHigh)
    {
        for (var mi = 0; mi < 390; mi++)
        {
            var t = U(2026, 10, d, 13, 30).AddMinutes(mi);
            var hi = mi < 60 ? ibHigh : (mi == 300 ? high : low + 1m);
            rbars.Add(new Bar(t, low + 0.5m, hi, low, low + 0.5m, 10, 0, 0, 0, 0, 0, 0));
        }
    }
    AddDay(12, 100m, 140m, 120m); AddDay(13, 100m, 160m, 120m); AddDay(14, 100m, 120m, 110m); AddDay(15, 100m, 180m, 140m);
    // today 10-16, 10:00 CT (15:00 UTC): 90 minutes in
    for (var mj = 0; mj < 90; mj++) rbars.Add(new Bar(U(2026, 10, 16, 13, 30).AddMinutes(mj), 100m, mj < 60 ? 110m : 115m, 100m, 105m, 10, 0, 0, 0, 0, 0, 0));
    var g = RangeGuide.Compute(rbars, U(2026, 10, 16, 15, 0), 10);
    Check("range days used", g.DaysUsed == 4);
    Check("range expected", Near(g.ExpectedRange ?? -1, 50m));                 // (40+60+20+80)/4
    Check("range today + used", Near(g.TodayRange ?? -1, 15m) && Near(g.UsedPct ?? -1, 0.3m));
    Check("range first hour today", Near(g.TodayIb ?? -1, 10m));
    Check("range median day/IB", Near(g.MedianDayToIb ?? -1, 2m));             // day/first-hour = 2, 3, 2, 2 -> median 2
    Check("regime at 10:00 CT", g.Regime == "MORNING");
    Check("typical 5m in window", g.TypicalMove5m is decimal tm && tm > 0);
    Check("too few days", RangeGuide.Compute(rbars.Where(b => b.TimeUtc.Day >= 14).ToList(), U(2026, 10, 16, 15, 0)).ExpectedRange == null);
    Check("lookback limit", RangeGuide.Compute(rbars, U(2026, 10, 16, 15, 0), 3).DaysUsed == 3);
    Check("incomplete day ignored", RangeGuide.Compute(rbars.Where(b => !(b.TimeUtc.Day == 15 && b.TimeUtc.Hour >= 19)).ToList(), U(2026, 10, 16, 15, 0)).DaysUsed == 3);
    Check("regimes", RangeGuide.RegimeAt(new TimeSpan(8, 45, 0)) == "OPEN SURGE" && RangeGuide.RegimeAt(new TimeSpan(12, 0, 0)) == "LUNCH LULL"
                     && RangeGuide.RegimeAt(new TimeSpan(14, 30, 0)) == "CLOSE" && RangeGuide.RegimeAt(new TimeSpan(15, 30, 0)) == "closed"
                     && RangeGuide.RegimeAt(new TimeSpan(8, 0, 0)) == "closed");
    Check("regime in CST (January)", RangeGuide.Compute(rbars, U(2027, 1, 12, 14, 45)).Regime == "OPEN SURGE");   // 08:45 CST
    Check("stop ticks", RangeGuide.StopTicks(10m, 1.5m, 0.25m) == 60 && RangeGuide.StopTicks(0.1m, 1.5m, 0.25m) == 4 && RangeGuide.StopTicks(null, 1.5m, 0.25m) == 0);

    // news calendar: ET -> UTC with DST (Oct = EDT, UTC-4; Dec = EST, UTC-5)
    var cal = NewsCalendar.Parse(new[] { "date,time_et,event,impact", "# comment", "2026-10-28,14:00,FOMC,high",
                                         "2026-12-04,08:30,NFP,HIGH", "bad line", "2026-10-27,10:00,Consumer confidence,medium" });
    Check("news parse count", cal.Count == 3);
    Check("news EDT", cal.Any(e => e.Name == "FOMC" && e.TimeUtc == U(2026, 10, 28, 18, 0)));
    Check("news EST", cal.Any(e => e.Name == "NFP" && e.TimeUtc == U(2026, 12, 4, 13, 30) && e.Impact == "high"));
    Check("news next", NewsCalendar.Next(cal, U(2026, 10, 28, 12, 0)).Name == "FOMC");
    Check("news just released still shown", NewsCalendar.Next(cal, U(2026, 10, 28, 18, 1)).Name == "FOMC");
    Check("news after", NewsCalendar.Next(cal, U(2026, 10, 28, 18, 3)).Name == "NFP");
    var fomc = cal.First(e => e.Name == "FOMC");
    Check("news levels", NewsCalendar.LevelFor(fomc, U(2026, 10, 28, 17, 30)) == Level.Ok
                         && NewsCalendar.LevelFor(fomc, U(2026, 10, 28, 17, 50)) == Level.Warn
                         && NewsCalendar.LevelFor(fomc, U(2026, 10, 28, 17, 59)) == Level.Violation
                         && NewsCalendar.LevelFor(fomc, U(2026, 10, 28, 18, 2)) == Level.Violation
                         && NewsCalendar.LevelFor(cal.First(e => e.Impact == "medium"), U(2026, 10, 27, 13, 59)) == Level.Ok);
    Check("news ET display", NewsCalendar.ToEt(U(2026, 10, 28, 18, 0)).Hour == 14);
    var real = Path.Combine(AppContext.BaseDirectory, "../../../../news_calendar.csv");
    if (File.Exists(real))
    {
        var lines = File.ReadAllLines(real);
        var rows = lines.Count(l => l.Length > 0 && char.IsDigit(l[0]));
        Check("shipped news_calendar.csv parses every row", NewsCalendar.Parse(lines).Count == rows && rows > 0);
    }
}

Console.WriteLine($"{pass} passed, {fail} failed");
return fail == 0 ? 0 : 1;
