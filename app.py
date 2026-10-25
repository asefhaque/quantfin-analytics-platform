import os
import sys
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

# Configure page
st.set_page_config(
    page_title="QuantFin Analytics Platform | Asef Haque",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for institutional dark styling
st.markdown("""
<style>
    .main {
        background-color: #0b0f19;
        color: #f1f5f9;
    }
    .stMetric {
        background: #1e293b;
        padding: 12px 18px;
        border-radius: 8px;
        border: 1px solid #334155;
    }
    .metric-card {
        background: #1e293b;
        padding: 16px 20px;
        border-radius: 10px;
        border: 1px solid #334155;
        margin-bottom: 12px;
    }
    .card-title {
        font-size: 0.85rem;
        color: #94a3b8;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .card-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #38bdf8;
    }
    .card-sub {
        font-size: 0.8rem;
        color: #64748b;
    }
    .badge-pass {
        background-color: #064e3b;
        color: #34d399;
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: 600;
        font-size: 0.8rem;
    }
    .badge-fail {
        background-color: #7f1d1d;
        color: #f87171;
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: 600;
        font-size: 0.8rem;
    }
    h1, h2, h3 {
        color: #f8fafc;
    }
</style>
""", unsafe_allow_html=True)

# Import quant engine
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import quant_engine as qe

# ---------------------------------------------------------------------------
# Sidebar Navigation & Branding
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## 📊 **QuantFin Suite**")
    st.caption("**Institutional Quantitative Analytics & Risk Engine**")
    st.caption("Developer: **Asef Haque** | Brandeis MSBA")
    st.markdown("---")

    selected_module = st.radio(
        "Select Analytics Module:",
        [
            "📈 Yield Curve & Term Structure",
            "🎯 Derivatives & Monte Carlo Lab",
            "⚖️ Black-Litterman Portfolio Optimization",
            "💱 Triangular FX Arbitrage Radar",
            "📖 Mathematical Methodology"
        ],
        index=0
    )

    st.markdown("---")
    st.markdown("### 🔗 Quick Links")
    st.markdown("[📁 GitHub Repository](https://github.com)")
    st.markdown("[💼 LinkedIn Profile](https://linkedin.com)")
    st.caption("Version 1.0.0 | Production Release")


# ===========================================================================
# MODULE 1: YIELD CURVE & TERM STRUCTURE
# ===========================================================================
if selected_module == "📈 Yield Curve & Term Structure":
    st.title("📈 Yield Curve & Term Structure Bootstrapper")
    st.markdown(
        "Bootstraps zero-coupon spot yield curves, discount factors, and forward rate curves from "
        "Treasury bills and coupon-bearing bonds, with automated sanity check and repricing diagnostics."
    )

    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        grid_choice = st.selectbox("Tenor Grid Resolution:", ["3M (Quarterly, 120 Tenors)", "6M (Semi-Annual, 60 Tenors)"])
        grid_code = "3M" if "3M" in grid_choice else "6M"
    with col2:
        interp_method = st.selectbox("Interpolation Scheme:", ["Linear Interpolation", "Cubic Spline"])

    with st.spinner("Bootstrapping term structure..."):
        market_df, curve_df, val_report = qe.run_term_structure_analysis(grid_code)

    # Status KPI Cards
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.metric("Max Repricing Error", f"{val_report['max_repricing_error']:.6f}",
                  delta="< 0.005 Tolerance" if val_report['is_repricing_valid'] else "Fail", delta_color="normal")
    with kpi2:
        st.metric("Monotonic Discount Factors", "PASS" if val_report['is_monotonic_df'] else "FAIL")
    with kpi3:
        st.metric("Non-Negative Forwards", "PASS" if val_report['is_positive_forward'] else "FAIL")
    with kpi4:
        st.metric("Reasonableness Status", val_report['overall_status'])

    # Plots
    tab_curve, tab_df, tab_data = st.tabs(["📊 Yield & Forward Curves", "📉 Discount Factors", "📋 Instrument & Grid Data"])

    with tab_curve:
        fig_curve = go.Figure()
        # Spot curve
        fig_curve.add_trace(go.Scatter(
            x=curve_df["tenor"], y=curve_df["spot_rate"],
            mode="lines", name="Zero Spot Rate (%)",
            line=dict(color="#38bdf8", width=3)
        ))
        # Forward curve
        fig_curve.add_trace(go.Scatter(
            x=curve_df["tenor"], y=curve_df["forward_rate_ann"],
            mode="lines", name=f"{grid_code} Annualized Forward Rate (%)",
            line=dict(color="#fb923c", width=2, dash="dash")
        ))
        # Market instruments
        fig_curve.add_trace(go.Scatter(
            x=market_df["tenor"], y=market_df["ytm"],
            mode="markers+text", name="Market Instruments (YTM)",
            text=market_df["name"], textposition="top center",
            marker=dict(color="#34d399", size=9, symbol="diamond")
        ))
        fig_curve.update_layout(
            title=f"Bootstrapped Term Structure of Interest Rates ({grid_code} Grid)",
            xaxis_title="Tenor (Years)",
            yaxis_title="Rate (%)",
            template="plotly_dark",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            hovermode="x unified",
            height=500
        )
        st.plotly_chart(fig_curve, use_container_width=True)

    with tab_df:
        fig_df = go.Figure()
        fig_df.add_trace(go.Scatter(
            x=curve_df["tenor"], y=curve_df["discount_factor"],
            mode="lines", name="Discount Factor P(0, t)",
            line=dict(color="#a78bfa", width=3)
        ))
        fig_df.update_layout(
            title="Discount Factor Curve P(0, T)",
            xaxis_title="Tenor (Years)",
            yaxis_title="Discount Factor",
            template="plotly_dark",
            height=450
        )
        st.plotly_chart(fig_df, use_container_width=True)

    with tab_data:
        c_left, c_right = st.columns(2)
        with c_left:
            st.markdown("#### Market Instruments & YTM")
            st.dataframe(market_df.style.format({
                "coupon": "{:.4f}%",
                "tenor": "{:.2f}y",
                "price": "{:.4f}",
                "ytm": "{:.4f}%"
            }), height=350)
        with c_right:
            st.markdown("#### Repricing Diagnostic Table")
            reprice_df = pd.DataFrame(val_report["repricing"])
            st.dataframe(reprice_df.style.format({
                "tenor": "{:.2f}y",
                "market_price": "{:.4f}",
                "model_price": "{:.4f}",
                "error": "{:.6f}"
            }), height=350)


# ===========================================================================
# MODULE 2: DERIVATIVES & MONTE CARLO LAB
# ===========================================================================
elif selected_module == "🎯 Derivatives & Monte Carlo Lab":
    st.title("🎯 Derivatives Pricing & Monte Carlo Simulation Lab")
    st.markdown(
        "Interactive options pricing engine comparing **Black-Scholes analytical formulas**, "
        "**Cox-Ross-Rubinstein Binomial Trees**, and **Vectorized Monte Carlo Geometric Brownian Motion**."
    )

    # Layout inputs
    col_in1, col_in2, col_in3, col_in4 = st.columns(4)
    with col_in1:
        s0 = st.number_input("Underlying Spot Price ($S_0$):", min_value=1.0, max_value=5000.0, value=100.0, step=1.0)
        strike = st.number_input("Strike Price ($K$):", min_value=1.0, max_value=5000.0, value=100.0, step=1.0)
    with col_in2:
        maturity = st.number_input("Time to Maturity ($T$ in years):", min_value=0.01, max_value=10.0, value=1.0, step=0.1)
        r_rate = st.number_input("Risk-Free Rate ($r$):", min_value=0.00, max_value=0.30, value=0.05, step=0.01, format="%.2f")
    with col_in3:
        sigma = st.number_input(r"Volatility ($\sigma$):", min_value=0.01, max_value=2.00, value=0.20, step=0.01, format="%.2f")
        opt_type = st.selectbox("Option Type:", ["Call", "Put"])
        opt_code = 'C' if opt_type == "Call" else 'P'
    with col_in4:
        contract_style = st.selectbox(
            "Contract Style / Exotics:",
            [
                "Vanilla European",
                "American (Early Exercise)",
                "Asian (Arithmetic Average)",
                "Barrier: Up-and-In",
                "Barrier: Up-and-Out",
                "Barrier: Down-and-In",
                "Barrier: Down-and-Out"
            ]
        )
        barrier_level = None
        if "Barrier" in contract_style:
            barrier_level = st.number_input("Barrier Level ($H$):", min_value=1.0, max_value=5000.0,
                                            value=120.0 if "Up" in contract_style else 80.0, step=1.0)

    # Simulation settings expander
    with st.expander("⚙️ Advanced Simulation Settings (Monte Carlo & Binomial)", expanded=False):
        c_sim1, c_sim2, c_sim3 = st.columns(3)
        with c_sim1:
            n_sims = st.slider("Number of Simulations:", min_value=1000, max_value=50000, value=10000, step=1000)
        with c_sim2:
            n_steps = st.slider("Timesteps per Path:", min_value=20, max_value=252, value=100, step=10)
        with c_sim3:
            rand_seed = st.number_input("Random Seed:", value=42, step=1)

    # Compute Prices
    bs_results = qe.AnalyticalBlackScholes.price_and_greeks(s0, strike, maturity, r_rate, sigma, opt_code)
    bin_exercise = 'A' if "American" in contract_style else 'E'
    bin_results = qe.price_binomial_tree(s0, strike, maturity, r_rate, sigma, opt_code, bin_exercise, n_steps)

    mc_style = "Vanilla"
    if "Asian" in contract_style:
        mc_style = "Asian"
    elif "Barrier" in contract_style:
        mc_style = contract_style

    mc_results = qe.simulate_monte_carlo(
        s0, strike, maturity, r_rate, sigma, opt_code,
        contract_style=mc_style, barrier=barrier_level,
        n_sims=n_sims, n_steps=n_steps, seed=rand_seed
    )

    # Display Price Comparisons
    st.markdown("### 💰 Model Price Comparison")
    p1, p2, p3 = st.columns(3)
    with p1:
        if "Asian" not in contract_style and "Barrier" not in contract_style and "American" not in contract_style:
            st.metric("Black-Scholes (Closed-Form)", f"${bs_results['price']:.4f}")
        else:
            st.metric("Black-Scholes Benchmark", f"${bs_results['price']:.4f}", help="Vanilla European reference price")
    with p2:
        st.metric(f"Binomial Tree ({'American' if bin_exercise=='A' else 'European'})", f"${bin_results['price']:.4f}",
                  delta=f"Diff vs BS: ${bin_results['price'] - bs_results['price']:+.4f}")
    with p3:
        st.metric(f"Monte Carlo ({contract_style})", f"${mc_results['price']:.4f}",
                  delta=f"±${mc_results['std_error']:.4f} StdErr")

    # Greeks Cards
    st.markdown("### 📐 Option Greeks (Risk Sensitivities)")
    g1, g2, g3, g4, g5 = st.columns(5)
    with g1:
        st.metric("Delta (Δ)", f"{bs_results['delta']:.4f}", help="Sensitivity to underlying price change")
    with g2:
        st.metric("Gamma (Γ)", f"{bs_results['gamma']:.4f}", help="Rate of change of Delta")
    with g3:
        st.metric("Vega (𝒱)", f"{bs_results['vega']:.4f}", help="Change per 1% change in volatility")
    with g4:
        st.metric("Theta (Θ)", f"{bs_results['theta']:.4f}", help="Daily time decay")
    with g5:
        st.metric("Rho (ρ)", f"{bs_results['rho']:.4f}", help="Change per 1% change in risk-free rate")

    # Interactive Plots
    t_paths, t_dist, t_greeks, t_iv = st.tabs([
        "📈 Monte Carlo Simulated Paths",
        "📊 Terminal Price Distribution",
        "🌊 Greek Sensitivity Curves",
        "🔍 Implied Volatility Solver"
    ])

    with t_paths:
        time_grid = mc_results["time_grid"]
        sample_paths = mc_results["sample_paths"]

        fig_paths = go.Figure()
        for idx in range(min(40, len(sample_paths))):
            fig_paths.add_trace(go.Scatter(
                x=time_grid, y=sample_paths[idx],
                mode="lines", line=dict(width=1),
                opacity=0.4, showlegend=False
            ))
        # Add Strike Line
        fig_paths.add_hline(y=strike, line_dash="dash", line_color="#fb923c",
                            annotation_text=f"Strike ($K={strike})", annotation_position="top right")
        # Add Barrier Line if applicable
        if barrier_level is not None:
            fig_paths.add_hline(y=barrier_level, line_dash="dot", line_color="#f43f5e",
                                annotation_text=f"Barrier ($H={barrier_level})", annotation_position="top left")

        fig_paths.update_layout(
            title=f"Sample Monte Carlo Simulated GBM Asset Paths ({contract_style})",
            xaxis_title="Time (Years)",
            yaxis_title="Asset Price ($S_t$)",
            template="plotly_dark",
            height=450
        )
        st.plotly_chart(fig_paths, use_container_width=True)

    with t_dist:
        term_prices = mc_results["terminal_prices"]
        fig_hist = go.Figure()
        fig_hist.add_trace(go.Histogram(
            x=term_prices, nbinsx=60,
            marker_color="#38bdf8", opacity=0.75, name="Terminal Price Distribution"
        ))
        fig_hist.add_vline(x=strike, line_dash="dash", line_color="#fb923c",
                           annotation_text="Strike Price", annotation_position="top right")
        fig_hist.update_layout(
            title="Terminal Asset Price Distribution at Maturity T",
            xaxis_title="Asset Price at Maturity ($S_T$)",
            yaxis_title="Frequency",
            template="plotly_dark",
            height=450
        )
        st.plotly_chart(fig_hist, use_container_width=True)

    with t_greeks:
        s_range = np.linspace(max(5.0, s0 * 0.5), s0 * 1.5, 60)
        greek_deltas, greek_gammas, greek_vegas, greek_thetas = [], [], [], []
        for s_val in s_range:
            g = qe.AnalyticalBlackScholes.price_and_greeks(s_val, strike, maturity, r_rate, sigma, opt_code)
            greek_deltas.append(g["delta"])
            greek_gammas.append(g["gamma"])
            greek_vegas.append(g["vega"])
            greek_thetas.append(g["theta"])

        selected_greek = st.radio("Select Greek to Chart across Spot Price:", ["Delta", "Gamma", "Vega", "Theta"], horizontal=True)
        fig_greek = go.Figure()
        if selected_greek == "Delta":
            fig_greek.add_trace(go.Scatter(x=s_range, y=greek_deltas, mode="lines", line=dict(color="#38bdf8", width=3), name="Delta"))
        elif selected_greek == "Gamma":
            fig_greek.add_trace(go.Scatter(x=s_range, y=greek_gammas, mode="lines", line=dict(color="#34d399", width=3), name="Gamma"))
        elif selected_greek == "Vega":
            fig_greek.add_trace(go.Scatter(x=s_range, y=greek_vegas, mode="lines", line=dict(color="#a78bfa", width=3), name="Vega"))
        else:
            fig_greek.add_trace(go.Scatter(x=s_range, y=greek_thetas, mode="lines", line=dict(color="#fb923c", width=3), name="Theta"))

        fig_greek.add_vline(x=s0, line_dash="dash", line_color="#94a3b8", annotation_text="Current Spot Price")
        fig_greek.update_layout(
            title=f"Option {selected_greek} vs. Underlying Spot Price ($S$)",
            xaxis_title="Spot Price ($)",
            yaxis_title=f"{selected_greek} Value",
            template="plotly_dark",
            height=450
        )
        st.plotly_chart(fig_greek, use_container_width=True)

    with t_iv:
        c_iv1, c_iv2 = st.columns([1, 1])
        with c_iv1:
            market_quote = st.number_input("Observed Option Market Price ($):", min_value=0.01, max_value=500.0, value=float(f"{bs_results['price']:.2f}"), step=0.5)
            calc_iv = qe.AnalyticalBlackScholes.implied_volatility(s0, strike, maturity, market_quote, r_rate, opt_code)
            st.metric("Extracted Implied Volatility (IV)", f"{calc_iv * 100.0:.2f}%")
        with c_iv2:
            st.info(
                "Uses the **Newton-Raphson numerical algorithm** to iteratively invert the Black-Scholes formula:\n\n"
                r"$$\sigma_{n+1} = \sigma_n + \frac{C_{\text{market}} - C(\sigma_n)}{\mathcal{V}(\sigma_n)}$$"
            )


# ===========================================================================
# MODULE 3: BLACK-LITTERMAN PORTFOLIO OPTIMIZATION
# ===========================================================================
elif selected_module == "⚖️ Black-Litterman Portfolio Optimization":
    st.title("⚖️ Black-Litterman Asset Allocation & Efficient Frontier")
    st.markdown(
        r"Combines market equilibrium returns ($\Pi = \delta \Sigma w_{eq}$) with subjective investor views "
        "via Bayesian updating to generate optimal, well-diversified portfolio weight tilts."
    )

    tickers, hist_returns, cov_matrix, w_market = qe.load_stock_universe()

    col_p1, col_p2, col_p3 = st.columns(3)
    with col_p1:
        delta_param = st.slider("Risk Aversion Parameter (δ):", min_value=1.0, max_value=6.0, value=2.5, step=0.25)
    with col_p2:
        tau_param = st.slider("Prior Uncertainty Scalar (τ):", min_value=0.01, max_value=0.20, value=0.05, step=0.01)
    with col_p3:
        rf_rate = st.slider("Risk-Free Rate ($r_f$):", min_value=0.00, max_value=0.10, value=0.03, step=0.005)

    st.markdown("### 🎯 Configure Subjective Investor Views")
    st.caption("Specify relative or absolute performance views to tilt your portfolio away from the benchmark market weights.")

    c_v1, c_v2, c_v3, c_v4 = st.columns([1.5, 1, 1.5, 1.5])
    with c_v1:
        view_asset1 = st.selectbox("Asset 1:", tickers, index=0)
    with c_v2:
        view_rel = st.selectbox("Relation:", [">", "<", "="])
    with c_v3:
        view_asset2 = st.selectbox("Asset 2 (for relative view):", ["None"] + [t for t in tickers if t != view_asset1], index=2)
    with c_v4:
        view_pct = st.number_input("Expected Outperformance (%):", min_value=-50.0, max_value=50.0, value=3.0, step=0.5)

    views_list = []
    if view_rel == "=" or view_asset2 == "None":
        views_list.append((view_asset1, "=", None, view_pct / 100.0))
    else:
        views_list.append((view_asset1, view_rel, view_asset2, view_pct / 100.0))

    # Compute Black-Litterman
    mu_bl, w_star, tilts = qe.compute_black_litterman(
        cov_matrix, w_market, views_list, tickers, delta=delta_param, tau=tau_param
    )

    # Solve Efficient Frontier
    with st.spinner("Solving Markowitz Efficient Frontier..."):
        frontier_res = qe.solve_markowitz_frontier(mu_bl, cov_matrix, rf=rf_rate)

    # Allocations Bar Chart
    comp_df = pd.DataFrame({
        "Ticker": tickers,
        "Benchmark Market Weight": w_market * 100.0,
        "Black-Litterman Optimal Weight": w_star * 100.0,
        "Active Tilt (Δw)": tilts * 100.0,
        "Posterior Return": mu_bl * 100.0
    })

    tab_alloc, tab_front, tab_cov = st.tabs(["📊 Portfolio Allocation Tilts", "📈 Efficient Frontier", "🧮 Covariance & Returns"])

    with tab_alloc:
        fig_alloc = go.Figure()
        fig_alloc.add_trace(go.Bar(
            x=tickers, y=comp_df["Benchmark Market Weight"],
            name="Benchmark Market Weight (%)", marker_color="#64748b"
        ))
        fig_alloc.add_trace(go.Bar(
            x=tickers, y=comp_df["Black-Litterman Optimal Weight"],
            name="Black-Litterman Optimal Weight (%)", marker_color="#38bdf8"
        ))
        fig_alloc.update_layout(
            barmode="group",
            title="Portfolio Weights: Benchmark Equilibrium vs. Black-Litterman Tilts",
            xaxis_title="Asset Ticker",
            yaxis_title="Weight (%)",
            template="plotly_dark",
            height=450
        )
        st.plotly_chart(fig_alloc, use_container_width=True)

        st.markdown("#### Portfolio Tilt Summary Table")
        st.dataframe(comp_df.style.format({
            "Benchmark Market Weight": "{:.2f}%",
            "Black-Litterman Optimal Weight": "{:.2f}%",
            "Active Tilt (Δw)": "{:+.2f}%",
            "Posterior Return": "{:.2f}%"
        }), use_container_width=True)

    with tab_front:
        fig_front = go.Figure()
        # Individual Assets
        vols = np.sqrt(np.diag(cov_matrix))
        fig_front.add_trace(go.Scatter(
            x=vols * 100.0, y=mu_bl * 100.0,
            mode="markers+text", text=tickers, textposition="top center",
            name="Individual Assets", marker=dict(color="#f43f5e", size=10)
        ))
        # Efficient Frontier
        fig_front.add_trace(go.Scatter(
            x=np.array(frontier_res["frontier_vols"]) * 100.0,
            y=np.array(frontier_res["frontier_rets"]) * 100.0,
            mode="lines", name="Efficient Frontier (SLSQP)",
            line=dict(color="#38bdf8", width=3)
        ))
        # Tangency Portfolio
        fig_front.add_trace(go.Scatter(
            x=[frontier_res["tangency_vol"] * 100.0],
            y=[frontier_res["tangency_ret"] * 100.0],
            mode="markers+text", text=["Max Sharpe Tangent"], textposition="top right",
            name="Tangency Portfolio", marker=dict(color="#34d399", size=14, symbol="star")
        ))
        fig_front.update_layout(
            title="Markowitz Efficient Frontier & Capital Allocation Line",
            xaxis_title="Annualized Volatility (%)",
            yaxis_title="Expected Return (%)",
            template="plotly_dark",
            height=500
        )
        st.plotly_chart(fig_front, use_container_width=True)

    with tab_cov:
        fig_heat = px.imshow(
            cov_matrix,
            x=tickers, y=tickers,
            color_continuous_scale="Viridis",
            title="Annualized Asset Covariance Matrix (Σ)"
        )
        fig_heat.update_layout(template="plotly_dark", height=450)
        st.plotly_chart(fig_heat, use_container_width=True)


# ===========================================================================
# MODULE 4: TRIANGULAR FX ARBITRAGE RADAR
# ===========================================================================
elif selected_module == "💱 Triangular FX Arbitrage Radar":
    st.title("💱 Triangular Foreign Exchange (FX) Arbitrage Radar")
    st.markdown(
        "Monitors global currency exchange rates, computes cross-rate matrices using Dijkstra's shortest/maximum "
        "path graph theory, and automatically detects triangular riskless arbitrage cycles."
    )

    fx_raw_df = qe.load_fx_rates()
    default_currencies = ["USD", "EUR", "GBP", "JPY", "CAD", "AUD", "CHF", "CNY", "HKD", "SGD"]

    col_fx1, col_fx2, col_fx3 = st.columns(3)
    with col_fx1:
        selected_curr = st.multiselect("Currency Universe:", list(fx_raw_df["Currency"].unique()), default=default_currencies)
    with col_fx2:
        bid_fee = st.number_input("Brokerage Bid Fee (%):", min_value=0.00, max_value=1.00, value=0.00, step=0.01, format="%.2f")
    with col_fx3:
        ask_fee = st.number_input("Brokerage Ask Fee (%):", min_value=0.00, max_value=1.00, value=0.00, step=0.01, format="%.2f")

    if len(selected_curr) < 3:
        st.warning("Please select at least 3 currencies to analyze triangular cycles.")
    else:
        filtered_df = fx_raw_df[fx_raw_df["Currency"].isin(selected_curr)].copy()
        base_rates = filtered_df["Rate"].values
        curr_nodes = filtered_df["Currency"].values

        matrix_df = qe.compute_cross_rates_dijkstra("USD", curr_nodes, base_rates, bid_fee, ask_fee)
        opps_df = qe.detect_triangular_arbitrage(matrix_df)

        st.markdown(f"### 🌐 Cross-Rate Matrix ({len(selected_curr)} Currencies)")
        fig_fx_mat = px.imshow(
            matrix_df.astype(float),
            labels=dict(x="Quote Currency", y="Base Currency", color="Rate"),
            color_continuous_scale="Blues",
            title="Cross-Currency Exchange Matrix"
        )
        fig_fx_mat.update_layout(template="plotly_dark", height=450)
        st.plotly_chart(fig_fx_mat, use_container_width=True)

        st.markdown("### ⚡ Arbitrage Scanner Results")
        if len(opps_df) == 0:
            st.info("✅ **Market Efficiency Confirmed:** No triangular arbitrage cycles detected above transaction cost thresholds.")
        else:
            st.success(f"🚨 **Arbitrage Cycles Detected:** Found {len(opps_df)} profitable conversion loops!")
            st.dataframe(opps_df.style.format({
                "net_return": "{:.6f}",
                "profit_pct": "{:+.4f}%",
                "rate_1": "{:.6f}",
                "rate_2": "{:.6f}",
                "rate_3": "{:.6f}"
            }), use_container_width=True)


# ===========================================================================
# MODULE 5: METHODOLOGY & MATHEMATICAL FOUNDATIONS
# ===========================================================================
elif selected_module == "📖 Mathematical Methodology":
    st.title("📖 Mathematical Methodology & Academic Foundations")
    st.markdown("### Core Formulations Implemented in this Platform")

    st.markdown("#### 1. Black-Scholes-Merton Partial Differential Equation (1973)")
    st.latex(r"\frac{\partial V}{\partial t} + \frac{1}{2}\sigma^2 S^2 \frac{\partial^2 V}{\partial S^2} + r S \frac{\partial V}{\partial S} - r V = 0")
    st.markdown("Closed-form European Call solution:")
    st.latex(r"C(S, t) = S N(d_1) - K e^{-r(T-t)} N(d_2)")
    st.latex(r"d_1 = \frac{\ln(S/K) + (r + \frac{1}{2}\sigma^2)(T-t)}{\sigma \sqrt{T-t}}, \quad d_2 = d_1 - \sigma \sqrt{T-t}")

    st.markdown("#### 2. Vectorized Monte Carlo Geometric Brownian Motion")
    st.latex(r"S_{t+\Delta t} = S_t \exp\left( \left(r - \frac{1}{2}\sigma^2\right)\Delta t + \sigma \sqrt{\Delta t} Z \right), \quad Z \sim \mathcal{N}(0, 1)")

    st.markdown("#### 3. Black-Litterman Bayesian Asset Allocation (He & Litterman 1999)")
    st.markdown("Implied Equilibrium Prior Returns via Reverse Optimization:")
    st.latex(r"\Pi = \delta \Sigma w_{\text{mkt}}")
    st.markdown("Master Black-Litterman Posterior Expected Returns:")
    st.latex(r"\mu_{\text{BL}} = \left[ (\tau \Sigma)^{-1} + P^T \Omega^{-1} P \right]^{-1} \left[ (\tau \Sigma)^{-1} \Pi + P^T \Omega^{-1} Q \right]")
    st.markdown(r"Where $\Omega = \tau \text{diag}(P \Sigma P^T)$ reflects uncertainty proportional to view portfolio variance.")

    st.markdown("#### 4. Term Structure Bootstrapping & Forward Rates")
    st.latex(r"P(0, T) = \exp\left( -s(T) \cdot T \right)")
    st.latex(r"F(t_1, t_2) = \frac{1}{t_2 - t_1}\left( \frac{s(t_2) t_2 - s(t_1) t_1}{1} \right)")

    st.markdown("---")
    st.caption("QuantFin Analytics Platform | Engineered by Asef Haque | Ready for Production Deployment")
