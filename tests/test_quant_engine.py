import quant_engine as qe

print("1. Testing Term Structure...")
m_df, c_df, val = qe.run_term_structure_analysis("3M")
print(f"Term Structure OK! Computed {len(c_df)} tenors. Overall status: {val['overall_status']}")

print("\n2. Testing Black-Scholes & Greeks...")
bs = qe.AnalyticalBlackScholes.price_and_greeks(100, 100, 1.0, 0.05, 0.20, 'C')
print(f"BS Price: {bs['price']:.4f}, Delta: {bs['delta']:.4f}, Gamma: {bs['gamma']:.4f}")

print("\n3. Testing Binomial Tree...")
bin_res = qe.price_binomial_tree(100, 100, 1.0, 0.05, 0.20, 'C', 'E', 50)
print(f"Binomial Price: {bin_res['price']:.4f}")

print("\n4. Testing Monte Carlo...")
mc = qe.simulate_monte_carlo(100, 100, 1.0, 0.05, 0.20, 'C', 'Vanilla', n_sims=5000, n_steps=50)
print(f"Monte Carlo Price: {mc['price']:.4f} +/- {mc['std_error']:.4f}")

print("\n5. Testing Black-Litterman...")
tickers, rets, cov, w_mkt = qe.load_stock_universe()
mu_bl, w_star, tilts = qe.compute_black_litterman(cov, w_mkt, [('AAPL', '>', 'GOOG', 0.03)], tickers)
print(f"Black-Litterman OK! Tickers: {tickers[:4]}... w_star sum: {sum(w_star):.4f}")

print("\n6. Testing FX Engine...")
fx_df = qe.load_fx_rates()
print(f"FX Rates loaded: {len(fx_df)} currencies.")

print("\n>>> ALL TESTS PASSED SUCCESSFULLY! <<<")
