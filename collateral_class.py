from loan_class import Loan
import numpy as np

class CollateralPortfolio(Loan):
    def __init__(self):
        self.__active_portfolio = []
        self.__storage_portfolio = []
        self.__initial_deal_size = 0

    def set_initial_deal_size(self, deal_size):
        self.__initial_deal_size = deal_size

    def get_initial_deal_size(self):
        return self.__initial_deal_size

    def get_active_portfolio(self):
        return self.__active_portfolio

    def get_storage_portfolio(self):
        return self.__storage_portfolio

    def add_initial_loan(self, loan_id, loan_balance, margin, index_floor, remaining_loan_term, extension_period, open_prepayment_period):
        loan = Loan(loan_id, loan_balance, margin, index_floor, remaining_loan_term, extension_period, open_prepayment_period)
        self.__active_portfolio.append(loan)
        self.__storage_portfolio.append(loan)

    # only during reinvestment period
    def add_new_loan(self, loan_balance, margin, month,ramp):
        print("new loan balance " + str("{:,}".format(loan_balance)))
        # make loan id higher than storage portfolio length -> so like 26
        loan_id = len(self.__storage_portfolio) + 1
        # index will be 20 cuz just removed another loan, where the list goes from [0, 1, ... 20]
        # same even if active portfolio shrinks
        if not ramp:
            index_in_portfolio = len(self.__active_portfolio)
        else:
            index_in_portfolio = len(self.__active_portfolio) + 1

        self.add_initial_loan(loan_id, loan_balance, margin, index_floor=0, remaining_loan_term=36, extension_period=12, open_prepayment_period=19)
        # sets term length in active portfolio
        self.__active_portfolio[index_in_portfolio].set_term_length(20)
        # sets month the loan came to birth
        self.__active_portfolio[index_in_portfolio].set_starting_month(month)
        # sets term length in storage portfolio by finding loan by its id
        # cuz storage portfolio will look like [1,2,..., None (was 21), 22]
        for lo in self.__storage_portfolio:
            if lo != None and lo.get_loan_id() == loan_id:
                lo.set_term_length(20)
      
    def generate_initial_margin(self):
        sum = 0
        for loan in self.__active_portfolio:
            sum += (loan.get_loan_balance() * loan.get_margin())
        return sum / self.get_initial_deal_size()

    def remove_loan(self, loan):
        self.__active_portfolio.remove(loan)
        # replace it in storage portfolio with None
        self.__storage_portfolio[int(loan.get_loan_id()) - 1] = None

    def get_collateral_sum(self):
        sum = 0
        for loan in self.__active_portfolio:
            sum+=loan.get_loan_balance()
        return sum

    #run this at the beginning of main
    def generate_loan_terms(self, case):
        # Calculate the number of loans to assign to each term
        num_loans = len(self.__active_portfolio)
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
        for loan, term_type in zip(self.active___portfolio, loan_terms):
            if term_type == "initial":
                loan.set_term_length(loan.get_remaining_loan_term())
            elif term_type == "extended":
                loan.set_term_length(loan.get_remaining_loan_term() + loan.get_extension_period())
            else:
                loan.set_term_length(loan.get_open_prepayment_period())
    
    def initial_loan_terms(self, case):
        term_lengths = [34, 15, 24, 18, 15, 35, 31, 14, 36, 31, 18, 16, 23, 15, 45, 23, 8, 54, 30, 13, 15]

        for i, loan in enumerate(self.__active_portfolio):
            term_length = term_lengths[i % len(term_lengths)]
            loan.set_term_length(term_length)

    def get_longest_term(self):
        max = 0
        for loan in self.__active_portfolio:
            if loan.get_term_length() > max:
                max = loan.get_term_length()
        return max

    def get_collateral_income(self, dataframe, months, sofr_value):
        margin_balance_sum = 0
        for loan in self.__active_portfolio:
          margin_balance_sum += (loan.get_margin() + sofr_value) * dataframe.loc[(loan.get_loan_id(), 0), 'Ending Balance']
        return 12 * margin_balance_sum / months # CLO interest cost is number per year, but all income is over duration of deal -> need to conv to annual num