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
    df_os = pd.read_excel("CLO_Input.xlsm", sheet_name = "Other Specifications", header=None)
    print(df_os)
    row_3 = df_os.iloc[2]

    # assume they're giving us a date at the end of the month
    first_payment_date = df_os.iloc[2, 1]
    date_str = first_payment_date.strftime("%m-%d-%Y")
    date = date_str.split("-") # ["MM", "DD", "YYYY"]
    date = list(map(int, date)) # [MM, DD, YYYY]
    # starting payment month
    starting_month = date[0]
    days_in_month = get_date_array(date)

    reinvestment_period = df_os.iloc[1,1]

    # --------------------------- UPFRONT COSTS --------------------------- #

    df_uc = pd.read_excel("CLO_Input.xlsm", sheet_name = "Upfront Costs", header=None)
    legal = df_uc.iloc[0, 1]
    accounting = df_uc.iloc[1, 1]
    trustee = df_uc.iloc[2, 1]
    printing = df_uc.iloc[3, 1]
    RA_site = df_uc.iloc[4, 1]
    modeling = df_uc.iloc[5, 1]
    misc = df_uc.iloc[6, 1]

    # ------------------------ INITIALIZE OBJECTS ------------------------ #
    ramp_up = df_os.iloc[0, 1]
    clo = CLO(ramp_up, reinvestment_period, first_payment_date)

    # read excel file for capital stack
    df_cs = pd.read_excel("CLO_Input.xlsm", sheet_name = "Capital Stack")

    # add tranches in a loop
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
    longest_duration = loan_portfolio.get_longest_term()
    # CREATE DATAFRAME
    loan_ids = list(range(1, 22))  # 21 loan IDs
    months = list(range(1, longest_duration))
    index = pd.MultiIndex.from_product([loan_ids, months],
                                   names=['Loan ID', 'Months Passed'])
    # Create an empty DataFrame with the multi-index
    loan_data = pd.DataFrame(index=index, columns=['Current Month', 'Ending Balance', 'Principal Paydown', 'Interest Income'])

    # START LOOP: goes for the longest possible month duration
    months_passed = 0
    while months_passed in range(longest_duration): # what if reinvestment makes it longer
      current_month = (starting_month + months_passed) % 12
      # ramp-up calculations 
      if months_passed == 1:
         extra_balance = clo.get_tda() - loan_portfolio.get_collateral_sum()
         if extra_balance > 0:
            loan_portfolio.add_new_loan(extra_balance)
      
      # monthly calculations 
      for loan in loan_portfolio.get_portfolio():
        beginning_bal = loan.beginning_balance(months_passed)
        principal_pay = loan.principal_paydown(months_passed)
        ending_bal = loan.ending_balance(beginning_bal, principal_pay)
        days = days_in_month[current_month - 1]
        interest_inc = loan.interest_income(beginning_bal, SOFR, days)

        # save to dataframe
        loan_data.loc[(loan.get_loan_id(), months_passed), 'Interest Income'] = interest_inc
        loan_data.loc[(loan.get_loan_id(), months_passed), 'Principal Paydown'] = principal_pay
        loan_data.loc[(loan.get_loan_id(), months_passed), 'Ending Balance'] = ending_bal
        
        # paying off loans
        if principal_pay != 0: 
           loan_portfolio.remove_loan(loan)
           clo.get_tranches()[0].subtract_size(beginning_bal)
           # reinvestment calculations 
           if months_passed < reinvestment_period and months_passed == loan.get_term_length():
              loan_portfolio.add_new_loan(beginning_bal)

        if clo.get_tranches()[0].get_size() <= threshold:
           
              
           
    print(loan_data)
