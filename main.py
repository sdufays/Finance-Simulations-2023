from collateral_class import CollateralPortfolio
from clo_class import CLO
import pandas as pd
import numpy_financial as npf
import math

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
    placement_percent = df_uc.iloc[0,1]
    legal = df_uc.iloc[1, 1]
    accounting = df_uc.iloc[2, 1]
    trustee = df_uc.iloc[3, 1]
    printing = df_uc.iloc[4, 1]
    RA_site = df_uc.iloc[5, 1]
    modeling = df_uc.iloc[6, 1]
    misc = df_uc.iloc[7, 1]

    # ------------------------ INITIALIZE OBJECTS ------------------------ #
    SOFR = 0.0408
    ramp_up = df_os.iloc[0, 1]
    print(ramp_up)
    clo = CLO(ramp_up, reinvestment_period, first_payment_date)
    upfront_costs = clo.get_upfront_costs(placement_percent, legal, accounting, trustee, printing, RA_site, modeling, misc)

    # read excel file for capital stack
    df_cs = pd.read_excel("CLO_Input.xlsm", sheet_name = "Capital Stack")

    # add tranches in a loop
    for index_t, row_t in df_cs.iterrows():
      tranche_data = row_t[['Name', 'Rating', 'Offered', 'Size', 'Spread (bps)', 'Price']]
      clo.add_tranche(tranche_data[0], tranche_data[1], tranche_data[2], tranche_data[3], tranche_data[4] / 10000, tranche_data[5])
    threshold = clo.get_threshold()
  
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
    longest_duration = 60 # int(loan_portfolio.get_longest_term())
    
    # CREATE LOAN DATAFRAME
    loan_ids = list(range(1, 1 + len(loan_portfolio.get_portfolio())))  # 21 loan IDs
    months = list(range(0, longest_duration))
    loan_index = pd.MultiIndex.from_product([loan_ids, months],
                                   names=['Loan ID', 'Months Passed'])
    # Create an empty DataFrame with the multi-index
    loan_data = pd.DataFrame(index=loan_index, columns=['Current Month', 'Ending Balance', 'Principal Paydown', 'Interest Income'])

    # START LOOP: goes for the longest possible month duration
    # will need loop that makes sim happen 100 or 1000x 
    months_passed = 0
    terminate_next = False
 # --------------------------------- MAIN FUNCTION & LOOP -------------------------------------- #
    total_tranche_cfs = []
    deal_call_mos = []
    initial_AAA_bal = clo.get_tranches()[0].get_size()
    initial_clo_tob = clo.get_tob()
    loan_portfolio.set_initial_deal_size(loan_portfolio.get_collateral_sum())
    loan_data = loan_data.fillna(0)

    while months_passed in range(longest_duration): # longest duration 
      current_month = (starting_month + months_passed) % 12 or 12
      # ramp-up calculations 
      if months_passed == 1:
         extra_balance = clo.get_tda() - loan_portfolio.get_collateral_sum()
         if extra_balance > 0:
            loan_portfolio.add_new_loan(extra_balance)
      
      # monthly calculations 
      for loan in loan_portfolio.get_portfolio():
        beginning_bal = loan.beginning_balance(months_passed, loan_data)
        #print("Begin bal " + str(beginning_bal))
        principal_pay = loan.principal_paydown(months_passed, loan_data)
        ending_bal = loan.ending_balance(beginning_bal, principal_pay)
        days = days_in_month[current_month - 1]
        interest_inc = loan.interest_income(beginning_bal, SOFR, days)

        # save to dataframe
        loan_data.loc[(loan.get_loan_id(), months_passed), 'Interest Income'] = interest_inc
        loan_data.loc[(loan.get_loan_id(), months_passed), 'Principal Paydown'] = principal_pay
        loan_data.loc[(loan.get_loan_id(), months_passed), 'Ending Balance'] = ending_bal
        loan_data.loc[(loan.get_loan_id(), months_passed), 'Current Month'] = current_month

        clo_principal = clo.get_tranche_principal_sum(months_passed, reinvestment_period, principal_pay, threshold)
        clo_cashflow = clo.total_tranche_cashflow(months_passed, upfront_costs, days, clo_principal) 
        # appends to list of cashflows
        total_tranche_cfs.append(clo_cashflow)

        # paying off loans
        if principal_pay != 0: 
           loan_portfolio.remove_loan(loan)
           
           # reinvestment calculations 
           if months_passed < reinvestment_period and months_passed == loan.get_term_length():
              print('new loan added')
              loan_portfolio.add_new_loan(beginning_bal)
           else:
              print(loan.get_loan_id())
              print("principay month " + str(months_passed))
              print('subtracting by ' + str(beginning_bal))
              clo.get_tranches()[0].subtract_size(beginning_bal)
              print("AAA SIZE " +str(clo.get_tranches()[0].get_size()))
              print("THRESHOLD " + str(threshold))

      # terminate 
      if terminate_next:
         deal_call_mos.append(months_passed)
         break 
      
      if clo.get_tranches()[0].get_size() <= threshold:
          print("WORK")
          terminate_next = True 
      #print("\nmonth " + str(months_passed))
      #print("AAA balance " + str(clo.get_tranches()[0].get_size()))
      #print("Thre " + str(threshold))
              
      months_passed += 1
      
    # test to make sure loan data is right
    print(loan_data.head(longest_duration))

    # ------------------ CALCULATING OUTPUTS ------------------ #
    # DEAL CALL MONTH
    print(deal_call_mos) # only one so far
    # WEIGHTED AVG COST OF FUNDS
    # multiplied by 100 cuz percent
    total_tranche_cfs = [x for x in total_tranche_cfs if not math.isnan(x)] # takes out NaN values from list
    wa_cof = (npf.irr(total_tranche_cfs)*360/365 - SOFR) * 100
    """
    # WEIGHTED AVG ADVANCE RATE
    # since all tranches have same balance except AAA, avg clo balance is total offered bonds - initial size of tranche AAA
    avg_clo_bal = initial_clo_tob - initial_AAA_bal
    avg_collateral_bal = loan_data['Ending Balance'].sum() / deal_call_mos[0] # deal_call_mos[trial_num]
    wa_adv_rate = avg_clo_bal/avg_collateral_bal

    # PROJECTED EQUITY YIELD
    # equity net spread
    collateral_income = loan_portfolio.get_collateral_income(loan_data) # income we get from loans
    clo_interest_cost = initial_clo_tob * wa_cof # interest we pay to tranches
    net_equity_amt = loan_portfolio.get_initial_deal_size() - initial_clo_tob # total amount of loans - amount offered as tranches
    equity_net_spread = (collateral_income - clo_interest_cost) / net_equity_amt # excess equity availalbe
    # origination fee add on (fee for creating the clo)
    origination_fee = loan_portfolio.get_initial_deal_size() * 0.01/(net_equity_amt * deal_call_mos[0]) # remember in simulation to put deal_call_mos[trial]
    # projected equity yield (times 100 cuz percent), represents expected return on the clo
    projected_equity_yield = (equity_net_spread + origination_fee + SOFR) * 100

    calculations_for_one_trial = [wa_cof, wa_adv_rate, projected_equity_yield]
    print(calculations_for_one_trial)"""