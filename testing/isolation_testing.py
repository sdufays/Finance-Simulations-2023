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
    clo = CLO(ramp_up, has_reinvestment, has_replenishment, reinvestment_period, replenishment_period, replenishment_amount, first_payment_date)
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
    loan_portfolio.initial_loan_terms(base)
    longest_duration = 60 # int(loan_portfolio.get_longest_term())
    
    # CREATE LOAN DATAFRAME
    loan_ids = list(range(1, 1 + len(loan_portfolio.get_storage_portfolio())))  # 21 loan IDs
    months = list(range(0, longest_duration))
    loan_index = pd.MultiIndex.from_product([loan_ids, months],
                                   names=['Loan ID', 'Months Passed'])
    # Create an empty DataFrame with the multi-index
    loan_data = pd.DataFrame(index=loan_index, columns=['Current Month', 'Beginning Balance', 'Ending Balance', 'Principal Paydown', 'Interest Income'])

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
    # will need loop that makes sim happen 100 or 1000x 
    months_passed = 0
    terminate_next = False
    total_tranche_cfs = []
    deal_call_mos = []
    initial_AAA_bal = clo.get_tranches()[0].get_size()
    initial_clo_tob = clo.get_tob()
    loan_portfolio.set_initial_deal_size(loan_portfolio.get_collateral_sum())
    margin = loan_portfolio.generate_initial_margin()
    loan_data = loan_data.fillna(0)
    replen_months = 0
    replen_cumulative = 0
    incremented_replen_month = False
    current_loan = 3

    while months_passed in range(50): # longest duration 
      portfolio_index = 0 
      current_month = (starting_month + months_passed) % 12 or 12
      # ramp-up calculations 
      if months_passed == 1:
         extra_balance = max(0, clo.get_tda() - loan_portfolio.get_collateral_sum())
         if extra_balance > 0:
            loan_portfolio.add_new_loan(extra_balance)
            print("added ramp-up loan")
            ramp_up_loan = loan_portfolio.get_active_portfolio()[-1]
            ramp_up_loan.print_loan_info()
      # monthly calculations 
      # NEED TO ADD REINVESTMENT LOANS
      #print("\nmonth " + str(months_passed))
      loan = loan_portfolio.get_active_portfolio()[current_loan - 1]
      beginning_bal = loan.beginning_balance(months_passed, loan_data)
      #print(months_passed)
      principal_pay = loan.principal_paydown(months_passed, loan_data)
      #print("Begin bal " + str(principal_pay) + " Loan id " + str(loan.get_loan_id()))
      ending_bal = loan.ending_balance(beginning_bal, principal_pay)
      days = days_in_month[current_month - 2]
      interest_inc = loan.interest_income(beginning_bal, SOFR, days)
      #print("index: " + str(portfolio_index))
      #print("beginning balance: " + str(beginning_bal))
      #print("principal pay: " + str(principal_pay))
      #print("ending balance " + str(ending_bal))
      #print("interest income " + str(interest_inc))
      #print("\n")


        # save to dataframe
      loan_data.loc[(loan.get_loan_id(), months_passed), 'Beginning Balance'] = beginning_bal
      loan_data.loc[(loan.get_loan_id(), months_passed), 'Interest Income'] = interest_inc
      loan_data.loc[(loan.get_loan_id(), months_passed), 'Principal Paydown'] = principal_pay
      loan_data.loc[(loan.get_loan_id(), months_passed), 'Ending Balance'] = ending_bal
      loan_data.loc[(loan.get_loan_id(), months_passed), 'Current Month'] = current_month
      
      # paying off loans
      if principal_pay != 0: 
          loan_portfolio.remove_loan(loan)
          reinvestment_bool = (clo.get_reinv_bool()) and (months_passed <= clo.get_reinv_period()) and (months_passed == loan.get_term_length())
          replenishment_bool = (clo.get_replen_bool() and not clo.get_reinv_bool()) and (months_passed <= clo.get_replen_period() and replen_cumulative <= clo.get_replen_amount()) and (months_passed == loan.get_term_length())
          replen_after_reinv_bool = (clo.get_reinv_bool() and clo.get_replen_bool()) and (months_passed > clo.get_reinv_period()) and (replen_months < clo.get_replen_period() and replen_cumulative <= clo.get_replen_amount()) and (months_passed == loan.get_term_length())

          if reinvestment_bool:
              loan_portfolio.add_new_loan(beginning_bal, margin, months_passed, ramp = False)
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
                      print(str(tranche.get_name()) + " SIZE: " + str("{:,}".format(tranche.get_size()))) 
                      tranche.subtract_size(remaining_subtract)
                      print("Subtracted beginning balance: " + str("{:,}".format(remaining_subtract)))
                      print("NEW SIZE: " + str("{:,}".format(tranche.get_size())))
                      if str(tranche.get_name()) == 'AAA':
                        print("THRESHOLD: " + str("{:,}".format(threshold)))
                        print("AMOUNT TO REACH THRESHOLD: " + str("{:,}".format(tranche.get_size() - threshold)))
                      remaining_subtract = 0
                      break
                  else:
                      print(str(tranche.get_name()) + " SIZE: " + str("{:,}".format(tranche.get_size()))) 
                      remaining_subtract -= tranche.get_size()
                      tranche.subtract_size(tranche.get_size())
                      print("Subtracted beginning balance: " + str("{:,}".format(remaining_subtract)))
                      print("NEW SIZE: " + str("{:,}".format(tranche.get_size())))
                      
                  # Check if remaining_subtract is 0, if it is, break the loop
                  if remaining_subtract == 0:
                      break
              # error condition if there's not enough total size in all tranches
              if remaining_subtract > 0:
                  raise ValueError("Not enough total size in all tranches to cover the subtraction.")   
              
      else:
          portfolio_index += 1

      #clo_principal_sum = clo.clo_principal_sum(months_passed, reinvestment_period, tranche_df, principal_pay, terminate_next, loan, loan_portfolio, portfolio_index)
      # add current balances to list
      for tranche in clo.get_tranches():
        tranche.save_balance(tranche_df, months_passed)

      # inner loop ends 
      #clo.append_cashflow(months_passed, upfront_costs, days, clo_principal_sum, SOFR, tranche_df) 

    # terminate in outer loop
      if terminate_next:
        deal_call_mos.append(months_passed)
        break 
    
      if clo.get_tranches()[0].get_size() <= threshold:
        terminate_next = True 
      
      incremented_replen_month = False
      months_passed += 1

    # for the tranches, put 0 as all the values
    # for the loans, leave as if (still outstanding)
     
    # Get the relevant loan data
    loan_data_subset = loan_data.loc[(current_loan, slice(None)), :].copy()
    # Specify the columns to format
    cols_to_format = ['Beginning Balance', 'Ending Balance', 'Interest Income']
    # Apply the formatting directly to the DataFrame
    for col in cols_to_format:
      loan_data_subset[col] = loan_data_subset[col].apply(lambda x: "{:,.0f}".format(x))
    # Now, print the DataFrame
    print(loan_data_subset)

    #print(tranche_df.loc['A-S'])

    # loan_data.to_excel('output.xlsx', index=True)

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
    avg_AAA_bal = # sum of all AAA bals over time / deal_call_mos[0]
    avg_clo_bal = (initial_clo_tob - initial_AAA_bal) / deal_call_mos[0] + avg_AAA_bal
    avg_collateral_bal = loan_data['Ending Balance'].sum() / deal_call_mos[0] # deal_call_mos[trial_num]
    wa_adv_rate = avg_clo_bal/avg_collateral_bal

    # PROJECTED EQUITY YIELD
    # equity net spread
    collateral_income = loan_portfolio.get_collateral_income(loan_data, deal_call_mos[0], SOFR) # income we get from loans
    clo_interest_cost = initial_clo_tob * (wa_cof + SOFR) # interest we pay to tranches
    net_equity_amt = loan_portfolio.get_initial_deal_size() - initial_clo_tob # total amount of loans - amount offered as tranches
    equity_net_spread = (collateral_income - clo_interest_cost) / net_equity_amt # excess equity availalbe
    # origination fee add on (fee for creating the clo)
    origination_fee = loan_portfolio.get_initial_deal_size() * 0.01/(net_equity_amt * deal_call_mos[0]) # remember in simulation to put deal_call_mos[trial]
    # projected equity yield (times 100 cuz percent), represents expected return on the clo
    projected_equity_yield = (equity_net_spread + origination_fee) * 100

    calculations_for_one_trial = [wa_cof, wa_adv_rate, projected_equity_yield]
    print(calculations_for_one_trial) """