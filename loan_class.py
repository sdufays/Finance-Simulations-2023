import random

# ------------------------ LOAN CLASS SETUP ------------------------ #
class Loan:
    def __init__(self, loan_id, collateral_balance, margin, index_floor, remaining_loan_term, extension_period, open_prepayment_period):
        self.__loan_id = loan_id
        self.__collateral_balance = collateral_balance
        self.__margin = margin
        self.__index_floor = index_floor
        self.__remaining_loan_term = remaining_loan_term
        self.__extension_period = extension_period
        self.__open_prepayment_period = open_prepayment_period

    def get_loan_id(self):
        return self.__loan_id
    
    def get_prev_id(self):
        return self.__prev_id

    def get_collateral_balance(self):
        return self.__collateral_balance

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

    def get_term(self):
        # make this align with ratios
        term_type = random.choice(['initial', 'extended', 'prepaid'])
        if term_type == "initial":
            return(self.get_remaining_loan_term())
        elif term_type == "extended":
            return(self.get_remaining_loan_term() + self.get_extension_period())
        else:
            return(self.get_open_prepayment_period())
        