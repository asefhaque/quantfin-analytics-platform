import matplotlib.pylab as plt
import seaborn as sns

from bonds.bill import Bill
from bonds.bond import Bond
from bonds.read_bond_info import read_bills_from_file, read_bonds_from_file
from term_structure.term_structure import TermStructure


def main():
    # bonds and bills filenames
    bills_data_file = "data/bills.txt"
    bonds_data_file = "data/bonds.txt"
    bonds = []

    # read bills from a file and instantiate bond objects
    #
    bill_instruments = read_bills_from_file(bills_data_file)
    for bill_instrument in bill_instruments:
        bill = Bill(bill_instrument[0], bill_instrument[1], bill_instrument[2], bill_instrument[3])
        bill.set_price(float(bill_instrument[3]))
        bonds.append(bill)

    # read bonds from a file and instantiate bond objects
    #
    bond_instruments = read_bonds_from_file(bonds_data_file)
    for bond_instrument in bond_instruments:
        bond = Bond(bond_instrument[0], bond_instrument[1], bond_instrument[2],
                    bond_instrument[3], bond_instrument[4])
        bond.set_price(float(bond_instrument[5]))
        bonds.append(bond)

    # compute yield-to-maturities for bonds
    #
    tenors_from_bonds, ytm_from_bonds = [], []
    for bond in bonds:
        tenors_from_bonds.append(bond.get_tenor_in_years())
        ytm_from_bonds.append(bond.compute_ytm())

    # print bonds
    #
    print(f'Name\tCoupon\tIssueDate\tMaturityDate\tQuote\t\tYTM')
    for bond in bonds:
        print(f'{bond.get_name()}\t{bond.get_coupon():10.4f}' +
              f'\t{bond.get_issue_date()}\t{bond.get_maturity_date()}' +
              f'\t{bond.get_price():10.4f}\t{bond.compute_ytm():10.4f}')

    # build the term structure
    # Supports both 3-Month ('3M': 120 tenors, 0.25 yrs) and 6-Month ('6M': 60 tenors, 0.50 yrs)
    #
    forward_rate_tenors = {
        '3M': (120, 0.25),
        '6M': (60, 0.50)
    }

    for forward_rate_tenor in forward_rate_tenors.keys():
        tenor_count = forward_rate_tenors[forward_rate_tenor][0]
        time_period = forward_rate_tenors[forward_rate_tenor][1]

        term_structure = TermStructure(tenor_count, time_period=time_period)
        term_structure.set_bonds(bonds)
        term_structure.compute_spot_rates()
        term_structure.compute_discount_factors()
        term_structure.compute_forward_rates()

        tenors = [(i + 1) * time_period for i in range(tenor_count)]
        spot_rates, forward_rates, forward_rates_ann, discount_factors = [], [], [], []
        for i in range(tenor_count):
            spot_rates.append(term_structure.get_spot_rate(i))
            forward_rates.append(term_structure.get_forward_rate(i))
            forward_rates_ann.append(term_structure.get_forward_rate_annualized(i))
            discount_factors.append(term_structure.get_discount_factor(i))

        print(f'\n========================================================================================')
        print(f'                    TERM STRUCTURE RESULTS ({forward_rate_tenor} GRID)')
        print(f'========================================================================================')
        print(f'Index\tTenor\tSpot Rate\tDiscount Factor\tFwd {forward_rate_tenor} (Period)\tFwd {forward_rate_tenor} (Annualized)')
        for i in range(tenor_count):
            tenor = (i + 1) * time_period
            print(f'{i:3d}\t' +
                  f'{tenor:4.2f}y\t{term_structure.get_spot_rate(i):9.4f}%' +
                  f'\t{term_structure.get_discount_factor(i):10.4f}' +
                  f'\t{term_structure.get_forward_rate(i):14.4f}%' +
                  f'\t{term_structure.get_forward_rate_annualized(i):14.4f}%')

        # Reasonableness validation checks
        validation = term_structure.check_reasonableness()
        print(f'\n----------------------------------------------------------------------------------------')
        print(f'                   REASONABLENESS & SANITY CHECK REPORT ({forward_rate_tenor})')
        print(f'----------------------------------------------------------------------------------------')
        print(f'Instrument\tTenor\tMarket Price\tModel Reprice\tPricing Error\tStatus')
        for item in validation['repricing']:
            status = 'PASS' if item['error'] < 0.005 else 'FAIL'
            print(f"{item['instrument']:10s}\t{item['tenor']:4.2f}y\t{item['market_price']:10.4f}\t{item['model_price']:10.4f}\t{item['error']:10.6f}\t{status}")

        print(f"\n1. Maximum Repricing Error: {validation['max_repricing_error']:.6f} -> {'[PASSED]' if validation['is_repricing_valid'] else '[FAILED]'}")
        print(f"2. Monotonic Discount Factors (No Negative Forward Rates): -> {'[PASSED]' if validation['is_monotonic_df'] else '[FAILED]'}")
        print(f"3. Non-Negative Forward Rates: -> {'[PASSED]' if validation['is_positive_forward'] else '[FAILED]'}")
        print(f"4. Maximum Forward Rate Step Jump: {validation['max_forward_jump']:.4f}%")
        print(f"OVERALL REASONABLENESS STATUS: [{validation['overall_status']}]")
        print(f'========================================================================================\n')

        # plot spot and forward rates and discount factors
        fig, (ax0, ax1, ax2) = plt.subplots(figsize=(9, 12), nrows=3)

        ax0.plot(tenors, spot_rates, linewidth=2, color='blue', label=f'Spot Rate ({forward_rate_tenor})')
        ax0.grid(True)
        ax0.set_title(f'Term Structure of Spot Rates ({forward_rate_tenor})', color='blue', fontsize=12, fontweight='bold')
        ax0.set_xlabel('Tenor (yrs)')
        ax0.set_ylabel('Spot Rate (%)')
        ax0.legend(loc='lower right')

        ax1.plot(tenors[:-1], forward_rates[:-1], linewidth=2, color='green', label=f'Forward Rate (Period)')
        ax1.plot(tenors[:-1], forward_rates_ann[:-1], linewidth=1.5, color='darkorange', linestyle='--', label=f'Forward Rate (Annualized)')
        ax1.grid(True)
        ax1.set_title(f'Term Structure of Forward Rates ({forward_rate_tenor})', color='green', fontsize=12, fontweight='bold')
        ax1.set_xlabel('Tenor (yrs)')
        ax1.set_ylabel(f'Forward Rate (%)')
        ax1.legend(loc='lower right')

        ax2.plot(tenors, discount_factors, linewidth=2, color='red', label=f'Discount Factor ({forward_rate_tenor})')
        ax2.grid(True)
        ax2.set_title(f'Term Structure of Discount Factors ({forward_rate_tenor})', color='red', fontsize=12, fontweight='bold')
        ax2.set_xlabel('Tenor (yrs)')
        ax2.set_ylabel('Discount Factor')
        ax2.legend(loc='upper right')

        plt.subplots_adjust(hspace=0.45)
        plot_filename = f'term_structure_{forward_rate_tenor}.png'
        fig.savefig(plot_filename, dpi=300, bbox_inches='tight')
        print(f'Saved plot to {plot_filename}')
        plt.show()


if __name__ == '__main__':
    main()
