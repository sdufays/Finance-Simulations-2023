from collateral_class import CollateralPortfolio
from clo_class import CLO
import pandas as pd

# assume starting date is in format MM/DD/YYYY
def get_date_array(date):
    if date[2] % 4 == 0:
      return [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    else: 
      return [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


if __name__ == "__main__":
    # ------------------------ GENERAL INFO ------------------------ #
    base = [.33, .33, .34]
    downside = [.30, .25, .45]
    upside = [.40, .35, .25]

    # read excel file for Other Specifications
    df_os = pd.read_excel("CLO_Input.xlsm", sheet_name = "Other Specifications")
    row_3 = df_os.iloc[2]

    # assume they're giving us a date at the end of the month
    # they don't start at the start, they start when the first payment is made
    first_payment_date = row_3['Deal Starting Date']
    date = first_payment_date.split("/") # ["MM", "DD", "YYYY"]
    date = list(map(int, date)) # [MM, DD, YYYY]
    # starting payment month
    starting_month = date[0]
    days_in_month = get_date_array(date)

    row_2 = df_os.iloc[1]
    reinvestment_period = row_2['Reinvestment period']

    # --------------------------- UPFRONT COSTS --------------------------- #

    #legal, accounting, trustee, printing, RA_site, modeling, misc
    # read excel file for upfront costs
    df_uc = pd.read_excel("CLO_Input.xlsm", sheet_name = "Upfront Costs")

    row_legal = df_uc.iloc[0]
    legal = row_legal['Legal']

    row_accounting = df_uc.iloc[1]
    accounting = row_accounting['Accounting']

    row_trustee = df_uc.iloc[2]
    trustee = row_trustee['Trustee']

    row_printing = df_uc.iloc[3]
    printing = row_printing['Printing']

    row_RA = df_uc.iloc[4]
    RA_site = row_RA['RA 17g-5 site']

    row_modeling = df_uc.iloc[5]
    modeling = row_modeling['3rd Part Modeling']

    row_misc = df_uc.iloc[6]
    misc = row_misc['Misc']

    # ------------------------ INITIALIZE OBJECTS ------------------------ #
    row_1 = df_os.iloc[0]
    ramp_up = row_1['Ramp up']
    clo = CLO(ramp_up)

    # read excel file for capital stack
    df_cs = pd.read_excel("CLO_Input.xlsm", sheet_name = "Capital Stack")

    # add tranches in  a loop
    for index_t, row_t in df_cs.iterrows():
      tranche_data = row_t[['Name', 'Rating', 'Offered', 'Size', 'Spread (bps)', 'Price']]
      clo.add_tranche(tranche_data[0], tranche_data[1], tranche_data[2], tranche_data[3], tranche_data[4], tranche_data[5])
    threshold = clo.get_clo_threshold()
    SOFR = 0.0408
  
    loan_portfolio = CollateralPortfolio()

    # read excel file for loans
    df_cp = pd.read_excel("CLO_Input.xlsm", sheet_name = "Collateral Portfolio")

    # add loans in a loop
    for index_l, row_l in df_cp.iterrows():
      loan_data = row_l[['Loan ID','Collateral Interest UPB', 'Margin', 'Index Floor', 'Loan Term (rem)', 'First Extension Period (mo)', 'Open Prepayment Period']] 
      loan_portfolio.add_initial_loan(loan_data[0], loan_data[1], loan_data[2], loan_data[3], loan_data[4], loan_data[5], loan_data[6])
  
    # ------------------------ START BASE SCENARIO ------------------------ #
    # sets term lengths
    loan_portfolio.generate_loan_terms(base)

    # will need loop that makes sim happen 100 or 1000x 
    # goes for the longest possible month duration
    months_passed = 0
    while months_passed in range(loan_portfolio.get_longest_term()): # what if reinvestment makes it longer
      # one more bc if starting date is 1/31/2023, current month is february
      current_month = (starting_month + months_passed + 1) % 12
      for loan in loan_portfolio.get_portfolio():
        funding_storeholder = loan.funding_amount_rein(months_passed, reinvestment_period)
        beginning_bal = loan.beginning_balance(months_passed, funding_storeholder)
        principal_pay = loan.principal_paydown(months_passed, funding_storeholder)
        ending_bal = loan.ending_balance(month, funding_storeholder, beginning_bal)
        days = days_in_month[current_month]
        interest_inc = loan.interest_income(month, funding_storeholder, SOFR, days)

        

        
        
        

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