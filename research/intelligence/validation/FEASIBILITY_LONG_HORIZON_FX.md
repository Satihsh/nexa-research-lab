# Feasibility check: long-horizon (daily+) FX strategies for NEXA (2026-10-11)

**Approval:** user, "Approved 1 and 3".
- Read-only.
- **No strategy outcome was computed.**
- No data was bought or downloaded, and MT5 was not touched.
- Inputs:
  - Pepperstone D1 files and `contracts.json` (2026-10-01 spec snapshot) on disk;
  - power arithmetic;
  - one literature search (Exa).

**Correction to the step-3 suggestion.** Daily trend-following was proposed as a candidate, but it **was already tested and REJECTED as C2** (`C2_REPORT.md`): daily TSMOM on 8 instruments, 2001–2026, all 16 cells negative net; ex-swap +0.12 %/mo, not significant. So it is **not** a candidate. The only untested long-horizon idea is **carry**.

## 1. Data inventory

| Item | Status |
|---|---|
| Pepperstone D1 prices | **On disk, 2000-01 → 2026-09** for the G10 USD pairs and XAU (USDNOK from 2006); ~97 FX symbols in total |
| D1 `spread` column | **Unusable for costs:** a flat 40–50 points before 2010 (placeholder) and 0 after 2020. Costs would need the M1-derived spreads (2017+ only) or an assumption |
| Historical swap / interest-rate differentials | **Not on disk.** Only today's swap snapshot (`contracts.json`). Applying it across decades was C2's methodological failure |
| Free rate-history sources (identified, **not downloaded**) | FRED / OECD 3-month interbank series per country (monthly); BIS central-bank policy rates. Collecting them is **new data collection and needs approval** |
| Contamination | The same 2000–2026 D1 price history was used by C2. A carry test would reuse seen price data with a new signal (disclosure required) |

## 2. Pepperstone's financing markup (2026-10 snapshot, % of notional per year)

Swap points per lot per night, converted at the last D1 close (× 365 nights, triple Wednesday included). For a symmetric financing schedule, the markup per side is −(long + short)/2.

| Pair | Long % p.a. | Short % p.a. | **Markup per side** | Implied rate differential |
|---|---|---|---|---|
| EURUSD | −2.36 | +0.48 | **0.94** | −1.42 |
| GBPUSD | −0.94 | −0.49 | **0.71** | −0.23 |
| AUDUSD | −0.45 | −1.05 | **0.75** | +0.30 |
| NZDUSD | −2.12 | +0.41 | **0.86** | −1.26 |
| USDJPY | +0.70 | −3.62 | **1.46** | +2.16 |
| USDCAD | +1.03 | −2.61 | **0.79** | +1.82 |
| USDCHF | +2.23 | −5.00 | **1.38** | +3.61 |
| USDNOK | −1.52 | −0.47 | **1.00** | −0.52 |
| USDSEK | +1.22 | −3.19 | **0.99** | +2.21 |
| XAUUSD | −7.37 | +2.76 | **2.31** | — |

**Reading:**
- A retail carry position at Pepperstone pays **≈ 0.7–1.5 % a year per position** above the interbank differential.
- For a position run at 10 % volatility, that is a **Sharpe haircut of ≈ 0.07–0.15** before any spread or commission.
- The best-yielding legs are also where the markup is largest (JPY, CHF funding: 1.4–1.5 %).
- The markup history is unknown. Today's markup is a lower bound only if the broker has not reduced its markups over time.

## 3. Literature prior (post-2008 decay)

- **Fan, Paseka, Qi & Zhang (2022, J. Int. Financial Markets, Institutions & Money 76, 101460):** a documented decline in carry performance after the 2008 GFC, attributed to the disappearance of downside-risk compensation.
- **Danso & Refalo (2025, JRFM 18(4):190):** G10 carry and covered interest arbitrage. Profits are concentrated pre-crisis, most losses post-crisis.
- **Bilkent working paper** (dollar vs dollar-neutral carry, 2004–2019): dollar-based carry Sharpe ≈ 0.04 after the crisis.
- **Koijen, Moskowitz, Pedersen & Vrugt (NBER w19325):** carry predicts returns across asset classes, with crashes concentrated in global recessions. The strong results rely on **broad multi-asset universes**, not a handful of USD pairs.
- **Honest prior for G10 carry after 2009:** an annual Sharpe of ≈ 0–0.3 gross. After the Pepperstone markup, ≈ −0.1 to +0.2.

## 4. Statistical power (annual Sharpe; one-sided α = 0.05)

| Evaluation span | Years | MDE Sharpe (80 % power) | Power if true SR = 0.2 | 0.3 | 0.5 |
|---|---|---|---|---|---|
| 2000-01 → 2026-09 (all) | 26.7 | **0.48** | 0.27 | 0.46 | 0.83 |
| Post-GFC 2009 → 2026-09 | 17.7 | **0.59** | 0.21 | 0.35 | 0.68 |
| 2020 → 2026-09 (holdout-sized) | 6.7 | **0.96** | 0.13 | 0.19 | 0.36 |
| COMMON holdout 2025 → 2026-09 | 1.7 | 1.91 | 0.08 | 0.10 | 0.16 |

**Reading:**
- The NEXA discipline needs a positive holdout and a pooled CI above 0. With a realistic post-2008 net Sharpe of ≤ 0.2–0.3, **the chance of passing is ≈ 10–35 % even if the edge is real**.
- The detectable effect (SR 0.5–1.0) is 2–5× the plausible effect. A pass would be suspect, and a failure uninformative.

## 5. Verdict

**NOT FEASIBLE: do not pre-register a carry test on this data.**
1. Trend-following is already rejected (C2).
2. Carry's post-2008 edge is small (literature) and Pepperstone's financing markup takes ≈ 0.07–0.15 Sharpe.
3. 26 years of a ≤ 10-pair USD universe cannot detect a Sharpe below ≈ 0.5. The holdout cannot detect below ≈ 1.0.
4. It would also need new rate-history data (approval) and reuse price history already seen in C2.

**What would change this:**
- a materially larger cross-section (e.g. 30+ currencies including EM, where the carry literature is stronger, but with EM crash risk, wider spreads and larger swap markups), or
- an institutional cost / financing venue.

Neither fits the current NEXA (MT5 / Pepperstone) setup. Recorded as **G1-BLOCKED (power / cost)** in RESEARCH_GATE.
