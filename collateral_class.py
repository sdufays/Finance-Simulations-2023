from loan_class import Loan

class CollateralPortfolio(Loan):
    def __init__(self):
        self.__portfolio = []

    def get_portfolio(self):
        return self.__portfolio
      
    def add_loan(self, loan_id, loan_balance, margin, index_floor, remaining_loan_term, extension_period, open_prepayment_period):
        loan = Loan(loan_id, loan_balance, margin, index_floor, remaining_loan_term, extension_period, open_prepayment_period)
        self.__portfolio.append(loan)

    def remove_loan(self):
        for loan in self.__portfolio:
          if loan.get_loan_balance() <= 0:
            self.__portfolio.remove(loan)

    def get_collateral_sum(self):
        sum = 0
        for loan in self.__portfolio:
            sum+=loan.get_collateral_balance()

"""base = [.33, .33, .34]
    downside = [.30, .25, .45]
    upside = [.40, .35, .25]
"""
  #run this at the beginning of main
  def generate_loan_terms(self, case):
      # Calculate the number of loans to assign to each term
      num_loans = len(self.__portfolio)
      prepay_amt = round(num_loans * case[0])
      intial_amt = round(num_loans * case[1])
      extended_amt = num_loans - prepay_amt - intial_amt
  
      # Create a list with the loan terms according to the scenario
      loan_terms = ['prepaid'] * prepay_amt + ['initial'] * intial_amt + ['extended'] * extended_amt
  
      # Shuffle the list to randomize the terms
      np.random.shuffle(loan_terms)
  
      # Assign each loan a term from the list
      for loan, term_type in zip(self.__portfolio, loan_terms):
          if term_type == "initial":
              loan.set_term_length(loan.get_remaining_loan_term())
          elif term_type == "extended":
              loan.set_term_length(loan.get_remaining_loan_term() + loan.get_extension_period())
          else:
              loan.set_term_length(loan.get_open_prepayment_period())