from loan_class import Loan

def CollateralPortfolio(Loan):
    def __init__(self):
        self.__portfolio = []

    def add_loan(self, loan):
        self.__portfolio.append(loan)

    def get_collateral_sum(collateral_portfolio):
        sum = 0
        for loan in collateral_portfolio:
            sum+=loan.get_collateral_balance()