# S38: Ki Hoon Hong, "Modelling Intervalling Effect of High Frequency Trading on Portfolio Volatility" (Theoretical Economics Letters 9, 2019, 2362–2370)

**File:** `tel_2019092615201272.pdf`. 9 pp. Hongik University. doi:10.4236/tel.2019.97150.

| Field | Value |
|---|---|
| **Source type** | Other academic institution. Peer-reviewed, open-access journal (SCIRP; low-tier). |
| **Evidence status** | **Theoretical claim; contradicted by our analysis** (the central result is a normalisation artefact). No empirical test. |
| **Processing** | All 9 pages read. The text extraction garbles the maths, so pp. 3, 4 and 7 (model, Remark 1 / Prop 1, Appendix A) were **rendered and read visually**. Appendix B (p. 8–9) was followed from the extracted symbols: its structure is sign-arguments on a(h), b(h), s(h). |

## 1. Model (SOURCE; verified on rendered pp. 3–4)
- **Price process:** the de-meaned log price q(t) = log p(t) − μt follows an OU process: dq = −θq dt + σdW (eq. 1).
- **Solution:** q(t+h) = e^{−θ(t+h)}q(0) + σ∫₀^{t+h} e^{−θ(t−u)}dW(u) (eq. 2, printed as written).
- **Variance (eq. 3):** Var q(t+h) = σ_q²(h) = ((1 − e^{−2θ(t+h)})/(2θ))σ².
- **MA rule (Def. 1, eq. 4):**
  - position = max(δ(t), 0), with δ = 1 if LMA(t) − SMA(t) > 0;
  - LMA is the l-period mean and SMA the s-period mean, with s > l.
  - So the "L" MA is the *shorter* window, which inverts the usual naming; it is a long-only momentum rule.
- **Remark 1 (eq. 5):** "unit-period variance of buy-and-hold" σ²_BH(h) = (1/h)·σ_q²(h) = ((1 − e^{−2θ(t+h)})/(2θ))·σ²/h.
- **Proposition 1:** ∂σ²_BH/∂h < 0. The author's reading: shorter trading intervals raise portfolio volatility.
- **MA "critical value" (eq. 6):** C(s, l; t) = LMA/SMA = exp(w′Q(t)), with w′ = ((1/l − 1/s)…, −1/s…) and Q = (q(t)…q(t−s+1)).
  - **Proposition 2:** the unit-period variance of C falls with h, so a faster MA rule is "more volatile".
- **Example scaling:** a 10-day MA corresponds to s = 2 (weekly), 10 (daily), 65 (hourly), 3,900 (minute) and 234,000 (second).

## 2. Our analysis (INFERENCE)
1. **Proposition 1 is an artefact of normalisation.**
   - σ_q²(h) is the variance of the *price level*, which is bounded (it tends to σ²/(2θ)). Dividing a bounded level variance by h makes it blow up as h → 0, whatever the market does.
   - A buy-and-hold position's P&L over a fixed horizon **does not depend on how often prices are reported or traded**. The conclusion "fast trading increases buy-and-hold portfolio volatility" does not follow.
2. **The legitimate kernel is the true intervalling effect of measured volatility under mean reversion.**
   - For an OU process, the increment variance per unit time over an interval h is σ²(1 − e^{−θh})/(θh). This tends to σ² as h → 0 and decreases in h: the variance-ratio effect.
   - So *measured* volatility depends on sampling frequency when prices mean-revert (e.g. microstructure bounce). This matches S15 (scaling, OU curvature) and the classical beta intervalling literature the paper cites (Pogue–Solnik; Dimson; Handa et al.).
3. **Eq. 6 is an approximation presented as an identity.**
   - A ratio of *arithmetic* averages of prices is not exp(w′Q). That identity holds for geometric means of p (equivalently, arithmetic means of log p).
   - The equality also ignores μt in q.
4. The variance includes the transient term e^{−2θ(t+h)} from the q(0) start, so the process is not stationary as written. That conflicts with the later stationarity assumption.
5. There is no empirical evidence, no costs and no market data. Claims about HFT causing volatility, herding and so on are background, not results.

## 3. Principles
- **SOURCE + INFERENCE:**
  - Volatility (and beta) *estimates* depend on sampling interval when returns are autocorrelated.
  - Positive autocorrelation (trend) makes long-horizon volatility exceed short-horizon volatility scaled by √h; negative autocorrelation (mean reversion, bid-ask bounce) does the reverse.
- **INFERENCE:** a strategy evaluated at one bar frequency inherits that frequency's realised-volatility level. Sizing rules calibrated on M1 volatility and applied on H1 will mis-scale unless they use the variance ratio.

## 4. NEXA relevance
- **H-VR-SCALE** (links H-HURST-GATE in S15; S23 RV):
  - Measure the variance ratio VR(k) = Var(r_k)/(k·Var(r_1)) for XAU and FX across M1→H4 on closed bars.
  - If VR(k) < 1 at short k (microstructure mean reversion), ATR or volatility measured on M1 overstates the per-unit risk relevant at M15/H1. The reverse holds if VR > 1.
  - Data: available (NEXA bars). Evidence: hypothesis.
- **Do not use:** the paper's conclusion about fast trading increasing portfolio risk.

**Cross-references:**
- S15 (OU and scaling);
- S23 (realised volatility depends on sampling);
- S04 (roughness at fine scales);
- S22 (TSMOM MA rules);
- S32 Harris (bid-ask bounce, microstructure noise).
