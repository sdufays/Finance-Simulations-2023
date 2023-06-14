# CLO Simulator Documentation
---
## THE CAPITAL STACK

### 01. *Tranche Class*
**Accessing Tranche Attributes:**
* `tranche.get_name()` returns the name of the tranche
* `tranche.get_rating()` returns the rating of the tranche
* `tranche.get_size()` returns the current balance of the tranche
* `tranche.get_spread()` returns the spread of the tranche (in bps)
* `tranche.get_offered()` returns whether the tranche was sold (0 or 1)
* `tranche.get_price()` returns price of tranche, ex: 99.75
* `tranche.get_bal_list()` returns list of tranche's balance over time (also stored in tranche_df)
* `tranche.get_principal_dict()` returns dictionary with {month: [principal payment values, ...]} for this particular tranche
* `print(tranche)` the __str__ method allows you to print all information about a tranche by just printing the object

**Tranche Methods:**
* `tranche.subtract_size(value)` subtracts `value` from tranche size
* `tranche.save_balance(dataframe, month)` appends the current size of the tranche to the `bal_list` as well as the dataframe
*  `tranche.init_principal_dict(self, total_months)` initializes the `principal_dict` dictionary {0: [], 1:[], ... final_month: []} with empty lists as values
* `tranche.append_to_principal_dict(month, value)` appends value to principal value list in the month-th key of this tranche's principal dictionary
* `tranche.tranche_interest(num_days, sofr_value, dataframe, month)` calculates tranche interest value for a particular month, and appends it to dataframe

### 02. *CLO Class*
**Accessing CLO Attributes:**
* `clo.get_tranches()` returns a list of Tranche objects within the capital stack
* `clo.get_ramp_up()` returns whether there is a ramp up feature (True/False)
* `clo.get_reinv_bool()` returns whether there is a reinvestment feature (True/False)
* `clo.get_reinv_period()` returns the length of the reinvestment period (default is 24)
* `clo.get_replen_bool()` returns whether there is a replenishment feature (True/False)
* `clo.get_replen_amount()` returns the allotted replenishment amount (default is $475mil)
* `clo.get_starting_date()` returns the starting date of the CLO
* `clo.get_total_cashflows()` returns a list of cashflows (sum of every tranche's individual cashflow) for every month

**CLO Methods**
* `clo.add_tranche(name, rating, size, spread, offered, price)` creates a Tranche object with the given specifications and appends it to the capital stack
* `clo.get_tda()` calculates and returns total deal amount of the CLO by adding up the sizes of each tranche
* `clo.get_tob()` calculates and returns total amount of offered bonds (aka investment grade bonds balance) by adding the sizes of only the tranches that were sold. *this value will change once the loans start getting paid off.*
* `clo.get_dda()` calculates and returns the deal discount amount (the amount discounted from the original price of the CLO)
* `clo.get_CE(tranche)` calculates and returns the size of the tranche divided by the total offered bonds of the CLO *unused*
* `clo.get_RA_fees()` *HELPER FUNCTION:* calculates and returns the rating agency fees.
* `clo.get_upfront_costs(placement_percent, legal, accounting, trustee, printing, RA_site, modeling, misc)` calculates and returns sum of all upfront costs
* `clo.get_upfront_percent()` calculates and returns the upfront costs as a percentage of the total offered bonds
* `clo.get_threshold()` calculates and returns 0.2 * the size of the AAA tranche
* `clo.append_cashflow(month, upfront_cost, num_days, sofr_value, dataframe, termin_next)` calculates and appends sum of all tranche cashflows for one month
---
## THE COLLATERAL PORTFOLIO
### 01. *Loan Class*
**Accessing Loan Attributes:**
* `loan.get_loan_id()` returns ID of loan (1, 2, 3, ... etc)
* `loan.get_loan_balance()` returns current balance of loan
* `loan.get_margin()` returns margin value of loan (in %)
* `loan.get_index_floor()` returns index floor value of loan
* `loan.get_remaining_loan_term()` returns remaining loan term of loan
* `loan.get_extension_period()` returns extension period of loan
* `loan.get_open_prepayment_period()` returns open prepayment period of loan
* `loan.get_term_length()` returns calculated and randomized term length of loan (in months)
* `print(loan)` the __str__ method allows you to print all information about a loan by just printing the object
* `loan.get_starting_month()` returns starting month of the loan
**Setting Loan Attributes:**
* `loan.set_term_length(term_length)` sets term length attribute to `term_length`
* `loan.set_starting_month(month)` sets the month the loan was created at (used to keep track of term lengths for newly created loans)
**Loan Methods:**
* `loan.update_loan_balance(self, month, etc etc etc)` *UNFINISHED* updates loan balance as it gets smaller and smaller each month
* `loan.print_loan_info()`
### 02. *CollateralPortfolio Class*
**Accessing CollateralPortfolio Attributes:**
* `portfolio.get_portfolio()` returns list of Loan objects
**CollateralPortfolio Methods:**
* `portfolio.add_loan(loan_id, loan_balance, margin, index_floor, remaining_loan_term, extension_period, open_prepayment_period)` adds a Loan object to the portfolio list
* `portfolio.remove_loan()` removes loans with balances of 0 from the portfolio
* `portfolio.get_collateral_sum()` calculates and returns the sum of the balances of all loans in the portfolio
* `portfolio.general_loan_terms(case)` calculates term lengths according to the desired case and uses loan.set_term_length() to assign these term lengths to loans in the portfolio