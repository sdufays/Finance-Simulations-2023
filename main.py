import random
from collateral_class import CollateralPortfolio
from clo_class import CLO

if __name__ == "__main__":
    # ------------------------ SCENARIOS ------------------------ #
    base = [.33, .33, .34]
    downside = [.30, .25, .45]
    upside = [.40, .35, .25]

    # import the data into these from excel
    clo = CLO()
    loan_portfolio = CollateralPortfolio()



    if clo.get_ramp_up():
        # after one month
        liability_balance = clo.get_tob()
        # total amount getting in loans
        collateral_balance = loan_portfolio.get_collateral_sum()
    
    if liability_balance > collateral_balance:
        # make new loan of size liability - collateral
        newloan = Loan(...)

    # AFTER A MONTH:
    # add new loan with collateral balance liability - collateral


    # remember here loan index starts at 0
    # but if we use the loan_id attribute then it would start at 1
    # not sure where this code should go (in the loan class? or outside while iterating through collateral_portfolio)
    def get_beginning_balance(loan_index):
        if loan_index == 1:
            beginning_balance = 0
        else:
            beginning_balance = get_ending_balance(loan_index-1)
        return beginning_balance

    def get_principal_paydown(loan_index):
        if loan_index == collateral_portfolio[loan_index].get_loan_term():
            return get_beginning_balance(loan_index)
        else:
            return 0

    def get_ending_balance(loan_index):
        # NEED TO FIND FUNDING AMOUNT
        funding_amount = 0
        return get_beginning_balance(loan_index) + funding_amount - get_principal_paydown(loan_index)

    def get_interest_income(loan_index, days_in_month):
        return get_beginning_balance(loan_index) * (collateral_portfolio[loan_index].get_spread() + max(collateral_portfolio[loan_index].get_index_floor(), loan_index) * days_in_month / 360)

    loan_index = 1
    while loan_index in range(len(collateral_portfolio)):
        d=''
        # iterate through loans in portfolio and store the four above calculations somewhere (where??)

    # ------------------------ REINVESTMENT COLLATERAL ------------------------ #
