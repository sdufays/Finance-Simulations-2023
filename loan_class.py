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

    # need all the equations for investors to pay off their loans each month 
    def update_loan_balance(self, month, etc):
        # add equation for loan getting smaller and smaller each month
        d=""

    def get_margin(self):
        return self.__margin

    def get_index_floor(self):
        return self.__index_floor

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