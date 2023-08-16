from tranche_class import Tranche
import math

class CLO(Tranche):
    def __init__(self, ramp_up, reinvestment_bool, replenishment_bool, reinvestment_period, replenishment_period, replenishment_amount, starting_date):
        # tranche objects stored here
        self.__tranches = []
        self.__all_tranches = []
        self.__ramp_up = ramp_up # boolean, default no
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
                
    def get_all_tranches(self):
        return self.__all_tranches
    
    def get_total_cashflows(self):
        self.__total_cashflows = [x for x in self.__total_cashflows if x != 0]
        self.__total_cashflows = [x for x in self.__total_cashflows if not math.isnan(x)]
        return self.__total_cashflows
    
    def set_total_cashflows_MANUAL(self, total_cashflow_list):
        self.__total_cashflows = total_cashflow_list
    
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
        self.__all_tranches.append(tranche)

    def get_tranches(self):
        return self.__tranches

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
   
    def append_cashflow(self, month, upfront_cost, num_days, sofr_value, dataframe, termin_next):
        if month == 0: # should return a negative number
            self.__total_cashflows.append(self.get_dda() + upfront_cost - self.get_tob())
            # stores month 0 tranche interest value in df
            for tranche in self.get_tranches():
                tranche.tranche_interest(num_days, sofr_value, dataframe, month)
        else:
            interest_sum = 0
            principal_sum = 0
            for tranche in self.get_tranches():
                if month == 0:
                    tranche_subtraction_amount = 0
                elif termin_next:
                    tranche_subtraction_amount = dataframe.loc[(tranche.get_name(), month-1), 'Tranche Size']
                    dataframe.loc[(tranche.get_name(), month), 'Principal Payment'] = tranche_subtraction_amount
                    principal_sum += tranche_subtraction_amount
                else:
                    tranche_subtraction_amount = dataframe.loc[(tranche.get_name(), month-1), 'Tranche Size'] - dataframe.loc[(tranche.get_name(), month), 'Tranche Size'] or 0
                    dataframe.loc[(tranche.get_name(), month), 'Principal Payment'] = tranche_subtraction_amount
                    principal_sum += tranche_subtraction_amount
                tranche_interest = tranche.tranche_interest(num_days, sofr_value, dataframe, month)
                interest_sum += tranche_interest
                if tranche.get_name() == self.get_tranches()[-1].get_name(): # if tranche is PREF tranche
                    tranche.add_tranche_cashflow_value(tranche_subtraction_amount + tranche_interest) # add this tranche principal + tranche interest
            self.__total_cashflows.append(interest_sum + principal_sum)

    def current_clo_size(self,dataframe, month):
        tranche_sum = 0
        for tranche in self.get_tranches():
            tranche_sum += dataframe.loc[(tranche.get_name(), month), 'Tranche Size']

        return tranche_sum
 # cash flow for loans 
 # principal sum of all loans + interest sum 
 # store all of it in a list 