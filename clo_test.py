from clo_class import CLO
import pandas as pd

if __name__ == "__main__":
    # ------------------------ GENERAL INFO ------------------------ #
    base = [.33, .33, .34]
    downside = [.30, .25, .45]
    upside = [.40, .35, .25]

    # read excel file for Other Specifications
    df_os = pd.read_excel("CLO_Input.xlsm", sheet_name = "Other Specifications")

    # assume they're giving us a date at the end of the month
    # they don't start at the start, they start when the first payment is made
    first_payment_date = "yeet"
    #date = first_payment_date.split("/") # ["MM", "DD", "YYYY"]
    #date = list(map(int, date)) # [MM, DD, YYYY]
    # starting payment month
    #starting_month = date[0]
    #days_in_month = get_date_array(date)

    #row_2 = df_os.iloc[1]
    #reinvestment_period = row_2['Reinvestment period']

    # --------------------------- UPFRONT COSTS --------------------------- #

    #legal, accounting, trustee, printing, RA_site, modeling, misc
    # read excel file for upfront costs
    #df_uc = pd.read_excel("CLO_Input.xlsm", sheet_name = "Upfront Costs")

    #row_legal = df_uc.iloc[0]
    #legal = row_legal['Legal']

    #row_accounting = df_uc.iloc[1]
    #accounting = row_accounting['Accounting']

    #row_trustee = df_uc.iloc[2]
    #trustee = row_trustee['Trustee']

    #row_printing = df_uc.iloc[3]
    #printing = row_printing['Printing']

    #row_RA = df_uc.iloc[4]
    #RA_site = row_RA['RA 17g-5 site']

    #row_modeling = df_uc.iloc[5]
    #modeling = row_modeling['3rd Part Modeling']

    #row_misc = df_uc.iloc[6]
    #misc = row_misc['Misc']

    # ------------------------ INITIALIZE OBJECTS ------------------------ #
    #row_1 = df_os.iloc[0]
    #ramp_up = row_1['Ramp up']
    #clo = CLO(ramp_up)

    # read excel file for capital stack
    #df_cs = pd.read_excel("CLO_Input.xlsm", sheet_name = "Capital Stack")

    # add tranches in  a loop
    #for index_t, row_t in df_cs.iterrows():
      #tranche_data = row_t[['Name', 'Rating', 'Offered', 'Size', 'Spread (bps)', 'Price']]
      #clo.add_tranche(tranche_data[0], tranche_data[1], tranche_data[2], tranche_data[3], tranche_data[4], tranche_data[5])
    #threshold = clo.get_clo_threshold()
    #SOFR = 0.0408

    print(df_os.columns)
    #print("\nRAMP UP")
    #clo.get_ramp_up()
    #print("\nREINVESTMENT PERIOD")
    #clo.get_reinvestment_period()
    #print("STARTING DATE")
    #clo.get_starting_date

    #clo.add_tranche('I', 'AA', 1, 327, 99.25)
    #print("\n")
    #clo.get_tranches()