def clo_principal_sum(self, month, dataframe, loan_principal_pay, loan, replen_cumu, replen_months, termin_next, portfolio):
    total_monthly_principal_sum = 0
    reinvestment_bool = (self.get_reinv_bool()) and (month <= self.get_reinv_period())
    replenishment_bool = (self.get_replen_bool() and not self.get_reinv_bool()) and (month <= self.get_replen_period() and replen_cumu <= self.get_replen_amount())
    replen_after_reinv_bool = (self.get_reinv_bool() and self.get_replen_bool()) and (month > self.get_reinv_period()) and (replen_months < self.get_replen_period() and replen_cumu < self.get_replen_amount())
    is_last_loan = False
    if loan.get_loan_id() == portfolio.get_active_portfolio()[-1].get_loan_id():
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
                if month == 18: print("loan id {} principal pay {:,.2f}".format(loan.get_loan_id(), loan_principal_pay))
                if is_last_loan:
                    #print(tranche.get_name())
                    #print(month)
                    #print(tranche.get_principal_dict()[month])
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