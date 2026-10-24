# H-SWING clarifications and deviations

## C-1: execution lag wording (recorded 2026-10-18, before any code was written or data read)
- **The problem:** PREREG_SWING_TREND §2 says the new weight "earns returns from the **next** trading day's close-to-close return onward (one-day implementation lag; no same-day fill)". This can be read as either:
  - (a) filled at the close of decision day t, earning r_{t+1} = C_{t+1}/C_t − 1; or
  - (b) filled at the close of the next day t+1, earning from r_{t+2}.
- The parenthetical "no same-day fill" rules out (a).
- **Binding reading (b):**
  - a weight decided at the close of day t is **executed at the close of day t+1**, so that day's trading cost is priced at C_{t+1};
  - it is first exposed to the return r_{t+2} = C_{t+2}/C_{t+1} − 1.
- This applies to P and every variant, including LONG-only.
- (b) is the more conservative choice. It is fixed before any result exists.

## C-2: "valid weight" for N_t
- A market counts in N_t on day t once it has passed warm-up: ≥ 252 + 60 bars at the decision that set its held position.
- For V-DON and V-MA a flat (0) position after warm-up still counts as valid and active. Flat is a decision.
- For P, a warmed-up market's s = 0 (zero log return over 252 days) also counts as active with weight 0.
