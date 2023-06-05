from collateral_class import CollateralPortfolio

if __name__ == "__main__":
    po = CollateralPortfolio()
    po.add_initial_loan(1, 79375000, 0.03650, 0.02188, 34, 12, 15)
    po.add_initial_loan(2, 72080000, 0.0389, 0.00250, 20, 12, 15)
    # print(po.get_portfolio())

    for loan in po.get_portfolio():
        print(loan.get_loan_balance())

    print(po.get_collateral_sum())