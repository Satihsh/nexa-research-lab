"""H-PROP-EV-TS: Monte Carlo of a Topstep 50K Trading Combine + Express Funded Account (XFA) payouts.

Pre-registration: PREREG_PROP_EV_TS.md. Rules: TOPSTEP_COMBINE_RULES_2026-10-18.md. No market data.
Trade model and per-trade engine imported unchanged from prop_ev.py (H-PROP-EV, ddd219c9).
Usage: python3 prop_ev_ts.py [out.json]   (full pre-registered grid, run once)
"""
import json
import sys
import time

import numpy as np

from prop_ev import p_win, loss_peak, win_dip, _trade, eod_threshold, DD  # noqa: F401  (unchanged H-PROP-EV engine)

START = 50_000.0
TARGET = 3_000.0
CONSIST_COMBINE = 0.55
COMBINE_LOCK = 50_000.0          # MLL locks at the starting balance
XFA_LOCK = 0.0                   # XFA MLL locks at $0
HORIZON = 250                    # trading days, Combine and XFA
FEE_BLOCK = 21                   # trading days per monthly fee
STD_WIN_DAY = 150.0
STD_DAYS = 5
STD_CAP = 2_000.0
CON_DAYS = 3
CON_PCT = 0.40
CON_CAP = 3_000.0
PAY_FRAC = 0.5
MIN_PAYOUT = 125.0
SPLIT = 0.90
WIRE_FEE = 30.0
FEES = {'F-STD': (49.0, 149.0), 'F-NOACT': (95.0, 0.0)}   # (monthly fee, activation fee)
MU_GRID = [-0.10, -0.08, -0.045, -0.04, 0.0, 0.025, 0.05, 0.10, 0.15, 0.20, 0.30]
B_GRID = [1.0, 1.52, 2.0]
RISK_GRID = [250.0, 500.0, 750.0]
K_GRID = [1, 2]
PATHS = ['STD', 'CON']
STOP_PTS = 25.0
COST_R = 2.0 / STOP_PTS
N_SIMS = 10_000
SEED = 20261018
NO_DLL = -np.inf


def combine_mll(prev, peak_close):
    """Combine MLL after a close: trails peak EOD - 2,000, never down, locks at 50,000."""
    return eod_threshold(prev, peak_close, COMBINE_LOCK)


def xfa_mll(prev, peak_close):
    """XFA MLL after a close: trails peak EOD - 2,000 from a $0 start, never down, locks at $0."""
    return eod_threshold(prev, peak_close, XFA_LOCK)


def combine_passed(profit, best_day):
    """Pass at a close: profit >= target and best day <= 55 % of profit (= raised target best/0.55)."""
    return (profit >= TARGET - 1e-9) & (best_day <= CONSIST_COMBINE * profit + 1e-9)


def fee_months(days):
    return np.ceil(np.maximum(days, 1) / FEE_BLOCK)


def std_eligible(win_days, net, npay, amount):
    return (win_days >= STD_DAYS) & ((npay == 0) | (net > 0)) & (amount >= MIN_PAYOUT)


def con_eligible(n_days, net, best_day, amount):
    return (n_days >= CON_DAYS) & (net > 0) & (best_day <= CON_PCT * net + 1e-9) & (amount >= MIN_PAYOUT)


def payout_amount(bal, path):
    return np.minimum(PAY_FRAC * bal, STD_CAP if path == 'STD' else CON_CAP)


def run_combine(rng, n, b, risk, k_trades, mu, c):
    p = p_win(mu, b, c)
    bal = np.full(n, START)
    thr = np.full(n, START - DD)
    peak = np.full(n, START)
    dll = np.full(n, NO_DLL)
    alive = np.ones(n, bool)
    passed = np.zeros(n, bool)
    days = np.zeros(n, int)
    best = np.zeros(n)
    for _ in range(HORIZON):
        act = alive & ~passed
        if not act.any():
            break
        days[act] += 1
        day_start = bal.copy()
        trading = act.copy()
        for _t in range(k_trades):
            if not trading.any():
                break
            dead, _, _ = _trade(rng, trading, bal, thr, peak, dll, 'EOD', COMBINE_LOCK, b, risk, c, p)
            alive &= ~dead
            prof = bal - START
            today = bal - day_start
            done = trading & ~dead & combine_passed(prof, np.maximum(best, today))
            trading &= ~dead & ~done
        live = act & alive
        today = bal - day_start
        best = np.where(live & (today > 0), np.maximum(best, today), best)
        passed |= live & combine_passed(bal - START, best)
        still = live & ~passed
        peak = np.where(still, np.maximum(peak, bal), peak)
        thr = np.where(still, combine_mll(thr, peak), thr)
    return passed, days


def run_xfa(rng, n, path, b, risk, k_trades, mu, c):
    p = p_win(mu, b, c)
    bal = np.zeros(n)
    thr = np.full(n, -DD)
    peak = np.zeros(n)
    dll = np.full(n, NO_DLL)
    alive = np.ones(n, bool)
    cash = np.zeros(n)
    npay = np.zeros(n, int)
    win_days = np.zeros(n, int)
    n_days = np.zeros(n, int)
    net = np.zeros(n)
    best = np.zeros(n)
    days = np.zeros(n, int)
    for _ in range(HORIZON):
        if not alive.any():
            break
        days[alive] += 1
        day_start = bal.copy()
        trading = alive.copy()
        for _t in range(k_trades):
            if not trading.any():
                break
            dead, _, _ = _trade(rng, trading, bal, thr, peak, dll, 'EOD', XFA_LOCK, b, risk, c, p)
            alive &= ~dead
            trading &= ~dead
        live = alive
        today = np.where(live, bal - day_start, 0.0)
        n_days += live.astype(int)
        win_days += (live & (today >= STD_WIN_DAY)).astype(int)
        net += today
        best = np.where(live & (today > 0), np.maximum(best, today), best)
        peak = np.where(live, np.maximum(peak, bal), peak)
        thr = np.where(live, xfa_mll(thr, peak), thr)
        amt = payout_amount(bal, path)
        if path == 'STD':
            elig = live & std_eligible(win_days, net, npay, amt)
        else:
            elig = live & con_eligible(n_days, net, best, amt)
        if elig.any():
            bal = np.where(elig, bal - amt, bal)
            cash = np.where(elig, cash + SPLIT * amt - WIRE_FEE, cash)
            npay = np.where(elig, npay + 1, npay)
            thr = np.where(elig, 0.0, thr)
            win_days = np.where(elig, 0, win_days)
            n_days = np.where(elig, 0, n_days)
            net = np.where(elig, 0.0, net)
            best = np.where(elig, 0.0, best)
    return cash, npay, days


def cell(path, b, risk, k_trades, mu, n=N_SIMS, seed=SEED, c=COST_R):
    rng = np.random.default_rng([seed, PATHS.index(path), B_GRID.index(b) if b in B_GRID else 9,
                                 int(risk), k_trades, int(round((mu + 1) * 10000))])
    passed, cdays = run_combine(rng, n, b, risk, k_trades, mu, c)
    npass = int(passed.sum())
    if npass:
        cash, npay, xdays = run_xfa(rng, npass, path, b, risk, k_trades, mu, c)
    else:
        cash, npay, xdays = np.zeros(0), np.zeros(0, int), np.zeros(0, int)
    pp = npass / n
    months = fee_months(cdays)
    e_x = float(cash.mean()) if npass else 0.0
    p_any_x = float((npay > 0).mean()) if npass else 0.0
    out = {
        'path': path, 'b': b, 'risk': risk, 'K': k_trades, 'mu': mu, 'p_win': p_win(mu, b, c),
        'p_pass': pp, 'combine_days_mean': float(cdays.mean()), 'fee_months_mean': float(months.mean()),
        'xfa_p_any_payout': p_any_x, 'xfa_e_cash': e_x,
        'xfa_mean_n_payouts': float(npay.mean()) if npass else 0.0,
        'xfa_days_mean': float(xdays.mean()) if npass else 0.0,
        'e_cash_per_attempt': pp * e_x,
        'p_any_payout_per_attempt': pp * p_any_x,
    }
    out['p_no_payout_10_attempts'] = (1.0 - out['p_any_payout_per_attempt']) ** 10
    for fs, (monthly, act) in FEES.items():
        cost = monthly * float(months.mean()) + pp * act
        out['cost_' + fs] = cost
        out['net_' + fs] = out['e_cash_per_attempt'] - cost
        out['ratio_' + fs] = out['e_cash_per_attempt'] / cost if cost > 0 else None
    return out


def main(path_out):
    t0 = time.time()
    rows = [cell(pa, b, r, k, mu) for pa in PATHS for b in B_GRID for r in RISK_GRID for k in K_GRID for mu in MU_GRID]
    summary, q = {}, {}
    for fs in FEES:
        for mu in MU_GRID:
            sub = [r for r in rows if r['mu'] == mu]
            best = max(sub, key=lambda r: r['net_' + fs])
            summary[f'{fs}|{mu}'] = {
                'best_net': best['net_' + fs], 'best_cfg': [best['path'], best['b'], best['risk'], best['K']],
                'best_p_pass': best['p_pass'], 'best_e_cash_attempt': best['e_cash_per_attempt'],
                'best_cost': best['cost_' + fs], 'best_p_any_payout_attempt': best['p_any_payout_per_attempt'],
                'best_p_no_payout_10': best['p_no_payout_10_attempts'],
                'n_cfg_positive': sum(1 for r in sub if r['net_' + fs] > 0)}
        q[f'Q1|{fs}'] = summary[f'{fs}|-0.08']['best_net'] > 0
        q[f'Q2|{fs}'] = summary[f'{fs}|-0.045']['best_net'] > 0
        pos = [mu for mu in MU_GRID if summary[f'{fs}|{mu}']['best_net'] > 0]
        q[f'Q3|{fs}'] = min(pos) if pos else None
    res = {'prereg': 'PREREG_PROP_EV_TS.md', 'n_sims': N_SIMS, 'seed': SEED, 'cost_R': COST_R,
           'runtime_s': round(time.time() - t0, 1), 'questions': q, 'summary': summary, 'cells': rows}
    with open(path_out, 'w') as f:
        json.dump(res, f, indent=1)
    print(json.dumps({'questions': q, 'runtime_s': res['runtime_s']}, indent=1))


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'prop_ev_ts_results.json')
