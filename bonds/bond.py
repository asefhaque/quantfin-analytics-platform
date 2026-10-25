import math


class Bond:

    def __init__(self, name, coupon, issue_date, maturity_date, compounding_frequency=2):
        self._name = name
        self._coupon = coupon
        self._issue_date = issue_date
        self._maturity_date = maturity_date
        self._compounding_frequency = compounding_frequency
        self._count_coupon_payments = 1 if (name in ['1m', '3m', '6m', '9m']) \
            else int((maturity_date - issue_date) / 10000 * compounding_frequency)
        self._price = 0.0
        self._face_value = 1000.0

    def get_name(self):
        return self._name

    def get_tenor_in_years(self):
        name_clean = self._name.lower().strip()
        if name_clean == "3m":
            return 0.25
        elif name_clean == "6m":
            return 0.50
        elif name_clean == "9m":
            return 0.75
        elif name_clean.endswith("m"):
            return float(name_clean[:-1]) / 12.0
        elif name_clean.endswith("y"):
            return float(name_clean[:-1])
        return int(self._maturity_date - self._issue_date) / 10000.0

    def get_coupon(self):
        return self._coupon

    def get_issue_date(self):
        return self._issue_date

    def get_maturity_date(self):
        return self._maturity_date

    def get_compounding_frequency(self):
        return self._compounding_frequency

    def get_price(self):
        return self._price

    def set_price(self, price, face_value=1000.0):
        self._price = price
        self._face_value = face_value

    def compute_ytm(self):
        """ Computes the bond yield-to-maturity via bisection method

        :return: yield to maturity
        """
        ytm, tolerance = 0.0, 0.0001
        a, b, c = 0.0, 100.0, 0.0

        while True:
            fa = self.compute_price(self._face_value,
                                    self._coupon / 100.0 / self._compounding_frequency,
                                    a / 100.0 / self._compounding_frequency,
                                    self._count_coupon_payments) - self._price / 100.0 * self._face_value
            fb = self.compute_price(self._face_value,
                                    self._coupon / 100.0 / self._compounding_frequency,
                                    b / 100.0 / self._compounding_frequency,
                                    self._count_coupon_payments) - self._price / 100.0 * self._face_value

            if math.fabs(fa) <= tolerance:
                ytm = a
                break
            elif math.fabs(fb) <= tolerance:
                ytm = b
                break
            elif fa * fb < 0.0:
                c = (a + b) / 2.0
                fc = self.compute_price(self._face_value,
                                        self._coupon / 100.0 / self._compounding_frequency,
                                        c / 100.0 / self._compounding_frequency,
                                        self._count_coupon_payments) - self._price / 100.0 * self._face_value
                if math.fabs(fc) <= tolerance:
                    ytm = c
                    break
                if fa * fc < 0.0:
                    b = c
                else:
                    a = c
            else:
                print("Problem:  Lower and upper bounds of the starting range does not have a root.")
                return -1.0
        return ytm

    def bootstrap_spot_rate(self, spot_rates, index_tenor_start, index_tenor_end, time_period=0.50):
        ytm, tolerance = 0.0, 0.0001
        a, b, c = 0.0, 20.0, 0.0
        target_price = self._price / 100.0 * self._face_value

        # setup working spot rates
        spot_rates_a = list(spot_rates[:index_tenor_end + 1])
        spot_rates_b = list(spot_rates[:index_tenor_end + 1])
        spot_rates_c = list(spot_rates[:index_tenor_end + 1])

        while True:
            # set starting spot rates
            for i in range(index_tenor_start + 1, index_tenor_end + 1):
                spot_rates_a[i] = spot_rates[index_tenor_start] + \
                                  (a - spot_rates[index_tenor_start]) * (i - index_tenor_start) / \
                                  (index_tenor_end - index_tenor_start)
                spot_rates_b[i] = spot_rates[index_tenor_start] + \
                                  (b - spot_rates[index_tenor_start]) * (i - index_tenor_start) / \
                                  (index_tenor_end - index_tenor_start)

            fa = (self.compute_price_from_spot(self._face_value, self._coupon,
                                               spot_rates_a, self._count_coupon_payments,
                                               time_period, self._compounding_frequency)
                  - target_price)
            fb = (self.compute_price_from_spot(self._face_value, self._coupon,
                                               spot_rates_b, self._count_coupon_payments,
                                               time_period, self._compounding_frequency)
                  - target_price)

            if math.fabs(fa) <= tolerance:
                for i in range(index_tenor_start + 1, index_tenor_end + 1):
                    spot_rates[i] = spot_rates_a[i]
                ytm = a
                break

            elif math.fabs(fb) <= tolerance:
                for i in range(index_tenor_start + 1, index_tenor_end + 1):
                    spot_rates[i] = spot_rates_b[i]
                ytm = b
                break

            elif fa * fb < 0.0:
                c = (a + b) / 2.0

                for i in range(index_tenor_start + 1, index_tenor_end + 1):
                    spot_rates_c[i] = spot_rates[index_tenor_start] + (
                            c - spot_rates[index_tenor_start]) * (i - index_tenor_start) / (
                                              index_tenor_end - index_tenor_start)

                fc = (self.compute_price_from_spot(
                    self._face_value,
                    self._coupon,
                    spot_rates_c,
                    self._count_coupon_payments,
                    time_period,
                    self._compounding_frequency) - target_price)

                if math.fabs(fc) <= tolerance:
                    for i in range(index_tenor_start + 1, index_tenor_end + 1):
                        spot_rates[i] = spot_rates_c[i]
                    ytm = c
                    break

                if fa * fc < 0.0:
                    b = c
                else:
                    a = c

            else:
                print("Problem: Lower and upper bounds of the starting range does not have a root.")
                return -1.0

        return ytm

    @classmethod
    def compute_price(cls, face_value, coupon, ytm, count_coupon_payments):
        price = 0.0
        for i in range(count_coupon_payments):
            price += coupon * face_value / math.pow(1.0 + ytm, i + 1)
        price += face_value / math.pow(1.0 + ytm, count_coupon_payments)
        return price

    @classmethod
    def compute_price_from_spot(cls, face_value, coupon, spot_rates, count_coupon_payments,
                                time_period=0.50, compounding_frequency=2):
        price = 0.0
        coupon_cash = (coupon / 100.0 / compounding_frequency) * face_value
        for k in range(1, count_coupon_payments + 1):
            t_k = k / compounding_frequency
            idx = int(round(t_k / time_period)) - 1
            rate = spot_rates[idx] / 100.0 / compounding_frequency
            price += coupon_cash / math.pow(1.0 + rate, k)

        t_mat = count_coupon_payments / compounding_frequency
        idx_mat = int(round(t_mat / time_period)) - 1
        rate_mat = spot_rates[idx_mat] / 100.0 / compounding_frequency
        price += face_value / math.pow(1.0 + rate_mat, count_coupon_payments)
        return price
