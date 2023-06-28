from loan_class import Loan
import random
import numpy as np
import pandas as pd


class CollateralPortfolio(Loan):
    def __init__(self, market_spread):
        self.__active_portfolio = []
        self.__storage_portfolio = []
        self.__collateral_list = []
        self.__loan_cashflow = []
        self.__initial_deal_size = 0
        self.__market_spread = market_spread
    
    def get_market_spread(self):
        return self.__market_spread

    def set_initial_deal_size(self, deal_size):
        self.__initial_deal_size = deal_size

    def get_initial_deal_size(self):
        return self.__initial_deal_size

    def get_active_portfolio(self):
        return self.__active_portfolio

    def get_loan_cashflow(self):
        return self.__loan_cashflow
    
    def get_storage_portfolio(self):
        return self.__storage_portfolio
    
    def get_collateral_list(self):
        return self.__collateral_list

    def add_initial_loan(self, loan_id, loan_balance, margin, index_floor, remaining_loan_term, extension_period, open_prepayment_period, manual_term):
        loan = Loan(loan_id, loan_balance, margin, index_floor, remaining_loan_term, extension_period, open_prepayment_period, manual_term)
        self.__active_portfolio.append(loan)
        self.__storage_portfolio.append(loan)

    # only during reinvestment / ramp-up period
    def add_new_loan(self, loan_balance, margin, month,ramp):
        new_loan_terms = [18, 20, 30]
        #term = new_loan_terms[1] # if you want consistent results
        term = new_loan_terms[random.randint(0,2)]
        # print("new loan balance " + str("{:,}".format(loan_balance)))
        # make loan id higher than storage portfolio length -> i.e. 26
        loan_id = len(self.__storage_portfolio) + 1
        # index will be 20 cuz just removed another loan, where the list goes from [0, 1, ... 20]
        # same even if active portfolio shrinks
        if not ramp:
            index_in_portfolio = len(self.__active_portfolio)
        else:
            index_in_portfolio = len(self.__active_portfolio) + 1

        self.add_initial_loan(loan_id, loan_balance, margin, index_floor=0, remaining_loan_term=36, extension_period=12, open_prepayment_period=1, manual_term=0)
        # sets term length in active portfolio
        self.__active_portfolio[index_in_portfolio].set_term_length(term)
        # sets month the loan came to birth
        self.__active_portfolio[index_in_portfolio].set_starting_month(month)
        # sets term length in storage portfolio by finding loan by its id
        # cuz storage portfolio will look like [1,2,..., None (was 21), 22]
        for lo in self.__storage_portfolio:
            if lo != None and lo.get_loan_id() == loan_id:
                lo.set_term_length(term)

    def update_loan_cashflow(self, monthly_amount):
        self.__loan_cashflow.append(monthly_amount)
      
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
        self.__collateral_list.append(sum)
        return sum
    
    def calculate_term_lengths(self, portfolio, loan_term_types):
        np.random.shuffle(loan_term_types)
        for loan, term_type in zip(portfolio, loan_term_types):
            if term_type == "initial":
                loan.set_term_length(loan.get_remaining_loan_term())
            elif term_type == "extended":
                loan.set_term_length(loan.get_remaining_loan_term() + loan.get_extension_period())
            else:
                loan.set_term_length(loan.get_open_prepayment_period())

    def generate_loan_terms(self, case):
        # Calculate the number of loans to assign to each term
        num_loans = len(self.__active_portfolio)
        prepay_amt = round(num_loans * case[2])
        initial_amt = round(num_loans * case[0])
        extended_amt = num_loans - prepay_amt - initial_amt
        # Create a list with the loan terms according to the scenario
        loan_terms = ['prepaid'] * prepay_amt + ['initial'] * initial_amt + ['extended'] * extended_amt
        # Shuffle the list to randomize the terms
        # Assign each loan a term from the list
        self.calculate_term_lengths(self.__active_portfolio, loan_terms)
    
    def market_aware_loan_terms(self):
        regular_loan_distribution = {'prepay': .20, 'initial': .50, 'extended': .30}
        big_spread_loan_distribution = {'prepay': .40, 'initial': .60}
        regular_loan_list = []
        big_spread_loan_list = []
        for loan in self.get_active_portfolio():
            # should it just be >?
            if loan.get_margin() >= 1.1 * self.get_market_spread():
                big_spread_loan_list.append(loan)
            else:
                regular_loan_list.append(loan)
        reg_prepay_amt = round(len(regular_loan_list) * regular_loan_distribution['prepay'])
        reg_initial_amt = round(len(regular_loan_list) * regular_loan_distribution['initial'])
        reg_extend_amt = len(regular_loan_list) - reg_prepay_amt - reg_initial_amt
        reg_loan_terms = ['prepaid'] * reg_prepay_amt + ['initial'] * reg_initial_amt + ['extended'] * reg_extend_amt
        self.calculate_term_lengths(regular_loan_list, reg_loan_terms)
        
        big_prepay_amt = round(len(big_spread_loan_list) * big_spread_loan_distribution['prepay'])
        big_initial_amt = len(big_spread_loan_list) - big_prepay_amt
        big_loan_terms = ['prepaid'] * big_prepay_amt + ['initial'] * big_initial_amt
        self.calculate_term_lengths(big_spread_loan_list, big_loan_terms)

    def initial_loan_terms(self):
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