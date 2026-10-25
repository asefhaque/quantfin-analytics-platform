import os
import sys
import math
import numpy as np
import pandas as pd
import scipy.stats as si
import scipy.optimize

# ---------------------------------------------------------------------------
# Base paths
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
STOCKS_DIR = os.path.join(DATA_DIR, "stocks")

# Add BASE_DIR to sys.path so packages can be imported cleanly
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from bonds.bill import Bill
from bonds.bond import Bond
from bonds.read_bond_info import read_bills_from_file, read_bonds_from_file
from term_structure.term_structure import TermStructure


# ===========================================================================
# 1. FIXED INCOME & TERM STRUCTURE ENGINE
# ===========================================================================

def run_term_structure_analysis(tenor_grid="3M", bills_file=None, bonds_file=None):
    """
    Bootstraps the spot yield curve, discount factors, and forward rate curves.
    """
    if bills_file is None:
        bills_file = os.path.join(DATA_DIR, "bills.txt")
    if bonds_file is None:
        bonds_file = os.path.join(DATA_DIR, "bonds.txt")

    bonds = []
    bill_instruments = read_bills_from_file(bills_file)
    for bill_instrument in bill_instruments:
        bill = Bill(bill_instrument[0], bill_instrument[1], bill_instrument[2], bill_instrument[3])
        bill.set_price(float(bill_instrument[3]))
        bonds.append(bill)

    bond_instruments = read_bonds_from_file(bonds_file)
    for bond_instrument in bond_instruments:
        bond = Bond(bond_instrument[0], bond_instrument[1], bond_instrument[2],
                    bond_instrument[3], bond_instrument[4])
        bond.set_price(float(bond_instrument[5]))
        bonds.append(bond)

    # Compute YTMs for market instruments
    market_instruments = []
    for bond in bonds:
        market_instruments.append({
            "name": bond.get_name(),
            "coupon": bond.get_coupon(),
            "tenor": bond.get_tenor_in_years(),
            "price": bond.get_price(),
            "ytm": bond.compute_ytm()
        })
    market_df = pd.DataFrame(market_instruments)

    # Grid config
    if tenor_grid == "3M":
        tenor_count = 120
        time_period = 0.25
    else:
        tenor_count = 60
        time_period = 0.50

    term_structure = TermStructure(tenor_count, time_period=time_period)
    term_structure.set_bonds(bonds)
    term_structure.compute_spot_rates()
    term_structure.compute_discount_factors()
    term_structure.compute_forward_rates()

    tenors = [(i + 1) * time_period for i in range(tenor_count)]
    spot_rates = [term_structure.get_spot_rate(i) for i in range(tenor_count)]
    forward_rates = [term_structure.get_forward_rate(i) for i in range(tenor_count)]
    forward_rates_ann = [term_structure.get_forward_rate_annualized(i) for i in range(tenor_count)]
    discount_factors = [term_structure.get_discount_factor(i) for i in range(tenor_count)]

    curve_df = pd.DataFrame({
        "tenor": tenors,
        "spot_rate": spot_rates,
        "forward_rate": forward_rates,
        "forward_rate_ann": forward_rates_ann,
        "discount_factor": discount_factors
    })

    validation = term_structure.check_reasonableness()
    return market_df, curve_df, validation


# ===========================================================================
# 2. DERIVATIVES & OPTIONS PRICING ENGINE
# ===========================================================================

class AnalyticalBlackScholes:
    @staticmethod
    def price_and_greeks(s, k, t, r, sigma, option_type='C'):
        if t <= 0:
            payoff = max(0.0, s - k) if option_type == 'C' else max(0.0, k - s)
            return {"price": payoff, "delta": 1.0 if (s > k and option_type == 'C') else 0.0,
                    "gamma": 0.0, "theta": 0.0, "vega": 0.0, "rho": 0.0}

        d1 = (np.log(s / k) + (r + 0.5 * sigma ** 2) * t) / (sigma * np.sqrt(t))
        d2 = d1 - sigma * np.sqrt(t)
        prob_density = (1.0 / np.sqrt(2.0 * np.pi)) * np.exp(-0.5 * d1 ** 2)

        if option_type == 'C':
            price = s * si.norm.cdf(d1) - k * np.exp(-r * t) * si.norm.cdf(d2)
            delta = si.norm.cdf(d1)
            theta = (-sigma * s * prob_density) / (2.0 * np.sqrt(t)) - r * k * np.exp(-r * t) * si.norm.cdf(d2)
            rho = t * k * np.exp(-r * t) * si.norm.cdf(d2)
        else:
            price = k * np.exp(-r * t) * si.norm.cdf(-d2) - s * si.norm.cdf(-d1)
            delta = -si.norm.cdf(-d1)
            theta = (-sigma * s * prob_density) / (2.0 * np.sqrt(t)) + r * k * np.exp(-r * t) * si.norm.cdf(-d2)
            rho = -t * k * np.exp(-r * t) * si.norm.cdf(-d2)

        gamma = prob_density / (s * sigma * np.sqrt(t))
        vega = s * prob_density * np.sqrt(t)  # per 100% vol change

        return {
            "price": float(price),
            "delta": float(delta),
            "gamma": float(gamma),
            "theta": float(theta) / 365.0,  # daily theta
            "vega": float(vega) / 100.0,    # 1% vol change
            "rho": float(rho) / 100.0       # 1% rate change
        }

    @staticmethod
    def implied_volatility(s, k, t, quote, r, option_type='C', max_iter=200, tol=1e-5):
        sigma = 0.5
        for _ in range(max_iter):
            res = AnalyticalBlackScholes.price_and_greeks(s, k, t, r, sigma, option_type)
            price = res["price"]
            vega = res["vega"] * 100.0
            diff = quote - price
            if abs(diff) < tol:
                return sigma
            if abs(vega) < 1e-12:
                break
            sigma += diff / vega
            if sigma <= 0.001:
                sigma = 0.001
        return float(sigma)


def price_binomial_tree(s, k, t, r, sigma, option_type='C', exercise_type='E', n_steps=100):
    """
    Cox-Ross-Rubinstein (CRR) Binomial Tree supporting European & American exercise.
    """
    dt = t / n_steps
    u = np.exp(sigma * np.sqrt(dt))
    d = 1.0 / u
    p = (np.exp(r * dt) - d) / (u - d)
    df = np.exp(-r * dt)

    # Terminal stock prices
    prices = s * (u ** np.arange(n_steps + 1)) * (d ** (n_steps - np.arange(n_steps + 1)))
    if option_type == 'C':
        payoffs = np.maximum(prices - k, 0.0)
    else:
        payoffs = np.maximum(k - prices, 0.0)

    f_1, f_2 = None, None
    p_1, p_2 = None, None

    for step in range(n_steps - 1, -1, -1):
        prices = s * (u ** np.arange(step + 1)) * (d ** (step - np.arange(step + 1)))
        payoffs = df * (p * payoffs[1:step + 2] + (1.0 - p) * payoffs[:step + 1])

        if exercise_type == 'A':
            if option_type == 'C':
                payoffs = np.maximum(payoffs, prices - k)
            else:
                payoffs = np.maximum(payoffs, k - prices)

        if step == 2:
            f_2 = payoffs.copy()
            p_2 = prices.copy()
        elif step == 1:
            f_1 = payoffs.copy()
            p_1 = prices.copy()

    price = float(payoffs[0])
    delta = float((f_1[1] - f_1[0]) / (p_1[1] - p_1[0])) if f_1 is not None else 0.0

    if f_2 is not None and p_2 is not None:
        delta_u = (f_2[2] - f_2[1]) / (p_2[2] - p_2[1])
        delta_d = (f_2[1] - f_2[0]) / (p_2[1] - p_2[0])
        gamma = float((delta_u - delta_d) / (0.5 * (p_2[2] - p_2[0])))
        theta = float((f_2[1] - price) / (2.0 * dt * 365.0))
    else:
        gamma, theta = 0.0, 0.0

    return {
        "price": price,
        "delta": delta,
        "gamma": gamma,
        "theta": theta
    }


def simulate_monte_carlo(s, k, t, r, sigma, option_type='C', contract_style='Vanilla',
                         barrier=None, n_sims=10000, n_steps=100, seed=42):
    """
    Vectorized Monte Carlo engine for Vanilla, Asian, and Barrier options.
    """
    if seed is not None:
        np.random.seed(seed)

    dt = t / n_steps
    z = np.random.normal(0, 1, (n_sims, n_steps))
    drift = (r - 0.5 * (sigma ** 2.0)) * dt
    diffusion = sigma * np.sqrt(dt) * z
    log_returns = drift + diffusion
    cum_returns = np.cumsum(log_returns, axis=1)

    # Full simulated price paths
    paths = s * np.exp(cum_returns)
    full_paths = np.hstack([np.full((n_sims, 1), s), paths])
    terminal_prices = full_paths[:, -1]

    # Evaluate payoffs based on contract style
    is_call = option_type.upper().startswith('C')

    if contract_style == 'Vanilla':
        payoff_terminal = terminal_prices
        active_mask = np.ones(n_sims, dtype=bool)

    elif contract_style == 'Asian':
        payoff_terminal = np.mean(full_paths, axis=1)
        active_mask = np.ones(n_sims, dtype=bool)

    elif contract_style.startswith('Barrier'):
        # Barrier classification: e.g. Up-and-In, Up-and-Out, Down-and-In, Down-and-Out
        max_prices = np.max(full_paths, axis=1)
        min_prices = np.min(full_paths, axis=1)
        payoff_terminal = terminal_prices

        if 'Up-and-In' in contract_style:
            active_mask = max_prices >= barrier
        elif 'Up-and-Out' in contract_style:
            active_mask = max_prices < barrier
        elif 'Down-and-In' in contract_style:
            active_mask = min_prices <= barrier
        elif 'Down-and-Out' in contract_style:
            active_mask = min_prices > barrier
        else:
            active_mask = np.ones(n_sims, dtype=bool)
    else:
        payoff_terminal = terminal_prices
        active_mask = np.ones(n_sims, dtype=bool)

    if is_call:
        raw_payoffs = np.maximum(payoff_terminal - k, 0.0)
    else:
        raw_payoffs = np.maximum(k - payoff_terminal, 0.0)

    effective_payoffs = np.where(active_mask, raw_payoffs, 0.0)
    discount_factor = np.exp(-r * t)
    price = float(discount_factor * np.mean(effective_payoffs))
    std_err = float(discount_factor * (np.std(effective_payoffs) / np.sqrt(n_sims)))

    # Greeks estimation via central finite differences (Common Random Numbers)
    eps_s = max(0.01, 0.01 * s)
    paths_up = (s + eps_s) * np.exp(cum_returns)
    full_up = np.hstack([np.full((n_sims, 1), s + eps_s), paths_up])
    paths_dn = (s - eps_s) * np.exp(cum_returns)
    full_dn = np.hstack([np.full((n_sims, 1), s - eps_s), paths_dn])

    if contract_style == 'Asian':
        p_up = np.mean(full_up, axis=1)
        p_dn = np.mean(full_dn, axis=1)
    else:
        p_up = full_up[:, -1]
        p_dn = full_dn[:, -1]

    pay_up = np.maximum(p_up - k, 0.0) if is_call else np.maximum(k - p_up, 0.0)
    pay_dn = np.maximum(p_dn - k, 0.0) if is_call else np.maximum(k - p_dn, 0.0)

    if contract_style.startswith('Barrier'):
        if 'Up-and-In' in contract_style:
            pay_up = np.where(np.max(full_up, axis=1) >= barrier, pay_up, 0.0)
            pay_dn = np.where(np.max(full_dn, axis=1) >= barrier, pay_dn, 0.0)
        elif 'Up-and-Out' in contract_style:
            pay_up = np.where(np.max(full_up, axis=1) < barrier, pay_up, 0.0)
            pay_dn = np.where(np.max(full_dn, axis=1) < barrier, pay_dn, 0.0)
        elif 'Down-and-In' in contract_style:
            pay_up = np.where(np.min(full_up, axis=1) <= barrier, pay_up, 0.0)
            pay_dn = np.where(np.min(full_dn, axis=1) <= barrier, pay_dn, 0.0)
        elif 'Down-and-Out' in contract_style:
            pay_up = np.where(np.min(full_up, axis=1) > barrier, pay_up, 0.0)
            pay_dn = np.where(np.min(full_dn, axis=1) > barrier, pay_dn, 0.0)

    price_up = float(discount_factor * np.mean(pay_up))
    price_dn = float(discount_factor * np.mean(pay_dn))

    delta_mc = (price_up - price_dn) / (2.0 * eps_s)
    gamma_mc = (price_up - 2.0 * price + price_dn) / (eps_s ** 2.0)

    return {
        "price": price,
        "std_error": std_err,
        "delta": float(delta_mc),
        "gamma": float(gamma_mc),
        "sample_paths": full_paths[:50],  # first 50 paths for visualization
        "time_grid": np.linspace(0, t, n_steps + 1),
        "terminal_prices": terminal_prices,
        "effective_payoffs": effective_payoffs
    }


# ===========================================================================
# 3. BLACK-LITTERMAN & PORTFOLIO OPTIMIZATION ENGINE
# ===========================================================================

DEFAULT_MARKET_CAPS = {
    'XOM': 403.0,
    'AAPL': 3450.0,
    'MSFT': 3100.0,
    'JNJ': 380.0,
    'GE': 200.0,
    'GOOG': 2050.0,
    'CVX': 290.0,
    'PG': 390.0,
    'WFC': 210.0
}

def load_stock_universe(tickers=None):
    if tickers is None:
        tickers = ['AAPL', 'MSFT', 'GOOG', 'XOM', 'JNJ', 'PG', 'WFC', 'CVX', 'GE']

    prices_dict = {}
    for ticker in tickers:
        fpath = os.path.join(STOCKS_DIR, f"{ticker}.csv")
        if os.path.exists(fpath):
            df = pd.read_csv(fpath, parse_dates=['date'])
            df = df.sort_values('date')
            prices_dict[ticker] = df['close'].values[-500:]

    prices_matrix = np.array([prices_dict[t] for t in tickers])
    rows, cols = prices_matrix.shape
    returns = (prices_matrix[:, 1:] / prices_matrix[:, :-1]) - 1.0

    exp_returns = np.mean(returns, axis=1)
    annualized_returns = ((1.0 + exp_returns) ** 252) - 1.0
    annualized_cov = np.cov(returns) * 252.0

    # Market capitalization weights
    caps = np.array([DEFAULT_MARKET_CAPS.get(t, 100.0) for t in tickers])
    w_market = caps / np.sum(caps)

    return tickers, annualized_returns, annualized_cov, w_market


def solve_markowitz_frontier(returns, cov, rf=0.03, n_points=40):
    n_assets = len(returns)

    def portfolio_stats(w):
        m = np.sum(w * returns)
        v = np.dot(w.T, np.dot(cov, w))
        return m, v

    # Max Sharpe / Tangency portfolio
    def neg_sharpe(w):
        m, v = portfolio_stats(w)
        return -(m - rf) / np.sqrt(max(1e-8, v))

    bounds = [(0.0, 1.0) for _ in range(n_assets)]
    constraints = [{'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0}]
    init_w = np.ones(n_assets) / n_assets

    res_tan = scipy.optimize.minimize(neg_sharpe, init_w, method='SLSQP', bounds=bounds, constraints=constraints)
    tan_w = res_tan.x
    tan_ret, tan_var = portfolio_stats(tan_w)

    # Frontier trace
    target_returns = np.linspace(min(returns) * 0.95, max(returns) * 1.05, n_points)
    frontier_vols = []
    frontier_rets = []

    for r_target in target_returns:
        def target_fitness(w):
            m, v = portfolio_stats(w)
            penalty = 1000.0 * (m - r_target) ** 2
            return v + penalty

        res = scipy.optimize.minimize(target_fitness, init_w, method='SLSQP', bounds=bounds, constraints=constraints)
        if res.success:
            m, v = portfolio_stats(res.x)
            frontier_vols.append(np.sqrt(v))
            frontier_rets.append(m)

    return {
        "tangency_weights": tan_w,
        "tangency_ret": float(tan_ret),
        "tangency_vol": float(np.sqrt(tan_var)),
        "frontier_vols": frontier_vols,
        "frontier_rets": frontier_rets
    }


def compute_black_litterman(cov, w_market, views_list, tickers, delta=2.5, tau=0.05):
    """
    Full Black-Litterman model implementation.
    views_list: list of tuples (Asset1, '>', Asset2, excess_return) or (Asset1, '=', None, absolute_return)
    """
    n = len(tickers)
    t_idx = {t: i for i, t in enumerate(tickers)}

    # 1. Reverse optimization: Implied equilibrium excess returns
    pi = delta * np.dot(cov, w_market)

    if not views_list:
        return pi, w_market, np.zeros(n)

    # 2. Build P and Q matrices
    k = len(views_list)
    P = np.zeros((k, n))
    Q = np.zeros(k)

    for i, view in enumerate(views_list):
        a1, relation, a2, q_val = view
        Q[i] = q_val
        if a2 is None or relation == '=':
            P[i, t_idx[a1]] = 1.0
        else:
            P[i, t_idx[a1]] = 1.0 if relation == '>' else -1.0
            P[i, t_idx[a2]] = -1.0 if relation == '>' else 1.0

    # 3. View uncertainty Omega = tau * diag(P * Sigma * P^T) (He & Litterman 1999)
    view_variances = np.diag(P @ cov @ P.T)
    Omega = tau * np.diag(view_variances)

    tau_sigma = tau * cov
    tau_sigma_inv = np.linalg.inv(tau_sigma)
    omega_inv = np.linalg.inv(Omega)

    # Master Black-Litterman posterior formula
    M_inv = tau_sigma_inv + P.T @ omega_inv @ P
    M = np.linalg.inv(M_inv)
    mu_bl = M @ (tau_sigma_inv @ pi + P.T @ omega_inv @ Q)

    # Optimal unconstrained weights: w* = (1/delta) * Sigma^-1 * mu_bl
    cov_inv = np.linalg.inv(cov)
    w_star = (1.0 / delta) * np.dot(cov_inv, mu_bl)

    # Normalized weights
    w_star_norm = w_star / np.sum(w_star)
    tilts = w_star_norm - w_market

    return mu_bl, w_star_norm, tilts


# ===========================================================================
# 4. TRIANGULAR FX ARBITRAGE ENGINE
# ===========================================================================

def load_fx_rates(filepath=None):
    if filepath is None:
        filepath = os.path.join(DATA_DIR, "usd_exchange_rates.csv")
    df = pd.read_csv(filepath)
    df.columns = [c.strip() for c in df.columns]
    return df


def compute_cross_rates_dijkstra(base_currency, currency_nodes, base_rates, bid_fee=0.0, ask_fee=0.0):
    """
    Computes cross-currency exchange matrix using Dijkstra's multiplicative algorithm.
    """
    rates_dict = dict(zip(currency_nodes, base_rates))
    costs = {}
    for node in currency_nodes:
        costs[node] = {}

    for c1 in currency_nodes:
        for c2 in currency_nodes:
            if c1 == c2:
                costs[c1][c2] = 1.0
            else:
                # Direct rate through base currency with bid/ask fees
                rate1 = rates_dict[c1]
                rate2 = rates_dict[c2]
                raw_cross = rate1 / rate2
                costs[c1][c2] = raw_cross * (1.0 - (bid_fee + ask_fee) / 100.0)

    # Generate full matrix
    matrix_df = pd.DataFrame(index=currency_nodes, columns=currency_nodes, dtype=float)
    for c1 in currency_nodes:
        for c2 in currency_nodes:
            matrix_df.loc[c1, c2] = costs[c1][c2]

    return matrix_df


def detect_triangular_arbitrage(matrix_df, threshold=1.0001):
    """
    Scans the cross-rate matrix for cycles C1 -> C2 -> C3 -> C1 with net return > 1.0.
    """
    currencies = list(matrix_df.index)
    n = len(currencies)
    opps = []

    for i in range(n):
        c1 = currencies[i]
        for j in range(n):
            if i == j:
                continue
            c2 = currencies[j]
            r12 = matrix_df.loc[c1, c2]
            for k in range(n):
                if k == i or k == j:
                    continue
                c3 = currencies[k]
                r23 = matrix_df.loc[c2, c3]
                r31 = matrix_df.loc[c3, c1]

                net_return = r12 * r23 * r31
                profit_pct = (net_return - 1.0) * 100.0

                if net_return > threshold:
                    opps.append({
                        "path": f"{c1} -> {c2} -> {c3} -> {c1}",
                        "net_return": net_return,
                        "profit_pct": profit_pct,
                        "rate_1": r12,
                        "rate_2": r23,
                        "rate_3": r31
                    })

    opps = sorted(opps, key=lambda x: x["profit_pct"], reverse=True)
    return pd.DataFrame(opps)
