from clo_class import CLO
import pandas as pd

def get_date_array(date):
    if date[2] % 4 == 0:
      return [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    else: 
      return [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


if __name__ == "__main__":
    # ------------------------ GENERAL INFO ------------------------ #
    base = [.33, .33, .34]
    downside = [.30, .25, .45]
    upside = [.40, .35, .25]

    # read excel file for Other Specifications
    df_os = pd.read_excel("CLO_Input.xlsm", sheet_name = "Other Specifications", header=None)

    # assume they're giving us a date at the end of the month
    # they don't start at the start, they start when the first payment is made
    first_payment_date = df_os.iloc[2, 1]
    date_str = first_payment_date.strftime("%m-%d-%Y")
    date = date_str.split("-") # ["MM", "DD", "YYYY"]
    date = list(map(int, date)) # [MM, DD, YYYY]
    # starting payment month
    starting_month = date[0]
    days_in_month = get_date_array(date)

    reinvestment_period = df_os.iloc[1, 1]

    # --------------------------- UPFRONT COSTS --------------------------- #

    df_uc = pd.read_excel("CLO_Input.xlsm", sheet_name = "Upfront Costs", header=None)
    placement_percent = 0.05 #<---<---<--- need a row for this in excel spreadsheet
    legal = df_uc.iloc[0, 1]
    accounting = df_uc.iloc[1, 1]
    trustee = df_uc.iloc[2, 1]
    printing = df_uc.iloc[3, 1]
    RA_site = df_uc.iloc[4, 1]
    modeling = df_uc.iloc[5, 1]
    misc = df_uc.iloc[6, 1]

    # ------------------------ INITIALIZE OBJECTS ------------------------ #
    ramp_up = df_os.iloc[0, 1]
    clo = CLO(ramp_up, reinvestment_period, first_payment_date)

    # read excel file for capital stack
    df_cs = pd.read_excel("CLO_Input.xlsm", sheet_name = "Capital Stack")

    # add tranches in  a loop
    for index_t, row_t in df_cs.iterrows():
      tranche_data = row_t[['Name', 'Rating', 'Offered', 'Size', 'Spread (bps)', 'Price']]
      clo.add_tranche(tranche_data[0], tranche_data[1], tranche_data[2], tranche_data[3], tranche_data[4], tranche_data[5])
    threshold = clo.get_threshold()
    SOFR = 0.0408

    print("TESTING ADDING TRANCHE")
    #clo.add_tranche('I', 'AA', 56743000, 341, 1, 99.25)
    print(clo.get_tranches()[-1].get_size())

    print("\nTOTAL DEAL AMOUNT")
    print(clo.get_tda())

    print("\nTOTAL OFFERED BONDS")
    print(clo.get_tob())

    print("\nDEAL DISCOUNT AMOUNT")
    print(clo.get_dda())

    print("\nTRANCHE PERCENT OF TOTAL")
    tranche_to_test = clo.get_tranches()[0]
    print(clo.get_CE(tranche_to_test))

    print("\n*************************")

    print("\nGETTING RA FEES")
    print(clo.get_RA_fees())

    print("\nGETTING UPFRONT COSTS")
    print(clo.get_upfront_costs(placement_percent, legal, accounting, trustee, printing, RA_site, modeling, misc))

    print("\nGETTING UPFRONT PERCENT")
    print(clo.get_upfront_percent(placement_percent, legal, accounting, trustee, printing, RA_site, modeling, misc))

    print("\nGETTING THRESHOLD")
    print(clo.get_threshold())

