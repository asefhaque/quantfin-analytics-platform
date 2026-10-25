# QuantFin Analytics Platform

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Live Interactive Web App:** [asef-haque-quant.streamlit.app](https://share.streamlit.io) *(Free 1-click cloud demo)*

---

### ⚡ Executive Summary for Hiring Managers & Recruiters (15-Second Overview)

| Pillar | Industry Problem Solved | Key Tech & Models Implemented |
| :--- | :--- | :--- |
| **📈 Term Structure & Yield Curves** | Bootstrapping zero-coupon discount curves from market Treasury bills and coupon bonds | Bisection YTM solver, quarterly/semi-annual forward rate curves, automated re-pricing sanity checks ($<0.005$ tolerance) |
| **🎯 Derivatives & Exotics Lab** | Fast, reliable multi-model pricing for vanilla and path-dependent exotic options | Black-Scholes analytical formulas, CRR Binomial Trees (American/European), vectorized Monte Carlo GBM ($10^4$ paths), Greeks ($\Delta, \Gamma, \mathcal{V}, \Theta, \rho$) |
| **⚖️ Portfolio Asset Allocation** | Overcoming Markowitz corner-portfolio concentration and input instability | Full Black-Litterman model (implied equilibrium prior $\Pi = \delta \Sigma w_{\text{mkt}}$, subjective investor views $P$ & $Q$, Bayesian posterior updates), SLSQP Efficient Frontier |
| **💱 FX Triangular Arbitrage** | Identifying multi-currency cross-rate conversion loops and mispricings | Dijkstra multiplicative shortest-path graph algorithm, bid/ask spread fee sensitivity |

---

## 🏛️ Platform Architecture & Core Modules

The platform is structured into four core analytical modules:

```
QuantFin/
├── app.py                      # Main Streamlit web application & interactive UI
├── quant_engine.py             # Unified quant API across all pricing & modeling engines
├── bonds/                      # Fixed income instrument classes (Bill, Bond, coupon cashflows)
├── term_structure/             # Spot rate bootstrapping, discount factors & forward curves
├── data/                       # Treasury bills, bonds, exchange rates, and stock price histories
│   ├── bills.txt               # Short-term Treasury bills quotes
│   ├── bonds.txt               # Benchmark coupon-bearing Treasury bonds
│   ├── usd_exchange_rates.csv  # Global cross-currency FX rates
│   └── stocks/                 # S&P 500 equities historical close prices
├── requirements.txt            # Dependency specification for one-click deployment
├── run_app.bat                 # One-click Windows launch script
└── README.md                   # Technical documentation and methodology
```

---

## 🔬 Core Methodologies

### 1. Fixed Income & Term Structure Bootstrapping
- **Zero-Coupon Spot Curve:** Bootstraps spot rates $s(t)$ across quarterly (3M, 120 tenors) and semi-annual (6M, 60 tenors) grids up to 30 years using market Treasury bills and coupon bonds.
- **Discount Factor Curve:** Computes continuous discount factors:
  $$P(0, T) = \exp(-s(T) \cdot T)$$
- **Forward Rate Modeling:** Evaluates period and annualized instantaneous forward rate curves:
  $$F(t_1, t_2) = \frac{s(t_2)t_2 - s(t_1)t_1}{t_2 - t_1}$$
- **Institutional Sanity Diagnostics:** Automated validation verifying repricing tolerance ($|\text{Price}_{\text{model}} - \text{Price}_{\text{market}}| < 0.005$), monotonicity of discount factors, and non-negative forward rates.

### 2. Derivatives & Exotic Options Pricing Engine
- **Analytical Black-Scholes-Merton:** Closed-form valuation for European Calls and Puts with first- and second-order Greeks ($\Delta, \Gamma, \mathcal{V}, \Theta, \rho$).
- **Cox-Ross-Rubinstein (CRR) Binomial Tree:** Lattice pricing supporting both European and American early-exercise contracts with backward induction.
- **Vectorized Monte Carlo Geometric Brownian Motion (GBM):**
  $$S_{t+\Delta t} = S_t \exp\left( \left(r - \frac{1}{2}\sigma^2\right)\Delta t + \sigma \sqrt{\Delta t} Z \right), \quad Z \sim \mathcal{N}(0, 1)$$
- **Exotic Contract Support:**
  - **Asian Options:** Arithmetic average price path-dependent call/put.
  - **Barrier Options:** Single-barrier contracts (**Up-and-In**, **Up-and-Out**, **Down-and-In**, **Down-and-Out**) with continuous path monitoring.
- **Newton-Raphson Implied Volatility Solver:** Iteratively solves for market implied volatility:
  $$\sigma_{n+1} = \sigma_n + \frac{C_{\text{market}} - C(\sigma_n)}{\mathcal{V}(\sigma_n)}$$

### 3. Black-Litterman Asset Allocation & Efficient Frontier
- **Reverse Optimization (He & Litterman 1999):** Extracts implied equilibrium prior returns from market capitalization weights:
  $$\Pi = \delta \Sigma w_{\text{mkt}}$$
- **Bayesian Master Formula:** Incorporates subjective investor views ($P$ and $Q$) with variance-proportional uncertainty $\Omega = \tau \text{diag}(P \Sigma P^T)$:
  $$\mu_{\text{BL}} = \left[ (\tau \Sigma)^{-1} + P^T \Omega^{-1} P \right]^{-1} \left[ (\tau \Sigma)^{-1} \Pi + P^T \Omega^{-1} Q \right]$$
  $$w^* = \frac{1}{\delta} \Sigma^{-1} \mu_{\text{BL}}$$
- **Markowitz Mean-Variance Frontier:** Solves constrained quadratic optimization (SLSQP) to trace the global efficient frontier and identify the maximum Sharpe ratio tangency portfolio.

### 4. Triangular FX Arbitrage Radar
- Evaluates multi-currency cross-rate exchange matrices across 50+ global currencies.
- Utilizes Dijkstra's multiplicative shortest path algorithm to detect triangular currency loops ($C_1 \to C_2 \to C_3 \to C_1$) exceeding transaction bid/ask fee thresholds.

---

## 🚀 Quickstart & Local Installation

### Prerequisites
- Python 3.10+ (or [uv](https://docs.astral.sh/uv/))

### 1. Clone the repository
```bash
git clone https://github.com/your-username/quantfin-analytics-platform.git
cd quantfin-analytics-platform
```

### 2. Set up a virtual environment & install dependencies
```bash
# Using standard venv:
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Or using uv (instant):
uv venv .venv --python 3.12
uv pip install -r requirements.txt
```

### 3. Launch the Web Application
```bash
streamlit run app.py
```
*(On Windows, you can simply double-click `run_app.bat`)*

---

## ☁️ Deploying to Streamlit Cloud (1-Click Free Hosting)

1. Push this directory to your personal GitHub account (e.g. `github.com/your-username/quantfin-suite`).
2. Log into [share.streamlit.io](https://share.streamlit.io/).
3. Select your repository, branch (`main`), and main file path (`app.py`).
4. Click **Deploy** — your interactive quant portfolio will be live at `https://your-name-quant.streamlit.app`!

---

## 👨‍💻 Author

**Asef Haque**  
- MS in Business Analytics | Brandeis University International Business School  
- BA in Psychology (Cognitive/Behavioral) | Temple University  
- Focus: Quantitative Finance, Financial Engineering, Statistical Modeling & Risk Analytics  
