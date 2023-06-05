# CLO Simulator Documentation
---
## THE CAPITAL STACK
### 01. *Tranche Class*
**Accessing Tranche Attributes:**
* `tranche.get_name()` returns the name of the tranche
* `tranche.get_rating()` returns the rating of the tranche
* `tranche.get_size()` returns the size (amount of money) of the tranche
* `tranche.get_spread()` returns the spread of the tranche
* `tranche.get_offered()` returns whether the tranche was sold (0 or 1)
* `tranche.get_price()` returns price of tranche, ex: 99.75
**Tranche Methods:**
* `tranche.update_size(value)` - updates tranche size by `value`
### 02. *CLO Class*
**Accessing CLO Attributes:**
* `clo.get_ramp_up()` returns whether there is a ramp up feature (True/False)
* `clo.get_tranches()` returns a list of Tranche objects within the capital stack
**CLO Methods**
* `clo.add_tranche(name, rating, size, spread, offered, price)` creates a Tranche object with the given specifications and appends it to the capital stack
* `clo.get_tda()` calculates and returns total deal amount of the CLO by adding up the sizes of each tranche
* `clo.get_tob()` calculates and returns total amount of offered bonds (aka investment grade bonds balance) by adding the sizes of only the tranches that were sold. *this value will change once the loans start getting paid off.*
* `clo.get_dda()` calculates and returns the deal discount amount (the amount discounted from the original price of the CLO)
* `clo.get_CE(tranche)` calculates and returns the size of the tranche divided by the total offered bonds of the CLO
* `clo.get_RA_fees()` *HELPER FUNCTION:* calculates and returns the rating agency fees.
* `clo.get_upfront_costs(placement_percent, legal, accounting, trustee, printing, RA_site, modeling, misc)` calculates and returns sum of all upfront costs
* `clo.get_upfront_percent()` calculates and returns the upfront costs as a percentage of the total offered bonds
* `clo.get_threshold()` calculates and returns 0.2 * the size of the AAA tranche
---
## THE COLLATERAL PORTFOLIO
### 01. *Loan Class*
**Accessing Loan Attributes:**
* `loan.get_loan_id()`
* `loan.get_loan_balance()`
* `loan.get_margin()`
* `loan.get_index_floor()`
* `loan.get_remaining_loan_term()`
* `loan.get_extension_period()`
* `loan.get_open_prepayment_period()`
* `loan.get_term_length()`
**Setting Loan Attributes:**
* `loan.set_term_length(term_length)` sets term length attribute to `term_length`
**Loan Methods:**
* `loan.update_loan_balance(self, month, etc etc etc)` *UNFINISHED* updates loan balance as it gets smaller and smaller each month
### 02. *CollateralPortfolio Class*
**Accessing CollateralPortfolio Attributes:**
* `portfolio.get_portfolio()` returns list of Loan objects
**CollateralPortfolio Methods:**
* `portfolio.add_loan(loan_id, loan_balance, margin, index_floor, remaining_loan_term, extension_period, open_prepayment_period)` adds a Loan object to the portfolio list
* `portfolio.remove_loan()` removes loans with balances of 0 from the portfolio
* `portfolio.get_collateral_sum()` calculates and returns the sum of the balances of all loans in the portfolio
* `portfolio.general_loan_terms(case)` calculates term lengths according to the desired case and uses loan.set_term_length() to assign these term lengths to loans in the portfolio