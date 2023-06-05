import pandas as pd

# Sample data
loan_ids = list(range(1, 22))  # 21 loan IDs
months_passed = list(range(1, 61))  # Assuming 60 months passed

# Create a multi-index
index = pd.MultiIndex.from_product([loan_ids, months_passed],
                                   names=['Loan ID', 'Months Passed'])

# Create an empty DataFrame with the multi-index
loan_data = pd.DataFrame(index=index, columns=['Current Month', 'Ending Balance', 'Principal Paydown', 'Interest Income'])

# Display the DataFrame
print(loan_data)

loan_id = 1
month = 3

loan_data.loc[(loan_id, month), 'Ending Balance'] = 90000

print(loan_data.loc[(loan_id, month), 'Ending Balance']) # gets beginning balance at month 6 of loan 1