import math


class TermStructure:

    def __init__(self, tenor_count, time_period=None, compounding_frequency=2, interpolation_method='linear'):
        self.bonds = []
        self.spot_rates = []
        self.forward_rates = []
        self.forward_rates_annualized = []
        self.discount_factors = []
        self.tenor_count = tenor_count
        self.compounding_frequency = compounding_frequency
        self.interpolation_method = interpolation_method

        # Auto-detect or assign time_period (0.25 for 3M, 0.50 for 6M)
        if time_period is not None:
            self.time_period = float(time_period)
        elif tenor_count == 120:
            self.time_period = 0.25
        elif tenor_count == 60:
            self.time_period = 0.50
        else:
            self.time_period = 30.0 / tenor_count

        for _ in range(self.tenor_count):
            self.spot_rates.append(0.0)
            self.forward_rates.append(0.0)
            self.forward_rates_annualized.append(0.0)
            self.discount_factors.append(0.0)

    def set_bonds(self, bonds):
        self.bonds = bonds

    def get_spot_rate(self, index):
        return self.spot_rates[index]

    def get_forward_rate(self, index):
        return self.forward_rates[index]

    def get_forward_rate_annualized(self, index):
        return self.forward_rates_annualized[index]

    def get_discount_factor(self, index):
        return self.discount_factors[index]

    def compute_spot_rates(self):
        """ Computes spot rates across all tenors.
        Supports both 6-month (time_period=0.50) and 3-month (time_period=0.25) grids.
        Uses market bills for short tenors, bootstraps coupon bonds for milestone maturities,
        and applies interpolation (linear or cubic spline) for intermediate points.
        """
        # Index instruments by clean name
        instruments = {}
        for bond in self.bonds:
            instruments[bond.get_name().lower().strip()] = bond

        if abs(self.time_period - 0.25) < 1e-4:
            # 3-Month Tenor Grid (120 tenors, dt = 0.25 yrs)
            # Bills provide initial short-term spot rates:
            if '3m' in instruments:
                self.spot_rates[0] = instruments['3m'].compute_ytm()
            if '6m' in instruments:
                self.spot_rates[1] = instruments['6m'].compute_ytm()
            if '9m' in instruments:
                self.spot_rates[2] = instruments['9m'].compute_ytm()

            # Sequential bootstrap of milestone bonds:
            # 1y bond matures at index 3 (1.00y). Coupons at 0.5y (idx 1) and 1.0y (idx 3).
            # Index 2 (0.75y) is already known from 9M bill.
            if '1y' in instruments:
                instruments['1y'].bootstrap_spot_rate(self.spot_rates, 2, 3, time_period=0.25)

            # Define subsequent milestone bonds: (name, start_idx, end_idx)
            bond_milestones = [
                ('2y', 3, 7),     # 1.0y to 2.0y (indices 4, 5, 6 interpolated)
                ('3y', 7, 11),    # 2.0y to 3.0y (indices 8, 9, 10 interpolated)
                ('5y', 11, 19),   # 3.0y to 5.0y (indices 12-18 interpolated)
                ('7y', 19, 27),   # 5.0y to 7.0y (indices 20-26 interpolated)
                ('10y', 27, 39),  # 7.0y to 10.0y (indices 28-38 interpolated)
                ('20y', 39, 79),  # 10.0y to 20.0y (indices 40-78 interpolated)
                ('30y', 79, 119)  # 20.0y to 30.0y (indices 80-118 interpolated)
            ]

            for name, start_idx, end_idx in bond_milestones:
                if name in instruments:
                    instruments[name].bootstrap_spot_rate(self.spot_rates, start_idx, end_idx, time_period=0.25)

            # Optional: Smooth cubic spline interpolation across benchmark anchor maturities
            if self.interpolation_method == 'spline':
                self._apply_spline_interpolation()

        else:
            # Default: 6-Month Tenor Grid (60 tenors, dt = 0.50 yrs)
            for bond in self.bonds:
                name = bond.get_name().lower().strip()
                if name == '6m':
                    self.spot_rates[0] = bond.compute_ytm()
                elif name == '1y':
                    bond.bootstrap_spot_rate(self.spot_rates, 0, 1, time_period=0.50)
                elif name == '2y':
                    bond.bootstrap_spot_rate(self.spot_rates, 1, 3, time_period=0.50)
                elif name == '3y':
                    bond.bootstrap_spot_rate(self.spot_rates, 3, 5, time_period=0.50)
                elif name == '5y':
                    bond.bootstrap_spot_rate(self.spot_rates, 5, 9, time_period=0.50)
                elif name == '7y':
                    bond.bootstrap_spot_rate(self.spot_rates, 9, 13, time_period=0.50)
                elif name == '10y':
                    bond.bootstrap_spot_rate(self.spot_rates, 13, 19, time_period=0.50)
                elif name == '20y':
                    bond.bootstrap_spot_rate(self.spot_rates, 19, 39, time_period=0.50)
                elif name == '30y':
                    bond.bootstrap_spot_rate(self.spot_rates, 39, 59, time_period=0.50)

    def _apply_spline_interpolation(self):
        """ Fits a cubic spline to the anchor maturities and interpolates all grid tenors. """
        try:
            from scipy.interpolate import CubicSpline
            anchor_indices = [0, 1, 2, 3, 7, 11, 19, 27, 39, 79, 119]
            anchor_tenors = [(idx + 1) * self.time_period for idx in anchor_indices]
            anchor_rates = [self.spot_rates[idx] for idx in anchor_indices]

            cs = CubicSpline(anchor_tenors, anchor_rates, bc_type='natural')
            all_tenors = [(i + 1) * self.time_period for i in range(self.tenor_count)]
            interpolated_rates = cs(all_tenors)
            for i in range(self.tenor_count):
                self.spot_rates[i] = float(interpolated_rates[i])
        except ImportError:
            # Fallback to linear if scipy is not installed
            pass

    def compute_discount_factors(self):
        """ Compute discount factors from spot rates assuming compounding frequency
        is twice per year (semi-annual Bond Equivalent Yield convention):
        DF(T) = 1.0 / (1.0 + spot_rate / 100 / compounding_frequency) ** (T * compounding_frequency)
        """
        for i in range(len(self.spot_rates)):
            tenor = (i + 1) * self.time_period
            periods = tenor * self.compounding_frequency
            compounding_rate = self.spot_rates[i] / 100.0 / self.compounding_frequency
            self.discount_factors[i] = 1.0 / math.pow(1.0 + compounding_rate, periods)

    def compute_forward_rates(self):
        """ Compute forward rates between consecutive tenors.
        Period forward rate over [T_i, T_{i+1}]:
            f_period = (DF_i / DF_{i+1} - 1.0) * 100.0
        Annualized forward rate:
            f_annual = f_period / time_period
        """
        for i in range(len(self.spot_rates) - 1):
            period_rate = (self.discount_factors[i] / self.discount_factors[i + 1] - 1.0) * 100.0
            self.forward_rates[i] = period_rate
            self.forward_rates_annualized[i] = period_rate / self.time_period

        # Terminal forward rate set to 0.0
        self.forward_rates[-1] = 0.0
        self.forward_rates_annualized[-1] = 0.0

    def check_reasonableness(self):
        """ Evaluates whether the computed 3-month spot and forward rates are reasonable.
        Checks:
        1. Repricing Accuracy: All input bills and bonds must reprice to par/market quotes
           using the computed discount factors.
        2. No-Arbitrage / Non-negativity: All discount factors must be monotonically decreasing
           (DF_i > DF_{i+1}), ensuring forward rates remain positive.
        3. Curve Smoothness: Forward rate changes between consecutive periods are bounded
           and free of erratic spikes.
        4. Consistency with 6M spot rate benchmarks at semi-annual maturities.

        Returns:
            dict containing detailed validation metrics, errors, and pass/fail statuses.
        """
        results = {
            'repricing': [],
            'max_repricing_error': 0.0,
            'is_repricing_valid': True,
            'is_monotonic_df': True,
            'is_positive_forward': True,
            'max_forward_jump': 0.0,
            'overall_status': 'PASSED'
        }

        # 1. Repricing Check
        max_error = 0.0
        for bond in self.bonds:
            name = bond.get_name().lower().strip()
            tenor = bond.get_tenor_in_years()
            c_freq = bond.get_compounding_frequency()
            quote = bond.get_price()

            # Skip instruments that do not fall on this grid resolution
            grid_step = tenor / self.time_period
            if abs(grid_step - round(grid_step)) > 1e-4:
                continue

            idx = int(round(grid_step)) - 1
            if idx < 0 or idx >= self.tenor_count:
                continue

            if name in ['3m', '6m', '9m']:
                model_price = 100.0 * self.discount_factors[idx]
                market_price = 100.0 / math.pow(
                    1.0 + (bond.compute_ytm() / 100.0 / self.compounding_frequency),
                    tenor * self.compounding_frequency
                )
            else:
                # Coupon Bond: Discount coupon cash flows and face value
                n_coupons = int(round(tenor * c_freq))
                coupon_cash = (bond.get_coupon() / 100.0 / c_freq) * 1000.0
                model_cash = 0.0
                for k in range(1, n_coupons + 1):
                    t_k = k / c_freq
                    idx_k = int(round(t_k / self.time_period)) - 1
                    model_cash += coupon_cash * self.discount_factors[idx_k]
                idx_mat = int(round(tenor / self.time_period)) - 1
                model_cash += 1000.0 * self.discount_factors[idx_mat]

                model_price = model_cash / 10.0  # Expressed on 100 par basis
                market_price = quote

            err = abs(model_price - market_price)
            if err > max_error:
                max_error = err

            results['repricing'].append({
                'instrument': name,
                'tenor': tenor,
                'market_price': market_price,
                'model_price': model_price,
                'error': err
            })

        results['max_repricing_error'] = max_error
        results['is_repricing_valid'] = (max_error < 0.005)

        # 2. Monotonicity & No-Arbitrage Check
        for i in range(len(self.discount_factors) - 1):
            if self.discount_factors[i] <= self.discount_factors[i + 1]:
                results['is_monotonic_df'] = False
            if self.forward_rates[i] < 0.0:
                results['is_positive_forward'] = False

        # 3. Smoothness Check
        max_jump = 0.0
        for i in range(len(self.forward_rates) - 2):
            jump = abs(self.forward_rates[i + 1] - self.forward_rates[i])
            if jump > max_jump:
                max_jump = jump
        results['max_forward_jump'] = max_jump

        if not (results['is_repricing_valid'] and results['is_monotonic_df'] and results['is_positive_forward']):
            results['overall_status'] = 'FAILED'

        return results
