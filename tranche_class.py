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

    # initializes dictionary to {1:[], 2:[],...}
    def init_principal_dict(self, total_months):
        for i in range(0, total_months):
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
            interest = self.get_size() * (self.get_spread() + sofr_value) * num_days / 360
            if self.get_name() == 'A' and month == 0:
                print("NUM DAYS" + str(num_days))
            dataframe.loc[(self.get_name(), month), 'Interest Payment'] = interest
            return interest
        else:
            return 0
    
    def tranche_principal(self, month, reinvest_per, dataframe, loan_paydown, termin_next, append, AAA_bal_list):
        # if in first tranche
        if self.get_name() == 'A':
            # if a loan pays down while not in reinvestment
            if month > reinvest_per and loan_paydown != 0:
                principal = min(loan_paydown,self.get_bal_list()[month-1]) # loan princi pay
            elif termin_next:
                principal = self.get_bal_list()[month-1]
            else:
                principal = 0 #self.get_size()
        else:
            if termin_next and append:
                if AAA_bal_list[month-1] == 0:
                    if self.get_name() == 'A-S':
                        principal = min(self.get_bal_list()[month-1], loan_paydown - AAA_bal_list[month-1])
                else:
                    principal = self.get_bal_list()[month-1]
            else:
                principal = 0
        self.__principal_dict[month].append(principal)
        if month == 36: 
                    print("princpal {:,.2f}".format(principal))
                    print(self.get_principal_dict()[36])
        #if self.get_name() == 'A':
            #print(self.__principal_dict[month])
        return principal

            


            