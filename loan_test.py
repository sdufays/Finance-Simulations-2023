from collateral_class import CollateralPortfolio
import pandas as pd

if __name__ == "__main__":
    base = [.33, .33, .34]

    po = CollateralPortfolio()
    
    # read excel file for loans
    df_cp = pd.read_excel("CLO_Input.xlsm", sheet_name = "Collateral Portfolio")

    # add loans in a loop
    for index, row in df_cp.iterrows():
      loan_data = row[['Loan ID','Collateral Interest UPB', 'Margin', 'Index Floor', 'Loan Term (rem)', 'First Extension Period (mo)', 'Open Prepayment Period']] 
      po.add_initial_loan(loan_data[0], loan_data[1], loan_data[2], loan_data[3],loan_data[4],loan_data[5],loan_data[6])

    # print(po.get_portfolio())

    for loan in po.get_portfolio():
        print(loan.get_loan_balance())

    # print(po.get_collateral_sum())

    # GENERATE LOAN TERMS WORKS!
    #po.generate_loan_terms(base)
    #for loan in po.get_portfolio():
        #print(loan.get_term_length())
    
