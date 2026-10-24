# S17: Tom DeMark & Rocke DeMark, "Countertrend forex trading with TD Sequential"
**File:** `TD SEQUENTAIL.pdf` (sic). 6 pp. *Currency Trader*, January 2005, pp. 28–33.

| Field | Value |
|---|---|
| **Source type** | Industry / practitioner. Written by the indicator's originator; TD terms are registered trademarks. |
| **Evidence status** | **Unverified claim** for predictive value: hand-picked chart examples (GBP, EUR, AUD/NZD daily, 2004) and no statistics. The **rule definitions are authoritative** (originator). |
| **Processing** | All 6 pages read. The chart pages (pp. 1–2 spread, Figs 1–3) were inspected visually. The numbers in the extracted text are chart labels. |

## Exact rules (SOURCE; this is the canonical spec)
**TD Price Flip** (initialisation)
- **Buy Setup:** the close of the bar *before* Setup bar 1 must be **≥** the close 4 bars before it.
- **Sell Setup:** **≤**.

**Buy Setup**
- ≥ 9 consecutive closes **<** the close 4 bars earlier.
- Numbered 1–9; any interruption erases the count.
- **Perfection:** the low of bar 8 or bar 9 (or a later bar) must be < the lows of both bars 6 and 7. Until perfection, the expected reaction "is less likely".
- Expected effect: "price has a tendency to at least react to the upside or move sideways". The setup is momentum-based.

**Sell Setup:** the mirror image (close > close[4]; perfection when the high of bar 8 or 9 > the highs of bars 6 and 7).

**Buy Countdown** (trend-based)
- **Begins on Setup bar 9 itself.**
- A count is recorded when close ≤ low two bars earlier. Counted bars need not be consecutive.
- **Completion at 13**, with the **qualifier**: the low of Countdown bar 13 ≤ the close of Countdown bar 8. Otherwise the 13 is deferred; the asterisks in Fig. 1 mark deferred bars.
- **Cancellation:**
  - (a) after Setup completion, a bar's low **and** the prior bar's close are both above the highest price of the entire buy Setup;
  - (b) an opposite (sell) Setup appears before the Countdown completes.
- **Recycle:** if a new buy Setup extends to ≥ 18 consecutive qualifying closes before the Countdown completes, the Countdown "recycles".

**Sell Countdown:** the mirror image (close ≥ high two bars earlier; the high of bar 13 ≥ the close of bar 8).

**Frequency claim:** on daily charts, completed 13s coincide with a top or bottom "approximately four or five times a year". On shorter time frames the number increases "commensurately".

**FX session convention:** for cash FX, use the New York close (22:00 London) as the end of the day.

## Claims (SOURCE, unverified)
- "Markets trend 25–30 % of the time, and are in ranges 70–75 %." Stated as "research proves"; **no citation**.
- FX used to trend because of coordinated central-bank policy. That interdependency has "diminished", so FX now behaves like other markets.
- Liquidity providers (specialists, MMs, desks) position against the trend. "Their collective countertrend activities are responsible for price exhaustion periods."
  - INFERENCE: this is consistent with inventory-based market-making theory (S10, S06), but the article does not test it.
- Endorsement by named bank strategists (UBS, Westpac, …). This is an authority claim, **not evidence**.

## Critical assessment
- **Selection bias:** the three hand-picked 2004 daily charts show the successes.
- **No base rate:** the article does not report how often 9s or 13s fail.

**Discrepancies vs NEXA's frozen 8E implementation** (`research/nexa_8e_engines.td_sequential`, read 2026-10-01). These are FACTS about the code vs this spec.

| # | Source spec | NEXA 8E code |
|---|---|---|
| 1 | Price flip uses **≥ / ≤** | Strict **> / <** (`c[t−1] > c[t−5]`) |
| 2 | Countdown counts **from Setup bar 9 inclusive** | Excludes the bar where count == 9 (`buy_count != 9`) |
| 3 | Bar-13 **qualifier** (low₁₃ ≤ close₈) | Not implemented: 13 is declared at the 13th count |
| 4 | Cancellation (a): price trades above the whole Setup range | Not implemented (only (b), the opposite setup) |
| 5 | Recycle at an 18-bar Setup | Not implemented: NEXA resets the setup count after 9, so it cannot see 18 |
| 6 | Perfection for Setup reactions | Not implemented |

The prior 8E Deep Research report already noted that TDST, perfection and recycling were omitted. The flip-inequality and countdown-start differences (1, 2) were not previously listed.

**Consequence (INFERENCE):** the 8E DEV verdict "TD 8/9/13 veto CONTRADICTED (adds no information)" applies to the **simplified** implementation used as an exhaustion *veto* on breakout signals. It is **not** a test of canonical TD Sequential as a countertrend *entry* system.

## NEXA relevance
- **Hypothesis (backlog):** canonical TD Sequential, with the qualifier, perfection, cancellation and recycle, as a **countertrend entry** on daily and H4 bars.
  - Measure the reversal / sideways base rate after perfected 9s and qualified 13s vs random bars, with costs.
  - Requires a new frozen protocol. **Do not modify the frozen 8E code.**
- **The "25–30 % trending" claim** is testable: regime-classification share on NEXA data (variance-ratio / Hurst; see S15 Boeker's mean reversion and scaling).

**Cross-references:** S15 (FX mean reversion), S10 / S06 (MM inventory), S22 (151 Strategies: contrarian strategies), S09 (Bollinger reversals), S01 (Forex Essentials).
