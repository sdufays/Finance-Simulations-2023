import random

# REINVESTMENT
# get reinvestment period length from user
# default is 24

# ------------------------ SCENARIOS ------------------------ #
base = [.33, .33, .34]
downside = [.30, .25, .45]
upside = [.40, .35, .25]

# ------------------------ VARIOUS TRANCHE OPERATIONS ------------------------ #
class Tranche:
    def __init__(self, rating, size, spread, offered, price):
        self.__rating = rating
        self.__size = size
        self.__spread = spread
        self.__offered = offered
        self.__price = price

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

class CLO(Tranche):
    def __init__(self, ramp_up):
        self.__tranches = []
        self.__ramp_up = ramp_up
    
    def get_ramp_up(self):
        return self.__ramp_up

    def add_tranche(self, tranche):
        self.__tranches.append(tranche)

    def get_tranches(self):
        return self.__tranches

    # get total deal amount
    def get_tda(self):
        total_deal_amount = 0 
        for tranche in self.get_tranches():
            total_deal_amount += tranche.get_size()
        return total_deal_amount

    # get total amount of offered bonds (IG bonds balance)
    def get_tob(self):
      total_offered_bonds = 0
      for tranche in self.get_tranches():
          total_offered_bonds += (tranche.get_size() * tranche.get_offered)
      return total_offered_bonds

    # get deal discount amount
    def get_dda(self):
        deal_discount_amount = 0
        for tranche in self.get_tranches():
            deal_discount_amount += (tranche.get_size() + tranche.get_offered() * (1-tranche.get_price()/100))
        return deal_discount_amount
  
    # c/e is the tranche cost / total cost
    # tranch percentage of total 
    def get_CE(self, tranche):
      return (tranche.get_size() / self.get_tob())

    # calculate rating agency fees (moody's + KRBA)
    def get_RA_fees(self):
      total_deal_amount = self.get_tda()
      moody_fee = max(0.0011 * total_deal_amount, 380000)
      KRBA_fee = max(0.0006 * total_deal_amount + 25000, 175000)
      return (moody_fee + KRBA_fee)

    # calculate placement fee
    def get_placement_fee(self):
      percent_fee = float(input("Input percent fee: ")) or 0.0006
      
      return(percent_fee * self.get_tob())

    def get_upfront_costs(self):
      RA = self.get_RA_fees(self.get_tda())
      placement = self.get_placement_fee()
      legal = int(input("Input legal fee: ")) or 1200000
      accounting = int(input("Input accounting fee: ")) or 155000
      trustee = int(input("Input trustee fee: ")) or 54000
      printing = int(input("Input printing fee: ")) or 27500
      RA_site = int(input("Input RA 17g-5 site fee: ")) or 32000
      modeling = int(input("Input 3rd party modeling fee: ")) or 40000
      misc = int(input("Input miscellaneous fee: ")) or 70000

      return(sum(RA, placement, legal, accounting, trustee, printing, RA_site, modeling, misc))

    def get_upfront_percent(self):
      return((self.get_upfront_costs() / self.get_tob()) * 100)



clo = CLO()
loan_portfolio = CollateralPortfolio()
if clo.get_ramp_up():
  # after one month
  liability_balance = clo.get_tob()
  # total amount getting in loans
  collateral_balance = loan_portfolio.get_collateral_sum()
  
  if liability_balance > collateral_balance:
      # make new loan of size liability - collateral
      newloan = Loan(...)
  
def get_collateral_sum(collateral_portfolio):
    d="get sum of collateral portfolio"

# AFTER A MONTH:
# add new loan with collateral balance liability - collateral

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
        
# ------------------------ COLLATERAL PORTFOLIO ------------------------ #

# create collateral portfolio class

def CollateralPortfolio(Loans):

    collateral_portfolio = ["""list of Loan objects"""]

    def get_collateral_sum(collateral_portfolio):
        sum = 0
        for loan in collateral_portfolio:
            sum+=loan.get_collateral_balance()
        return sum

# NEED TO KNOW MONTH FOR THIS

# remember here loan index starts at 0
# but if we use the loan_id attribute then it would start at 1
# not sure where this code should go (in the loan class? or outside while iterating through collateral_portfolio)
def get_beginning_balance(loan_index):
    if loan_index == 1:
        beginning_balance = 0
    else:
        beginning_balance = get_ending_balance(loan_index-1)
    return beginning_balance

def get_principal_paydown(loan_index):
    if loan_index == collateral_portfolio[loan_index].get_loan_term():
        return get_beginning_balance(loan_index)
    else:
        return 0

def get_ending_balance(loan_index):
    # NEED TO FIND FUNDING AMOUNT
    funding_amount = 0
    return get_beginning_balance(loan_index) + funding_amount - get_principal_paydown(loan_index)

def get_interest_income(loan_index, days_in_month):
    return get_beginning_balance(loan_index) * (collateral_portfolio[loan_index].get_spread() + max(collateral_portfolio[loan_index].get_index_floor(), loan_index) * days_in_month / 360)

loan_index = 1
while loan_index in range(len(collateral_portfolio)):
    d=''
    # iterate through loans in portfolio and store the four above calculations somewhere (where??)

# ------------------------ REINVESTMENT COLLATERAL ------------------------ #
