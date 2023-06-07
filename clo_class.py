from tranche_class import Tranche

class CLO(Tranche):
    def __init__(self, ramp_up, reinvestment_period, starting_date):
        # tranche objects stored here
        self.__tranches = []
        # boolean, default no
        self.__ramp_up = ramp_up
        self.__reinvestment_period = reinvestment_period
        self.__starting_date = starting_date
        self.__total_cashflows = []
    
    def get_total_cashflows(self):
        return self.__total_cashflows
    
    def get_ramp_up(self):
        return self.__ramp_up

    def get_reinvestment_period(self):
        return self.__reinvestment_period

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
    
    def get_tranche_principal_sum(self, month,  reinvest_per, loan_paydown, A_thres):
        princi_sum = 0
        for tranche in self.get_tranches():
          if tranche.get_name() == "A":
              # after rein, before deal call
              if month > reinvest_per and tranche.get_size() > A_thres:
                  #print('adding loan paydown')
                  princi_sum += loan_paydown
              else:
                  #print('adding tranche size')
                  princi_sum += tranche.get_size()
          else:
              if self.get_tranches()[0].get_size() > A_thres:
                  #print('adding 0')
                  princi_sum += 0
              else:
                  #print('adding tranche size 2')
                  princi_sum += tranche.get_size()
        return princi_sum
  
    def append_cashflow(self, month, upfront_cost, num_days, principal_sum, sofr_value):
        if month == 0: # should return a negative number
            print("DDA " + str(self.get_dda()))
            print("TOB " + str(self.get_tob()))
            self.__total_cashflows.append(self.get_dda() + upfront_cost - self.get_tob())
        else:
            interest_sum = 0
            for tranche in self.get_tranches():
                interest_sum += tranche.tranche_interest(num_days, sofr_value)
            self.__total_cashflows.append(interest_sum + principal_sum)