from tranche_class import Tranche
import math

class CLO(Tranche):
    def __init__(self, ramp_up, reinvestment_bool, replenishment_bool, reinvestment_period, replenishment_period, replenishment_amount, starting_date):
        # tranche objects stored here
        self.__tranches = []
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
                    print("month {} tranche subtraction {:,.2f}".format(month, tranche_subtraction_amount))
                    dataframe.loc[(tranche.get_name(), month), 'Principal Payment'] = tranche_subtraction_amount
                    principal_sum += tranche_subtraction_amount
                interest_sum += tranche.tranche_interest(num_days, sofr_value, dataframe, month)
            self.__total_cashflows.append(interest_sum + principal_sum)
"""
    def clo_principal_sum(self, month, dataframe, loan_principal_pay, loan, replen_cumu, replen_months, termin_next, portfolio):
        total_monthly_principal_sum = 0
        reinvestment_bool = (self.get_reinv_bool()) and (month <= self.get_reinv_period())
        replenishment_bool = (self.get_replen_bool() and not self.get_reinv_bool()) and (month <= self.get_replen_period() and replen_cumu < self.get_replen_amount())
        replen_after_reinv_bool = (self.get_reinv_bool() and self.get_replen_bool()) and (month > self.get_reinv_period()) and (replen_months < self.get_replen_period() and replen_cumu < self.get_replen_amount())
        is_last_loan = False
        if loan.get_loan_id() >= portfolio.get_active_portfolio()[-1].get_loan_id():
            is_last_loan = True
        
        if termin_next and is_last_loan:
            for tranche in self.get_tranches():
                monthly_principal_one_tranche = dataframe.loc[(tranche.get_name(), month-1), 'Tranche Size']
                dataframe.loc[(tranche.get_name(), month), 'Principal Payment'] = monthly_principal_one_tranche
                total_monthly_principal_sum += monthly_principal_one_tranche
            return total_monthly_principal_sum
        elif not reinvestment_bool and not replenishment_bool and not replen_after_reinv_bool:
            for tranche in self.get_tranches():
                tranche_name = tranche.get_name()
                tranche_size = dataframe.loc[(tranche.get_name(), month-1), 'Tranche Size']
                AAA_size = dataframe.loc[(self.get_tranches()[0].get_name(), month-1), 'Tranche Size']
                if tranche_name == self.get_tranches()[0].get_name(): # AAA
                    tranche.append_to_principal_dict(month, loan_principal_pay)
                    if is_last_loan:
                        #print(tranche.get_name())
                        #print(month)
                        if month == 17 and loan_principal_pay!=0: print(tranche.get_principal_dict()[month])
                        monthly_principal_one_tranche = sum(tranche.get_principal_dict()[month])
                        # no waterfall
                        if AAA_size >= monthly_principal_one_tranche:
                            #print("added {:,.2f} to {:,.2f}".format(monthly_principal_one_tranche, total_monthly_principal_sum))
                            total_monthly_principal_sum += monthly_principal_one_tranche
                            dataframe.loc[(tranche.get_name(), month), 'Principal Payment'] = monthly_principal_one_tranche
                            #if tranche.get_name() == "A": print("month {} tranche monthly principal {:,.2f}".format(month, monthly_principal_one_tranche))
                            return total_monthly_principal_sum
                        # if waterfall
                        else:
                            total_monthly_principal_sum += tranche_size
                            dataframe.loc[(tranche.get_name(), month), 'Principal Payment'] = tranche_size
                            waterfall_amount = monthly_principal_one_tranche - tranche_size
                            total_monthly_principal_sum = self.principay_waterfall(waterfall_amount, dataframe, month, total_monthly_principal_sum)
                return total_monthly_principal_sum
        else:
            return 0
    

    def principay_waterfall(self, waterfall_amount,dataframe, month, total_monthly_principal_sum):
        tranche_i = 1
        while tranche_i < len(self.get_tranches()):
            tranche = self.get_tranches()[tranche_i]
            tranche_size = dataframe.loc[(tranche.get_name(), month-1), 'Tranche Size']
            # no waterfall
            if tranche_size >= waterfall_amount:
                total_monthly_principal_sum += waterfall_amount
                dataframe.loc[(tranche.get_name(), month), 'Principal Payment'] = waterfall_amount
                remaining_waterfall = 0
                return total_monthly_principal_sum
            # if waterfall
            else:
                total_monthly_principal_sum += tranche_size
                dataframe.loc[(tranche.get_name(), month), 'Principal Payment'] = tranche_size
                waterfall_amount = waterfall_amount - tranche_size
            tranche_i += 1
        if waterfall_amount > 0:
            raise ValueError("Not enough balance in tranches")

                
                    """