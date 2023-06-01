from collateral_class import CollateralPortfolio
from clo_class import CLO

if __name__ == "__main__":
    # ------------------------ SCENARIOS ------------------------ #
    base = [.33, .33, .34]
    downside = [.30, .25, .45]
    upside = [.40, .35, .25]

    # ------------------------ IMPORTING DATA FROM EXCEL ------------------------ #
    clo = CLO(False) # need rampup here
    # add tranches
    clo.add_tranche("various parameters")
  
    loan_portfolio = CollateralPortfolio()
    # add loans
    loan_portfolio.add_loan("various parameters")
  
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

    # ------------------------ VARIOUS FUNCTIONS ------------------------ #
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

    # ------------------------ REINVESTMENT FUNCTIONS ------------------------ #
