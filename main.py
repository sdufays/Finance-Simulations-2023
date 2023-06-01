from collateral_class import CollateralPortfolio
from clo_class import CLO

if __name__ == "__main__":
    # ------------------------ SCENARIOS ------------------------ #
    base = [.33, .33, .34]
    downside = [.30, .25, .45]
    upside = [.40, .35, .25]

    # leap year?
    days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

    clo = CLO(False) # need rampup here
    threshold = clo.get_clo_threshold()
    # add tranches
    clo.add_tranche("various parameters")

  
    loan_portfolio = CollateralPortfolio()
    # add loans
    loan_portfolio.add_loan("various parameters")
    loan_portfolio.generate_loan_terms(base)
  
    # OTHER SPECIFICATIONS NEEDED:
    """
    reinvestment_period = 
    deal_start_month = 
    deal_end_threshold = 
    """

    # ------------------------ RAMP UP CALCULATIONS ------------------------ #
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

    # ------------------------ VARIOUS FUNCTIONS (A BIG MESS RN) ------------------------ #
    # I just realized i = month... so these are WRONG IGNORE
    # this has reinvestment
    def get_beginning_balance(reinvestment, month, loan:
        if (reinvestment and month <= loan.get_term_length()) or (month == 1)
            return 0
        else:
            return get_ending_balance(month - 1)

    def get_principal_paydown(reinvestment, month, loan):
        if month == loan.get_term_length():
            return get_beginning_balance(reinvestment, month, loan)
        else:
            return 0

    def get_ending_balance(reinvestment, month, loan):
        # NEED TO FIND FUNDING AMOUNT
        funding_amount = 0
        return get_beginning_balance(reinvestment, month, loan) + funding_amount - get_principal_paydown(loan_index)

    def get_interest_income(loan_index, days_in_month):
        return get_beginning_balance(loan_index) * (collateral_portfolio[loan_index].get_spread() + max(collateral_portfolio[loan_index].get_index_floor(), loan_index) * days_in_month / 360)

    loan_index = 1
    while loan_index in range(len(collateral_portfolio)):
        d=''
        # iterate through loans in portfolio and store the four above calculations somewhere (where??)