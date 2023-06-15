from collateral_class import CollateralPortfolio
from clo_class import CLO
import pandas as pd
import numpy_financial as npf
import math
import numpy as np
import xlsxwriter
from collections import Counter

def get_date_array(date):
    if date[2] % 4 == 0:
      return [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    else: 
      return [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


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


def run_simulation(case, output_dataframe, trial_index):
 # ------------------------ INITIALIZE OBJECTS ------------------------ #
    ramp_up = df_os.iloc[0, 1]
    clo = CLO(ramp_up, has_reinvestment, has_replenishment, reinvestment_period, replenishment_period, replenishment_amount, first_payment_date)

    # read excel file for capital stack
    df_cs = pd.read_excel(excel_file_path, sheet_name = "Capital Stack")

    # add tranches in a loop
    for index_t, row_t in df_cs.iterrows():
      tranche_data = row_t[['Name', 'Rating', 'Offered', 'Size', 'Spread (bps)', 'Price']]
      clo.add_tranche(tranche_data[0], tranche_data[1], tranche_data[2], tranche_data[3], tranche_data[4] / 10000, tranche_data[5])
    threshold = clo.get_threshold()

    upfront_costs = clo.get_upfront_costs(placement_percent, legal, accounting, trustee, printing, RA_site, modeling, misc)
  
    loan_portfolio = CollateralPortfolio()

    # read excel file for loans
    df_cp = pd.read_excel(excel_file_path, sheet_name = "Collateral Portfolio")

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
            replenishment_bool = (clo.get_replen_bool() and not clo.get_reinv_bool()) and (months_passed <= clo.get_replen_period() and replen_cumulative < clo.get_replen_amount()) and (months_passed == loan.get_term_length())
            replen_after_reinv_bool = (clo.get_reinv_bool() and clo.get_replen_bool()) and (months_passed > clo.get_reinv_period()) and (replen_months < clo.get_replen_period() and replen_cumulative < clo.get_replen_amount()) and (months_passed == loan.get_term_length())

            if reinvestment_bool:
               loan_portfolio.add_new_loan(beginning_bal, margin, months_passed, ramp=False)
            elif replenishment_bool:
               loan_value = min(beginning_bal, clo.get_replen_amount() - replen_cumulative)
               loan_portfolio.add_new_loan(loan_value, margin, months_passed, ramp=False)
               replen_cumulative += loan_value
               remaining_subtract = beginning_bal - loan_value
               #if months_passed == 17: print("remaining subtract {:,.2f}".format(remaining_subtract))
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
            else:  # waterfall it
               #print("NO NEW LOAN " + str(months_passed))
               #print("month {}\n principal pay {:,.2f}".format(months_passed, principal_pay))
               loan_waterfall(beginning_bal, clo.get_tranches())
        else:
               portfolio_index += 1

        tranche_df = tranche_df.fillna(0)

      # add current balances to list
      for tranche in clo.get_tranches():
        tranche.save_balance(tranche_df, months_passed)

      # inner loop ends 
      clo.append_cashflow(months_passed, upfront_costs, days, SOFR, tranche_df, terminate_next)

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
    #print(tranche_df.loc['A-S'])
    #print(tranche_df.loc['B'])
    #print(tranche_df.head(longest_duration))
    #tranche_df.to_excel('one_trial.xlsx', index=True)
    cashflow_data = {'Cashflows': clo.get_total_cashflows()}
    #print(pd.DataFrame(cashflow_data))
    

    # WEIGHTED AVG COST OF FUNDS
    wa_cof = (npf.irr(clo.get_total_cashflows())*12*360/365 - SOFR) * 100 # in bps
    #if wa_cof < 0:
      #tranche_df.to_excel('neg_cof_replen.xlsx', index=True)
      #print(loan_term_df)
    #print("WACOF {}".format(wa_cof))
    
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


def graphs(output_df):
# ---------------------------- READING DF ----------------------------- #
    deal_call_months_dict = {}
    wa_cof_dict = {}
    equity_yield_dict = {}
    adv_rate_dict = {}
    for case in cases:
       deal_call_months_list = []
       wa_cof_list = []
       equity_yield_list = []
       adv_rate_list = []
       for trial in trial_numbers:
          call_month = output_df.loc[(case, trial), 'Deal Call Month']
          call_month2 = output_df.loc[(case, trial), 'WA COF']
          call_month3 = output_df.loc[(case, trial), 'Projected Equity Yield']
          call_month4 = output_df.loc[(case, trial), 'WA Adv Rate']
          deal_call_months_list.append(call_month)
          wa_cof_list.append(call_month2)
          equity_yield_list.append(call_month3)
          adv_rate_list.append(call_month4)

       deal_call_months_dict[case] = deal_call_months_list
       wa_cof_dict[case] = wa_cof_list
       equity_yield_dict[case] = equity_yield_list
       adv_rate_dict[case] = adv_rate_list

    deal_call_months_sort = sorted(deal_call_months_list)

    dcm_unique = []
    for num in deal_call_months_sort:
       if num not in dcm_unique:
          dcm_unique.append(num)

    dcm_base_list = deal_call_months_dict['base']
    dcm_down_list = deal_call_months_dict['downside']
    dcm_up_list = deal_call_months_dict['upside']

    occ_dcm = Counter(deal_call_months_list)
    occ_dcm_base = Counter(dcm_base_list)
    occ_dcm_down = Counter(dcm_down_list)
    occ_dcm_up = Counter(dcm_up_list)
    occ_list_dcm_b = list(occ_dcm_base.items())
    occ_list_dcm_d = list(occ_dcm_down.items())
    occ_list_dcm_u = list(occ_dcm_up.items())
    occ_list_dcm = list(occ_dcm.items())
    occ_list_dcm.sort(key=lambda x: x[0])
    occ_list_dcm_b.sort(key=lambda x: x[0])
    occ_list_dcm_d.sort(key=lambda x: x[0])
    occ_list_dcm_u.sort(key=lambda x: x[0])

    counts_dcm = [count for num, count in occ_list_dcm]
    counts_dcm_base = [count for num, count in occ_list_dcm_b]
    counts_dcm_downside = [count for num, count in occ_list_dcm_d]
    counts_dcm_upside = [count for num, count in occ_list_dcm_u]
    


   # ------------------------- GRAPHING OUTPUTS -------------------------- #
    workbook = xlsxwriter.Workbook('graphs.xlsx')
    worksheet_dcm = workbook.add_worksheet("Deal Call Months")
    worksheet_base = workbook.add_worksheet("Base")
    worksheet_downside = workbook.add_worksheet("Downside")
    worksheet_upside = workbook.add_worksheet("Upside")
    bold = workbook.add_format({'bold': 1})
    headings_dcm = ['Sims', 'Base', 'Downside', 'Upside']
    headings_base = ['Sims', 'Base']
    headings_downside = ['Sims', 'Downside']
    headings_upside = ['Sims', 'Upside']

    # deal call months
    data_dcm = [
       list(range(1, NUM_TRIALS + 1)), # this is my x-axis
       deal_call_months_dict['base'], # this is one batch of data aka the y-axis
       deal_call_months_dict['downside'],
       deal_call_months_dict['upside']
    ]

    data_base = [ # lol
       list(range(1, NUM_TRIALS + 1)),
       deal_call_months_dict['base']
    ]

    data_downside = [
       list(range(1, NUM_TRIALS + 1)),
       deal_call_months_dict['downside']
    ]

    data_upside = [
       list(range(1, NUM_TRIALS + 1)),
       deal_call_months_dict['upside']
    ]

    worksheet_dcm.write_row('A1', headings_dcm, bold)
    worksheet_base.write_row('A1', headings_base, bold)
    worksheet_downside.write_row('A1', headings_downside, bold)
    worksheet_upside.write_row('A1', headings_upside, bold)
   
    # writing columns for dcm
    worksheet_dcm.write_column('A2', data_dcm[0])
    worksheet_dcm.write_column('B2', data_dcm[1])
    worksheet_dcm.write_column('C2', data_dcm[2])
    worksheet_dcm.write_column('D2', data_dcm[3])

    # writing columns for base
    worksheet_base.write_column('A2', data_base[0])
    worksheet_base.write_column('B2', data_base[1])

    # writing columns for downside
    worksheet_downside.write_column('A2', data_downside[0])
    worksheet_downside.write_column('B2', data_downside[1])

    # writing columns for upside
    worksheet_upside.write_column('A2', data_upside[0])
    worksheet_upside.write_column('B2', data_upside[1])

    # scatter chart object
    chart1 = workbook.add_chart({'type': 'scatter'})
    chart2 = workbook.add_chart({'type': 'scatter'})
    chart3 = workbook.add_chart({'type': 'scatter'})
    chart4 = workbook.add_chart({'type': 'scatter'})

    # base, downside, upside
    chart1.add_series({
       'name':       ['Deal Call Months', 0, 1],
       'categories': ['Deal Call Months', 1, 0, NUM_TRIALS, 0], # x axis values placement ['Sheet name', first_row, first_column, last_row, last_column]
       'values':     ['Deal Call Months', 1, 1, NUM_TRIALS, 1] # y axis values placement ['Sheet name', first_row, first_column, last_row, last_column]
    })

    chart1.add_series({
       'name':       ['Deal Call Months', 0, 2],
       'categories': ['Deal Call Months', 1, 0, NUM_TRIALS, 0], 
       'values':     ['Deal Call Months', 1, 2, NUM_TRIALS, 2]
    })

    chart1.add_series({
       'name':       ['Deal Call Months', 0, 3],
       'categories': ['Deal Call Months', 1, 0, NUM_TRIALS, 0],
       'values':     ['Deal Call Months', 1, 3, NUM_TRIALS, 3]
    })

    # just base
    chart2.add_series({
       'name':       ['Base', 0, 1],
       'categories': ['Base', 1, 0, NUM_TRIALS, 0], 
       'values':     ['Base', 1, 1, NUM_TRIALS, 1]
    })

    # just downside
    chart3.add_series({
       'name':       ['Downside', 0, 2],
       'categories': ['Downside', 1, 0, NUM_TRIALS, 0],
       'values':     ['Downside', 1, 1, NUM_TRIALS, 1]
    })

    # just upside
    chart4.add_series({
       'name':       ['Upside', 0, 3],
       'categories': ['Upside', 1, 0, NUM_TRIALS, 0], 
       'values':     ['Upside', 1, 1, NUM_TRIALS, 1]
    })

    # chart title 
    chart1.set_title ({'name': 'Deal Call Months for All Scenarios'})
    chart2.set_title ({'name': 'Deal Call Months for Base Scenario'})
    chart3.set_title ({'name': 'Deal Call Months for Downside Scenario'})
    chart4.set_title ({'name': 'Deal Call Months for Upside Scenario'})
   
    # x-axis label
    chart1.set_x_axis({'name': 'Simulation Number'})
    chart2.set_x_axis({'name': 'Simulation Number'})
    chart3.set_x_axis({'name': 'Simulation Number'})
    chart4.set_x_axis({'name': 'Simulation Number'})
   
    # y-axis label
    chart1.set_y_axis({'name': 'Deal Call Month', 'min': 20})
    chart2.set_y_axis({'name': 'Deal Call Month', 'min': 20})
    chart3.set_y_axis({'name': 'Deal Call Month', 'min': 20})
    chart4.set_y_axis({'name': 'Deal Call Month', 'min': 20})
   
    # Set an Excel chart style.
    # 1 - grey / 2 - blue, red / 3 - blues / 4 - reds / 5  - greens / 6 - purples 
    # 7 - like a light blueish green / 8 - oranges / 9 - ew / 10 - blue, orangey red
    chart1.set_style(2)
    chart2.set_style(3)
    chart3.set_style(4)
    chart4.set_style(5)
    chart1.set_size({'width': 600, 'height': 400})
    chart2.set_size({'width': 600, 'height': 400})
    chart3.set_size({'width': 600, 'height': 400})
    chart4.set_size({'width': 600, 'height': 400})

    worksheet_dcm.insert_chart('F2', chart1)
    worksheet_base.insert_chart('E2', chart2)
    worksheet_downside.insert_chart('E2', chart3)
    worksheet_upside.insert_chart('E2', chart4)

    # ------------------------------- SWAPPED --------------------------------- #
    worksheet_swapped = workbook.add_worksheet("Deal Call Months Frequency")
    bold = workbook.add_format({'bold': 1})
    headings_swapped = ['Deal Call Months']

    data_swapped = [
       dcm_unique,
       counts_dcm
    ]
    
    worksheet_swapped.write_row('A1', headings_swapped, bold)
    worksheet_swapped.write_column('A2', data_swapped[0])
    worksheet_swapped.write_column('B2', data_swapped[1])

    chart5 = workbook.add_chart({'type': 'column'})
    chart5.add_series({
       'name':       ['Deal Call Months Frequency', 0, 1],
       'categories': ['Deal Call Months Frequency', 1, 0, max(dcm_unique), 0],
       'values':     ['Deal Call Months Frequency', 1, 1, max(dcm_unique), 1]
    })

    chart5.set_title ({'name': 'ALL Deal Call Month Frequency'})
    chart5.set_x_axis({'name': 'Deal Call Month'})
    chart5.set_y_axis({'name': 'Frequency'})
    chart5.set_size({'width': 1700, 'height': 400})

    chart5.set_style(8)
    worksheet_swapped.insert_chart('F2', chart5)

    # ------------------------------- SWAPPED BASE --------------------------------- #
    worksheet_sb = workbook.add_worksheet("Deal Call Months Base Frequency")
    bold = workbook.add_format({'bold': 1})
    headings_swapped = ['Deal Call Months']

    data_sb = [
       dcm_unique,
       counts_dcm_base
    ]
    
    worksheet_sb.write_row('A1', headings_swapped, bold)
    worksheet_sb.write_column('A2', data_sb[0])
    worksheet_sb.write_column('B2', data_sb[1])

    chart6 = workbook.add_chart({'type': 'column'})
    chart6.add_series({
       'name':       ['Deal Call Months Base Frequency', 0, 1],
       'categories': ['Deal Call Months Base Frequency', 1, 0, max(dcm_unique), 0],
       'values':     ['Deal Call Months Base Frequency', 1, 1, max(dcm_unique), 1]
    })

    chart6.set_title ({'name': 'Deal Call Month Frequency'})
    chart6.set_x_axis({'name': 'Deal Call Month'})
    chart6.set_y_axis({'name': 'Frequency'})
    chart6.set_size({'width': 1700, 'height': 400})

    chart6.set_style(3)
    worksheet_sb.insert_chart('F2', chart6)

    # ------------------------------- SWAPPED DOWNSIDE --------------------------------- #
    worksheet_sd = workbook.add_worksheet("Deal Call Months Downside Freq")

    data_sd = [
       dcm_unique,
       counts_dcm_downside
    ]
    
    worksheet_sd.write_row('A1', headings_swapped, bold)
    worksheet_sd.write_column('A2', data_sd[0])
    worksheet_sd.write_column('B2', data_sd[1])

    chart7 = workbook.add_chart({'type': 'column'})
    chart7.add_series({
       'name':       ['Deal Call Months Downside Freq', 0, 1],
       'categories': ['Deal Call Months Downside Freq', 1, 0, max(dcm_unique), 0],
       'values':     ['Deal Call Months Downside Freq', 1, 1, max(dcm_unique), 1]
    })

    chart7.set_title ({'name': 'Deal Call Month Frequency'})
    chart7.set_x_axis({'name': 'Deal Call Month'})
    chart7.set_y_axis({'name': 'Frequency'})
    chart7.set_size({'width': 1700, 'height': 400})

    chart7.set_style(4)
    worksheet_sd.insert_chart('F2', chart7)

    # ------------------------------- SWAPPED UPSIDE --------------------------------- #
    worksheet_su = workbook.add_worksheet("Deal Call Months Upside Freq")

    data_su = [
       dcm_unique,
       counts_dcm_upside
    ]
    
    worksheet_su.write_row('A1', headings_swapped, bold)
    worksheet_su.write_column('A2', data_su[0])
    worksheet_su.write_column('B2', data_su[1])

    chart8 = workbook.add_chart({'type': 'column'})
    chart8.add_series({
       'name':       ['Deal Call Months Upside Freq', 0, 1],
       'categories': ['Deal Call Months Upside Freq', 1, 0, max(dcm_unique), 0],
       'values':     ['Deal Call Months Upside Freq', 1, 1, max(dcm_unique), 1]
    })

    chart8.set_title ({'name': 'Deal Call Month Frequency'})
    chart8.set_x_axis({'name': 'Deal Call Month'})
    chart8.set_y_axis({'name': 'Frequency'})
    chart8.set_size({'width': 1700, 'height': 400})

    chart8.set_style(5)
    worksheet_su.insert_chart('F2', chart8)

    # --------------------------------- WEIGHTED AVERAGE COST OF FUNDS ------------------------------------ #
    worksheet_wa_cof = workbook.add_worksheet("WA Cost of Funds")

    bin_ranges = [round(x, 1) for x in np.linspace(3.7, 4.4, 11)]

    hist, bins = np.histogram(output_df['WA COF'].unique(), bins=bin_ranges)

    worksheet_wa_cof.write_column('A1', [f"[{bins[i]}-{bins[i+1]}]" for i in range(len(bins)-1)], bold)
    worksheet_wa_cof.write_column('B1', hist)
    chart9 = workbook.add_chart({'type': 'column'})

    chart9.add_series({
       'name':       'Frequency',
       'categories': ['WA Cost of Funds', 0, 0, len(hist)-2, 0],
       'values':     ['WA Cost of Funds', 0, 1, len(hist)-1, 1]
    })

    chart9.set_title ({'name': 'ALL WA Cost of Funds Frequency'})
    chart9.set_x_axis({'name': 'Weighted Average Cost of Fund'})
    chart9.set_y_axis({'name': 'Frequency'})
    chart9.set_x_axis({
       'name': 'Weighted Average Cost of Fund',
       'categories': ['WA Cost of Funds', 1, 0, len(hist)-1, 0],
       'num_format': '0.00'
    })
   
    chart9.set_style(6)
    chart9.set_size({'width': 600, 'height': 400})
    worksheet_wa_cof.insert_chart('E2', chart9)

    # --------------------------------- WEIGHTED AVERAGE COST OF FUNDS BASE ------------------------------------ #
    worksheet_wa_cofb = workbook.add_worksheet("WA Cost of Funds Base")

    bin_ranges = [round(x, 1) for x in np.linspace(3.7, 4.4, 11)]

    hist, bins = np.histogram(wa_cof_dict['base'], bins=bin_ranges)

    worksheet_wa_cofb.write_column('A1', [f"[{bins[i]}-{bins[i+1]}]" for i in range(len(bins)-1)], bold)
    worksheet_wa_cofb.write_column('B1', hist)
    chart10 = workbook.add_chart({'type': 'column'})

    chart10.add_series({
       'name':       'Frequency',
       'categories': ['WA Cost of Funds Base', 0, 0, len(hist)-2, 0],
       'values':     ['WA Cost of Funds Base', 0, 1, len(hist)-1, 1]
    })

    chart10.set_title ({'name': 'BASE  WA Cost of Funds Frequency'})
    chart10.set_x_axis({'name': 'Weighted Average Cost of Fund'})
    chart10.set_y_axis({'name': 'Frequency'})
    chart10.set_x_axis({
       'name': 'Weighted Average Cost of Fund',
       'categories': ['WA Cost of Funds', 1, 0, len(hist)-1, 0],
       'num_format': '0.00'
    })
   
    chart10.set_style(3)
    chart10.set_size({'width': 600, 'height': 400})
    worksheet_wa_cofb.insert_chart('E2', chart10)

    # --------------------------------- WEIGHTED AVERAGE COST OF FUNDS DOWNSIDE ------------------------------------ #
    worksheet_wa_cofd = workbook.add_worksheet("WA Cost of Funds Downside")

    bin_ranges = [round(x, 1) for x in np.linspace(3.7, 4.4, 11)]

    hist, bins = np.histogram(wa_cof_dict['downside'], bins=bin_ranges)

    worksheet_wa_cofd.write_column('A1', [f"[{bins[i]}-{bins[i+1]}]" for i in range(len(bins)-1)], bold)
    worksheet_wa_cofd.write_column('B1', hist)
    chart11 = workbook.add_chart({'type': 'column'})

    chart11.add_series({
       'name':       'Frequency',
       'categories': ['WA Cost of Funds Downside', 0, 0, len(hist)-2, 0],
       'values':     ['WA Cost of Funds Downside', 0, 1, len(hist)-1, 1]
    })

    chart11.set_title ({'name': 'DOWNSIDE WA Cost of Funds Frequency'})
    chart11.set_x_axis({'name': 'Weighted Average Cost of Fund'})
    chart11.set_y_axis({'name': 'Frequency'})
    chart11.set_x_axis({
       'name': 'Weighted Average Cost of Fund',
       'categories': ['WA Cost of Funds', 1, 0, len(hist)-1, 0],
       'num_format': '0.00'
    })
   
    chart11.set_style(4)
    chart11.set_size({'width': 600, 'height': 400})
    worksheet_wa_cofd.insert_chart('E2', chart11)

    # --------------------------------- WEIGHTED AVERAGE COST OF FUNDS UPSIDE ------------------------------------ #
    worksheet_wa_cofu = workbook.add_worksheet("WA Cost of Funds Upside")

    bin_ranges = [round(x, 1) for x in np.linspace(3.7, 4.4, 11)]

    hist, bins = np.histogram(wa_cof_dict['upside'], bins=bin_ranges)

    worksheet_wa_cofu.write_column('A1', [f"[{bins[i]}-{bins[i+1]}]" for i in range(len(bins)-1)], bold)
    worksheet_wa_cofu.write_column('B1', hist)
    chart12 = workbook.add_chart({'type': 'column'})

    chart12.add_series({
       'name':       'Frequency',
       'categories': ['WA Cost of Funds Upside', 0, 0, len(hist)-2, 0],
       'values':     ['WA Cost of Funds Upside', 0, 1, len(hist)-1, 1]
    })

    chart12.set_title ({'name': 'UPSIDE WA Cost of Funds Frequency'})
    chart12.set_x_axis({'name': 'Weighted Average Cost of Fund'})
    chart12.set_y_axis({'name': 'Frequency'})
    chart12.set_x_axis({
       'name': 'Weighted Average Cost of Fund',
       'categories': ['WA Cost of Funds', 1, 0, len(hist)-1, 0],
       'num_format': '0.00'
    })
   
    chart12.set_style(5)
    chart12.set_size({'width': 600, 'height': 400})
    worksheet_wa_cofu.insert_chart('E2', chart12)

    # -------------------------------- EQUITY YIELD ALL ------------------------------ #
    worksheet_ey = workbook.add_worksheet("Equity Yield")

    bin_ranges_eq = [round(x, 1) for x in np.linspace(8.5, 13, 9)]
    hist_eq, bins_eq = np.histogram(output_df['Projected Equity Yield'].unique(), bins=bin_ranges_eq)

    worksheet_ey.write_column('A1', [f"[{bins_eq[i]}-{bins_eq[i+1]}]" for i in range(len(bins_eq)-1)], bold)
    worksheet_ey.write_column('B1', hist_eq)
    chart13 = workbook.add_chart({'type': 'column'})

    chart13.add_series({
       'name':       'Frequency',
       'categories': ['Equity Yield', 0, 0, len(hist_eq)-2, 0],
       'values':     ['Equity Yield', 0, 1, len(hist_eq)-1, 1]
    })

    chart13.set_title ({'name': 'Equity Yield Frequency'})
    chart13.set_x_axis({'name': 'Equity Yield'})
    chart13.set_y_axis({'name': 'Frequency'})
    chart13.set_x_axis({
       'name': 'Equity Yield',
       'categories': ['Equity Yield', 1, 0, len(hist_eq)-2, 0],
       'num_format': '0.00'
    })
   
    chart13.set_style(1)
    chart13.set_size({'width': 600, 'height': 400})
    worksheet_ey.insert_chart('E2', chart13)

    # -------------------------------- EQUITY YIELD BASE------------------------------ #
    worksheet_eyb = workbook.add_worksheet("Equity Yield Base")

    bin_ranges_eq = [round(x, 1) for x in np.linspace(8.5, 13, 9)]
    hist_eq, bins_eq = np.histogram(equity_yield_dict['base'], bins=bin_ranges_eq)

    worksheet_eyb.write_column('A1', [f"[{bins_eq[i]}-{bins_eq[i+1]}]" for i in range(len(bins_eq)-1)], bold)
    worksheet_eyb.write_column('B1', hist_eq)
    chart14 = workbook.add_chart({'type': 'column'})

    chart14.add_series({
       'name':       'Frequency',
       'categories': ['Equity Yield Base', 0, 0, len(hist_eq)-2, 0],
       'values':     ['Equity Yield Base', 0, 1, len(hist_eq)-1, 1]
    })

    chart14.set_title ({'name': 'BASE Equity Yield Frequency'})
    chart14.set_x_axis({'name': 'Equity Yield'})
    chart14.set_y_axis({'name': 'Frequency'})
    chart14.set_x_axis({
       'name': 'Equity Yield',
       'categories': ['Equity Yield', 1, 0, len(hist_eq)-2, 0],
       'num_format': '0.00'
    })
   
    chart14.set_style(3)
    chart14.set_size({'width': 600, 'height': 400})
    worksheet_eyb.insert_chart('E2', chart14)

    # -------------------------------- EQUITY YIELD DOWNSIDE------------------------------ #
    worksheet_eyd = workbook.add_worksheet("Equity Yield Downside")

    bin_ranges_eq = [round(x, 1) for x in np.linspace(8.5, 13, 9)]
    hist_eq, bins_eq = np.histogram(equity_yield_dict['downside'], bins=bin_ranges_eq)

    worksheet_eyd.write_column('A1', [f"[{bins_eq[i]}-{bins_eq[i+1]}]" for i in range(len(bins_eq)-1)], bold)
    worksheet_eyd.write_column('B1', hist_eq)
    chart15 = workbook.add_chart({'type': 'column'})

    chart15.add_series({
       'name':       'Frequency',
       'categories': ['Equity Yield Downside', 0, 0, len(hist_eq)-2, 0],
       'values':     ['Equity Yield Downside', 0, 1, len(hist_eq)-1, 1]
    })

    chart15.set_title ({'name': 'DOWNSIDE Equity Yield Frequency'})
    chart15.set_x_axis({'name': 'Equity Yield'})
    chart15.set_y_axis({'name': 'Frequency'})
    chart15.set_x_axis({
       'name': 'Equity Yield',
       'categories': ['Equity Yield', 1, 0, len(hist_eq)-2, 0],
       'num_format': '0.00'
    })
   
    chart15.set_style(4)
    chart15.set_size({'width': 600, 'height': 400})
    worksheet_eyd.insert_chart('E2', chart15)

    # -------------------------------- EQUITY YIELD UPSIDE ------------------------------ #
    worksheet_eyu = workbook.add_worksheet("Equity Yield Upside")

    bin_ranges_eq = [round(x, 1) for x in np.linspace(8.5, 13, 9)]
    hist_eq, bins_eq = np.histogram(equity_yield_dict['upside'], bins=bin_ranges_eq)

    worksheet_eyu.write_column('A1', [f"[{bins_eq[i]}-{bins_eq[i+1]}]" for i in range(len(bins_eq)-1)], bold)
    worksheet_eyu.write_column('B1', hist_eq)
    chart16 = workbook.add_chart({'type': 'column'})

    chart16.add_series({
       'name':       'Frequency',
       'categories': ['Equity Yield Upside', 0, 0, len(hist_eq)-2, 0],
       'values':     ['Equity Yield Upside', 0, 1, len(hist_eq)-1, 1]
    })

    chart16.set_title ({'name': 'UPSIDE Equity Yield Frequency'})
    chart16.set_x_axis({'name': 'Equity Yield'})
    chart16.set_y_axis({'name': 'Frequency'})
    chart16.set_x_axis({
       'name': 'Equity Yield',
       'categories': ['Equity Yield', 1, 0, len(hist_eq)-2, 0],
       'num_format': '0.00'
    })
   
    chart16.set_style(5)
    chart16.set_size({'width': 600, 'height': 400})
    worksheet_eyu.insert_chart('E2', chart16)

    # -------------------------------- WA Adv Rate ALL ------------------------------ #
    worksheet_ar = workbook.add_worksheet("WA Adv Rate")

    bin_ranges_ar = np.linspace(0.83, 0.90, 10)
    hist_ar, bins_ar = np.histogram(output_df['WA Adv Rate'].unique(), bins=bin_ranges_ar)

    worksheet_ar.write_column('A1', [f"[{bins_ar[i]}-{bins_ar[i+1]}]" for i in range(len(bins_ar)-1)], bold)
    worksheet_ar.write_column('B1', hist_ar)
    chart17 = workbook.add_chart({'type': 'column'})

    chart17.add_series({
       'name':       'Frequency',
       'categories': ['WA Adv Rate', 0, 0, len(hist_ar)-2, 0],
       'values':     ['WA Adv Rate', 0, 1, len(hist_ar)-1, 1]
    })

    chart17.set_title ({'name': 'ALL WA Adv Rate Frequency'})
    chart17.set_x_axis({'name': 'WA Adv Rate'})
    chart17.set_y_axis({'name': 'Frequency'})
    chart17.set_x_axis({
       'name': 'WA Adv Rate',
       'categories': ['WA Adv Rate', 1, 0, len(hist_ar)-2, 0],
       'num_format': '0.00'
    })
   
    chart17.set_style(7)
    chart17.set_size({'width': 600, 'height': 400})
    worksheet_ar.insert_chart('E2', chart17)

    # -------------------------------- WA Adv Rate BASE ------------------------------ #
    worksheet_arb = workbook.add_worksheet("WA Adv Rate Base")

    bin_ranges_ar = np.linspace(0.83, 0.90, 10)
    hist_ar, bins_ar = np.histogram(adv_rate_dict['base'], bins=bin_ranges_ar)

    worksheet_arb.write_column('A1', [f"[{bins_ar[i]}-{bins_ar[i+1]}]" for i in range(len(bins_ar)-1)], bold)
    worksheet_arb.write_column('B1', hist_ar)
    chart18 = workbook.add_chart({'type': 'column'})

    chart18.add_series({
       'name':       'Frequency',
       'categories': ['WA Adv Rate Base', 0, 0, len(hist_ar)-2, 0],
       'values':     ['WA Adv Rate Base', 0, 1, len(hist_ar)-1, 1]
    })

    chart18.set_title ({'name': 'BASE WA Adv Rate Frequency'})
    chart18.set_x_axis({'name': 'WA Adv Rate'})
    chart18.set_y_axis({'name': 'Frequency'})
    chart18.set_x_axis({
       'name': 'WA Adv Rate',
       'categories': ['WA Adv Rate', 1, 0, len(hist_ar)-2, 0],
       'num_format': '0.00'
    })
   
    chart18.set_style(3)
    chart18.set_size({'width': 600, 'height': 400})
    worksheet_arb.insert_chart('E2', chart18)

    # -------------------------------- WA Adv Rate DOWNSIDE ------------------------------ #
    worksheet_ard = workbook.add_worksheet("WA Adv Rate Downside")

    bin_ranges_ar = np.linspace(0.83, 0.90, 10)
    hist_ar, bins_ar = np.histogram(adv_rate_dict['downside'], bins=bin_ranges_ar)

    worksheet_ard.write_column('A1', [f"[{bins_ar[i]}-{bins_ar[i+1]}]" for i in range(len(bins_ar)-1)], bold)
    worksheet_ard.write_column('B1', hist_ar)
    chart19 = workbook.add_chart({'type': 'column'})

    chart19.add_series({
       'name':       'Frequency',
       'categories': ['WA Adv Rate Downside', 0, 0, len(hist_ar)-2, 0],
       'values':     ['WA Adv Rate Downside', 0, 1, len(hist_ar)-1, 1]
    })

    chart19.set_title ({'name': 'DOWNSIDE WA Adv Rate Frequency'})
    chart19.set_x_axis({'name': 'WA Adv Rate'})
    chart19.set_y_axis({'name': 'Frequency'})
    chart19.set_x_axis({
       'name': 'WA Adv Rate',
       'categories': ['WA Adv Rate', 1, 0, len(hist_ar)-2, 0],
       'num_format': '0.00'
    })
   
    chart19.set_style(4)
    chart19.set_size({'width': 600, 'height': 400})
    worksheet_ard.insert_chart('E2', chart19)

    # -------------------------------- WA Adv Rate UPSIDE ------------------------------ #
    worksheet_aru = workbook.add_worksheet("WA Adv Rate Upside")

    bin_ranges_ar = np.linspace(0.83, 0.90, 10)
    hist_ar, bins_ar = np.histogram(adv_rate_dict['upside'], bins=bin_ranges_ar)

    worksheet_aru.write_column('A1', [f"[{bins_ar[i]}-{bins_ar[i+1]}]" for i in range(len(bins_ar)-1)], bold)
    worksheet_aru.write_column('B1', hist_ar)
    chart20 = workbook.add_chart({'type': 'column'})

    chart20.add_series({
       'name':       'Frequency',
       'categories': ['WA Adv Rate Upside', 0, 0, len(hist_ar)-2, 0],
       'values':     ['WA Adv Rate Upside', 0, 1, len(hist_ar)-1, 1]
    })

    chart20.set_title ({'name': 'UPSIDE WA Adv Rate Frequency'})
    chart20.set_x_axis({'name': 'WA Adv Rate'})
    chart20.set_y_axis({'name': 'Frequency'})
    chart20.set_x_axis({
       'name': 'WA Adv Rate',
       'categories': ['WA Adv Rate', 1, 0, len(hist_ar)-2, 0],
       'num_format': '0.00'
    })
   
    chart20.set_style(5)
    chart20.set_size({'width': 600, 'height': 400})
    worksheet_aru.insert_chart('E2', chart20)

    workbook.close()



if __name__ == "__main__":
   # ------------------------ GENERAL INFO ------------------------ #
    base = [.33, .33, .34]
    downside = [.30, .25, .45]
    upside = [.40, .35, .25]

    excel_file_path = "CLO_Input2.xlsm"

    # read excel file for Other Specifications
    df_os = pd.read_excel(excel_file_path, sheet_name = "Other Specifications", header=None)

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

    
    has_reinvestment = df_os.iloc[4,1]
    has_replenishment = df_os.iloc[5,1]

    reinvestment_period = df_os.iloc[1,1]
    replenishment_period = df_os.iloc[6,1]

    replenishment_amount = df_os.iloc[7,1]


    # --------------------------- UPFRONT COSTS --------------------------- #

    df_uc = pd.read_excel(excel_file_path, sheet_name = "Upfront Costs", header=None)
    placement_percent = df_uc.iloc[0,1]
    legal = df_uc.iloc[1, 1]
    accounting = df_uc.iloc[2, 1]
    trustee = df_uc.iloc[3, 1]
    printing = df_uc.iloc[4, 1]
    RA_site = df_uc.iloc[5, 1]
    modeling = df_uc.iloc[6, 1]
    misc = df_uc.iloc[7, 1]

    NUM_TRIALS = 100
    cases = ['base', 'downside', 'upside']
    trial_numbers = range(0, NUM_TRIALS)
    index = pd.MultiIndex.from_product([cases, trial_numbers], names=['Case', 'Trial Number'])
    columns = ['Deal Call Month', 'WA COF', 'WA Adv Rate', 'Projected Equity Yield']
    output_df = pd.DataFrame(index=index, columns=columns)


   # ------------------------ RUN SIMULATION ------------------------ #

    #run_simulation(base, output_df, trial_index=0)

   # ------------------------ RUN SIMULATION LOOPS ------------------------ #
   
    scenarios = [base, downside, upside]
    
    for scenario in scenarios:
        for run in range(NUM_TRIALS):
            output_df = run_simulation(scenario, output_df, run)
    print(output_df)
    graphs(output_df)

