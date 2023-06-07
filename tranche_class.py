# ------------------------ VARIOUS TRANCHE OPERATIONS ------------------------ #
class Tranche:
    def __init__(self, name, rating, offered, size, spread, price):
        self.__name = name
        self.__rating = rating
        self.__size = size
        self.__spread = spread
        self.__offered = offered
        self.__price = price
        self.__AAA_bal_list = []
    
    def save_AAA_balance(self):
        if self.get_name() == 'A':
            self.__AAA_bal_list.append(self.get_size())
    
    def get_AAA_bal_list(self):
        return self.__AAA_bal_list

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

    def tranche_interest(self, num_days, sofr_value):
        return self.get_size() * (self.get_spread() + sofr_value) * num_days / 360