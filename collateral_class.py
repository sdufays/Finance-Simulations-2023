from loan_class import Loan

class CollateralPortfolio(Loan):
    def __init__(self):
        self.__portfolio = []

    def get_portfolio(self):
        return self.__portfolio

    def add_initial_loan(self, loan_id, loan_balance, margin, index_floor, remaining_loan_term, extension_period, open_prepayment_period):
        loan = Loan(loan_id, loan_balance, margin, index_floor, remaining_loan_term, extension_period, open_prepayment_period)
        self.__portfolio.append(loan)

    # only during reinvestment period
    def add_new_loan(self, loan_balance):
      loan_id = len(self.__portfolio) + 1
      sum = 0
      for loan in self.__portfolio:
        sum += (loan.get_loan_balance() * loan.get_margin())
      margin = sum / self._get_collateral_sum()
      self.add_initial_loan(loan_id, loan_balance, margin, index_floor=0, remaining_loan_term=36, extension_period=12, open_prepayment_period=19)
      self.__portfolio[loan_id-1].set_term_length(30)
      
    def remove_loans(self):
        for loan in self.__portfolio:
          if loan.get_loan_balance() <= 0:
            self.__portfolio.remove(loan)

    def get_collateral_sum(self):
        sum = 0
        for loan in self.__portfolio:
            sum+=loan.get_collateral_balance()
        return sum

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

    def get_longest_term(self):
      max = 0
      for loan in self.__portfolio:
        if loan.get_term_length() > max:
          max = loan.get_term_length()
      return max
