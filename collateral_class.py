from loan_class import Loan

class CollateralPortfolio(Loan):
    def __init__(self):
        self.__portfolio = []

    def add_loan(self, loan_id, collateral_balance, margin, index_floor, remaining_loan_term, extension_period, open_prepayment_period):
        loan = Loan(loan_id, collateral_balance, margin, index_floor, remaining_loan_term, extension_period, open_prepayment_period)
        self.__portfolio.append(loan)

    def get_collateral_sum(collateral_portfolio):
        sum = 0
        for loan in collateral_portfolio:
            sum+=loan.get_collateral_balance()