from collateral_class import CollateralPortfolio
from clo_class import CLO
import pandas as pd
import numpy_financial as npf
import math
import numpy as np
import xlsxwriter

def get_date_array(date):
    if date[2] % 4 == 0:
      return [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    else: 
      return [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

def run_simulation(case):

 # ------------------------ INITIALIZE OBJECTS ------------------------ #
    ramp_up = df_os.iloc[0, 1]
    clo = CLO(ramp_up, has_reinvestment, has_replenishment, reinvestment_period, replenishment_period, replenishment_amount, first_payment_date)

    # read excel file for capital stack
    df_cs = pd.read_excel("CLO_Input.xlsm", sheet_name = "Capital Stack")

    # add tranches in a loop
    for index_t, row_t in df_cs.iterrows():
      tranche_data = row_t[['Name', 'Rating', 'Offered', 'Size', 'Spread (bps)', 'Price']]
      clo.add_tranche(tranche_data[0], tranche_data[1], tranche_data[2], tranche_data[3], tranche_data[4] / 10000, tranche_data[5])
    threshold = clo.get_threshold()

    upfront_costs = clo.get_upfront_costs(placement_percent, legal, accounting, trustee, printing, RA_site, modeling, misc)
  
    loan_portfolio = CollateralPortfolio()

    # read excel file for loans
    df_cp = pd.read_excel("CLO_Input.xlsm", sheet_name = "Collateral Portfolio")

    # add loans in a loop
    for index_l, row_l in df_cp.iterrows():
      loan_data = row_l[['Loan ID','Collateral Interest UPB', 'Margin', 'Index Floor', 'Loan Term (rem)', 'First Extension Period (mo)', 'Open Prepayment Period']] 
      loan_portfolio.add_initial_loan(loan_data[0], loan_data[1], loan_data[2], loan_data[3], loan_data[4], loan_data[5], loan_data[6])

    # ------------------------ START BASE SCENARIO ------------------------ #
    # sets term lengthsi think
    loan_portfolio.initial_loan_terms(case)
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
    # storage variables
    deal_call_mos = [] # stores month when each deal is called
    AAA_bal_list = []

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
           # reinvestment calculations 
           if months_passed <= reinvestment_period and months_passed == loan.get_term_length():
              loan_portfolio.add_new_loan(beginning_bal, margin, months_passed, ramp = False)
           else: #waterfall
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

        append = False # this fixes non-AAA tranches principal payment
        clo_principal_sum = 0 
        for tranche in clo.get_tranches():
          # if we're on the last loan in the month
          if loan.get_loan_id() == loan_portfolio.get_active_portfolio()[-1].get_loan_id():
             append = True # then append the nonzero principal paydown ONLY ONCE to the list of principal paydowns in non-AAA tranches
          tranche.tranche_principal(months_passed, reinvestment_period, tranche_df, principal_pay, terminate_next, append, AAA_bal_list)
          # if we're on the last iteration for the month
          if portfolio_index == len(loan_portfolio.get_active_portfolio()):
             if tranche.get_offered() == 1:
              #print("month " + str(months_passed) + " tranche " + tranche.get_name())
              #print(tranche.get_principal_dict()[months_passed])
              tranche_principal_sum = sum(tranche.get_principal_dict()[months_passed])
              tranche_df.loc[(tranche.get_name(), months_passed), 'Principal Payment'] = tranche_principal_sum
              clo_principal_sum += tranche_principal_sum

      # add current balances to list
      for tranche in clo.get_tranches():
        tranche.save_balance(tranche_df, months_passed)

      # inner loop ends 
      clo.append_cashflow(months_passed, upfront_costs, days, clo_principal_sum, SOFR, tranche_df) 

      # terminate in outer loop
      if terminate_next:
         deal_call_mos.append(months_passed)
         break 
      
      if clo.get_tranches()[0].get_size() <= threshold:
          terminate_next = True 

      months_passed += 1

    # testing loan data
    #print(loan_df.tail(longest_duration))
    # loan_df.to_excel('output.xlsx', index=True)

    # testing tranche data
    #print(tranche_df.loc['A-S'])
    #print(tranche_df.head(longest_duration))
    #tranche_df.to_excel('tranches.xlsx', index=True)

    # ------------------ CALCULATING OUTPUTS ------------------ #
    # DEAL CALL MONTH
    if case == "base":
       clo.append_base_last_month(deal_call_mos)
    elif case == "downside":
       clo.append_downside_last_month(deal_call_mos)
    else:
       clo.append_upside_last_month(deal_call_mos)
       
    wa_cof = (npf.irr(clo.get_total_cashflows())*12*360/365 - SOFR) * 100 # in bps
    
    # WEIGHTED AVG ADVANCE RATE
    avg_AAA_bal = sum(clo.get_tranches()[0].get_bal_list()) / deal_call_mos[0]
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


   # ------------------------ RUN SIMULATION ------------------------ #

    run_simulation(base)

   # ------------------------ RUN SIMULATION LOOPS ------------------------ #
    scenarios = [base, downside, upside]
    num_of_runs = 10

    for scenario in scenarios:
      # chnage 10 to number of simulation runs per scenario 
      for _ in range(num_of_runs):
          run_simulation(scenario)

   # ------------------------ GET OUTPUTS ------------------------ #
    print(clo.get_base_last_months()) # [34, 36, 36, 37, 32 ... ] x = sim 
    print(clo.get_downside_last_months())
    print(clo.get_upside_last_months())

   # ---------------------- GRAPHING DEAL CALL MONTHS ---------------------- #
    workbook = xlsxwriter.Workbook('chart_scatter.xlsx')

    worksheet = workbook.add_worksheet()

    bold = workbook.add_format({'bold': 1})

    headings = ['Number of Sims', 'Deal Call Months']

    """
    for scenario in scenarios:
       # chnage 10 to number of simulation runs per scenario 
       # i think 10 needs to be made into a variable so that whatever number is in that variable 
       # can be inputed into the data list below
       for _ in range(10):
           run_simulation(scenario)"""

    data = [
       list(range(1, num_of_runs + 1)), # this is my x-axis
       [clo.get_base_last_months()], # this is one batch of data aka the y-axis
       # i need this one to be deal call months
    ]

    worksheet.write_row('A1', headings, bold)
   
    # Write a column of data starting from 
    # 'A2', 'B2', 'C2' respectively .
    worksheet.write_column('A2', data[0])
    worksheet.write_column('B2', data[1])

    # here we create a scatter chart object .
    chart1 = workbook.add_chart({'type': 'scatter'})

    chart1.add_series({
       'name':       ['Deal Call Months', 0, 1],
       'categories': ['Deal Call Months', 1, 0, 6, 0], # x axis values placement ['Sheet name', first_row, first_column, last_row, last_column]
       'values':     ['Deal Call Months', 1, 1, 6, 1], # y axis values placement ['Sheet name', first_row, first_column, last_row, last_column]
    })

    # Add a chart title 
    chart1.set_title ({'name': 'Results of CLO Simulation'})
   
    # Add x-axis label
    chart1.set_x_axis({'name': 'Sim Number'})
   
    # Add y-axis label
    chart1.set_y_axis({'name': 'Deal Call Month'})
   
    # Set an Excel chart style.
    # 1 - grey
    # 2 - blue, red
    # 3 - blues
    # 4 - reds   
    # 5  - greens
    # 6 - purples
    # 7 - like a light blueish green
    # 8 - oranges
    # 9 - ew
    # 10 - blue, orangey red
    chart1.set_style(6)

    # add chart to the worksheet 
    # the top-left corner of a chart 
    # is anchored to cell E2 . 
    worksheet.insert_chart('E2', chart1)

    # TODO: i need a summary kind of thing to go near
    # so user can specify month they are looking for the deal to be called
    # and then it prints how many times it was called as well as shows it in the graph
   
    # Finally, close the Excel file 
    # via the close() method. 
    workbook.close()