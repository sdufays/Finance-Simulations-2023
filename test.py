deal_call_month = 40
quarterly_tax_inc = {}
for i in range(deal_call_month // 12):
    quarterly_tax_inc[i] = []

print(quarterly_tax_inc)


"""
#calculate and append this month's loan cashflow 
# maybe we should ask vlad why he asked us to calculate this? cuz idk if it's needed for the outputs
total_principal_paydown = loan_df.loc[(slice(None), months_passed), 'Principal Paydown'].sum()
total_interest_income = loan_df.loc[(slice(None), months_passed), 'Interest Income'].sum()
month_cashflow = total_interest_income + total_principal_paydown
loan_portfolio.update_loan_cashflow(month_cashflow)
"""