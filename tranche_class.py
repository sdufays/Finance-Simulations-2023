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
        self.__principal_dict = {}

    def get_principal_dict(self):
        return self.__principal_dict

    def append_to_principal_dict(self, month, value):
        self.__principal_dict[month].append(value)

    # initializes dictionary to {0:[0,0,0,50000, 40000, 0,], 1:[],...}
    def init_principal_dict(self, total_months):
        for i in range(0, total_months):
            self.__principal_dict[i] = []
    
    def init_principal_dict_MANUAL(self, start_month, total_months):
        for i in range(start_month, total_months):
            self.__principal_dict[i] = []

    def save_balance(self, dataframe, month):
        self.__bal_list.append(self.get_size())
        dataframe.loc[(self.get_name(), month), 'Tranche Size'] = self.get_size()
    
    def get_bal_list(self):
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
            if month > 0:
                interest = dataframe.loc[(self.get_name(), month-1), 'Tranche Size'] * (self.get_spread() + sofr_value) * num_days / 360
            else:
                interest = self.get_size() * (self.get_spread() + sofr_value) * num_days / 360
            dataframe.loc[(self.get_name(), month), 'Interest Payment'] = interest
            return interest
        else:
            return 0
    
    # NEED TO MAKE THIS GET FROM OLD DATAFRAME IN MONTH 47
    def tranche_interest_MANUAL(self, num_days, sofr_value, dataframe, month, orig_mo, old_dataframe):
        if self.get_name() != 'R':
            if month == orig_mo + 1:
                interest = self.get_size() * (self.get_spread() + sofr_value) * num_days / 360
            else:
                interest = dataframe.loc[(self.get_name(), month-1), 'Tranche Size'] * (self.get_spread() + sofr_value) * num_days / 360
            dataframe.loc[(self.get_name(), month), 'Interest Payment'] = interest
            return interest
        else:
            return 0
        
    # save cash flow list functions
    def init_tranche_cashflow_list(self, cashflow_list, tranche_R_balance):
        self.__cashflow_list = cashflow_list
        # first element of cashflow list is -1 * balance of tranche R
        self.__cashflow_list[0] = tranche_R_balance * -1

    def add_tranche_cashflow_value(self, cashflow_value):
        self.__cashflow_list.append(cashflow_value)
    
    def get_tranche_cashflow_list(self):
        return self.__cashflow_list
        
    def __str__(self):
        return "Name: {}\nRating: {}\nSize: {:,.2f}\nSpread: {}\nOffered: {}\nPrice: {:.2f}\nBalance List: {}\nPrincipal Dictionary: {}".format(self.get_name(), self.get_rating(), self.get_size(), self.get_spread(), self.get_offered(),self.get_price(), self.get_bal_list(), self.get_principal_dict())