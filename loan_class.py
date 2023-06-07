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
        self.__starting_month = 0
    
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
    
    def set_starting_month(self, month):
        self.__starting_month = month
    
    def get_starting_month(self):
        return self.__starting_month

    def print_loan_info(self):
        print("Loan ID: ", self.get_loan_id())
        print("Loan Balance: ", self.get_loan_balance())
        print("Margin: ", self.get_margin())
        print("Index Floor: ", self.get_index_floor())
        print("Remaining Loan Term: ", self.get_remaining_loan_term())
        print("Extension Period: ", self.get_extension_period())
        print("Open Prepayment Period: ", self.get_open_prepayment_period())
        print("Term Length: ", self.get_term_length())


    # ----------------------- FOUR MAJOR CALCULATIONS --------------------------- #
    # month = months passed
    def beginning_balance(self, month, loan_data):
        if month == self.get_starting_month():
            return self.get_loan_balance()
        else:
            return loan_data.loc[(self.get_loan_id(), month-1), 'Ending Balance']

    # month = months passed
    def principal_paydown(self, month, loan_data):
        if month == self.get_term_length() + self.get_starting_month():
            # ending/beginning balance is same
            return loan_data.loc[(self.get_loan_id(), month - 1), 'Ending Balance']
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
        return beginning_balance * (self.get_margin() + max(self.get_index_floor(), INDEX_VALUE)) * num_days / 360