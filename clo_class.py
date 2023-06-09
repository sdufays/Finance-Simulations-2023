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

    def clo_principal_sum(self, month, reinvest_per, dataframe, loan_paydown, termin_next, loan, portfolio, po_index):
        append = False
        need_waterfall = False
        clo_principal_sum = 0
        for tranche in self.get_tranches():
            # if we're on the last loan in the month
            if loan.get_loan_id() == portfolio.get_active_portfolio()[-1].get_loan_id():
                append = True # then append the nonzero principal paydown ONLY ONCE to the list of principal paydowns in non-AAA tranches
            if tranche.get_name() == "A":
                 # if a loan pays down while not in reinvestment
                if month > reinvest_per and loan_paydown != 0:
                    principal = loan_paydown
                elif termin_next:
                    principal = tranche.get_bal_list()[month-1]
                else:
                    principal = 0 #self.get_size()
            else:
                if (termin_next and append): # CANT ONLY BE TERMIN NEXT IF WATERFAL
                    # if loan paydown is greater than the last element of the AAA balance list
                    principal = tranche.get_size()
                else:
                    principal = 0
            tranche.append_to_principal_dict(month, principal)
            # if on last iteration of the month
            if po_index == len(portfolio.get_active_portfolio()):
                tranche_principal_sum = sum(tranche.get_principal_dict()[month]) # sum for one tranche
                if tranche.get_name() == 'A':
                    tranche_principal_sum = min(tranche_principal_sum, tranche.get_size())
                    #print("A PRINC SUM {:,.2f}".format(tranche_principal_sum))
                    need_waterfall = True
                elif tranche.get_name() == 'A-S' and need_waterfall:
                    tranche_principal_sum = min(tranche_principal_sum, tranche.get_size())
                # why is it one off for AAA???
                dataframe.loc[(tranche.get_name(), month), 'Principal Payment'] = tranche_principal_sum
                clo_principal_sum += tranche_principal_sum
        return clo_principal_sum # sum for ALL TRANCHES