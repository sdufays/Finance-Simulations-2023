# ------------------------ VARIOUS TRANCHE OPERATIONS ------------------------ #
class Tranche:
    def __init__(self, name, rating, offered, size, spread, price):
        self.__name = name
        self.__rating = rating
        self.__size = size
        self.__spread = spread
        self.__offered = offered
        self.__price = price
        self.__bal_list = []
    
    def save_balance(self, dataframe, month):
        self.__bal_list.append(self.get_size())
        dataframe.loc[('A', month), 'Tranche Size'] = self.get_size()
    
    def get__bal_list(self):
        return self.__bal_list

    def get_name(self):
        return self.__name
    
    def get_rating(self):
        return self.__rating
      
    def get_size(self):
        return self.__size

    def get_spread(self):
        return self.__spread

    def get_offered(self):
        return self.__offered

    def get_price(self):
        return self.__price

    def subtract_size(self, value):
        self.__size -= value

    def tranche_interest(self, num_days, sofr_value, dataframe, month):
        if self.get_offered() == 1:
            interest = self.get_size() * (self.get_spread() + sofr_value) * num_days / 360
            dataframe.loc[(self.get_name(), month), 'Interest Payment'] = interest
            return interest
        else:
            return 0
    
    def tranche_principal(self, month, reinvest_per, dataframe, loan_paydown, termin_next):
        if self.get_name() == 'A':
            if month > reinvest_per:
                principal = loan_paydown
            else:
                principal = self.get_size()
        else:
            if termin_next:
                principal = self.get__bal_list()[month-1]
            else:
                principal = 0
        dataframe.loc[(self.get_name(), month), 'Principal Payment'] = principal
        return principal