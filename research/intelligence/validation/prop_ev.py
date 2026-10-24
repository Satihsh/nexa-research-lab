"""H-PROP-EV: Monte Carlo of Apex 50K evaluation + Performance Account (PA) payouts.

Pre-registration: PREREG_PROP_EV.md. Rules: APEX_RULES_SNAPSHOT_2026-10-18.md. No market data.
Usage: python3 prop_ev.py [out.json]   (full pre-registered grid, run once)
"""
import json
import sys
import time

import numpy as np

START = 50_000.0
TARGET_BAL = 53_000.0
DD = 2_000.0
EVAL_DAYS = 21
EVAL_DLL = 1_000.0          # EOD evaluation only
EVAL_CAP = 53_000.0         # threshold stops trailing here (Rithmic/WealthCharts)
PA_CAP = 50_100.0           # PA threshold lock
PA_DAYS = 250
SAFETY_NET = 52_100.0
MIN_REQ_BAL = 52_600.0
MIN_PAYOUT = 500.0
MAX_PAYOUTS = 6
MIN_QUAL_DAYS = 5
MIN_DAILY = {'EOD': 250.0, 'INTRA': 200.0}
CAPS = {'EOD': [1500, 1500, 2000, 2500, 2500, 3000], 'INTRA': [1500, 2000, 2500, 2500, 3000, 3000]}
STOP_PTS = 25.0
FEES = {  # (eval fee, activation fee)
    'F-LIST': {'EOD': (197.0, 99.0), 'INTRA': (131.0, 79.0)},
    'F-COUPON': {'EOD': (19.70, 99.0), 'INTRA': (13.10, 79.0)},
    'F-ZERO-ACT': {'EOD': (19.70, 0.0), 'INTRA': (13.10, 0.0)},
}
MU_GRID = [-0.10, -0.08, -0.045, -0.04, 0.0, 0.025, 0.05, 0.10, 0.15, 0.20, 0.30]
B_GRID = [1.0, 1.52, 2.0]
RISK_GRID = [250.0, 500.0, 750.0]
K_GRID = [1, 3]
DTYPES = ['EOD', 'INTRA']
COST_R = 2.0 / STOP_PTS     # S1 = 2 NQ points round trip
N_SIMS = 10_000
SEED = 20261018


def p_win(mu, b, c):
    """Win probability so that p*(b-c) - (1-p)*(1+c) = mu."""
    return (mu + 1.0 + c) / (b + 1.0)


def loss_peak(u, b):
    """Peak excursion (R) before the stop, driftless BM conditioned on hitting -1 before +b."""
    return b * (1.0 - u) / (1.0 + u * b)


def win_dip(u, b):
    """Deepest excursion depth k (R, positive) before the target, conditioned on hitting +b first."""
    return b * (1.0 - u) / (u + b)


def eod_threshold(prev_thr, peak_close, cap):
    return np.maximum(prev_thr, np.minimum(peak_close - DD, cap))


def dll_for_profit(profit):
    """PA 50K tier DLL from the previous close's profit."""
    return np.where(profit < 3000, 1000.0, np.where(profit < 6000, 2000.0, 3000.0))


def consistency_ok(max_day, net):
    return (net > 0) & (max_day <= 0.5 * net + 1e-9)


def payout_amount(bal, k, dtype):
    """Amount for payout number k (0-based); 0 if below the minimum."""
    cap = CAPS[dtype][k]
    amt = min(cap, bal - SAFETY_NET)
    return amt if amt >= MIN_PAYOUT else 0.0


def _trade(rng, m, bal, thr, peak, dll_level, dtype, cap, b, risk, c, p):
    """One bracket trade for accounts in mask m. Updates arrays in place.
    Returns (dead, dll_hit, won) masks over the full arrays."""
    n = int(m.sum())
    dead = np.zeros(bal.shape, bool)
    dll_hit = np.zeros(bal.shape, bool)
    won = np.zeros(bal.shape, bool)
    if n == 0:
        return dead, dll_hit, won
    idx = np.nonzero(m)[0]
    w = rng.random(n) < p
    u = rng.random(n)
    b0 = bal[idx]
    th = thr[idx].copy()
    pk = peak[idx].copy()
    dl = dll_level[idx]
    intra = dtype == 'INTRA'
    # losers move up first (peak), then to the stop
    up_first = np.where(w, 0.0, loss_peak(u, b))
    if intra:
        hi = b0 + up_first * risk
        pk = np.maximum(pk, hi)
        th = np.maximum(th, np.minimum(pk - DD, cap))
    low = np.where(w, b0 - win_dip(u, b) * risk, b0 - risk * (1.0 + c))
    acc_dead = (low <= th) & (th >= dl)
    acc_dll = (low <= dl) & ~acc_dead
    exit_val = np.where(w, b0 + risk * (b - c), b0 - risk * (1.0 + c))
    newbal = np.where(acc_dead, th, np.where(acc_dll, dl, exit_val))
    if intra:
        ok_win = w & ~acc_dead & ~acc_dll
        pk = np.where(ok_win, np.maximum(pk, b0 + b * risk), pk)
        th = np.where(ok_win, np.maximum(th, np.minimum(pk - DD, cap)), th)
    bal[idx] = newbal
    thr[idx] = th
    peak[idx] = pk
    dead[idx] = acc_dead
    dll_hit[idx] = acc_dll
    won[idx] = w & ~acc_dead & ~acc_dll
    return dead, dll_hit, won


def run_eval(rng, n, dtype, b, risk, k_trades, mu, c):
    p = p_win(mu, b, c)
    bal = np.full(n, START)
    thr = np.full(n, START - DD)
    peak = np.full(n, START)
    alive = np.ones(n, bool)
    passed = np.zeros(n, bool)
    days = np.zeros(n, int)
    for _ in range(EVAL_DAYS):
        act = alive & ~passed
        if not act.any():
            break
        days[act] += 1
        dll_level = np.where(act, bal - EVAL_DLL, -np.inf) if dtype == 'EOD' else np.full(n, -np.inf)
        trading = act.copy()
        consec = np.zeros(n, int)
        for _t in range(k_trades):
            if not trading.any():
                break
            dead, dll_hit, won = _trade(rng, trading, bal, thr, peak, dll_level, dtype, EVAL_CAP, b, risk, c, p)
            alive &= ~dead
            consec = np.where(trading, np.where(won, 0, consec + 1), consec)
            hit = trading & ~dead & (bal >= TARGET_BAL)
            passed |= hit
            trading &= ~dead & ~dll_hit & ~hit & (consec < 3)
        if dtype == 'EOD':
            live = alive & ~passed
            peak = np.where(live, np.maximum(peak, bal), peak)
            thr = np.where(live, eod_threshold(thr, peak, EVAL_CAP), thr)
    return passed, days


def run_pa(rng, n, dtype, b, risk, k_trades, mu, c):
    p = p_win(mu, b, c)
    bal = np.full(n, START)
    thr = np.full(n, START - DD)
    peak = np.full(n, START)
    alive = np.ones(n, bool)
    total = np.zeros(n)
    npay = np.zeros(n, int)
    qual = np.zeros(n, int)
    net = np.zeros(n)
    maxday = np.zeros(n)
    days = np.zeros(n, int)
    minq = MIN_DAILY[dtype]
    caps = np.array(CAPS[dtype], float)
    for _ in range(PA_DAYS):
        if not alive.any():
            break
        days[alive] += 1
        day_start = bal.copy()
        dll_level = np.where(alive, day_start - dll_for_profit(day_start - START), -np.inf)
        trading = alive.copy()
        consec = np.zeros(n, int)
        for _t in range(k_trades):
            if not trading.any():
                break
            dead, dll_hit, won = _trade(rng, trading, bal, thr, peak, dll_level, dtype, PA_CAP, b, risk, c, p)
            alive &= ~dead
            consec = np.where(trading, np.where(won, 0, consec + 1), consec)
            trading &= ~dead & ~dll_hit & (consec < 3)
        if dtype == 'EOD':
            peak = np.where(alive, np.maximum(peak, bal), peak)
            thr = np.where(alive, eod_threshold(thr, peak, PA_CAP), thr)
        pnl = np.where(alive, bal - day_start, 0.0)
        qual += (alive & (pnl >= minq)).astype(int)
        net += pnl
        maxday = np.where(alive & (pnl > 0), np.maximum(maxday, pnl), maxday)
        elig = alive & (qual >= MIN_QUAL_DAYS) & consistency_ok(maxday, net) & (bal >= MIN_REQ_BAL) & (npay < MAX_PAYOUTS)
        if elig.any():
            cap_now = caps[np.minimum(npay, MAX_PAYOUTS - 1)]
            amt = np.minimum(cap_now, bal - SAFETY_NET)
            elig &= amt >= MIN_PAYOUT
            bal = np.where(elig, bal - amt, bal)
            total = np.where(elig, total + amt, total)
            npay = np.where(elig, npay + 1, npay)
            qual = np.where(elig, 0, qual)
            net = np.where(elig, 0.0, net)
            maxday = np.where(elig, 0.0, maxday)
            alive &= npay < MAX_PAYOUTS
    return total, npay, days


def cell(dtype, b, risk, k_trades, mu, n=N_SIMS, seed=SEED, c=COST_R):
    rng = np.random.default_rng([seed, DTYPES.index(dtype), B_GRID.index(b) if b in B_GRID else 9,
                                 int(risk), k_trades, int(round((mu + 1) * 10000))])
    passed, edays = run_eval(rng, n, dtype, b, risk, k_trades, mu, c)
    npass = int(passed.sum())
    if npass:
        tot, npay, pdays = run_pa(rng, npass, dtype, b, risk, k_trades, mu, c)
    else:
        tot, npay, pdays = np.zeros(0), np.zeros(0, int), np.zeros(0, int)
    pp = npass / n
    e_pa = float(tot.mean()) if npass else 0.0
    e_att = pp * e_pa
    out = {
        'dtype': dtype, 'b': b, 'risk': risk, 'K': k_trades, 'mu': mu, 'p_win': p_win(mu, b, c),
        'p_pass': pp, 'eval_days_mean': float(edays.mean()),
        'pa_p_any_payout': float((npay > 0).mean()) if npass else 0.0,
        'pa_e_payouts': e_pa, 'pa_mean_n_payouts': float(npay.mean()) if npass else 0.0,
        'pa_p_six': float((npay == MAX_PAYOUTS).mean()) if npass else 0.0,
        'pa_days_mean': float(pdays.mean()) if npass else 0.0,
        'e_payout_per_attempt': e_att,
        'p_any_payout_per_attempt': pp * (float((npay > 0).mean()) if npass else 0.0),
    }
    for fs, fees in FEES.items():
        ev, act = fees[dtype]
        cost = ev + pp * act
        out['net_' + fs] = e_att - cost
        out['ratio_' + fs] = e_att / cost if cost > 0 else None
    return out


def main(path):
    t0 = time.time()
    rows = []
    for dtype in DTYPES:
        for b in B_GRID:
            for risk in RISK_GRID:
                for k in K_GRID:
                    for mu in MU_GRID:
                        rows.append(cell(dtype, b, risk, k, mu))
    summary = {}
    for fs in FEES:
        for dtype in DTYPES:
            for mu in MU_GRID:
                sub = [r for r in rows if r['dtype'] == dtype and r['mu'] == mu]
                best = max(sub, key=lambda r: r['net_' + fs])
                summary[f'{fs}|{dtype}|{mu}'] = {
                    'best_net': best['net_' + fs], 'best_cfg': [best['b'], best['risk'], best['K']],
                    'best_p_pass': best['p_pass'], 'best_e_payout_attempt': best['e_payout_per_attempt'],
                    'n_cfg_positive': sum(1 for r in sub if r['net_' + fs] > 0)}
    q = {}
    for fs in FEES:
        for dtype in DTYPES:
            q[f'Q1|{fs}|{dtype}'] = summary[f'{fs}|{dtype}|-0.08']['best_net'] > 0
            q[f'Q2|{fs}|{dtype}'] = summary[f'{fs}|{dtype}|-0.045']['best_net'] > 0
            pos = [mu for mu in MU_GRID if summary[f'{fs}|{dtype}|{mu}']['best_net'] > 0]
            q[f'Q3|{fs}|{dtype}'] = min(pos) if pos else None
    res = {'prereg': 'PREREG_PROP_EV.md', 'n_sims': N_SIMS, 'seed': SEED, 'cost_R': COST_R,
           'runtime_s': round(time.time() - t0, 1), 'questions': q, 'summary': summary, 'cells': rows}
    with open(path, 'w') as f:
        json.dump(res, f, indent=1)
    print(json.dumps({'questions': q, 'runtime_s': res['runtime_s']}, indent=1))


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'prop_ev_results.json')
