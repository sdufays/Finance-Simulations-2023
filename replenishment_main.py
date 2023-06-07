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
    base = [.33, .33, .34]
    downside = [.30, .25, .45]
    upside = [.40, .35, .25]

    df_os = pd.read_excel("CLO_Input.xlsm", sheet_name = "Other Specifications", header=None)

    first_payment_date = df_os.iloc[2, 1]
    date_str = first_payment_date.strftime("%m-%d-%Y")
    date = date_str.split("-") # ["MM", "DD", "YYYY"]
    date = list(map(int, date)) # [MM, DD, YYYY]
    starting_month = date[0]
    days_in_month = get_date_array(date)

    reinvestment_period = df_os.iloc[1,1]
    SOFR = df_os.iloc[3,1]

    replenishment_amount = df_os.iloc[6,1]
    replenishment_period = df_os.iloc[4,1]
    has_replenishment = df_os.iloc[5,1]
    replenishment_cumulative = 0
    reinvestment_percentage = 0.1

    has_reinvestment = df_os.iloc[7,1]

    remaining_reinvestment_period = reinvestment_period

    remaining_replenishment_period = replenishment_period


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

    df_cs = pd.read_excel("CLO_Input.xlsm", sheet_name = "Capital Stack")

    for index_t, row_t in df_cs.iterrows():
      tranche_data = row_t[['Name', 'Rating', 'Offered', 'Size', 'Spread (bps)', 'Price']]
      clo.add_tranche(tranche_data[0], tranche_data[1], tranche_data[2], tranche_data[3], tranche_data[4] / 10000, tranche_data[5])
    threshold = clo.get_threshold()
  
    loan_portfolio = CollateralPortfolio()

    df_cp = pd.read_excel("CLO_Input.xlsm", sheet_name = "Collateral Portfolio")

    for index_l, row_l in df_cp.iterrows():
      loan_data = row_l[['Loan ID','Collateral Interest UPB', 'Margin', 'Index Floor', 'Loan Term (rem)', 'First Extension Period (mo)', 'Open Prepayment Period']] 
      loan_portfolio.add_initial_loan(loan_data[0], loan_data[1], loan_data[2], loan_data[3], loan_data[4], loan_data[5], loan_data[6])

    loan_portfolio.generate_loan_terms(base)
    longest_duration = 60
    loan_ids = list(range(1, 1 + len(loan_portfolio.get_active_portfolio())))  # 21 loan IDs
    months = list(range(0, longest_duration))
    loan_index = pd.MultiIndex.from_product([loan_ids, months],
                                   names=['Loan ID', 'Months Passed'])
    loan_data = pd.DataFrame(index=loan_index, columns=['Current Month', 'Beginning Balance', 'Ending Balance', 'Principal Paydown', 'Interest Income'])

 # --------------------------------- MAIN FUNCTION & LOOP -------------------------------------- #
    total_tranche_cfs = []
    deal_call_mos = []
    months_passed = 0
    terminate_next = False
    loan_data = loan_data.fillna(0)
    initial_AAA_bal = clo.get_tranches()[0].get_size()
    initial_clo_tob = clo.get_tob()
    loan_portfolio.set_initial_deal_size(loan_portfolio.get_collateral_sum())
    margin = loan_portfolio.generate_initial_margin()
    loan_data = loan_data.fillna(0)

    while months_passed in range(longest_duration) and (remaining_reinvestment_period > 0 or months_passed <= replenishment_period): # longest duration 
      portfolio_index = 0 
      current_month = (starting_month + months_passed) % 12 or 12
      if months_passed == 1:
         extra_balance = clo.get_tda() - loan_portfolio.get_collateral_sum()
         if extra_balance > 0:
            loan_portfolio.add_new_loan(extra_balance, margin, months_passed) 
      print("\nmonth " + str(months_passed))

      while portfolio_index < len(loan_portfolio.get_active_portfolio()):
        loan = loan_portfolio.get_active_portfolio()[portfolio_index]
        loan_id = loan.get_loan_id()
        if loan_id not in loan_ids:
            loan_ids.append(loan_id)
        loan_index = pd.MultiIndex.from_product([loan_ids, months], names=['Loan ID', 'Months Passed'])
        loan_data = loan_data.reindex(loan_index)
        loan_data = loan_data.fillna(0)
        beginning_bal = loan.beginning_balance(months_passed, loan_data)
        principal_pay = loan.principal_paydown(months_passed, loan_data)
        ending_bal = loan.ending_balance(beginning_bal, principal_pay)
        days = days_in_month[current_month - 2]
        interest_inc = loan.interest_income(beginning_bal, SOFR, days)

        if loan.get_loan_id() > 21:
          print("LOAN #"+str(loan.get_loan_id()))
          print([beginning_bal, principal_pay, ending_bal, interest_inc])

        loan_data.loc[(loan.get_loan_id(), months_passed), 'Beginning Balance'] = beginning_bal
        loan_data.loc[(loan.get_loan_id(), months_passed), 'Interest Income'] = interest_inc
        loan_data.loc[(loan.get_loan_id(), months_passed), 'Principal Paydown'] = principal_pay
        loan_data.loc[(loan.get_loan_id(), months_passed), 'Ending Balance'] = ending_bal
        loan_data.loc[(loan.get_loan_id(), months_passed), 'Current Month'] = current_month

        if principal_pay != 0: 
           print("loan payed off  prev loan term length: " + str(loan.get_term_length()) + ", loan id: " + str(loan.get_loan_id()))
           loan_portfolio.remove_loan(loan)
           
           if has_reinvestment and remaining_reinvestment_period > 0 and months_passed <= reinvestment_period and months_passed == loan.get_term_length():
              print('new loan added (Reinvestment), beginning bal: ' + str(beginning_bal))
              loan_portfolio.add_new_loan(beginning_bal, margin, months_passed)
              loan_data.loc[(loan.get_loan_id(), months_passed), 'Beginning Balance'] = beginning_bal
              new_loan = loan_portfolio.get_active_portfolio()[-1]

              print(loan_portfolio.get_active_portfolio()[-1].get_loan_id(), months_passed)
              loan_data.loc[(loan_portfolio.get_active_portfolio()[-1].get_loan_id(), months_passed), 'Beginning Balance'] = beginning_bal

              remaining_reinvestment_period -= 1
           elif has_replenishment and remaining_reinvestment_period == 0 and remaining_replenishment_period > 0 and months_passed <= replenishment_period and months_passed == loan.get_term_length():
              print('new loan added (Replenishment), beginning bal: ' + str(beginning_bal))
              loan_portfolio.add_new_loan(beginning_bal, margin, months_passed)
              replenishment_cumulative += replenishment_amount
              loan_data.loc[(loan.get_loan_id(), months_passed), 'Beginning Balance'] = beginning_bal
              new_loan = loan_portfolio.get_active_portfolio()[-1]

              print(loan_portfolio.get_active_portfolio()[-1].get_loan_id())
              loan_data.loc[(loan_portfolio.get_active_portfolio()[-1].get_loan_id(), months_passed), 'Beginning Balance'] = beginning_bal

              remaining_replenishment_period -= 1
           else:
              clo.get_tranches()[0].subtract_size(beginning_bal)

              print("\nLOAN: " + str(loan.get_loan_id()))
              print("Subtracted beginning balance: " + str(beginning_bal))
              print("AAA SIZE " + str(clo.get_tranches()[0].get_size()))
              print("THRESHOLD " + str(threshold))
        else:
           portfolio_index += 1
             
        clo_principal = clo.get_tranche_principal_sum(months_passed, reinvestment_period, principal_pay, threshold)
        clo_cashflow = clo.total_tranche_cashflow(months_passed, upfront_costs, days, clo_principal, SOFR) 

        total_tranche_cfs.append(clo_cashflow)
      # inner loop ends

      if months_passed > reinvestment_period and has_replenishment:
        replenishment_amount = reinvestment_percentage * loan_portfolio.get_initial_deal_size()
        loan_portfolio.add_new_loan(replenishment_amount, margin, months_passed)
        replenishment_cumulative += replenishment_amount
        remaining_replenishment_period -= 1      

      # terminate in outer loop
      if terminate_next:
         deal_call_mos.append(months_passed)
         break 
      
      if clo.get_tranches()[0].get_size() <= threshold:
          print("WORK")
          terminate_next = True 
       
      months_passed += 1

    print(loan_data.tail(longest_duration))

    # ------------------ CALCULATING OUTPUTS ------------------ #
    print(deal_call_mos)

    total_tranche_cfs = [x for x in total_tranche_cfs if not math.isnan(x)] # takes out NaN values from list
    wa_cof = (npf.irr(total_tranche_cfs)*360/365 - SOFR) * 100