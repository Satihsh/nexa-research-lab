# Apex Trader Funding: rules snapshot for H-PROP-EV (read 2026-10-18)

- Read live (Firecrawl, `maxAge: 0`) from Apex's own help centre on 2026-10-18, before any simulation.
- Rules apply to the **new products (after 2026-03-01)**. Legacy accounts are not modelled.
- Only the **50K** account size is modelled.
- "Page modified" is the page's own `article:modified_time`.

## Sources (official)
| Topic | URL | Page modified |
|---|---|---|
| EOD Evaluation | https://apextraderfunding.com/help-center/eod-trailing-drawdown-accounts/eod-evaluations/ | (search excerpt) |
| Intraday Evaluation | https://apextraderfunding.com/help-center/evaluation-accounts-ea/intraday-trailing-drawdown-evaluations/ | (search excerpt) |
| EOD drawdown mechanics | https://apextraderfunding.com/help-center/eod-trailing-drawdown-accounts/eod-drawdown-explained/ | 2026-04-28 |
| EOD Performance Account | https://apextraderfunding.com/help-center/eod-trailing-drawdown-accounts/eod-performance-accounts-pa/ | 2026-04-28 |
| Intraday PA | https://apextraderfunding.com/help-center/intraday-trailing-drawdown-accounts/intraday-trailing-drawdown-performance-accounts-pa/ | (search excerpt) |
| EOD payouts | https://apextraderfunding.com/help-center/eod-trailing-drawdown-accounts/eod-payouts/ | (search excerpt) |
| Intraday payouts | https://apextraderfunding.com/help-center/intraday-trailing-drawdown-accounts/intraday-trailing-drawdown-payouts/ | (search excerpt) |
| 50 % consistency | https://apextraderfunding.com/help-center/additional-helpful-items/50-consistency-requirement/ | 2026-04-24 |
| Scaling tiers | https://apextraderfunding.com/help-center/additional-helpful-items/scaling-levels-pa-explained/ | 2026-04-16 |
| Daily loss limit | https://apextraderfunding.com/help-center/additional-helpful-items/daily-loss-limit-explained/ | 2026-04-15 |
| PA activation | https://apextraderfunding.com/help-center/billing/pa-activation-process-deadline-explained/ | (search excerpt) |
| Prohibited activities | https://apextraderfunding.com/help-center/getting-started/prohibited-activities/ | 2026-07-31 |
| Home / product picker | https://apextraderfunding.com/ | 2026-10-15 |

## 50K Evaluation (both drawdown types)
- **Profit target:** $3,000.
- **Max drawdown:** $2,000.
- **Max contracts:** 6.
- **Access:** 30 calendar days.
- **No minimum days.** Passing is possible in one day, as soon as the target is reached.
- **No consistency rule. No scaling.**
- **No resets.** A failed evaluation means buying a new one.
- **EOD type:**
  - The threshold is recalculated once per day at 16:59:59 ET from the highest EOD balance, and is enforced in real time in the next session. It never moves down.
  - **Daily loss limit (DLL) $1,000, fixed.** Hitting it pauses trading for the day; it does not fail the account.
  - Rithmic / WealthCharts: the threshold stops trailing at $53,000. Tradovate: it trails indefinitely.
- **Intraday type:** the threshold trails the peak balance **including unrealised gains**, in real time. No DLL.
- **No hedging across evaluations.**
- **PA activation:** must be paid within 7 calendar days of passing. One-time fee, non-refundable.

## 50K Performance Account (PA; simulated funded)
- **Max drawdown $2,000.**
  - EOD type: the threshold trails the highest EOD balance.
  - Intraday type: the threshold trails the peak including unrealised gains.
  - **Both stop trailing once the threshold reaches $50,100** (i.e. after a peak of $52,100).
- **Scaling tiers** (from end-of-day profit):

  | Profit range | Max contracts | DLL | Tier |
  |---|---|---|---|
  | $0–1,499 | 2 | $1,000 | L1 |
  | $1,500–2,999 | 3 | $1,000 | L2 |
  | $3,000–5,999 | 4 | $2,000 | L3 |
  | ≥ $6,000 | 4 | $3,000 | L4 |

  - 10 micros = 1 mini.
  - Tiers never fall below L1.
  - The DLL pauses the day; it does not close the account.
- **Up to 20 PAs** at once.
- **Inactivity:** at least two $50 profit days per 30 calendar days (Intraday PA page).
- **No overnight positions.**

### Payouts (50K)
| | EOD PA | Intraday PA |
|---|---|---|
| Minimum qualifying days (each ≥ min daily profit) | 5 | 5 |
| Minimum daily profit | **$250** | **$200** |
| Safety net (drawdown + $100) | $52,100 | $52,100 |
| Minimum balance to request | $52,600 | $52,600 |
| Minimum payout | $500 | $500 |
| Maximum payouts per PA | 6 | 6 |
| Cap per request, #1–#6 | 1,500 / 1,500 / 2,000 / 2,500 / 2,500 / 3,000 | 1,500 / 2,000 / 2,500 / 2,500 / 3,000 / 3,000 |

- **Split: 100 %.**
- **Payout frequency:** up to weekly ("5 trading days between rewards").
- **50 % consistency:** the largest profitable day since the last approved payout must be < 50 % of the **net** profit since that payout. Losing days reduce the net. The calculation resets after each approved payout. If net profit is ≤ 0, the trader is not eligible.
- "After the sixth payout, the account completes its payout cycle."
- **Live transfer is by invitation only.** The Apex founder (SRC-YT-123): "maybe 1.5–2 %" of traders.

## Fees
- **Official page (2026-10-18):** the product picker shows **only the 25K Intraday price by default**:
  - $167.00 list, **$16.70 "with coupon code"** (i.e. 90 % off);
  - 5-pack $374.80, or $37.48 with the coupon;
  - **PA activation fee $89** (25K).
  - The 50K prices are rendered client-side and were not readable.
- **Secondary source** (phidiaspropfirm.com, a *competitor's* page, 2026):
  - **50K EOD: eval $197 + activation $99.**
  - **50K Intraday: eval $131 + activation $79.**
- **"No Activation Fee" evaluations** exist (activation $0) at an unstated higher eval price.
- Fees are therefore treated as **scenarios**, and the **break-even fee** is reported for every cell.

## Prohibited activities relevant to NEXA (verbatim headings)
- "**No Automation or Algorithm Usage allowed**". A human must place the trades. A mechanical plan executed by hand is the only compliant form.
- "**Stockpiling Evaluation Accounts:** Purchasing multiple discounted evaluation accounts to cycle through and intentionally 'blow up' accounts in pursuit of windfall profits is not permitted."
- "**High-Risk Strategies:** small profit targets while risking disproportionately large amounts" (example: 5-tick target, 150-tick stop).
- "**Using the Trailing Threshold as a Stop Loss**", "**Unsustainable Strategies**", "**No Hedging of Any Kind**", no trade copying with others.
- "Holding open trade positions through the market close" is prohibited.
