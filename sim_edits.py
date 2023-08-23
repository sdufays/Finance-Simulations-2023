from collateral_class import CollateralPortfolio
from clo_class import CLO
from graphing import *
import pandas as pd
import numpy_financial as npf
import numpy as np
from collections import Counter

from datetime import datetime, timedelta

def month_end_date(year, month):
    # Start with the first day of the next month
    next_month = month % 12 + 1
    if month == 12:
        year += 1
    # Subtract one day to get the last day of the input month
    return datetime(year, next_month, 1) - timedelta(days=1)

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
def run_simulation(output_dataframe, trial_index, clo, loan_portfolio, starting_month, starting_year, days_in_month, SOFR, upfront_costs, advance_rate_threshold, months_passed, old_tranche_df, curr_date, margin_lower, margin_upper):
    longest_duration = 100
    original_months_passed = months_passed

    # --------------------------------- INITIALIZE LOOP VARIABLES -------------------------------------- #
    terminate_next = False

    # initial CLO variables
    initial_clo_tob = clo.get_tob()
    for tranche in clo.get_tranches():
       tranche.init_principal_dict_MANUAL(original_months_passed, longest_duration)

    # ------------------------ CREATE LOAN DATAFRAME ------------------------ #
    loan_ids = list(range(1, 1 + len(loan_portfolio.get_active_portfolio())))  # generate loan ids
    months = list(range(months_passed + 1, longest_duration))
    loan_index = pd.MultiIndex.from_product([loan_ids, months],
                                   names=['Loan ID', 'Months Passed'])
    loan_df = pd.DataFrame(index=loan_index, columns=['Current Month', 'Beginning Balance', 'Ending Balance', 'Principal Paydown', 'Interest Income'])
    loan_df = loan_df.fillna(0)
    #print(loan_df.head(longest_duration-months_passed))

    # ------------------------ CREATE TRANCHE DATAFRAME ------------------------ #
    # SAVE CASH FLOWS
    # saves a list of single tranche cashflows to all tranches
    for tranche in clo.get_tranches():
      tranche.init_tranche_cashflow_list(old_tranche_df.loc[tranche.get_name(), "Total Cashflow"].tolist())
    # sums cash flows for all other tranches
    monthly_cashflow_sums = old_tranche_df.groupby(level=1).sum()
    cashflow_list = monthly_cashflow_sums['Total Cashflow'].tolist()
    clo.set_total_cashflows_MANUAL(cashflow_list)
    
    # CREATE TRANCHE DF
    tranche_names = []
    for tranche in clo.get_tranches():
      tranche_names.append(tranche.get_name())
    tranche_index = pd.MultiIndex.from_product([tranche_names, months], names=['Tranche Name', 'Month'])
    tranche_df = pd.DataFrame(index=tranche_index, columns=['Interest Payment', 'Principal Payment', 'Tranche Size'])
    
    replen_months = 0
    replen_cumulative = 0
    incremented_replen_month = False

    # we're now in the 47th month
    months_passed += 1

    # --------------------------------- START MONTH LOOP -------------------------------------- #
    while months_passed in range(longest_duration):
      # loan counter starts at 0 
      portfolio_index = 0 
      current_month = (starting_month + months_passed) % 12 or 12
      # START LOANS LOOP
      while portfolio_index < len(loan_portfolio.get_active_portfolio()):
        # initialize loan object
        loan = loan_portfolio.get_active_portfolio()[portfolio_index]
        # update remaining term length
        loan.update_remaining_loan_term()
        # update dataframe indexes when new loans are added
        loan_id = loan.get_loan_id()
        if loan_id not in loan_ids:
            loan_ids.append(loan_id)
        loan_index = pd.MultiIndex.from_product([loan_ids, months], names=['Loan ID', 'Months Passed'])
        loan_df = loan_df.reindex(loan_index)
        # fill nan values in df with 0
        loan_df = loan_df.fillna(0)
        tranche_df = tranche_df.fillna(0)

        # GET CALCULATIONS
        beginning_bal = loan.beginning_balance_MANUAL(months_passed, loan_df, original_months_passed)
        principal_pay = loan.principal_paydown_MANUAL(months_passed, loan_df, original_months_passed) # WRONG RN i haven't edited it so loans aren't paying off cuz they don't have starting month
        ending_bal = loan.ending_balance_MANUAL(beginning_bal, principal_pay)
        days = days_in_month[current_month - 2]
        interest_inc = loan.interest_income(beginning_bal, SOFR, days) 
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
               loan_portfolio.add_new_loan_MANUAL(beginning_bal, margin_lower, margin_upper, months_passed, ramp=False)
            elif replenishment_bool:
               loan_value = min(beginning_bal, clo.get_replen_amount() - replen_cumulative)
               loan_portfolio.add_new_loan_MANUAL(loan_value, margin_lower, margin_upper, months_passed, ramp=False)
               replen_cumulative += loan_value
               remaining_subtract = beginning_bal - loan_value
               if remaining_subtract > 0:
                  loan_waterfall(remaining_subtract, clo.get_tranches())
            elif replen_after_reinv_bool:
               loan_value = min(beginning_bal, clo.get_replen_amount() - replen_cumulative)
               loan_portfolio.add_new_loan_MANUAL(loan_value,  margin_lower, margin_upper, months_passed, ramp=False)
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
      
      # calculate and append this month's clo cashflow
      # use old_tranche_df to get tranche size
      clo.append_cashflow_MANUAL(months_passed, days, SOFR, tranche_df, terminate_next, original_months_passed, old_tranche_df, curr_date) 

      # terminate outer (months) loop, if below threshold in prev month
      if terminate_next:
         deal_call_month = months_passed
         break 
      
      # check if wa advance rate is below threshold
      if (clo.current_clo_size(tranche_df, months_passed) / loan_portfolio.get_collateral_sum()) < advance_rate_threshold:
          terminate_next = True 
         
      # increment months
      months_passed += 1

    # ------------------ TEST SIMULATION ------------------- #
    # VIEW LOAN DATAFRAME
    #print(loan_df.tail(longest_duration))
    #loan_df.to_excel('loandata.xlsx', index=True)
    # VIEW TRANCHE DATAFRAME
    #print(tranche_df.loc['A'])
    #print(tranche_df.loc['A-S'])
    #print(tranche_df.loc['B'])
    #print(tranche_df.head(longest_duration))
    tranche_df.to_excel('tranchedata.xlsx', index=True)
    # VIEW CASHFLOW DATA AS DATAFRAME
    #cashflow_data = {'Cashflows': clo.get_total_cashflows()}
    #print(pd.DataFrame(cashflow_data))

    # -------------------------------- CALCULATE OUTPUTS --------------------------------- #
    monthly_tax_inc = {}
    net_loss_dict = {} # {1:[q1,q2,q3,q4], 2:[q1,q2,q3,q4]...}
    for i in range(deal_call_month // 12):
       net_loss_dict[i] = []

    year = 0
    # MONTHLY TAX CALCULATIONS
    for mo in range(deal_call_month): 
      current_month = (starting_month + mo) % 12 or 12
      # for indexing old tranche df
      mo_end_date = month_end_date(start_year + year, current_month)

      # COLLATERAL INTEREST: sum of interest rates of all tranches (A-R) from starting_month to mo
      if mo > original_months_passed:
         past_interest_sum = old_tranche_df['Interest Payment'].sum()
         new_interest_sum = tranche_df.loc[(tranche_df.index.get_level_values('Month') <= mo)].groupby(level='Tranche Name')['Interest Payment'].sum()
         collateral_interest_amt = past_interest_sum + new_interest_sum
      else:
         collateral_interest_amt = old_tranche_df.loc[(old_tranche_df.index.get_level_values('Period Date') <= mo_end_date)].groupby(level='Tranche Name')['Interest Payment'].sum()

      # NET TAXABLE INCOME
      interest_expense_sum = 0
      for tranche in clo.get_tranches():
         if tranche.get_name() != 'R':
            if mo > original_months_passed:
               interest_expense_sum += tranche_df.loc[(tranche.get_name(), mo), 'Interest Payment']
            else:
               interest_expense_sum += old_tranche_df.loc[(tranche.get_name(), mo_end_date), 'Interest Payment']
      # some cash flow values are 0 for some reason
      print(clo.get_tranches()[-1].get_tranche_cashflow_list())
      # this is nan for some reason
      discount_rate_R = npf.irr(clo.get_tranches()[-1].get_tranche_cashflow_list())
      print('discount rate {}'.format(discount_rate_R))
      # this is also nan
      tax_expense_accrual_R = npf.npv(discount_rate_R, clo.get_tranches()[-1].get_tranche_cashflow_list()[mo:deal_call_month])
      net_taxable_income = collateral_interest_amt - interest_expense_sum - tax_expense_accrual_R
      monthly_tax_inc[mo] = net_taxable_income

      # QUARTERLY TAX CALCULATIONS
      if current_month == 3 or current_month == 6 or current_month == 9 or current_month == 12:
         # keep track of quarter number and year
         quarter = 0 if current_month==3 else (1 if current_month==6 else (2 if current_month==9 else 3))
         if mo >= 12 and mo % 12 == 0:
            year+=1
         
         # if 3 or more months have passed
         if mo >= 2:
            # calculate sum of month-2, month-1, and month net taxable income and "apply" it on month-1
            taxable_income_sum = monthly_tax_inc[mo-2] + monthly_tax_inc[mo-1] + monthly_tax_inc[mo]
         # if deal starts in the middle or end of a quarter
         elif mo == 1:
            taxable_income_sum = monthly_tax_inc[mo-1] + monthly_tax_inc[mo]
         elif mo == 0:
            taxable_income_sum = monthly_tax_inc[mo]
            
         # calculate cumulative taxable loss for THIS quarter using quarterly taxable amount net loss from PREV quarter
         # if no previous quarter
         if mo <= 2:
            cumulative_taxable_loss = 0
         else:
            if quarter == 0: # if first quarter
               # get net loss of last quarter of prev year
               cumulative_taxable_loss = taxable_income_sum - net_loss_dict[year-1][-1]
            else: # if not the first quarter
               # get net loss of the previous quarter of current year
               cumulative_taxable_loss = taxable_income_sum - net_loss_dict[year][quarter-1]
         
         # calculate taxable amount net of loss for THIS quarter
         if taxable_income_sum < 0 or cumulative_taxable_loss < 0:
            quart_net_loss = 0
         else:
            if cumulative_taxable_loss > 0 and taxable_income_sum <= cumulative_taxable_loss:
               quart_net_loss = taxable_income_sum
            elif cumulative_taxable_loss > 0 and taxable_income_sum > cumulative_taxable_loss:
               quart_net_loss = cumulative_taxable_loss
         net_loss_dict[year].append(quart_net_loss)

         
         # YEARLY TAX LIABILITY
         yearly_tax_liability = []
         for year in net_loss_dict.keys():
            yearly_tax_liability.append(net_loss_dict[year].sum() * .25)
         print(yearly_tax_liability)
      
    # WEIGHTED AVG COST OF FUNDS
    wa_cof = (npf.irr(clo.get_total_cashflows())*12*360/365 - SOFR) * 100 # in bps
 
    # -------------------------------- SAVE OUTPUTS TO DATAFRAME --------------------------------- #
    output_dataframe.loc[trial_index, 'Deal Call Month'] = deal_call_month
    output_dataframe.loc[trial_index, 'WA COF'] = wa_cof

    return output_dataframe


if __name__ == "__main__":
   # ------------------------ PRESET INFO ------------------------ #
    excel_file_path = "FL1_Setup_InternalMethod.xlsx"
    NUM_TRIALS = 1
    trial_numbers = range(0, NUM_TRIALS)
    columns = ['Deal Call Month', 'WA COF']
    output_df = pd.DataFrame(index=trial_numbers, columns=columns)

   # ------------------------ READ EXCEL: OTHER SPECIFICATIONS ------------------------ #
    df_os = pd.read_excel(excel_file_path, sheet_name = "Other Specifications", header=None)

    # assume they're giving us a date at the end of the month
    first_payment_date = df_os.iloc[2, 1]
    date_str = first_payment_date.strftime("%m-%d-%Y")
    date = date_str.split("-") # ["MM", "DD", "YYYY"]
    date = list(map(int, date)) # [MM, DD, YYYY]
    # starting payment month
    starting_mos = date[0]
    start_year = date[2]
    days_in_mos = get_date_array(date)
    SOFR_value = df_os.iloc[3,1]
    has_reinvestment = df_os.iloc[4,1]
    has_replenishment = df_os.iloc[5,1]
    reinvestment_period = df_os.iloc[1,1]
    replenishment_period = df_os.iloc[6,1]
    replenishment_amount = df_os.iloc[7,1]
    has_existing_data = df_os.iloc[10,1]
    generic_spread_upper = df_os.iloc[11,1]
    generic_spread_lower = df_os.iloc[12,1]
    tranche_p_balance = df_os.iloc[13,1]
    adv_rate_threshold = df_os.iloc[14,1]
  
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
    df_cs = pd.read_excel(excel_file_path, sheet_name = "Capital Stack for Tax Calc")
    df_orig_cs = pd.read_excel(excel_file_path, sheet_name = "Original Capital Stack")


    # read excel file for loans
    df_cp = pd.read_excel(excel_file_path, sheet_name = "Collateral Portfolio")

   # ------------------------ RUN SIMULATION IN LOOP ------------------------ #
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

      #print(df_cs)

      # get CLO start date and current date
      start_date = df_cs.loc['A', :].index[0]
      current_date = df_cs.loc['A', :].index[-1]
      mos_passed = df_cs.index.get_level_values(1).nunique()

      # extract tranche names
      unique_tranche_names = df_cs.index.get_level_values('Tranche Name').unique()
      for tranche_name in unique_tranche_names:
         # get data for each tranche based on name
         tranche_data = df_cs.loc[tranche_name]
         last_row = tranche_data.iloc[-1] # most recent values
         
         if tranche_name in df_orig_cs['Name'].tolist():
            offered = df_orig_cs.loc[df_orig_cs['Name'].str.upper() == tranche_name.upper(), 'Offered'].iloc[0]
            spread = df_orig_cs.loc[df_orig_cs['Name'].str.upper() == tranche_name.upper(), 'Spread (bps)'].iloc[0]
            price = df_orig_cs.loc[df_orig_cs['Name'].str.upper() == tranche_name.upper(), 'Price'].iloc[0]
         else: # for PREF vs P and R
            offered = 0
            spread = 0 # not sure if they have spread?
            price = 0 # don't have price cuz it's not sold
         # populating the clo / tranche classes
         clo_obj.add_tranche(name=tranche_name,
                              rating="n/a",
                              offered=offered, 
                              size=last_row["Tranche Size"],
                              spread=spread / 10000, # cuz in bps
                              price=price)
      # prints out the tranches
      #for tranche in clo_obj.get_all_tranches():
      #   print(tranche)

      # we're not using markeket aware so it's 0
      loan_portfolio_obj = CollateralPortfolio(0)

      # ---------------- READ EXCEL FOR LOANS -------------------
      # drop unneeded columns
      df_cp.drop(columns=['Loan Name'], inplace=True)
      df_cp.drop(columns=['Market Repo Spread'], inplace=True)
      df_cp.drop(columns=['Market Repo Adv Rate'], inplace=True)

      # adds all remaining loans to the loan portfolio
      for loan_num in range(df_cp.shape[0]):
         loan_portfolio_obj.add_initial_loan(loan_id=loan_num + 1, 
                                             loan_balance=df_cp.at[loan_num, 'Collateral Balance'], 
                                             margin=df_cp.at[loan_num, 'Spread'], 
                                             index_floor=df_cp.at[loan_num, 'Index Floor'],
                                             # need to actually calculate remaining loan terms
                                             remaining_loan_term=df_cp.at[loan_num, 'Loan Term'] - mos_passed, 
                                             extension_period=0, # don't need these periods anymore
                                             open_prepayment_period=0, 
                                             manual_term=0)
         # set term length instead of calculating it
         loan_portfolio_obj.get_active_portfolio()[loan_num].set_term_length(df_cp.at[loan_num, 'Loan Term']) 
      
         total_upfront_costs = clo_obj.get_upfront_costs(placement_percent, legal, accounting, trustee, printing, RA_site, modeling, misc)
         
      output_df = run_simulation(output_df, run, clo_obj, loan_portfolio_obj, starting_mos, start_year, days_in_mos, SOFR_value, total_upfront_costs, adv_rate_threshold, mos_passed, df_cs, current_date, generic_spread_lower, generic_spread_upper)
    # exit loop and display dataframe data in excel graphs
    manual_loan_graphs(output_df)

    #print(output_df)

    
