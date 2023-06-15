import pandas as pd
import numpy_financial as npf
import math
import numpy as np
import xlsxwriter
from collections import Counter

def graphs(output_df, cases, trial_numbers, NUM_TRIALS):
# ---------------------------- READING DF ----------------------------- #
    deal_call_months_dict = {}
    wa_cof_dict = {}
    equity_yield_dict = {}
    adv_rate_dict = {}
    for case in cases:
       deal_call_months_list = []
       wa_cof_list = []
       equity_yield_list = []
       adv_rate_list = []
       for trial in trial_numbers:
          call_month = output_df.loc[(case, trial), 'Deal Call Month']
          call_month2 = output_df.loc[(case, trial), 'WA COF']
          call_month3 = output_df.loc[(case, trial), 'Projected Equity Yield']
          call_month4 = output_df.loc[(case, trial), 'WA Adv Rate']
          deal_call_months_list.append(call_month)
          wa_cof_list.append(call_month2)
          equity_yield_list.append(call_month3)
          adv_rate_list.append(call_month4)

       deal_call_months_dict[case] = deal_call_months_list
       wa_cof_dict[case] = wa_cof_list
       equity_yield_dict[case] = equity_yield_list
       adv_rate_dict[case] = adv_rate_list

    deal_call_months_sort = sorted(deal_call_months_list)

    dcm_unique = []
    for num in deal_call_months_sort:
       if num not in dcm_unique:
          dcm_unique.append(num)

    dcm_base_list = deal_call_months_dict['base']
    dcm_down_list = deal_call_months_dict['downside']
    dcm_up_list = deal_call_months_dict['upside']

    occ_dcm = Counter(deal_call_months_list)
    occ_dcm_base = Counter(dcm_base_list)
    occ_dcm_down = Counter(dcm_down_list)
    occ_dcm_up = Counter(dcm_up_list)
    occ_list_dcm_b = list(occ_dcm_base.items())
    occ_list_dcm_d = list(occ_dcm_down.items())
    occ_list_dcm_u = list(occ_dcm_up.items())
    occ_list_dcm = list(occ_dcm.items())
    occ_list_dcm.sort(key=lambda x: x[0])
    occ_list_dcm_b.sort(key=lambda x: x[0])
    occ_list_dcm_d.sort(key=lambda x: x[0])
    occ_list_dcm_u.sort(key=lambda x: x[0])

    counts_dcm = [count for num, count in occ_list_dcm]
    counts_dcm_base = [count for num, count in occ_list_dcm_b]
    counts_dcm_downside = [count for num, count in occ_list_dcm_d]
    counts_dcm_upside = [count for num, count in occ_list_dcm_u]
    


   # ------------------------- GRAPHING OUTPUTS -------------------------- #
    workbook = xlsxwriter.Workbook('graphs.xlsx')
    worksheet_dcm = workbook.add_worksheet("Deal Call Months")
    worksheet_base = workbook.add_worksheet("Base")
    worksheet_downside = workbook.add_worksheet("Downside")
    worksheet_upside = workbook.add_worksheet("Upside")
    bold = workbook.add_format({'bold': 1})
    headings_dcm = ['Sims', 'Base', 'Downside', 'Upside']
    headings_base = ['Sims', 'Base']
    headings_downside = ['Sims', 'Downside']
    headings_upside = ['Sims', 'Upside']

    # deal call months
    data_dcm = [
       list(range(1, NUM_TRIALS + 1)), # this is my x-axis
       deal_call_months_dict['base'], # this is one batch of data aka the y-axis
       deal_call_months_dict['downside'],
       deal_call_months_dict['upside']
    ]

    data_base = [ # lol
       list(range(1, NUM_TRIALS + 1)),
       deal_call_months_dict['base']
    ]

    data_downside = [
       list(range(1, NUM_TRIALS + 1)),
       deal_call_months_dict['downside']
    ]

    data_upside = [
       list(range(1, NUM_TRIALS + 1)),
       deal_call_months_dict['upside']
    ]

    worksheet_dcm.write_row('A1', headings_dcm, bold)
    worksheet_base.write_row('A1', headings_base, bold)
    worksheet_downside.write_row('A1', headings_downside, bold)
    worksheet_upside.write_row('A1', headings_upside, bold)
   
    # writing columns for dcm
    worksheet_dcm.write_column('A2', data_dcm[0])
    worksheet_dcm.write_column('B2', data_dcm[1])
    worksheet_dcm.write_column('C2', data_dcm[2])
    worksheet_dcm.write_column('D2', data_dcm[3])

    # writing columns for base
    worksheet_base.write_column('A2', data_base[0])
    worksheet_base.write_column('B2', data_base[1])

    # writing columns for downside
    worksheet_downside.write_column('A2', data_downside[0])
    worksheet_downside.write_column('B2', data_downside[1])

    # writing columns for upside
    worksheet_upside.write_column('A2', data_upside[0])
    worksheet_upside.write_column('B2', data_upside[1])

    # scatter chart object
    chart1 = workbook.add_chart({'type': 'scatter'})
    chart2 = workbook.add_chart({'type': 'scatter'})
    chart3 = workbook.add_chart({'type': 'scatter'})
    chart4 = workbook.add_chart({'type': 'scatter'})

    # base, downside, upside
    chart1.add_series({
       'name':       ['Deal Call Months', 0, 1],
       'categories': ['Deal Call Months', 1, 0, NUM_TRIALS, 0], # x axis values placement ['Sheet name', first_row, first_column, last_row, last_column]
       'values':     ['Deal Call Months', 1, 1, NUM_TRIALS, 1] # y axis values placement ['Sheet name', first_row, first_column, last_row, last_column]
    })

    chart1.add_series({
       'name':       ['Deal Call Months', 0, 2],
       'categories': ['Deal Call Months', 1, 0, NUM_TRIALS, 0], 
       'values':     ['Deal Call Months', 1, 2, NUM_TRIALS, 2]
    })

    chart1.add_series({
       'name':       ['Deal Call Months', 0, 3],
       'categories': ['Deal Call Months', 1, 0, NUM_TRIALS, 0],
       'values':     ['Deal Call Months', 1, 3, NUM_TRIALS, 3]
    })

    # just base
    chart2.add_series({
       'name':       ['Base', 0, 1],
       'categories': ['Base', 1, 0, NUM_TRIALS, 0], 
       'values':     ['Base', 1, 1, NUM_TRIALS, 1]
    })

    # just downside
    chart3.add_series({
       'name':       ['Downside', 0, 2],
       'categories': ['Downside', 1, 0, NUM_TRIALS, 0],
       'values':     ['Downside', 1, 1, NUM_TRIALS, 1]
    })

    # just upside
    chart4.add_series({
       'name':       ['Upside', 0, 3],
       'categories': ['Upside', 1, 0, NUM_TRIALS, 0], 
       'values':     ['Upside', 1, 1, NUM_TRIALS, 1]
    })

    # chart title 
    chart1.set_title ({'name': 'Deal Call Months for All Scenarios'})
    chart2.set_title ({'name': 'Deal Call Months for Base Scenario'})
    chart3.set_title ({'name': 'Deal Call Months for Downside Scenario'})
    chart4.set_title ({'name': 'Deal Call Months for Upside Scenario'})
   
    # x-axis label
    chart1.set_x_axis({'name': 'Simulation Number'})
    chart2.set_x_axis({'name': 'Simulation Number'})
    chart3.set_x_axis({'name': 'Simulation Number'})
    chart4.set_x_axis({'name': 'Simulation Number'})
   
    # y-axis label
    chart1.set_y_axis({'name': 'Deal Call Month', 'min': 20})
    chart2.set_y_axis({'name': 'Deal Call Month', 'min': 20})
    chart3.set_y_axis({'name': 'Deal Call Month', 'min': 20})
    chart4.set_y_axis({'name': 'Deal Call Month', 'min': 20})
   
    # Set an Excel chart style.
    # 1 - grey / 2 - blue, red / 3 - blues / 4 - reds / 5  - greens / 6 - purples 
    # 7 - like a light blueish green / 8 - oranges / 9 - ew / 10 - blue, orangey red
    chart1.set_style(2)
    chart2.set_style(3)
    chart3.set_style(4)
    chart4.set_style(5)
    chart1.set_size({'width': 600, 'height': 400})
    chart2.set_size({'width': 600, 'height': 400})
    chart3.set_size({'width': 600, 'height': 400})
    chart4.set_size({'width': 600, 'height': 400})

    worksheet_dcm.insert_chart('F2', chart1)
    worksheet_base.insert_chart('E2', chart2)
    worksheet_downside.insert_chart('E2', chart3)
    worksheet_upside.insert_chart('E2', chart4)

    # ------------------------------- SWAPPED --------------------------------- #
    worksheet_swapped = workbook.add_worksheet("Deal Call Months Frequency")
    bold = workbook.add_format({'bold': 1})
    headings_swapped = ['Deal Call Months']

    data_swapped = [
       dcm_unique,
       counts_dcm
    ]
    
    worksheet_swapped.write_row('A1', headings_swapped, bold)
    worksheet_swapped.write_column('A2', data_swapped[0])
    worksheet_swapped.write_column('B2', data_swapped[1])

    chart5 = workbook.add_chart({'type': 'column'})
    chart5.add_series({
       'name':       ['Deal Call Months Frequency', 0, 1],
       'categories': ['Deal Call Months Frequency', 1, 0, max(dcm_unique), 0],
       'values':     ['Deal Call Months Frequency', 1, 1, max(dcm_unique), 1]
    })

    chart5.set_title ({'name': 'ALL Deal Call Month Frequency'})
    chart5.set_x_axis({'name': 'Deal Call Month'})
    chart5.set_y_axis({'name': 'Frequency'})
    chart5.set_size({'width': 1700, 'height': 400})

    chart5.set_style(8)
    worksheet_swapped.insert_chart('F2', chart5)

    # ------------------------------- SWAPPED BASE --------------------------------- #
    worksheet_sb = workbook.add_worksheet("Deal Call Months Base Frequency")
    bold = workbook.add_format({'bold': 1})
    headings_swapped = ['Deal Call Months']

    data_sb = [
       dcm_unique,
       counts_dcm_base
    ]
    
    worksheet_sb.write_row('A1', headings_swapped, bold)
    worksheet_sb.write_column('A2', data_sb[0])
    worksheet_sb.write_column('B2', data_sb[1])

    chart6 = workbook.add_chart({'type': 'column'})
    chart6.add_series({
       'name':       ['Deal Call Months Base Frequency', 0, 1],
       'categories': ['Deal Call Months Base Frequency', 1, 0, max(dcm_unique), 0],
       'values':     ['Deal Call Months Base Frequency', 1, 1, max(dcm_unique), 1]
    })

    chart6.set_title ({'name': 'Deal Call Month Frequency'})
    chart6.set_x_axis({'name': 'Deal Call Month'})
    chart6.set_y_axis({'name': 'Frequency'})
    chart6.set_size({'width': 1700, 'height': 400})

    chart6.set_style(3)
    worksheet_sb.insert_chart('F2', chart6)

    # ------------------------------- SWAPPED DOWNSIDE --------------------------------- #
    worksheet_sd = workbook.add_worksheet("Deal Call Months Downside Freq")

    data_sd = [
       dcm_unique,
       counts_dcm_downside
    ]
    
    worksheet_sd.write_row('A1', headings_swapped, bold)
    worksheet_sd.write_column('A2', data_sd[0])
    worksheet_sd.write_column('B2', data_sd[1])

    chart7 = workbook.add_chart({'type': 'column'})
    chart7.add_series({
       'name':       ['Deal Call Months Downside Freq', 0, 1],
       'categories': ['Deal Call Months Downside Freq', 1, 0, max(dcm_unique), 0],
       'values':     ['Deal Call Months Downside Freq', 1, 1, max(dcm_unique), 1]
    })

    chart7.set_title ({'name': 'Deal Call Month Frequency'})
    chart7.set_x_axis({'name': 'Deal Call Month'})
    chart7.set_y_axis({'name': 'Frequency'})
    chart7.set_size({'width': 1700, 'height': 400})

    chart7.set_style(4)
    worksheet_sd.insert_chart('F2', chart7)

    # ------------------------------- SWAPPED UPSIDE --------------------------------- #
    worksheet_su = workbook.add_worksheet("Deal Call Months Upside Freq")

    data_su = [
       dcm_unique,
       counts_dcm_upside
    ]
    
    worksheet_su.write_row('A1', headings_swapped, bold)
    worksheet_su.write_column('A2', data_su[0])
    worksheet_su.write_column('B2', data_su[1])

    chart8 = workbook.add_chart({'type': 'column'})
    chart8.add_series({
       'name':       ['Deal Call Months Upside Freq', 0, 1],
       'categories': ['Deal Call Months Upside Freq', 1, 0, max(dcm_unique), 0],
       'values':     ['Deal Call Months Upside Freq', 1, 1, max(dcm_unique), 1]
    })

    chart8.set_title ({'name': 'Deal Call Month Frequency'})
    chart8.set_x_axis({'name': 'Deal Call Month'})
    chart8.set_y_axis({'name': 'Frequency'})
    chart8.set_size({'width': 1700, 'height': 400})

    chart8.set_style(5)
    worksheet_su.insert_chart('F2', chart8)

    # --------------------------------- WEIGHTED AVERAGE COST OF FUNDS ------------------------------------ #
    worksheet_wa_cof = workbook.add_worksheet("WA Cost of Funds")

    bin_ranges = [round(x, 1) for x in np.linspace(3.7, 4.4, 11)]

    hist, bins = np.histogram(output_df['WA COF'].unique(), bins=bin_ranges)

    worksheet_wa_cof.write_column('A1', [f"[{bins[i]}-{bins[i+1]}]" for i in range(len(bins)-1)], bold)
    worksheet_wa_cof.write_column('B1', hist)
    chart9 = workbook.add_chart({'type': 'column'})

    chart9.add_series({
       'name':       'Frequency',
       'categories': ['WA Cost of Funds', 0, 0, len(hist)-2, 0],
       'values':     ['WA Cost of Funds', 0, 1, len(hist)-1, 1]
    })

    chart9.set_title ({'name': 'ALL WA Cost of Funds Frequency'})
    chart9.set_x_axis({'name': 'Weighted Average Cost of Fund'})
    chart9.set_y_axis({'name': 'Frequency'})
    chart9.set_x_axis({
       'name': 'Weighted Average Cost of Fund',
       'categories': ['WA Cost of Funds', 1, 0, len(hist)-1, 0],
       'num_format': '0.00'
    })
   
    chart9.set_style(6)
    chart9.set_size({'width': 600, 'height': 400})
    worksheet_wa_cof.insert_chart('E2', chart9)

    # --------------------------------- WEIGHTED AVERAGE COST OF FUNDS BASE ------------------------------------ #
    worksheet_wa_cofb = workbook.add_worksheet("WA Cost of Funds Base")

    bin_ranges = [round(x, 1) for x in np.linspace(3.7, 4.4, 11)]

    hist, bins = np.histogram(wa_cof_dict['base'], bins=bin_ranges)

    worksheet_wa_cofb.write_column('A1', [f"[{bins[i]}-{bins[i+1]}]" for i in range(len(bins)-1)], bold)
    worksheet_wa_cofb.write_column('B1', hist)
    chart10 = workbook.add_chart({'type': 'column'})

    chart10.add_series({
       'name':       'Frequency',
       'categories': ['WA Cost of Funds Base', 0, 0, len(hist)-2, 0],
       'values':     ['WA Cost of Funds Base', 0, 1, len(hist)-1, 1]
    })

    chart10.set_title ({'name': 'BASE  WA Cost of Funds Frequency'})
    chart10.set_x_axis({'name': 'Weighted Average Cost of Fund'})
    chart10.set_y_axis({'name': 'Frequency'})
    chart10.set_x_axis({
       'name': 'Weighted Average Cost of Fund',
       'categories': ['WA Cost of Funds', 1, 0, len(hist)-1, 0],
       'num_format': '0.00'
    })
   
    chart10.set_style(3)
    chart10.set_size({'width': 600, 'height': 400})
    worksheet_wa_cofb.insert_chart('E2', chart10)

    # --------------------------------- WEIGHTED AVERAGE COST OF FUNDS DOWNSIDE ------------------------------------ #
    worksheet_wa_cofd = workbook.add_worksheet("WA Cost of Funds Downside")

    bin_ranges = [round(x, 1) for x in np.linspace(3.7, 4.4, 11)]

    hist, bins = np.histogram(wa_cof_dict['downside'], bins=bin_ranges)

    worksheet_wa_cofd.write_column('A1', [f"[{bins[i]}-{bins[i+1]}]" for i in range(len(bins)-1)], bold)
    worksheet_wa_cofd.write_column('B1', hist)
    chart11 = workbook.add_chart({'type': 'column'})

    chart11.add_series({
       'name':       'Frequency',
       'categories': ['WA Cost of Funds Downside', 0, 0, len(hist)-2, 0],
       'values':     ['WA Cost of Funds Downside', 0, 1, len(hist)-1, 1]
    })

    chart11.set_title ({'name': 'DOWNSIDE WA Cost of Funds Frequency'})
    chart11.set_x_axis({'name': 'Weighted Average Cost of Fund'})
    chart11.set_y_axis({'name': 'Frequency'})
    chart11.set_x_axis({
       'name': 'Weighted Average Cost of Fund',
       'categories': ['WA Cost of Funds', 1, 0, len(hist)-1, 0],
       'num_format': '0.00'
    })
   
    chart11.set_style(4)
    chart11.set_size({'width': 600, 'height': 400})
    worksheet_wa_cofd.insert_chart('E2', chart11)

    # --------------------------------- WEIGHTED AVERAGE COST OF FUNDS UPSIDE ------------------------------------ #
    worksheet_wa_cofu = workbook.add_worksheet("WA Cost of Funds Upside")

    bin_ranges = [round(x, 1) for x in np.linspace(3.7, 4.4, 11)]

    hist, bins = np.histogram(wa_cof_dict['upside'], bins=bin_ranges)

    worksheet_wa_cofu.write_column('A1', [f"[{bins[i]}-{bins[i+1]}]" for i in range(len(bins)-1)], bold)
    worksheet_wa_cofu.write_column('B1', hist)
    chart12 = workbook.add_chart({'type': 'column'})

    chart12.add_series({
       'name':       'Frequency',
       'categories': ['WA Cost of Funds Upside', 0, 0, len(hist)-2, 0],
       'values':     ['WA Cost of Funds Upside', 0, 1, len(hist)-1, 1]
    })

    chart12.set_title ({'name': 'UPSIDE WA Cost of Funds Frequency'})
    chart12.set_x_axis({'name': 'Weighted Average Cost of Fund'})
    chart12.set_y_axis({'name': 'Frequency'})
    chart12.set_x_axis({
       'name': 'Weighted Average Cost of Fund',
       'categories': ['WA Cost of Funds', 1, 0, len(hist)-1, 0],
       'num_format': '0.00'
    })
   
    chart12.set_style(5)
    chart12.set_size({'width': 600, 'height': 400})
    worksheet_wa_cofu.insert_chart('E2', chart12)

    # -------------------------------- EQUITY YIELD ALL ------------------------------ #
    worksheet_ey = workbook.add_worksheet("Equity Yield")

    bin_ranges_eq = [round(x, 1) for x in np.linspace(8.5, 13, 9)]
    hist_eq, bins_eq = np.histogram(output_df['Projected Equity Yield'].unique(), bins=bin_ranges_eq)

    worksheet_ey.write_column('A1', [f"[{bins_eq[i]}-{bins_eq[i+1]}]" for i in range(len(bins_eq)-1)], bold)
    worksheet_ey.write_column('B1', hist_eq)
    chart13 = workbook.add_chart({'type': 'column'})

    chart13.add_series({
       'name':       'Frequency',
       'categories': ['Equity Yield', 0, 0, len(hist_eq)-2, 0],
       'values':     ['Equity Yield', 0, 1, len(hist_eq)-1, 1]
    })

    chart13.set_title ({'name': 'Equity Yield Frequency'})
    chart13.set_x_axis({'name': 'Equity Yield'})
    chart13.set_y_axis({'name': 'Frequency'})
    chart13.set_x_axis({
       'name': 'Equity Yield',
       'categories': ['Equity Yield', 1, 0, len(hist_eq)-2, 0],
       'num_format': '0.00'
    })
   
    chart13.set_style(1)
    chart13.set_size({'width': 600, 'height': 400})
    worksheet_ey.insert_chart('E2', chart13)

    # -------------------------------- EQUITY YIELD BASE------------------------------ #
    worksheet_eyb = workbook.add_worksheet("Equity Yield Base")

    bin_ranges_eq = [round(x, 1) for x in np.linspace(8.5, 13, 9)]
    hist_eq, bins_eq = np.histogram(equity_yield_dict['base'], bins=bin_ranges_eq)

    worksheet_eyb.write_column('A1', [f"[{bins_eq[i]}-{bins_eq[i+1]}]" for i in range(len(bins_eq)-1)], bold)
    worksheet_eyb.write_column('B1', hist_eq)
    chart14 = workbook.add_chart({'type': 'column'})

    chart14.add_series({
       'name':       'Frequency',
       'categories': ['Equity Yield Base', 0, 0, len(hist_eq)-2, 0],
       'values':     ['Equity Yield Base', 0, 1, len(hist_eq)-1, 1]
    })

    chart14.set_title ({'name': 'BASE Equity Yield Frequency'})
    chart14.set_x_axis({'name': 'Equity Yield'})
    chart14.set_y_axis({'name': 'Frequency'})
    chart14.set_x_axis({
       'name': 'Equity Yield',
       'categories': ['Equity Yield', 1, 0, len(hist_eq)-2, 0],
       'num_format': '0.00'
    })
   
    chart14.set_style(3)
    chart14.set_size({'width': 600, 'height': 400})
    worksheet_eyb.insert_chart('E2', chart14)

    # -------------------------------- EQUITY YIELD DOWNSIDE------------------------------ #
    worksheet_eyd = workbook.add_worksheet("Equity Yield Downside")

    bin_ranges_eq = [round(x, 1) for x in np.linspace(8.5, 13, 9)]
    hist_eq, bins_eq = np.histogram(equity_yield_dict['downside'], bins=bin_ranges_eq)

    worksheet_eyd.write_column('A1', [f"[{bins_eq[i]}-{bins_eq[i+1]}]" for i in range(len(bins_eq)-1)], bold)
    worksheet_eyd.write_column('B1', hist_eq)
    chart15 = workbook.add_chart({'type': 'column'})

    chart15.add_series({
       'name':       'Frequency',
       'categories': ['Equity Yield Downside', 0, 0, len(hist_eq)-2, 0],
       'values':     ['Equity Yield Downside', 0, 1, len(hist_eq)-1, 1]
    })

    chart15.set_title ({'name': 'DOWNSIDE Equity Yield Frequency'})
    chart15.set_x_axis({'name': 'Equity Yield'})
    chart15.set_y_axis({'name': 'Frequency'})
    chart15.set_x_axis({
       'name': 'Equity Yield',
       'categories': ['Equity Yield', 1, 0, len(hist_eq)-2, 0],
       'num_format': '0.00'
    })
   
    chart15.set_style(4)
    chart15.set_size({'width': 600, 'height': 400})
    worksheet_eyd.insert_chart('E2', chart15)

    # -------------------------------- EQUITY YIELD UPSIDE ------------------------------ #
    worksheet_eyu = workbook.add_worksheet("Equity Yield Upside")

    bin_ranges_eq = [round(x, 1) for x in np.linspace(8.5, 13, 9)]
    hist_eq, bins_eq = np.histogram(equity_yield_dict['upside'], bins=bin_ranges_eq)

    worksheet_eyu.write_column('A1', [f"[{bins_eq[i]}-{bins_eq[i+1]}]" for i in range(len(bins_eq)-1)], bold)
    worksheet_eyu.write_column('B1', hist_eq)
    chart16 = workbook.add_chart({'type': 'column'})

    chart16.add_series({
       'name':       'Frequency',
       'categories': ['Equity Yield Upside', 0, 0, len(hist_eq)-2, 0],
       'values':     ['Equity Yield Upside', 0, 1, len(hist_eq)-1, 1]
    })

    chart16.set_title ({'name': 'UPSIDE Equity Yield Frequency'})
    chart16.set_x_axis({'name': 'Equity Yield'})
    chart16.set_y_axis({'name': 'Frequency'})
    chart16.set_x_axis({
       'name': 'Equity Yield',
       'categories': ['Equity Yield', 1, 0, len(hist_eq)-2, 0],
       'num_format': '0.00'
    })
   
    chart16.set_style(5)
    chart16.set_size({'width': 600, 'height': 400})
    worksheet_eyu.insert_chart('E2', chart16)

    # -------------------------------- WA Adv Rate ALL ------------------------------ #
    worksheet_ar = workbook.add_worksheet("WA Adv Rate")

    bin_ranges_ar = np.linspace(0.83, 0.90, 10)
    hist_ar, bins_ar = np.histogram(output_df['WA Adv Rate'].unique(), bins=bin_ranges_ar)

    worksheet_ar.write_column('A1', [f"[{bins_ar[i]}-{bins_ar[i+1]}]" for i in range(len(bins_ar)-1)], bold)
    worksheet_ar.write_column('B1', hist_ar)
    chart17 = workbook.add_chart({'type': 'column'})

    chart17.add_series({
       'name':       'Frequency',
       'categories': ['WA Adv Rate', 0, 0, len(hist_ar)-2, 0],
       'values':     ['WA Adv Rate', 0, 1, len(hist_ar)-1, 1]
    })

    chart17.set_title ({'name': 'ALL WA Adv Rate Frequency'})
    chart17.set_x_axis({'name': 'WA Adv Rate'})
    chart17.set_y_axis({'name': 'Frequency'})
    chart17.set_x_axis({
       'name': 'WA Adv Rate',
       'categories': ['WA Adv Rate', 1, 0, len(hist_ar)-2, 0],
       'num_format': '0.00'
    })
   
    chart17.set_style(7)
    chart17.set_size({'width': 600, 'height': 400})
    worksheet_ar.insert_chart('E2', chart17)

    # -------------------------------- WA Adv Rate BASE ------------------------------ #
    worksheet_arb = workbook.add_worksheet("WA Adv Rate Base")

    bin_ranges_ar = np.linspace(0.83, 0.90, 10)
    hist_ar, bins_ar = np.histogram(adv_rate_dict['base'], bins=bin_ranges_ar)

    worksheet_arb.write_column('A1', [f"[{bins_ar[i]}-{bins_ar[i+1]}]" for i in range(len(bins_ar)-1)], bold)
    worksheet_arb.write_column('B1', hist_ar)
    chart18 = workbook.add_chart({'type': 'column'})

    chart18.add_series({
       'name':       'Frequency',
       'categories': ['WA Adv Rate Base', 0, 0, len(hist_ar)-2, 0],
       'values':     ['WA Adv Rate Base', 0, 1, len(hist_ar)-1, 1]
    })

    chart18.set_title ({'name': 'BASE WA Adv Rate Frequency'})
    chart18.set_x_axis({'name': 'WA Adv Rate'})
    chart18.set_y_axis({'name': 'Frequency'})
    chart18.set_x_axis({
       'name': 'WA Adv Rate',
       'categories': ['WA Adv Rate', 1, 0, len(hist_ar)-2, 0],
       'num_format': '0.00'
    })
   
    chart18.set_style(3)
    chart18.set_size({'width': 600, 'height': 400})
    worksheet_arb.insert_chart('E2', chart18)

    # -------------------------------- WA Adv Rate DOWNSIDE ------------------------------ #
    worksheet_ard = workbook.add_worksheet("WA Adv Rate Downside")

    bin_ranges_ar = np.linspace(0.83, 0.90, 10)
    hist_ar, bins_ar = np.histogram(adv_rate_dict['downside'], bins=bin_ranges_ar)

    worksheet_ard.write_column('A1', [f"[{bins_ar[i]}-{bins_ar[i+1]}]" for i in range(len(bins_ar)-1)], bold)
    worksheet_ard.write_column('B1', hist_ar)
    chart19 = workbook.add_chart({'type': 'column'})

    chart19.add_series({
       'name':       'Frequency',
       'categories': ['WA Adv Rate Downside', 0, 0, len(hist_ar)-2, 0],
       'values':     ['WA Adv Rate Downside', 0, 1, len(hist_ar)-1, 1]
    })

    chart19.set_title ({'name': 'DOWNSIDE WA Adv Rate Frequency'})
    chart19.set_x_axis({'name': 'WA Adv Rate'})
    chart19.set_y_axis({'name': 'Frequency'})
    chart19.set_x_axis({
       'name': 'WA Adv Rate',
       'categories': ['WA Adv Rate', 1, 0, len(hist_ar)-2, 0],
       'num_format': '0.00'
    })
   
    chart19.set_style(4)
    chart19.set_size({'width': 600, 'height': 400})
    worksheet_ard.insert_chart('E2', chart19)

    # -------------------------------- WA Adv Rate UPSIDE ------------------------------ #
    worksheet_aru = workbook.add_worksheet("WA Adv Rate Upside")

    bin_ranges_ar = np.linspace(0.83, 0.90, 10)
    hist_ar, bins_ar = np.histogram(adv_rate_dict['upside'], bins=bin_ranges_ar)

    worksheet_aru.write_column('A1', [f"[{bins_ar[i]}-{bins_ar[i+1]}]" for i in range(len(bins_ar)-1)], bold)
    worksheet_aru.write_column('B1', hist_ar)
    chart20 = workbook.add_chart({'type': 'column'})

    chart20.add_series({
       'name':       'Frequency',
       'categories': ['WA Adv Rate Upside', 0, 0, len(hist_ar)-2, 0],
       'values':     ['WA Adv Rate Upside', 0, 1, len(hist_ar)-1, 1]
    })

    chart20.set_title ({'name': 'UPSIDE WA Adv Rate Frequency'})
    chart20.set_x_axis({'name': 'WA Adv Rate'})
    chart20.set_y_axis({'name': 'Frequency'})
    chart20.set_x_axis({
       'name': 'WA Adv Rate',
       'categories': ['WA Adv Rate', 1, 0, len(hist_ar)-2, 0],
       'num_format': '0.00'
    })
   
    chart20.set_style(5)
    chart20.set_size({'width': 600, 'height': 400})
    worksheet_aru.insert_chart('E2', chart20)

    workbook.close()

