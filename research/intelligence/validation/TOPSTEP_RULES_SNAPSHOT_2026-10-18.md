# Topstep rules snapshot (read 2026-10-18)

**Why this file:** the user plans to use **Topstep**, not Apex (user, 2026-10-18). H-PROP-EV and the H-SWING notes assumed Apex. That was NEXA's assumption, not the user's choice. These are the Topstep rules relevant to NEXA so far, paraphrased from Topstep's own pages, fetched live 2026-10-18.

| Rule | Topstep (paraphrased) | Source |
|---|---|---|
| Holding overnight / swing trading | **Not allowed.** Topstep calls itself a day-trading program. All positions must be flat by **3:10 PM CT** each weekday (or the product's earlier close); risk managers start flattening at 3:08 PM. The FAQ answers "can I swing trade or hold overnight?" with **No**. | help.topstep.com, "When and What Products Can I Trade?" (article dated 2026-07-13) |
| Express Funded Account (XFA) close | Same 3:10 PM CT (or product close) rule | topstep.com/express-funded-account-rules (last updated 2025-06-26) |
| Live Funded Account | Topstep auto-flattens about 10 seconds before 3:10 PM CT | topstep.com/live-funded-account-rules |
| XFA Max Loss Limit | $2,000 (50K), $3,000 (100K), $4,500 (150K), trailing from the highest end-of-day balance; the account closes permanently if hit | XFA rules page |
| XFA payouts | Standard: 5 winning days of $150+, up to 50 % of balance (max $5,000), 90/10 split. Consistency XFA: ≥ 3 days, 40 % consistency target, max $6,000 | XFA rules page |
| Max active XFAs | 5 | XFA rules page |
| Back2Funded reactivation | $599 (50K) / $699 (100K) / $829 (150K), up to 2 times, before the first payout only | XFA rules page |
| Products | CME equity index (incl. MES, MNQ, M2K, MYM), FX futures, energy, metals, grains, rates. **No spot forex.** | help article above |

## Consequences for NEXA
1. **H-SWING (daily trend-following) cannot run at Topstep either.** Positions are held for weeks to months; Topstep forbids holding across sessions. Any use of a trend rule needs an own futures account (FCM), which falls under the user's capital rule (tested + forward demo first, then a capital review).
2. **The prop route at Topstep requires an intraday edge.** No NEXA intraday rule has passed so far.
3. **H-PROP-EV used Apex fees and rules.** Its +0.025R threshold is Apex-specific. A Topstep version (Combine fees, XFA loss limit, payout rules) would be a separate pre-registration. It has not been done. Combine prices and Combine rules were **not** read for this snapshot.
