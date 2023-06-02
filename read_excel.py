#-----------------------------------------TRANCHES/CAPITAL STACK SHEET-----------------------------------------#
import pandas as pd

class Tranche:
    def __init__(self, name, rating, size, spread, offered, price):
        self.__name = name
        self.__rating = rating
        self.__size = size
        self.__spread = spread
        self.__offered = offered
        self.__price = price

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

    def update_size(self, value):
        d=""
      # formulas

df = pd.read_excel("CLO_Input.xlsm", sheet_name = "Capital Stack")

tranches = []

for index, row in df.iterrows():
    tranche_data = row[['Name','Rating', 'Offered', 'Size', 'Spread (bps)', 'Price']]
    tranche_instance = Tranche(
        tranche_data['Name'],
        tranche_data['Rating'],
        tranche_data['Size'],
        tranche_data['Spread (bps)'],
        tranche_data['Offered'],
        tranche_data['Price']
    )
    tranches.append(tranche_instance)

target_name = input("What tranche are you looking for? Type a name to find data: ")

for tranche in tranches:
    if tranche.get_name() == target_name:
        tranche_data = {
            'Name': tranche.get_name(),
            'Rating': tranche.get_rating(),
            'Size': tranche.get_size(),
            'Spread': tranche.get_spread(),
            'Offered': tranche.get_offered(),
            'Price': tranche.get_price()
        }
        print(tranche_data)
        break

    
    
    #This is for something else though
    #You can access other attributes as needed
        #print(tranche.get_rating())
        #print(tranche.get_size())
        #print(tranche.get_spread())
        #print(tranche.get_offered())
        #print(tranche.get_price())

#---------------------------------------LOANS/COLLATERAL PORTFOLIO SHEET----------------------------------------#
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
    
    def get_prev_id(self):
        print("")
        #return self.__prev_id

    def get_loan_balance(self):
        return self.__loan_balance

    # need all the equations for investors to pay off their loans each month 
    def update_loan_balance(self, month, etc):
        print("")
        # add equation for loan getting smaller and smaller each month
  
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

    def set_term_length(self, term):
        print("")
        #self.__term_length = term

    def get_term_length(self):
        print("")
        #return self.__term_length
    
df = pd.read_excel("CLO_Input.xlsm", sheet_name = "Collateral Portfolio")

loans = []

for index, row in df.iterrows():
    loan_data = row[['Loan ID','Collateral Interest UPB', 'Margin', 'Index Floor', 'Loan Term (rem)', 'First Extension Period (mo)', 'Open Prepayment Period']]
    loan_instance = Loan(
        loan_data['Loan ID'],
        loan_data['Collateral Interest UPB'],
        loan_data['Margin'],
        loan_data['Index Floor'],
        loan_data['Loan Term (rem)'],
        loan_data['First Extension Period (mo)'],
        loan_data['Open Prepayment Period']
    )
    loans.append(loan_instance)

str_id = input("Which loan are you looking for? Type a number to locate the correct loan: ")

target_id = int(str_id)

for loan in loans:
    if loan.get_loan_id() == target_id:
        loan_data = {
            'Loan ID': loan.get_loan_id(),
            'Collateral Interest UPB': loan.get_loan_balance(),
            'Margin': loan.get_margin(),
            'Index Floor': loan.get_index_floor(),
            'Loan Term (rem)': loan.get_remaining_loan_term(),
            'First Extension Period (mo)': loan.get_extension_period(),
            'Open Prepayment Period': loan.get_open_prepayment_period()
        }
        print(loan_data)
        break

#-------------------------------------------------UPFRONT COSTS-------------------------------------------------#

#in clo class under def get_upfront_cost()

#---------------------------------------------OTHER SPECIFICATIONS----------------------------------------------#

#in clo class under their own functions:
            #get_revest_period()
            #get_deal_start_date()
    

