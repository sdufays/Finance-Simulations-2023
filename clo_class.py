from tranche_class import Tranche

class CLO(Tranche):
    def __init__(self, ramp_up):
        self.__tranches = []
        self.__ramp_up = ramp_up
    
    def get_ramp_up(self):
        return self.__ramp_up

    def add_tranche(self, name, rating, size, spread, offered, price):
        tranche = Tranche(name, rating, size, spread, offered, price)
        self.__tranches.append(tranche)

    def get_tranches(self):
        return self.__tranches

    # need cascade function

    # get total deal amount
    def get_tda(self):
        total_deal_amount = 0 
        for tranche in self.get_tranches():
            total_deal_amount += tranche.get_size()
        return total_deal_amount

    # get total amount of offered bonds (IG bonds balance)
    def get_tob(self):
      total_offered_bonds = 0
      for tranche in self.get_tranches():
          total_offered_bonds += (tranche.get_size() * tranche.get_offered)
      return total_offered_bonds

    # get deal discount amount
    def get_dda(self):
        deal_discount_amount = 0
        for tranche in self.get_tranches():
            deal_discount_amount += (tranche.get_size() + tranche.get_offered() * (1-tranche.get_price()/100))
        return deal_discount_amount
  
    # c/e is the tranche cost / total cost
    # tranch percentage of total 
    def get_CE(self, tranche):
      return (tranche.get_size() / self.get_tob())

    # calculate rating agency fees (moody's + KRBA)
    def get_RA_fees(self):
      total_deal_amount = self.get_tda()
      moody_fee = max(0.0011 * total_deal_amount, 380000)
      KRBA_fee = max(0.0006 * total_deal_amount + 25000, 175000)
      return (moody_fee + KRBA_fee)

    # calculate placement fee
    def get_placement_fee(self):
      percent_fee = float(input("Input percent fee: ")) or 0.0006
      
      return(percent_fee * self.get_tob())

    def get_upfront_costs(self):
      RA = self.get_RA_fees(self.get_tda())
      placement = self.get_placement_fee()
      legal = int(input("Input legal fee: ")) or 1200000
      accounting = int(input("Input accounting fee: ")) or 155000
      trustee = int(input("Input trustee fee: ")) or 54000
      printing = int(input("Input printing fee: ")) or 27500
      RA_site = int(input("Input RA 17g-5 site fee: ")) or 32000
      modeling = int(input("Input 3rd party modeling fee: ")) or 40000
      misc = int(input("Input miscellaneous fee: ")) or 70000

      return(sum(RA, placement, legal, accounting, trustee, printing, RA_site, modeling, misc))

    def get_upfront_percent(self):
      return((self.get_upfront_costs() / self.get_tob()) * 100)