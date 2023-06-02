import random

# ------------------------ LOAN CLASS SETUP ------------------------ #
class Loan:
    def __init__(self, loan_id, collateral_balance, margin, index_floor, remaining_loan_term, extension_period, open_prepayment_period):
        self.__loan_id = loan_id
        self.__loan_balance = collateral_balance
        self.__margin = margin
        self.__index_floor = index_floor
        self.__remaining_loan_term = remaining_loan_term
        self.__extension_period = extension_period
        self.__open_prepayment_period = open_prepayment_period
        self.__term_length = 0
  
    def get_loan_id(self):
        return self.__loan_id

    def get_loan_balance(self):
        return self.__loan_balance

    def get_margin(self):
        return self.__margin

    def get_index_floor(self):
        return self.__index_floor

    # TODO: UPDATE REMAINING LOAN TERM AS MONTHS PASSED
    def get_remaining_loan_term(self):
        return self.__remaining_loan_term

    def get_extension_period(self):
        return self.__extension_period

    def get_open_prepayment_period(self):
        return self.__open_prepayment_period

    def set_term_length(self, term_length):
        self.__term_length = term_length

    def get_term_length(self):
        return self.__term_length

    # ----------------------- FOUR MAJOR CALCULATIONS --------------------------- #
    # MONTH - 1 DOESN'T WORK
  
    # for reinvestment, calculate beginning balance of NEW loan using original loan
    # month here is the months passed
    def beginning_balance(self, month, funding_amount):
        if month == 1:
            return self.get_loan_balance()
        else:
            return self.ending_balance(month-1, funding_amount)

    # not doing partial paydown, only full
    # month is months passed
    def principal_paydown(self, month, funding_amount):
        if month == self.get_term_length():
            # ending/beginning balance is basically same
            return self.beginning_balance(month-1, funding_amount)
        else:
            return 0

    # no funding amount if no reinvestment (funding_amt = 0)
    # at the end, beginning - paydown = 0 cuz no partial paydown
    def ending_balance(self, month, funding_amount, beginning_balance):
        # funding amount - if you sell loan in reinvestment period, that money is the funding amount
        return beginning_balance + funding_amount - self.principal_paydown(month, funding_amount)

    # gets interest income as fraction over the total year
    # changes due to # days in month
    # index value is SOFR
    def interest_income(self, month, funding_amount, INDEX_VALUE, num_days):
        return beginning_balance(month, funding_amount) * (self.get_spread() + max(self.get_index_floor(), INDEX_VALUE) * num_days / 360)

    # -------------------------- WITH REINVESTMENT -------------------------
    # this is the loan balance of the new loan we create using .add_new_loan(loan_balance)
    # make sure to tell it to recalculate the stuff
    def funding_amount_rein(month, loan, rein_period):
      if month == loan.get_term_length() and month < rein_period:
        return ending_balance(month - 1, loan)
      else:
        return 0

    def principal_paydown_rein(month, loan):
      if month == loan.get_term_length():
        return(beginning_balance_rein(month - 1, loan))
      else:
        return 0