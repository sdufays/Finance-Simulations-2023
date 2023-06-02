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
    # these functions will be called when iterating through both months and loans in portfolio
    def beginning_balance(month):
        if month == 1:
            return 0
        else:
            return ending_balance(month-1)

    def principal_paydown(month, loan):
        if month == loan.get_term_length():
            return beginning_balance(month)
        else:
            return 0

    def ending_balance(month, loan):
        # NEED TO FIND FUNDING AMOUNT
        funding_amount = 0
        return beginning_balance(month) + funding_amount - principal_paydown(month, loan)

    def interest_income(month, loan, INDEX_VALUE):
        return beginning_balance(month) * (loan.get_spread() + max(loan.get_index_floor(), INDEX_VALUE) * days_in_month[month-1] / 360)

    # -------------------------- WITH REINVESTMENT (these are so confusing)-------------------------
    def beginning_balance_rein(month, loan):
      if month <= loan.get_term_length():
        return 0
      else:
        return ending_balance_rein(month - 1, loan)

    def ending_balance_rein(month, loan):
      return (beginning_balance_rein(month, loan) + funding_amount_rein(month, loan) - principal_paydown_rein(month, loan))

    def funding_amount_rein(month, loan, rein_period):
      if month == loan.get_term_length() and month < rein_period:
        return ending_balance_rein(month - 1, loan)
      else:
        return 0

    def principal_paydown_rein(month, loan):
      if month == loan.get_term_length():
        return(beginning_balance_rein(month - 1, loan))
      else:
        return 0

    def interest_income_rein(month, loan, INDEX_VALUE):
      return(beginning_balance_rein(month, loan) * (loan.get_spread() + max(loan.get_index_floor(), INDEX_VALUE) * days_in_month[month-1] / 360))

    
    loan_index = 1
    while loan_index in range(len(loan_portfolio)):
        d=''
        # iterate through loans in portfolio and store the four above calculations somewhere (where??)