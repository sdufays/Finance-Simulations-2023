from collateral_class import CollateralPortfolio
import pandas as pd

if __name__ == "__main__":
    base = [.33, .33, .34]
    downside = [.30, .25, .45]
    upside = [.40, .35, .25]

    SOFR = 0.0408

    po = CollateralPortfolio()
    
    # read excel file for loans
    df_cp = pd.read_excel("CLO_Input.xlsm", sheet_name = "Collateral Portfolio")

    # add loans in a loop
    for index, row in df_cp.iterrows():
      loan_data = row[['Loan ID','Collateral Interest UPB', 'Margin', 'Index Floor', 'Loan Term (rem)', 'First Extension Period (mo)', 'Open Prepayment Period']] 
      po.add_initial_loan(loan_data[0], loan_data[1], loan_data[2], loan_data[3],loan_data[4],loan_data[5],loan_data[6])

    print("TESTING GETTERS")
    for loan in po.get_portfolio():
        print(loan.get_loan_balance())

    # print(po.get_collateral_sum())

    # GENERATE LOAN TERMS WORKS!
    print("TESTING GENERATE LOAN TERMS")
    #po.generate_loan_terms(base)
    #for loan in po.get_portfolio():
        #print(loan.get_term_length())

    # print(po.get_portfolio())

    print("\nUPSIDE")
    po.generate_loan_terms(upside)
    print("\nDOWNSIDE")
    po.generate_loan_terms(downside)
    print('\nBASE')
    po.generate_loan_terms(base)
    
    print("TESTING GET LONGEST TERM")
    print("LONGEST TERM:")
    print(po.get_longest_term())
    print("ALL TERMS:")
    for loan in po.get_portfolio():
       print(loan.get_term_length())

    print("TESTING ADD NEW LOAN")
    po.add_new_loan(90000)
    print(po.get_portfolio()[-1].get_loan_balance())

    print("TESTING BEGINNING BALANCE")
    loan = po.get_portfolio()[0]
    begin = loan.beginning_balance(0, [1,2,3])
    print("beginning balance " + str(begin))

    print("TESTING INTEREST INCOME")
    print("interest income " + str(loan.interest_income(begin, SOFR, 30)))