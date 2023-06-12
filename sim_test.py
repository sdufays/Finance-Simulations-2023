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


def waterfall(subtract_value, tranches):
    """
    Perform waterfall algorithm over tranches.
    :param subtract_value: Value to be subtracted from tranches.
    :param tranches: List of tranches.
    :return: None.
    """
    for tranche in tranches:
        if tranche.get_size() >= subtract_value:
            tranche.subtract_size(subtract_value)
            subtract_value = 0
            break
        else:
            subtract_value -= tranche.get_size()
            tranche.subtract_size(tranche.get_size())

        if subtract_value == 0:
            break

    if subtract_value > 0:
        raise ValueError("Not enough total size in all tranches to cover the subtraction.")  


def run_simulation(case, output_dataframe, trial_index):
 # ------------------------ INITIALIZE OBJECTS ------------------------ #
    ramp_up = df_os.iloc[0, 1]
    clo = CLO(ramp_up, has_reinvestment, has_replenishment, reinvestment_period, replenishment_period, replenishment_amount, first_payment_date)

    # read excel file for capital stack
    df_cs = pd.read_excel("CLO_Input2.xlsm", sheet_name = "Capital Stack")

    # add tranches in a loop
    for index_t, row_t in df_cs.iterrows():
      tranche_data = row_t[['Name', 'Rating', 'Offered', 'Size', 'Spread (bps)', 'Price']]
      clo.add_tranche(tranche_data[0], tranche_data[1], tranche_data[2], tranche_data[3], tranche_data[4] / 10000, tranche_data[5])
    threshold = clo.get_threshold()

    upfront_costs = clo.get_upfront_costs(placement_percent, legal, accounting, trustee, printing, RA_site, modeling, misc)
  
    loan_portfolio = CollateralPortfolio()

    # read excel file for loans
    df_cp = pd.read_excel("CLO_Input2.xlsm", sheet_name = "Collateral Portfolio")

    # add loans in a loop
    for index_l, row_l in df_cp.iterrows():
      loan_data = row_l[['Loan ID','Collateral Interest UPB', 'Margin', 'Index Floor', 'Loan Term (rem)', 'First Extension Period (mo)', 'Open Prepayment Period']] 
      loan_portfolio.add_initial_loan(loan_data[0], loan_data[1], loan_data[2], loan_data[3], loan_data[4], loan_data[5], loan_data[6])

    # ------------------------ START BASE SCENARIO ------------------------ #
    # sets term lengthsi think
    loan_portfolio.generate_loan_terms(case)
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
       if tranche.get_offered() == 1:
        tranche_names.append(tranche.get_name())
    tranche_index = pd.MultiIndex.from_product([tranche_names, months], names=['Tranche Name', 'Month'])
    tranche_df = pd.DataFrame(index=tranche_index, columns=['Interest Payment', 'Principal Payment', 'Tranche Size'])
    # SET DATAFRAME FORMAT OPTIONS
    # Set the display format for floating-point numbers
    pd.options.display.float_format = '{:,.2f}'.format

 # --------------------------------- MAIN FUNCTION & LOOP -------------------------------------- #
    # START LOOP: goes for the longest possible month duration

    # initializing variables
    months_passed = 0
    terminate_next = False
    # fill nan values in dataframe
    loan_df = loan_df.fillna(0)
    # initial CLO variables
    initial_AAA_bal = clo.get_tranches()[0].get_size()
    initial_clo_tob = clo.get_tob()
    for tranche in clo.get_tranches():
       tranche.init_principal_dict(longest_duration)
    # initial collateral portfolio variables
    loan_portfolio.set_initial_deal_size(loan_portfolio.get_collateral_sum())
    margin = loan_portfolio.generate_initial_margin()
    loan_df = loan_df.fillna(0)
    replen_months = 0
    replen_cumulative = 0
    incremented_replen_month = False
    loan_income_df = pd.DataFrame(columns=['Loan ID','Income'])
    for loan in loan_portfolio.get_active_portfolio():
       loan.loan_income(SOFR, loan_income_df)
    loan_term_df = pd.DataFrame(columns=['Loan ID','Loan Term'])
    # calculate wa loan spread for day 1
    wa_spread = 0
    for loan in loan_portfolio.get_active_portfolio():
        loan_term_df.loc[loan_term_df.shape[0]] = [loan.get_loan_id(), loan.get_term_length()]
        wa_spread += loan.get_margin()
    wa_spread /= len(loan_portfolio.get_active_portfolio())
    
    
    # removing unsold tranches so they don't get in the way
    clo.remove_unsold_tranches()
    while months_passed in range(longest_duration): # longest duration 
      # loan counter starts at 0 
      portfolio_index = 0 
      current_month = (starting_month + months_passed) % 12 or 12
      # ramp-up calculations 
      if months_passed == 1:
         extra_balance = max(0, clo.get_tda() - loan_portfolio.get_collateral_sum())
         if extra_balance > 0:
            loan_portfolio.add_new_loan(extra_balance, margin, months_passed, ramp = True )
      
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
        
        tranche_df = tranche_df.fillna(0)

        # GET CALCULATIONS
        beginning_bal = loan.beginning_balance(months_passed, loan_df)
        principal_pay = loan.principal_paydown(months_passed, loan_df)
        ending_bal = loan.ending_balance(beginning_bal, principal_pay)
        days = days_in_month[current_month - 2]
        interest_inc = loan.interest_income(beginning_bal, SOFR, days)

        # save to loan dataframe
        loan_df.loc[(loan.get_loan_id(), months_passed), 'Beginning Balance'] = beginning_bal
        loan_df.loc[(loan.get_loan_id(), months_passed), 'Interest Income'] = interest_inc
        loan_df.loc[(loan.get_loan_id(), months_passed), 'Principal Paydown'] = principal_pay
        loan_df.loc[(loan.get_loan_id(), months_passed), 'Ending Balance'] = ending_bal
        loan_df.loc[(loan.get_loan_id(), months_passed), 'Current Month'] = current_month

        # paying off loans
        if principal_pay != 0: 
           loan_portfolio.remove_loan(loan)
           reinvestment_bool = (clo.get_reinv_bool()) and (months_passed <= clo.get_reinv_period()) and (months_passed == loan.get_term_length())
           replenishment_bool = (clo.get_replen_bool() and not clo.get_reinv_bool()) and (months_passed <= clo.get_replen_period() and replen_cumulative <= clo.get_replen_amount()) and (months_passed == loan.get_term_length())
           replen_after_reinv_bool = (clo.get_reinv_bool() and clo.get_replen_bool()) and (months_passed > clo.get_reinv_period()) and (replen_months < clo.get_replen_period() and replen_cumulative <= clo.get_replen_amount()) and (months_passed == loan.get_term_length())

           if reinvestment_bool:
                loan_portfolio.add_new_loan(beginning_bal, margin, months_passed, ramp = False)
                loan = loan_portfolio.get_active_portfolio()[-1]
                loan_term_df.loc[loan_term_df.shape[0]] = [loan.get_loan_id(), loan.get_term_length()]
           elif replenishment_bool:
                loan_portfolio.add_new_loan(beginning_bal, margin, months_passed, ramp = False)
                replen_cumulative += beginning_bal
           elif replen_after_reinv_bool:
                loan_portfolio.add_new_loan(beginning_bal, margin, months_passed, ramp = False)
                replen_cumulative += beginning_bal
                 # increment replen_months only once in a month
                if not incremented_replen_month:
                   replen_months += 1
                   incremented_replen_month = True # set flag to True so that it won't increment again within this month
           else: #waterfall it
                remaining_subtract = beginning_bal
                for tranche in clo.get_tranches():
                    if tranche.get_size() >= remaining_subtract:
                        tranche.subtract_size(remaining_subtract)
                        remaining_subtract = 0
                        break
                    else:
                        remaining_subtract -= tranche.get_size()
                        tranche.subtract_size(tranche.get_size())
                    # Check if remaining_subtract is 0, if it is, break the loop
                    if remaining_subtract == 0:
                        break
                # error condition if there's not enough total size in all tranches
                if remaining_subtract > 0:
                    raise ValueError("Not enough total size in all tranches to cover the subtraction.")   
                
        else:
           portfolio_index += 1

        clo_principal_sum = clo.clo_principal_sum(months_passed, reinvestment_period, tranche_df, principal_pay, terminate_next, loan, loan_portfolio, portfolio_index, replen_cumulative, replen_months)

      # add current balances to list
      for tranche in clo.get_tranches():
        tranche.save_balance(tranche_df, months_passed)

      # inner loop ends 
      clo.append_cashflow(months_passed, upfront_costs, days, clo_principal_sum, SOFR, tranche_df) 

      # terminate in outer loop
      if terminate_next:
         deal_call_month = months_passed
         break 
      
      if clo.get_tranches()[0].get_size() <= threshold:
          terminate_next = True 

      months_passed += 1

    # TESTING PURPOSES ONLY
    # testing loan data
    #print(loan_df.tail(longest_duration))
    #loan_df.to_excel('output.xlsx', index=True)
    # testing tranche data
    #print(tranche_df.loc['A'])
    #print(tranche_df.head(longest_duration))
    #tranche_df.to_excel('tranches.xlsx', index=True)

    # WEIGHTED AVG COST OF FUNDS
    wa_cof = (npf.irr(clo.get_total_cashflows())*12*360/365 - SOFR) * 100 # in bps
    if wa_cof < 0:
      tranche_df.to_excel('output.xlsx', index=True)
    
    # WEIGHTED AVG ADVANCE RATE
    avg_clo_bal = 0
    for i in range(len(clo.get_tranches())):
       avg_clo_bal += sum(clo.get_tranches()[i].get_bal_list()) / deal_call_month
    avg_collateral_bal = loan_df['Ending Balance'].sum() / deal_call_month
    wa_adv_rate = avg_clo_bal/avg_collateral_bal

    # PROJECTED EQUITY YIELD
    # equity net spread
    collateral_income = loan_portfolio.get_initial_deal_size() *  (wa_spread + SOFR)
    clo_interest_cost = initial_clo_tob * (wa_cof / 100 + SOFR) # interest we pay to tranches
    net_equity_amt = loan_portfolio.get_initial_deal_size() - initial_clo_tob # total amount of loans - amount offered as tranches
    equity_net_spread = (collateral_income - clo_interest_cost) / net_equity_amt # excess equity availalbe
    # origination fee add on (fee for creating the clo)
    origination_fee = loan_portfolio.get_initial_deal_size() * 0.01/(net_equity_amt * deal_call_month) # remember in simulation to put deal_call_mos[trial]
    # projected equity yield (times 100 cuz percent), represents expected return on the clo
    projected_equity_yield = (equity_net_spread + origination_fee) * 100

    if case == base:
       case_name = "base"
    elif case == upside:
       case_name = "upside"
    else:
       case_name = "downside"

    output_dataframe.loc[(case_name, trial_index), 'Deal Call Month'] = deal_call_month
    output_dataframe.loc[(case_name, trial_index), 'WA COF'] = wa_cof
    output_dataframe.loc[(case_name, trial_index), 'WA Adv Rate'] = wa_adv_rate
    output_dataframe.loc[(case_name, trial_index), 'Projected Equity Yield'] = projected_equity_yield
    # technically don't even need to return it
    return output_dataframe

if __name__ == "__main__":
   # ------------------------ GENERAL INFO ------------------------ #
    base = [.33, .33, .34]
    downside = [.30, .25, .45]
    upside = [.40, .35, .25]

    # read excel file for Other Specifications
    df_os = pd.read_excel("CLO_Input2.xlsm", sheet_name = "Other Specifications", header=None)

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

    
    has_reinvestment = df_os.iloc[7,1]
    has_replenishment = df_os.iloc[5,1]

    reinvestment_period = df_os.iloc[1,1]
    replenishment_period = df_os.iloc[4,1]

    replenishment_amount = df_os.iloc[6,1]


    # --------------------------- UPFRONT COSTS --------------------------- #

    df_uc = pd.read_excel("CLO_Input2.xlsm", sheet_name = "Upfront Costs", header=None)
    placement_percent = df_uc.iloc[0,1]
    legal = df_uc.iloc[1, 1]
    accounting = df_uc.iloc[2, 1]
    trustee = df_uc.iloc[3, 1]
    printing = df_uc.iloc[4, 1]
    RA_site = df_uc.iloc[5, 1]
    modeling = df_uc.iloc[6, 1]
    misc = df_uc.iloc[7, 1]

    NUM_TRIALS = 5
    cases = ['base', 'downside', 'upside']
    trial_numbers = range(0, NUM_TRIALS)
    index = pd.MultiIndex.from_product([cases, trial_numbers], names=['Case', 'Trial Number'])
    columns = ['Deal Call Month', 'WA COF', 'WA Adv Rate', 'Projected Equity Yield']
    output_df = pd.DataFrame(index=index, columns=columns)


   # ------------------------ RUN SIMULATION ------------------------ #

    #run_simulation(base)

   # ------------------------ RUN SIMULATION LOOPS ------------------------ #
   
    scenarios = [base, downside, upside]

    for scenario in scenarios:
        for run in range(NUM_TRIALS):
            # Run the simulation and get the data dictionary
            output_df = run_simulation(scenario, output_df, run)
    print(output_df)
         
   # ------------------------ GET OUTPUTS ------------------------ #
    """print("base_last_month: ", end="")
    print(*base_last_month, sep=", ")

    print("downside_last_month: ", end="")
    print(*downside_last_month, sep=", ")

    print("upside_last_month: ", end="")
    print(*upside_last_month, sep=", ")"""







    
