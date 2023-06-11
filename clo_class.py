from tranche_class import Tranche
import math

class CLO(Tranche):
    def __init__(self, ramp_up, reinvestment_bool, replenishment_bool, reinvestment_period, replenishment_period, replenishment_amount, starting_date):
        # tranche objects stored here
        self.__tranches = []
        # boolean, default no
        self.__ramp_up = ramp_up
        self.__reinvestment_bool = reinvestment_bool
        self.__replenishment_bool = replenishment_bool
        self.__reinvestment_period = reinvestment_period
        self.__replenishment_period = replenishment_period
        self.__replenishment_amount = replenishment_amount             
        self.__starting_date = starting_date
        self.__total_cashflows = []

    def remove_unsold_tranches(self):
        t = 0
        while t in range(len(self.get_tranches())):
            if self.get_tranches()[t].get_offered() == 0:
                self.__tranches.remove(self.get_tranches()[t])
            else:
                t+=1

    
    def get_total_cashflows(self):
        self.__total_cashflows = [x for x in self.__total_cashflows if x != 0]
        self.__total_cashflows = [x for x in self.__total_cashflows if not math.isnan(x)]
        return self.__total_cashflows
    
    def get_ramp_up(self):
        return self.__ramp_up

    def get_reinv_period(self):
        return self.__reinvestment_period
    
    def get_replen_period(self):
        return self.__replenishment_period
    
    def get_reinv_bool(self):
        return self.__reinvestment_bool
    
    def get_replen_bool(self):
        return self.__replenishment_bool
    
    def get_replen_amount(self):
        return self.__replenishment_amount

    def get_starting_date(self):
        return self.__starting_date

    def add_tranche(self, name, rating, offered, size, spread, price):
        tranche = Tranche(name, rating, offered, size, spread, price)
        self.__tranches.append(tranche)

    def get_tranches(self):
        return self.__tranches

    # need cascade function to update tranches

    # get current total deal amount
    def get_tda(self):
        total_deal_amount = 0 
        for tranche in self.get_tranches():
            total_deal_amount += tranche.get_size()
        return total_deal_amount

    # get total amount of offered bonds (IG bonds balance)
    # starts changing once loans get paid off
    def get_tob(self):
        total_offered_bonds = 0
        for tranche in self.get_tranches():
            total_offered_bonds += (tranche.get_size() * tranche.get_offered())
        return total_offered_bonds

    # get deal discount amount
    def get_dda(self):
        deal_discount_amount = 0
        for tranche in self.get_tranches():
            price = tranche.get_price()
            if price < 100:
                deal_discount_amount += tranche.get_size() * tranche.get_offered() * (1 - price / 100)
        return deal_discount_amount
  
    # c/e is the tranche cost / total cost
    # tranch percentage of total 
    def get_CE(self, tranche):
        return (1 - (tranche.get_size() / self.get_tob()))
    # rewrite it later (only right for aaa)

    # calculate rating agency fees (moody's + KRBA)
    def get_RA_fees(self):
        total_deal_amount = self.get_tda()
        moody_fee = max(0.0011 * total_deal_amount, 380000)
        KRBA_fee = max(0.0006 * total_deal_amount + 25000, 175000)
        return (moody_fee + KRBA_fee)

    def get_upfront_costs(self, placement_percent, legal, accounting, trustee, printing, RA_site, modeling, misc):
        RA_fees = self.get_RA_fees()
        placement = placement_percent * self.get_tob()
        costs = [RA_fees, placement, legal, accounting, trustee, printing, RA_site, modeling, misc]
        return sum(costs)

    def get_upfront_percent(self, placement_percent, legal, accounting, trustee, printing, RA_site, modeling, misc):
        return((self.get_upfront_costs(placement_percent, legal, accounting, trustee, printing, RA_site, modeling, misc) / self.get_tob()) * 100)

    def get_threshold(self):
        return self.get_tranches()[0].get_size() * 0.2
    
    def append_cashflow(self, month, upfront_cost, num_days, principal_sum, sofr_value, dataframe):
        if month == 0: # should return a negative number
            self.__total_cashflows.append(self.get_dda() + upfront_cost - self.get_tob())
        else:
            interest_sum = 0
            for tranche in self.get_tranches():
                interest_sum += tranche.tranche_interest(num_days, sofr_value, dataframe, month)
            self.__total_cashflows.append(interest_sum + principal_sum)

    def waterfall(self, index, month, remaining_payment, dataframe):
        if index >= len(self.get_tranches()): # if there are no more tranches left
            print(f"Warning: payment of {remaining_payment:,.2f} could not be allocated to any tranche.")
            outputs = [remaining_payment, False, True]
            return outputs # indicating 'overflow'
        
        # get current tranche i'm iterating through
        tranche = self.get_tranches()[index]

        # get current balance of this tranche
        current_balance = dataframe.loc[(tranche.get_name(), month-1), 'Tranche Size']

        # get principal payment value to this tranche
        payment_to_this_tranche = min(remaining_payment, current_balance)

        # waterfall remaining payment
        remaining_payment -= payment_to_this_tranche

        # append principal payment
        tranche.append_to_principal_dict(month, payment_to_this_tranche)

        print(tranche.get_name() + " month " + str(month))
        print("current balance {:,.2f}\n principal payment {:,.2f}\n remaining waterfall needed {:,.2f}\n".format(current_balance, payment_to_this_tranche, remaining_payment))

        # add to dataframe
        dataframe.loc[(tranche.get_name(), month), 'Principal Payment'] = payment_to_this_tranche

        # if there's still payment left after paying to this tranche
        just_ended = False
        if remaining_payment > 0: 
            #print(f"Waterfall from tranche {tranche.get_name()} to next tranche with remaining value {remaining_payment:,.2f}")
            if remaining_payment == payment_to_this_tranche:
                just_ended = False
            else:
                just_ended = True
            remaining_payment = self.waterfall(index+1, month, remaining_payment, dataframe)[0]
        
        return [remaining_payment, False, just_ended]


    def clo_principal_sum(self, month, reinvest_per, dataframe, loan_paydown, termin_next, loan, portfolio, po_index):
        append = False
        clo_principal_sum = 0
        need_waterfall = False
        waterfall_value = 0
        just_ended = False
        for tranche_index in range(len(self.get_tranches())):
            tranche = self.get_tranches()[tranche_index]
            # if we're on the last loan in the month
            if loan.get_loan_id() == portfolio.get_active_portfolio()[-1].get_loan_id():
                append = True # then append the nonzero principal paydown ONLY ONCE to the list of principal paydowns in non-AAA tranches
            # ------- PRINCIPAL PAYMENTS FOR EVERY LOAN IN A MONTH ------- #
            # IF TRANCHE AAA
            if tranche == self.get_tranches()[0]: 
                # if a loan pays down while not in reinvestment
                if month > reinvest_per and loan_paydown != 0: 
                    single_loan_principal = loan_paydown
                # elif we're about to call the deal -> it's the prev month AAA balance (except rn it's the current month? what)
                elif termin_next and append:
                    single_loan_principal = dataframe.loc[(tranche.get_name(), month - 1), 'Tranche Size']
                else:
                    single_loan_principal = 0
            # ELSE IF OTHER TRANCHES
            else:
                if (termin_next and append): # CANT ONLY BE TERMIN NEXT IF WATERFAL
                    # if loan paydown is greater than the last element of the AAA balance list
                    single_loan_principal = dataframe.loc[(tranche.get_name(), month - 1), 'Tranche Size']
                else:
                    single_loan_principal = 0
            # APPENDS INDIV PRINCIPAL PAYMENTS TO DICTIONARY
            # {month 0: [principay1, principay 2, .... for all loans]}
            tranche.append_to_principal_dict(month, single_loan_principal)
            # ----------- PRINCIPAL PAYMENTS FOR ONE MONTH FOR EVERY TRANCHE ----------#
            # if on last iteration of the month
            if po_index == len(portfolio.get_active_portfolio()):
                # get sum of all principal payments for this ONE tranche for this ONE month
                tranche_principal_sum = sum(tranche.get_principal_dict()[month])
                # if this tranche is tranche AAA
                if tranche == self.get_tranches()[0]:
                    # if the principal is more than the tranche balance, need waterfall!
                    if month > 0 and tranche_principal_sum > dataframe.loc[(tranche.get_name(), month-1), 'Tranche Size']:
                        #print("month {}".format(month))
                        #print("tranche principal {:,.2f}\n tranche size {:,.2f}".format(tranche_principal_sum, dataframe.loc[(tranche.get_name(), month-1), 'Tranche Size']))
                        need_waterfall = True
                        waterfall_value = tranche_principal_sum - dataframe.loc[(tranche.get_name(), month-1), 'Tranche Size']
                        #print("waterfal value {:,.2f}".format(waterfall_value))
                    # calculate final value of tranche principal sum for this month
                    if month != 0:
                        tranche_principal_sum = min(tranche_principal_sum, dataframe.loc[(tranche.get_name(), month-1), 'Tranche Size'])
                    dataframe.loc[(tranche.get_name(), month), 'Principal Payment'] = tranche_principal_sum
                # else if this tranche is the second one AND you need waterfall
                elif need_waterfall:
                    outputs = self.waterfall(tranche_index, month, waterfall_value, dataframe)
                    need_waterfall = outputs[1]
                    just_ended = outputs[2]
                elif just_ended: # waterfall just ended so the principal payment was already added to dataframe right??
                    just_ended = False
                elif not need_waterfall and not just_ended:
                    dataframe.loc[(tranche.get_name(), month), 'Principal Payment'] = tranche_principal_sum
                clo_principal_sum += tranche_principal_sum
        return clo_principal_sum # sum for ALL TRANCHES
    """ 
    # WORKING
    def clo_principal_sum(self, month, reinvest_per, dataframe, loan_paydown, termin_next, loan, portfolio, po_index):
        append = False
        clo_principal_sum = 0
        need_waterfall = False
        waterfall_value = 0
        for tranche in self.get_tranches():
            # if we're on the last loan in the month
            if loan.get_loan_id() == portfolio.get_active_portfolio()[-1].get_loan_id():
                append = True # then append the nonzero principal paydown ONLY ONCE to the list of principal paydowns in non-AAA tranches
            # ------- PRINCIPAL PAYMENTS FOR EVERY LOAN IN A MONTH ------- #
            # IF TRANCHE AAA
            if tranche == self.get_tranches()[0]: 
                # if a loan pays down while not in reinvestment
                if month > reinvest_per and loan_paydown != 0: 
                    single_loan_principal = loan_paydown
                # elif we're about to call the deal -> it's the prev month AAA balance (except rn it's the current month? what)
                elif termin_next and append:
                    single_loan_principal = dataframe.loc[('A', month - 1), 'Tranche Size']
                else:
                    single_loan_principal = 0
            # ELSE IF OTHER TRANCHES
            else:
                if (termin_next and append): # CANT ONLY BE TERMIN NEXT IF WATERFAL
                    # if loan paydown is greater than the last element of the AAA balance list
                    single_loan_principal = tranche.get_size()
                else:
                    single_loan_principal = 0
            # APPENDS INDIV PRINCIPAL PAYMENTS TO DICTIONARY
            # {month 0: [principay1, principay 2, .... for all loans]}
            tranche.append_to_principal_dict(month, single_loan_principal)
            # ----------- PRINCIPAL PAYMENTS FOR ONE MONTH FOR EVERY TRANCHE ----------#
            # if on last iteration of the month
            if po_index == len(portfolio.get_active_portfolio()):
                # get sum of all principal payments for this ONE tranche for this ONE month
                tranche_principal_sum = sum(tranche.get_principal_dict()[month])
                # if this tranche is tranche AAA
                if tranche == self.get_tranches()[0]:
                    # if the principal is more than the tranche balance, need waterfall!
                    if month > 0 and tranche_principal_sum > dataframe.loc[(tranche.get_name(), month-1), 'Tranche Size']:
                        need_waterfall = True
                        waterfall_value = tranche_principal_sum - dataframe.loc[(tranche.get_name(), month-1), 'Tranche Size']
                    # calculate final value of tranche principal sum for this month
                    tranche_principal_sum = min(tranche_principal_sum, tranche.get_size())
                # else if this tranche is the second one AND you need waterfall
                elif tranche == self.get_tranches()[1] and need_waterfall:
                    print("Waterfall value {:,.2f}".format(waterfall_value))
                    tranche_principal_sum = waterfall_value # waterfall value is original sum - AAA bal():
                # why is it one off for AAA???
                dataframe.loc[(tranche.get_name(), month), 'Principal Payment'] = tranche_principal_sum
                clo_principal_sum += tranche_principal_sum
        return clo_principal_sum # sum for ALL TRANCHES
    """