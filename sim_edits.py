from collateral_class import CollateralPortfolio
from clo_class import CLO
from graphing import *
import pandas as pd
import numpy_financial as npf
import numpy as np
from collections import Counter

# ------------------- GET NUM DAYS IN MONTH -------------------- #
def get_date_array(date):
    if date[2] % 4 == 0:
      return [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    else: 
      return [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

# ------------------- WATERFALL FUNCTION FOR LOANS -------------------- #
def loan_waterfall(subtract_value, tranches):
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

# ------------------- SIMULATION FUNCTION -------------------- #
def run_simulation(case, output_dataframe, trial_index, clo, loan_portfolio, starting_month, days_in_month, SOFR, upfront_costs, threshold, months_passed, old_tranche_df, curr_date):
    longest_duration = 70
    original_months_passed = months_passed

    # --------------------------------- INITIALIZE LOOP VARIABLES -------------------------------------- #
    terminate_next = False

    # initial CLO variables
    initial_clo_tob = clo.get_tob()
    for tranche in clo.get_tranches():
       tranche.init_principal_dict(longest_duration)

    # ------------------------ CREATE LOAN DATAFRAME ------------------------ #
    loan_ids = list(range(1, 1 + len(loan_portfolio.get_active_portfolio())))  # generate loan ids
    months = list(range(months_passed, longest_duration))
    loan_index = pd.MultiIndex.from_product([loan_ids, months],
                                   names=['Loan ID', 'Months Passed'])
    loan_df = pd.DataFrame(index=loan_index, columns=['Current Month', 'Beginning Balance', 'Ending Balance', 'Principal Paydown', 'Interest Income'])
    loan_df = loan_df.fillna(0)
    #print(loan_df.head(longest_duration-months_passed))

    # ------------------------ CREATE TRANCHE DATAFRAME ------------------------ #
    # SAVE CASH FLOWS
    monthly_cashflow_sums = old_tranche_df.groupby(level=1).sum()
    cashflow_list = monthly_cashflow_sums['Total Cashflow'].tolist()
    clo.set_total_cashflows_MANUAL(cashflow_list)
    
    # CREATE TRANCHE DF
    tranche_names = []
    for tranche in clo.get_tranches():
       if tranche.get_offered() == 1:
        tranche_names.append(tranche.get_name())
    tranche_index = pd.MultiIndex.from_product([tranche_names, months], names=['Tranche Name', 'Month'])
    tranche_df = pd.DataFrame(index=tranche_index, columns=['Interest Payment', 'Principal Payment', 'Tranche Size'])
    
    # SAVE FIRST LINE
    for tranche in clo.get_tranches():
       tranche_df.loc[(tranche.get_name(), months_passed), 'Tranche Size'] = old_tranche_df.loc[(tranche.get_name(), curr_date), 'Tranche Size']
       tranche_df.loc[(tranche.get_name(), months_passed), 'Principal Payment'] = old_tranche_df.loc[(tranche.get_name(), curr_date), 'Principal Payment']
       tranche_df.loc[(tranche.get_name(), months_passed), 'Interest Payment'] = old_tranche_df.loc[(tranche.get_name(), curr_date), 'Interest Payment']
    
    print(tranche_df)
    
    # initial collateral portfolio variables
    loan_portfolio.set_initial_deal_size(loan_portfolio.get_collateral_sum())
    margin = loan_portfolio.generate_initial_margin()
    replen_months = 0
    replen_cumulative = 0
    incremented_replen_month = False
   
    # calculate wa loan spread for day 1, for use in final output
    # NOT SURE IF STILL NEEDED
    loan_term_df = pd.DataFrame(columns=['Loan ID','Loan Term'])
    wa_spread = 0
    for loan in loan_portfolio.get_active_portfolio():
        loan_term_df.loc[loan_term_df.shape[0]] = [loan.get_loan_id(), loan.get_term_length()]
        wa_spread += loan.get_margin()
    wa_spread /= len(loan_portfolio.get_active_portfolio()) # THIS IS WRONG NOW, need original portfolio

    # removing unsold tranches so they don't get in the way
    # unsure if we want this lol, but we still have the full stack saved in .get_all_tranches()
    clo.remove_unsold_tranches()

    # we're now in the 47th month
    months_passed += 1

    # --------------------------------- START MONTH LOOP -------------------------------------- #
    while months_passed in range(longest_duration):
      print("months passed {}".format(months_passed))
      # loan counter starts at 0 
      portfolio_index = 0 
      current_month = (starting_month + months_passed) % 12 or 12
      # ramp-up calculations, won't happen in this case but ig we can leave it
      if months_passed == 1:
         extra_balance = max(0, clo.get_tda() - loan_portfolio.get_collateral_sum())
         if extra_balance > 0:
            loan_portfolio.add_new_loan(extra_balance, margin, months_passed, ramp = True )
      
      # START LOANS LOOP
      while portfolio_index < len(loan_portfolio.get_active_portfolio()):
        # initialize loan object
        loan = loan_portfolio.get_active_portfolio()[portfolio_index]
        # update dataframe indexes when new loans are added
        loan_id = loan.get_loan_id()
        if loan_id not in loan_ids:
            loan_ids.append(loan_id)
        loan_index = pd.MultiIndex.from_product([loan_ids, months], names=['Loan ID', 'Months Passed'])
        loan_df = loan_df.reindex(loan_index)
        # fill nan values in df with 0
        loan_df = loan_df.fillna(0)

        # GET CALCULATIONS
        beginning_bal = loan.beginning_balance_MANUAL(months_passed, loan_df, original_months_passed)
        principal_pay = loan.principal_paydown(months_passed, loan_df) # WRONG RN i haven't edited it
        ending_bal = loan.ending_balance(beginning_bal, principal_pay)
        days = days_in_month[current_month - 2]
        interest_inc = loan.interest_income(beginning_bal, SOFR, days) # WRONG RN cuz we don't have index floor
        # save to loan dataframe
        loan_df.loc[(loan.get_loan_id(), months_passed), 'Beginning Balance'] = beginning_bal
        loan_df.loc[(loan.get_loan_id(), months_passed), 'Interest Income'] = interest_inc
        loan_df.loc[(loan.get_loan_id(), months_passed), 'Principal Paydown'] = principal_pay
        loan_df.loc[(loan.get_loan_id(), months_passed), 'Ending Balance'] = ending_bal
        loan_df.loc[(loan.get_loan_id(), months_passed), 'Current Month'] = current_month
        #print(loan_df.head(longest_duration-months_passed))


        # WHEN LOANS START PAYING OFF
        if principal_pay != 0:
            # remove loan
            loan_portfolio.remove_loan(loan)
            # check if reinv/replen/both
            reinvestment_bool = (clo.get_reinv_bool()) and (months_passed <= clo.get_reinv_period()) and (months_passed == loan.get_term_length())
            replenishment_bool = (clo.get_replen_bool() and not clo.get_reinv_bool()) and (months_passed <= clo.get_replen_period() and replen_cumulative < clo.get_replen_amount()) and (months_passed == loan.get_term_length())
            replen_after_reinv_bool = (clo.get_reinv_bool() and clo.get_replen_bool()) and (months_passed > clo.get_reinv_period()) and (replen_months < clo.get_replen_period() and replen_cumulative < clo.get_replen_amount()) and (months_passed == loan.get_term_length())

            if reinvestment_bool:
               loan_portfolio.add_new_loan(beginning_bal, margin, months_passed, ramp=False)
            elif replenishment_bool:
               loan_value = min(beginning_bal, clo.get_replen_amount() - replen_cumulative)
               loan_portfolio.add_new_loan(loan_value, margin, months_passed, ramp=False)
               replen_cumulative += loan_value
               remaining_subtract = beginning_bal - loan_value
               if remaining_subtract > 0:
                  loan_waterfall(remaining_subtract, clo.get_tranches())
            elif replen_after_reinv_bool:
               loan_value = min(beginning_bal, clo.get_replen_amount() - replen_cumulative)
               loan_portfolio.add_new_loan(loan_value, margin, months_passed, ramp=False)
               replen_cumulative += loan_value
               remaining_subtract = beginning_bal - loan_value
               # increment replen_months only once in a month
               if not incremented_replen_month:
                  replen_months += 1
                  incremented_replen_month = True  # set flag to True so that it won't increment again within this month
               if remaining_subtract > 0:
                  loan_waterfall(remaining_subtract, clo.get_tranches())
            else: # waterfall it
               loan_waterfall(beginning_bal, clo.get_tranches())
        else: # if no principal paydown value, just move on
               portfolio_index += 1

      # INNER (LOANS) LOOP ENDS

      # save current balances of each tranche object (for final output)
      for tranche in clo.get_tranches():
        tranche.save_balance(tranche_df, months_passed)
      
      print(tranche_df)

      # calculate and append this month's clo cashflow
      clo.append_cashflow(months_passed, upfront_costs, days, SOFR, tranche_df, terminate_next) 

      #calculate and appednd this month's loan cashflow 
      total_principal_paydown = loan_df.loc[(slice(None), months_passed), 'Principal Paydown'].sum()
      total_interest_income = loan_df.loc[(slice(None), months_passed), 'Interest Income'].sum()
      month_cashflow = total_interest_income + total_principal_paydown
      loan_portfolio.update_loan_cashflow(month_cashflow)

      # calculate and append each month's total collateral balance to the collateral list 
      loan_portfolio.get_collateral_sum()

      # terminate outer (months) loop, if AAA was below threshold in prev month
      if terminate_next:
         deal_call_month = months_passed
         break 
      
      # check if AAA is below threshold -> if so, signal to terminate
      if clo.get_tranches()[0].get_size() <= threshold:
          terminate_next = True 

      # increment months
      months_passed += 1

    # ------------------ TESTING PURPOSES ONLY ------------------- #
    # VIEW LOAN DATAFRAME
    #print(loan_df.tail(longest_duration))
    #loan_df.to_excel('loandata.xlsx', index=True)
    # VIEW TRANCHE DATAFRAME
    #print(tranche_df.loc['A'])
    #print(tranche_df.loc['A-S'])
    #print(tranche_df.loc['B'])
    #print(tranche_df.head(longest_duration))
    #tranche_df.to_excel('tranchedata.xlsx', index=True)
    # VIEW CASHFLOW DATA AS DATAFRAME
    #cashflow_data = {'Cashflows': clo.get_total_cashflows()}
    #print(pd.DataFrame(cashflow_data))

    # -------------------------------- CALCULATE OUTPUTS --------------------------------- #
    # WEIGHTED AVG COST OF FUNDS
    wa_cof = (npf.irr(clo.get_total_cashflows())*12*360/365 - SOFR) * 100 # in bps
    
    # WEIGHTED AVG ADVANCE RATE
    avg_clo_bal = 0
    for i in range(len(clo.get_tranches())):
       avg_clo_bal += sum(clo.get_tranches()[i].get_bal_list()) / deal_call_month
    avg_collateral_bal = loan_df['Ending Balance'].sum() / deal_call_month
    wa_adv_rate = (avg_clo_bal/avg_collateral_bal) * 100

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
 
    # -------------------------------- SAVE OUTPUTS TO DATAFRAME --------------------------------- #
    output_dataframe.loc[trial_index, 'Deal Call Month'] = deal_call_month
    output_dataframe.loc[trial_index, 'WA COF'] = wa_cof
    output_dataframe.loc[trial_index, 'WA Adv Rate'] = wa_adv_rate
    output_dataframe.loc[trial_index, 'Projected Equity Yield'] = projected_equity_yield
    
    return output_dataframe


if __name__ == "__main__":
   # ------------------------ PRESET INFO ------------------------ #
    excel_file_path = "FL1_Setup_InternalMethod.xlsx"
    NUM_TRIALS = 3
    trial_numbers = range(0, NUM_TRIALS)
    columns = ['Deal Call Month', 'WA COF', 'WA Adv Rate', 'Projected Equity Yield']
    ma_output_df = pd.DataFrame(index=trial_numbers, columns=columns)

   # ------------------------ READ EXCEL: OTHER SPECIFICATIONS ------------------------ #
    df_os = pd.read_excel(excel_file_path, sheet_name = "Other Specifications", header=None)

    # assume they're giving us a date at the end of the month
    first_payment_date = df_os.iloc[2, 1]
    date_str = first_payment_date.strftime("%m-%d-%Y")
    date = date_str.split("-") # ["MM", "DD", "YYYY"]
    date = list(map(int, date)) # [MM, DD, YYYY]
    # starting payment month
    starting_mos = date[0]
    days_in_mos = get_date_array(date)
    SOFR_value = df_os.iloc[3,1]
    has_reinvestment = df_os.iloc[4,1]
    has_replenishment = df_os.iloc[5,1]
    reinvestment_period = df_os.iloc[1,1]
    replenishment_period = df_os.iloc[6,1]
    replenishment_amount = df_os.iloc[7,1]
    has_existing_data = df_os.iloc[10,1]
  
    # --------------------------- READ EXCEL: UPFRONT COSTS --------------------------- #

    df_uc = pd.read_excel(excel_file_path, sheet_name = "Upfront Costs", header=None)
    placement_percent = df_uc.iloc[0,1]
    legal = df_uc.iloc[1, 1]
    accounting = df_uc.iloc[2, 1]
    trustee = df_uc.iloc[3, 1]
    printing = df_uc.iloc[4, 1]
    RA_site = df_uc.iloc[5, 1]
    modeling = df_uc.iloc[6, 1]
    misc = df_uc.iloc[7, 1]

 # ------------------------ READ EXCEL: OBJECT DATA ------------------------ #
    ramp_up = df_os.iloc[0, 1]

    # read excel file for capital stack
    df_cs = pd.read_excel(excel_file_path, sheet_name = "Capital Stack")

    # read excel file for loans
    df_cp = pd.read_excel(excel_file_path, sheet_name = "Collateral Portfolio")

# ------------------------ READ EXCEL: EXISTING DATA ------------------------ #

# pseudocode 

# read sheet with existing tranche data 
# calculate months_passed / current_month 
# store all data to dataframe (tranche balance, tranche principal / interest)
# populate loan dataframe
   # get month 0 data from portfolio
   # run regular loan calculations 
   # calculate which loans have paid off and delete them from the active portfolio 
   # calculate loan interest 
   # check if any new loans have been added 
# store existing clo cashflows 

# run the simulation starting with x months_passed 

    # ------------------------ RUN SIMULATION IN LOOP ------------------------ #
    if has_existing_data:
      for run in range(NUM_TRIALS):
         # initialize objects (must redo every run)
         clo_obj = CLO(ramp_up, has_reinvestment, has_replenishment, reinvestment_period, replenishment_period, replenishment_amount, first_payment_date)

         pd.options.display.float_format = '{:,.2f}'.format

         # ------------- READ EXCEL FOR TRANCHES -----------------
         # delete unused column
         df_cs.drop(columns=['Payment Date'], inplace=True)
         df_cs.rename(columns={
               'Class Name' : 'Tranche Name',
               'Period Date' : 'Period Date',
               'Balance' : 'Tranche Size',
               'Principal' : 'Principal Payment',
               'Interest' : 'Interest Payment'
            }, inplace=True)
         # set two indexes
         df_cs.set_index(['Tranche Name', 'Period Date'], inplace=True)
         # sort the index for better formatting
         df_cs.sort_index(inplace=True)

         print(df_cs)

         # get CLO start date and current date
         # lol we actually don't need these two here
         start_date = df_cs.loc['A', :].index[0]
         current_date = df_cs.loc['A', :].index[-1]
         mos_passed = df_cs.index.get_level_values(1).nunique()
         aaa_threshold = 0.2 * df_cs.loc[('A', start_date), 'Tranche Size']
         #print(aaa_threshold)

         # extract tranche names
         unique_tranche_names = df_cs.index.get_level_values('Tranche Name').unique()
         for tranche_name in unique_tranche_names:
            # get data for each tranche based on name
            tranche_data = df_cs.loc[tranche_name]
            last_row = tranche_data.iloc[-1] # most recent values

            clo_obj.add_tranche(name=tranche_name,
                                 rating="n/a",
                                 offered=1, # we don't know which are offered sigh
                                 size=last_row["Tranche Size"],
                                 spread=0.05,
                                 price=99)
         # prints out the tranches
         #for tranche in clo_obj.get_all_tranches():
         #   print(tranche)

         loan_portfolio_obj = CollateralPortfolio(0)

         # ---------------- READ EXCEL FOR LOANS -------------------
         # drop unneeded column
         df_cp.drop(columns=['Loan Name'], inplace=True)
         #print(df_cp)

         # adds all remaining loans to the loan portfolio
         for loan_num in range(df_cp.shape[0]):
            loan_portfolio_obj.add_initial_loan(loan_id=loan_num + 1, 
                                                loan_balance=df_cp.at[loan_num, 'Collateral Balance'], 
                                                margin=df_cp.at[loan_num, 'Market Repo Spread'], 
                                                index_floor=1, # what is this
                                                # need to actually calculate remaining loan terms
                                                remaining_loan_term=df_cp.at[loan_num, 'Loan Term'] - mos_passed, 
                                                extension_period=0, 
                                                open_prepayment_period=0, 
                                                manual_term=0)
            loan_portfolio_obj.get_active_portfolio()[loan_num].set_term_length(df_cp.at[loan_num, 'Loan Term'])
         
         total_upfront_costs = clo_obj.get_upfront_costs(placement_percent, legal, accounting, trustee, printing, RA_site, modeling, misc)
         
         output_df = run_simulation("manual terms", ma_output_df, run, clo_obj, loan_portfolio_obj, starting_mos, days_in_mos, SOFR_value, total_upfront_costs, aaa_threshold, mos_passed, df_cs, current_date)
      # exit loop and display dataframe data in excel graphs
      manual_loan_graphs(output_df)

    print(output_df)

    
