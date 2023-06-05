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
    # month = months passed
    def beginning_balance(self, month, loan_data):
        if month == 0:
            return self.get_loan_balance()
        else:
            return loan_data.loc[(self.get_loan_id(), month-1), 'Ending Balance']

    # not doing partial paydown, only full
    # month = months passed
    def principal_paydown(self, month, loan_data):
        if month == self.get_term_length():
            # ending/beginning balance is same
            return loan_data.loc[(self.get_loan_id(), month-1), 'Ending Balance']
        else:
            return 0

    # at the end, beginning - paydown = 0 cuz no partial paydown
    def ending_balance(self, beginning_balance, principal_paydown):
        # update balance
        self.__loan_balance = beginning_balance -  principal_paydown
        # update remaining loan term
        self.__remaining_loan_term = self.__remaining_loan_term - 1
        # return ending loan balance
        return self.__loan_balance
    
    # gets interest income as fraction over the total year
    # changes due to # days in month
    # index value is SOFR
    def interest_income(self, beginning_balance, INDEX_VALUE, num_days):
        print("index floor" + str(self.get_index_floor()))
        print("margin" + str(self.get_margin()))
        return beginning_balance * (self.get_margin() + max(self.get_index_floor(), INDEX_VALUE)) * num_days / 360
