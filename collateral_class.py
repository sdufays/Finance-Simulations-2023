from loan_class import Loan
import numpy as np

class CollateralPortfolio(Loan):
    def __init__(self):
        self.__portfolio = []
        self.__initial_deal_size = 0

    def set_initial_deal_size(self, deal_size):
        self.__initial_deal_size = deal_size

    def get_initial_deal_size(self):
        return self.__initial_deal_size

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
        margin = sum / self.get_collateral_sum()
        # CHANGE THIS loan balance and collateral sum are original numbers
        self.add_initial_loan(loan_id, loan_balance, margin, index_floor=0, remaining_loan_term=36, extension_period=12, open_prepayment_period=19)
        self.__portfolio[loan_id-1].set_term_length(20)
      
    def remove_loan(self, loan):
        self.__portfolio.remove(loan)

    def get_collateral_sum(self):
        sum = 0
        for loan in self.__portfolio:
            sum+=loan.get_loan_balance()
        return sum

    """
    #run this at the beginning of main
    def generate_loan_terms(self, case):
        # Calculate the number of loans to assign to each term
        num_loans = len(self.__portfolio)
        prepay_amt = round(num_loans * case[0])
        # print("prepay: " + str(prepay_amt/num_loans))
        initial_amt = round(num_loans * case[1])
        # print("initial: " + str(initial_amt/num_loans))
        extended_amt = num_loans - prepay_amt - initial_amt
        # print("extended: " + str(extended_amt/num_loans))
        # Create a list with the loan terms according to the scenario
        loan_terms = ['prepaid'] * prepay_amt + ['initial'] * initial_amt + ['extended'] * extended_amt
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
        """
    
    def generate_loan_terms(self, case):
        term_lengths = [34, 15, 24, 18, 15, 35, 31, 14, 36, 31, 18, 16, 23, 15, 45, 23, 8, 54, 30, 13, 15]

        for i, loan in enumerate(self.get_portfolio()):
            term_length = term_lengths[i % len(term_lengths)]
            loan.set_term_length(term_length)

    def get_longest_term(self):
        max = 0
        for loan in self.__portfolio:
            if loan.get_term_length() > max:
                max = loan.get_term_length()
        return max

    def get_collateral_income(self, dataframe, months):
        margin_balance_sum = 0
        for loan in self.get_portfolio():
          margin_balance_sum += (loan.get_margin() + 0.0408) * dataframe.loc[(loan.get_loan_id(), 0), 'Ending Balance']
        return 12 * margin_balance_sum / months # CLO interest cost is number per year, but all income is over duration of deal -> need to conv to annual num