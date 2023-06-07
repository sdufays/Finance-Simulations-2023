from collateral_class import CollateralPortfolio
from clo_class import CLO
import pandas as pd
import numpy_financial as npf
import math
import numpy as np

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

    # assume they're giving us a date at the end of the month
    first_payment_date = df_os.iloc[2, 1]
    date_str = first_payment_date.strftime("%m-%d-%Y")
    date = date_str.split("-") # ["MM", "DD", "YYYY"]
    date = list(map(int, date)) # [MM, DD, YYYY]
    # starting payment month
    starting_month = date[0]
    days_in_month = get_date_array(date)

    reinvestment_period = df_os.iloc[1,1]
    SOFR = df_os.iloc[3,1]


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
    ramp_up = df_os.iloc[0, 1]
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
    # sets term lengthsi think
    loan_portfolio.generate_loan_terms(upside)
    longest_duration = 60 # int(loan_portfolio.get_longest_term())
    
    # CREATE LOAN DATAFRAME
    loan_ids = list(range(1, 1 + len(loan_portfolio.get_active_portfolio())))  # 21 loan IDs
    months = list(range(0, longest_duration))
    loan_index = pd.MultiIndex.from_product([loan_ids, months],
                                   names=['Loan ID', 'Months Passed'])
    loan_df = pd.DataFrame(index=loan_index, columns=['Current Month', 'Beginning Balance', 'Ending Balance', 'Principal Paydown', 'Interest Income'])

    # CREATE TRANCHE DATAFRAME
    tranche_names = []
    for tranche in clo.get_tranches():
       tranche_names.append(tranche.get_name())
    tranche_index = pd.MultiIndex.from_product([tranche_names, months], names=['Tranche Name', 'Month'])
    tranche_df = pd.DataFrame(index=tranche_index, columns=['Interest Payment', 'Principal Payment'])

 # --------------------------------- MAIN FUNCTION & LOOP -------------------------------------- #
    # START LOOP: goes for the longest possible month duration
    # storage variables
    total_tranche_cfs = [] # stores tranche cashflow for IRR calculation
    deal_call_mos = [] # stores month when each deal is called

    # initializing variables
    months_passed = 0
    terminate_next = False
    # fill nan values in dataframe
    loan_df = loan_df.fillna(0)
    # initial CLO variables
    initial_AAA_bal = clo.get_tranches()[0].get_size()
    initial_clo_tob = clo.get_tob()
    # initial collateral portfolio variables
    loan_portfolio.set_initial_deal_size(loan_portfolio.get_collateral_sum())
    margin = loan_portfolio.generate_initial_margin()
    loan_df = loan_df.fillna(0)

    while months_passed in range(longest_duration): # longest duration 
      # loan counter starts at 0 
      portfolio_index = 0 
      # keeps track of current month
      current_month = (starting_month + months_passed) % 12 or 12
      # ramp-up calculations 
      if months_passed == 1:
         extra_balance = max(0, clo.get_tda() - loan_portfolio.get_collateral_sum())
         if extra_balance > 0:
            loan_portfolio.add_new_loan(extra_balance, margin, months_passed, ramp = True )
      
      # add current balances to list
      for tranche in clo.get_tranches():
        tranche.save_balance(tranche_df, months_passed)

      # loops through ACTIVE loans only
      while portfolio_index < len(loan_portfolio.get_active_portfolio()):
        # initialize loan object
        loan = loan_portfolio.get_active_portfolio()[portfolio_index]
        loan_id = loan.get_loan_id()
        if loan_id not in loan_ids:
            loan_ids.append(loan_id)
        # UPDATE DATAFRAME WITH HIGHER LOAN INDEXES
        loan_index = pd.MultiIndex.from_product([loan_ids, months], names=['Loan ID', 'Months Passed'])
        loan_df = loan_df.reindex(loan_index)
        loan_df = loan_df.fillna(0)

        # GET CALCULATIONS
        beginning_bal = loan.beginning_balance(months_passed, loan_df)
        #print(months_passed)
        if months_passed == 0:
            print(loan.get_loan_id())
            print("begin bal isn't the issue")
        principal_pay = loan.principal_paydown(months_passed, loan_df)
        #print("Begin bal " + str(principal_pay) + " Loan id " + str(loan.get_loan_id()))
        ending_bal = loan.ending_balance(beginning_bal, principal_pay)
        days = days_in_month[current_month - 2]
        interest_inc = loan.interest_income(beginning_bal, SOFR, days)
        # somehow all these calculations are 0

        # save to dataframe
        loan_df.loc[(loan.get_loan_id(), months_passed), 'Beginning Balance'] = beginning_bal
        loan_df.loc[(loan.get_loan_id(), months_passed), 'Interest Income'] = interest_inc
        loan_df.loc[(loan.get_loan_id(), months_passed), 'Principal Paydown'] = principal_pay
        loan_df.loc[(loan.get_loan_id(), months_passed), 'Ending Balance'] = ending_bal
        loan_df.loc[(loan.get_loan_id(), months_passed), 'Current Month'] = current_month

        # paying off loans
        if principal_pay != 0: 
           loan_portfolio.remove_loan(loan)
           
           # reinvestment calculations 
           if months_passed <= reinvestment_period and months_passed == loan.get_term_length():
              loan_portfolio.add_new_loan(beginning_bal, margin, months_passed, ramp = False)
           else:
              clo.get_tranches()[0].subtract_size(beginning_bal)
        else:
           portfolio_index += 1
             
        clo_principal_sum = 0   
        for tranche in clo.get_tranches():
           tranche.tranche_principal(months_passed, reinvestment_period, tranche_df, principal_pay, terminate_next)

        if months_passed == 0:
           print("month: " + str(months_passed))
           for tranche in clo.get_tranches():
              print("tranche: " + tranche.get_name())
              print(tranche.tranche_interest(days, SOFR, tranche_df, months_passed))
        clo.append_cashflow(months_passed, upfront_costs, days, clo_principal_sum, SOFR, tranche_df) 
        
        

      # inner loop ends 

      # terminate in outer loop
      if terminate_next:
         deal_call_mos.append(months_passed)
         break 
      
      if clo.get_tranches()[0].get_size() <= threshold:
          terminate_next = True 

      months_passed += 1

    # for the tranches, put 0 as all the values
    # for the loans, leave as if (still outstanding)
      
    # test to make sure loan data is right
    print(loan_df.tail(longest_duration))
    # loan_df.to_excel('output.xlsx', index=True)

    # ------------------ CALCULATING OUTPUTS ------------------ #
    # DEAL CALL MONTH
    print(deal_call_mos) # only one so far
    """
    # WEIGHTED AVG COST OF FUNDS
    # multiplied by 100 cuz percent
    total_tranche_cfs = [x for x in total_tranche_cfs if not math.isnan(x)] # takes out NaN values from list
    print(total_tranche_cfs)
    print(npf.irr(total_tranche_cfs))
    wa_cof = (npf.irr(total_tranche_cfs)*360/365 - SOFR) * 100
    
    # WEIGHTED AVG ADVANCE RATE
    # since all tranches have same balance except AAA, avg clo balance is total offered bonds - initial size of tranche AAA
    avg_AAA_bal = sum(clo.get_tranches()[0].get_AAA_bal_list()) / deal_call_mos[0]
    avg_clo_bal = (initial_clo_tob - initial_AAA_bal) / deal_call_mos[0] + avg_AAA_bal
    avg_collateral_bal = loan_df['Ending Balance'].sum() / deal_call_mos[0] # deal_call_mos[trial_num]
    wa_adv_rate = avg_clo_bal/avg_collateral_bal

    # PROJECTED EQUITY YIELD
    # equity net spread
    collateral_income = loan_portfolio.get_collateral_income(loan_df, deal_call_mos[0], SOFR) # income we get from loans
    clo_interest_cost = initial_clo_tob * (wa_cof + SOFR) # interest we pay to tranches
    net_equity_amt = loan_portfolio.get_initial_deal_size() - initial_clo_tob # total amount of loans - amount offered as tranches
    equity_net_spread = (collateral_income - clo_interest_cost) / net_equity_amt # excess equity availalbe
    # origination fee add on (fee for creating the clo)
    origination_fee = loan_portfolio.get_initial_deal_size() * 0.01/(net_equity_amt * deal_call_mos[0]) # remember in simulation to put deal_call_mos[trial]
    # projected equity yield (times 100 cuz percent), represents expected return on the clo
    projected_equity_yield = (equity_net_spread + origination_fee) * 100

    calculations_for_one_trial = [wa_cof, wa_adv_rate, projected_equity_yield]
    print(calculations_for_one_trial)
  """