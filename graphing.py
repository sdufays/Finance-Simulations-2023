import pandas as pd
import numpy_financial as npf
import math
import numpy as np
import xlsxwriter
from collections import Counter

def create_dcm_chart(workbook, worksheet_name, data, chart_title, chart_style):
   worksheet = workbook.add_worksheet(worksheet_name)
   bold = workbook.add_format({'bold': 1})
   headings = ['Deal Call Months']

   bin_ranges = [round(x, 0) for x in np.linspace(23, 38, 12)]
   hist, bins = np.histogram(data, bins=bin_ranges)

   worksheet.write_row('A1', headings, bold)
   worksheet.write_column('A1', [f"[{bins[i]}-{bins[i+1]}]" for i in range(len(bins)-1)], bold)
   worksheet.write_column('B1', hist)

   chart = workbook.add_chart({'type': 'column'})
   chart.add_series({
      'name': 'Frequency',
      'categories': [worksheet_name, 0, 0, len(hist)-2, 0],
      'values': [worksheet_name, 0, 1, len(hist)-1, 1]
   })

   chart.set_title({'name': chart_title})
   chart.set_x_axis({'name': 'Deal Call Month'})
   chart.set_x_axis({
      'name': 'Weighted Average Cost of Fund',
      'categories': [worksheet_name, 1, 0, len(hist)-1, 0],
      'num_format': '0'
   })
   chart.set_y_axis({'name': 'Frequency'})
   chart.set_size({'width': 600, 'height': 400})
   chart.set_style(chart_style)

   worksheet.insert_chart('E2', chart)

def create_wa_cof_chart(workbook, worksheet_name, data, title, chart_style):
   worksheet = workbook.add_worksheet(worksheet_name)
   bold = workbook.add_format({'bold': 1})
   
   bin_ranges = [round(x, 1) for x in np.linspace(3.7, 4.4, 11)]
   hist, bins = np.histogram(data, bins=bin_ranges)
   
   worksheet.write_column('A1', [f"[{bins[i]}-{bins[i+1]}]" for i in range(len(bins)-1)], bold)
   worksheet.write_column('B1', hist)
   
   chart = workbook.add_chart({'type': 'column'})
   chart.add_series({
      'name': 'Frequency',
      'categories': [worksheet_name, 0, 0, len(hist)-2, 0],
      'values': [worksheet_name, 0, 1, len(hist)-1, 1]
   })
   
   chart.set_title({'name': title})
   chart.set_x_axis({'name': 'Weighted Average Cost of Fund'})
   chart.set_y_axis({'name': 'Frequency'})
   chart.set_x_axis({
      'name': 'Weighted Average Cost of Fund',
      'categories': [worksheet_name, 1, 0, len(hist)-1, 0],
      'num_format': '0.00',
      'num_font': {'rotation': -45}
   })
   
   chart.set_style(chart_style)
   chart.set_size({'width': 600, 'height': 400})
   worksheet.insert_chart('E2', chart)

def create_equity_yield_graph(workbook, worksheet_name, data, chart_title, chart_style):
   bold = workbook.add_format({'bold': True})
   worksheet = workbook.add_worksheet(worksheet_name)

   bin_ranges_eq = [round(x, 1) for x in np.linspace(8.5, 13, 9)]
   hist_eq, bins_eq = np.histogram(data, bins=bin_ranges_eq)

   worksheet.write_column('A1', [f"[{bins_eq[i]}-{bins_eq[i+1]}]" for i in range(len(bins_eq)-1)], bold)
   worksheet.write_column('B1', hist_eq)

   chart = workbook.add_chart({'type': 'column'})

   chart.add_series({
      'name':       'Frequency',
      'categories': [worksheet_name, 0, 0, len(hist_eq)-2, 0],
      'values':     [worksheet_name, 0, 1, len(hist_eq)-1, 1]
   })

   chart.set_title({'name': chart_title})
   chart.set_x_axis({'name': 'Equity Yield'})
   chart.set_y_axis({'name': 'Frequency'})
   chart.set_x_axis({
      'name': 'Equity Yield',
      'categories': [worksheet_name, 1, 0, len(hist_eq)-2, 0],
      'num_format': '0.00',
      'num_font': {'rotation': -45}
   })

   chart.set_style(chart_style)
   chart.set_size({'width': 600, 'height': 400})
   worksheet.insert_chart('E2', chart)

def create_waar_graph(workbook, sheet_name, data, chart_title, chart_style):
   bold = workbook.add_format({'bold': True})
   worksheet = workbook.add_worksheet(sheet_name)

   bin_ranges = [round(x, 4) for x in np.linspace(0.83, 0.90, 10)]
   hist, bins = np.histogram(data, bins=bin_ranges)

   worksheet.write_column('A1', [f"[{bins[i]}-{bins[i+1]}]" for i in range(len(bins)-1)], bold)
   worksheet.write_column('B1', hist)
   chart = workbook.add_chart({'type': 'column'})

   chart.add_series({
      'name': 'Frequency',
      'categories': [sheet_name, 0, 0, len(hist)-2, 0],
      'values': [sheet_name, 0, 1, len(hist)-1, 1]
   })

   chart.set_title({'name': chart_title})
   chart.set_x_axis({'name': 'WA Adv Rate'})
   chart.set_y_axis({'name': 'Frequency'})
   chart.set_x_axis({
      'name': 'WA Adv Rate',
      'categories': [sheet_name, 1, 0, len(hist)-2, 0],
      'num_format': '0.00',
      'num_font': {'rotation': -45}
   })

   chart.set_style(chart_style)
   chart.set_size({'width': 600, 'height': 400})
   worksheet.insert_chart('E2', chart)

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

    # Set an Excel chart style.
    # 1 - grey / 2 - blue, red / 3 - blues / 4 - reds / 5  - greens / 6 - purples 
    # 7 - like a light blueish green / 8 - oranges / 9 - ew / 10 - blue, orangey red

    # ------------------------------- SWAPPED --------------------------------- #
    create_dcm_chart(workbook, "Deal Call Months", output_df['Deal Call Month'].unique(), "ALL Deal Call Months Frequency", 7)
    create_dcm_chart(workbook, "Deal Call Months Base", deal_call_months_dict['base'], "BASE Deal Call Months Frequency", 3)
    create_dcm_chart(workbook, "Deal Call Months Downside", deal_call_months_dict['downside'], "DOWNSIDE Deal Call Months Frequency", 4)
    create_dcm_chart(workbook, "Deal Call Months Upside", deal_call_months_dict['upside'], "UPSIDE Deal Call Months Frequency", 5)
    # --------------------------------- WEIGHTED AVERAGE COST OF FUNDS ------------------------------------ #
    create_wa_cof_chart(workbook, "WA Cost of Funds", output_df['WA COF'].unique(), "ALL WA Cost of Funds Frequency", 7)
    create_wa_cof_chart(workbook, "WA Cost of Funds Base", wa_cof_dict['base'], "BASE WA Cost of Funds Frequency", 3)
    create_wa_cof_chart(workbook, "WA Cost of Funds Downside", wa_cof_dict['downside'], "DOWNSIDE WA Cost of Funds Frequency", 4)
    create_wa_cof_chart(workbook, "WA Cost of Funds Upside", wa_cof_dict['upside'], "UPSIDE WA Cost of Funds Frequency", 5)
    # --------------------------------- PROJECTED EQUITY YIELD ------------------------------------ #
    create_equity_yield_graph(workbook, "Proj Equity Yield", output_df['Projected Equity Yield'].unique(), "ALL Hypothetical Equity Yield Frequency", 7)
    create_equity_yield_graph(workbook, "Proj Equity Yield Base", equity_yield_dict['base'], "BASE Hypothetical Equity Yield Frequency", 3)
    create_equity_yield_graph(workbook, "Proj Equity Yield Downside", equity_yield_dict['downside'], "DOWNSIDE Hypothetical Equity Yield Frequency", 4)
    create_equity_yield_graph(workbook, "Proj Equity Yield Upside", equity_yield_dict['upside'], "UPSIDE Hypothetical Equity Yield Frequency", 5)
    # -------------------------------- WA ADVANCE RATE  ------------------------------ #
    create_waar_graph(workbook, "WA Adv Rate", output_df['WA Adv Rate'].unique(), "ALL WA Adv Rate Frequency", 7)
    create_waar_graph(workbook, "WA Adv Rate Base", adv_rate_dict['base'], "BASE WA Adv Rate Frequency", 3)
    create_waar_graph(workbook, "WA Adv Rate Downside", adv_rate_dict['downside'], "DOWNSIDE WA Adv Rate Frequency", 4)
    create_waar_graph(workbook, "WA Adv Rate Upside", adv_rate_dict['upside'], "UPSIDE WA Adv Rate Frequency", 5)
    # -------------------------------- CLOSE WORKBOOK  ------------------------------ #
    workbook.close()