# QuantFin: Quantitative Finance & Portfolio Analytics Engine

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![NumPy](https://img.shields.io/badge/NumPy-013243?logo=numpy&logoColor=white)](https://numpy.org/)
[![SciPy](https://img.shields.io/badge/SciPy-8CAAE6?logo=scipy&logoColor=white)](https://scipy.org/)
[![Matplotlib](https://img.shields.io/badge/Matplotlib-11557c.svg)](https://matplotlib.org/)

A multi-asset quantitative finance, derivatives pricing, term structure modeling, and asset allocation engine developed in Python (NumPy, SciPy, Matplotlib). Designed to bridge mathematical financial engineering with practical, empirical portfolio analysis.

---

### ⚡ Executive Summary

| Pillar | Industry Problem Solved | Key Tech & Models Implemented |
| :--- | :--- | :--- |
| **📈 Term Structure & Yield Curves** | Bootstrapping zero-coupon discount curves from market Treasury bills and coupon bonds | Bisection YTM solver, quarterly/semi-annual forward rate curves, automated re-pricing sanity checks ($<0.005$ tolerance) |
| **🎯 Derivatives & Exotics Lab** | Fast, reliable multi-model pricing for vanilla and path-dependent exotic options | Black-Scholes analytical formulas, CRR Binomial Trees (American/European), vectorized Monte Carlo GBM ($10^4$ paths), Greeks ($\Delta, \Gamma, \mathcal{V}, \Theta, \rho$) |
| **⚖️ Portfolio Asset Allocation** | Overcoming Markowitz corner-portfolio concentration and input instability | Full Black-Litterman model (implied equilibrium prior $\Pi = \delta \Sigma w_{\text{mkt}}$, subjective investor views $P$ & $Q$, Bayesian posterior updates), SLSQP Efficient Frontier |
| **💱 FX Triangular Arbitrage** | Identifying multi-currency cross-rate conversion loops and mispricings | Dijkstra multiplicative shortest-path graph algorithm, bid/ask spread fee sensitivity |

---

## 📊 Visual Gallery & Model Outputs

### 1. Portfolio Risk & Asset Allocation Analysis
> Built in Python to analyze how to balance risk and return in an investment portfolio. This project maps the trade-off between volatility and return using the Markowitz Efficient Frontier, and applies the Black-Litterman model across global market indices to show how an investor can adjust portfolio weights based on their own market expectations.

| Markowitz Efficient Frontier & CML | Black-Litterman Optimal Tilts |
| :---: | :---: |
| <img src="assets/efficient%20frontier.png" width="480"/> | <img src="assets/black%20litterman.png" width="480"/> |

---

### 2. Options Simulation & Interest Rate Modeling
> A Python modeling project focused on financial pricing and yield curves. It uses Monte Carlo simulations to model price trajectories for exotic Barrier Up-and-Out Call options (BuoC), and bootstraps U.S. Treasury spot rates, forward rates, and discount factors across maturities up to 30 years.

| Monte Carlo Barrier Up-and-Out Call (BuoC) | Bootstrapped U.S. Treasury Curves (30y) |
| :---: | :---: |
| <img src="assets/monte%20carlo%20pricing.png" width="480"/> | <img src="assets/term%20structures.png" width="480"/> |

---

## 🏛️ Platform Architecture & Core Modules

The platform is structured into clean analytical modules:

```
QuantFin/
├── quant_engine.py             # Unified quant API across pricing, curves & portfolio models
├── driver.py                   # Model execution script for term structure and analytics
├── bonds/                      # Fixed income instrument classes (Bill, Bond, coupon cashflows)
├── term_structure/             # Spot rate bootstrapping, discount factors & forward curves
├── data/                       # Treasury bills, bonds, exchange rates, and stock price histories
│   ├── bills.txt               # Short-term Treasury bills quotes
│   ├── bonds.txt               # Benchmark coupon-bearing Treasury bonds
│   ├── usd_exchange_rates.csv  # Global cross-currency FX rates
│   └── stocks/                 # S&P 500 equities historical close prices
├── assets/                     # Visual charts generated directly by the Python models
├── tests/                      # Automated validation and pricing test suite
├── requirements.txt            # Python dependencies (NumPy, SciPy, Matplotlib, Pandas)
└── README.md                   # Technical documentation and visual gallery
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

## 💻 Running the Models Locally (Optional)

All model outputs and charts are already generated and documented in the visual gallery above. If you wish to replicate the calculations or run the test suite locally:

```bash
# 1. Clone the repository
git clone https://github.com/asefhaque/quantfin-analytics-platform.git
cd quantfin-analytics-platform

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the automated test suite
python tests/test_quant_engine.py

# 4. Run the fixed-income term structure analytics
python driver.py
```

---

## 👨‍💻 Author

**Asef Haque**  
- 1 year work experience in supply chain analytics
- 1 year work experience in early learning education development
- MS in Business Analytics | Brandeis University, School of Business & Economics  
- BA in Psychology | Temple University  
- Focus: Quantitative Finance, Statistical Modeling & Risk Analytics, Consumer Behavior  
