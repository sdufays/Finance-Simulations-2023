import pandas as pd
import numpy_financial as npf
import math
import numpy as np
import xlsxwriter

def create_dcm_chart(workbook, worksheet_name, data, chart_title, chart_style):
   worksheet = workbook.add_worksheet(worksheet_name)
   bold = workbook.add_format({'bold': 1})
   headings = ['Deal Call Months']

   bin_ranges = [round(x, 0) for x in np.linspace(min(data)-1, max(data)+1, 15)]
   hist, bins = np.histogram(data, bins=bin_ranges)

   worksheet.write_row('A1', headings, bold)
   worksheet.write_column('A1', [f"[{bins[i]}-{bins[i+1]}]" for i in range(len(bins)-1)], bold)
   worksheet.write_column('B1', hist)

   chart = workbook.add_chart({'type': 'column'})
   chart.add_series({
      'name': 'Frequency',
      'categories': [worksheet_name, 0, 0, len(hist), 0],
      'values': [worksheet_name, 0, 1, len(hist), 1]
   })

   chart.set_title({'name': chart_title})
   chart.set_x_axis({
      'name': 'Deal Call Months',
      'num_format': '0',
      'min_value': min(data) - 2,
      'max_value': max(data) + 2
   })
   chart.set_y_axis({'name': 'Frequency'})
   chart.set_size({'width': 600, 'height': 400})
   chart.set_style(chart_style)

   worksheet.insert_chart('E2', chart)

def create_wa_cof_chart(workbook, worksheet_name, data, title, chart_style):
   worksheet = workbook.add_worksheet(worksheet_name)
   bold = workbook.add_format({'bold': 1})
   
   bin_ranges = [round(x, 4) for x in np.linspace(min(data)-0.01, max(data)+0.01, 15)]
   hist, bins = np.histogram(data, bins=bin_ranges)
   
   worksheet.write_column('A1', [f"[{bins[i]}-{bins[i+1]}]" for i in range(len(bins)-1)], bold)
   worksheet.write_column('B1', hist)
   
   chart = workbook.add_chart({'type': 'column'})
   chart.add_series({
      'name': 'Frequency',
      'categories': [worksheet_name, 0, 0, len(hist), 0],
      'values': [worksheet_name, 0, 1, len(hist), 1]
   })
   
   chart.set_title({'name': title})
   chart.set_y_axis({'name': 'Frequency'})
   chart.set_x_axis({
      'name': 'Weighted Average Cost of Fund',
      'num_format': '0.00',
      'num_font': {'rotation': -45},
      'min_value': min(data) - 1.5,
      'max_value': max(data) + 1.5
   })
   
   chart.set_style(chart_style)
   chart.set_size({'width': 600, 'height': 400})
   worksheet.insert_chart('E2', chart)

def create_equity_yield_graph(workbook, worksheet_name, data, chart_title, chart_style):
   bold = workbook.add_format({'bold': True})
   worksheet = workbook.add_worksheet(worksheet_name)

   bin_ranges_eq = [round(x, 3) for x in np.linspace(min(data)-0.05, max(data)+0.05, 15)]
   hist_eq, bins_eq = np.histogram(data, bins=bin_ranges_eq)

   worksheet.write_column('A1', [f"[{bins_eq[i]}-{bins_eq[i+1]}]" for i in range(len(bins_eq)-1)], bold)
   worksheet.write_column('B1', hist_eq)

   chart = workbook.add_chart({'type': 'column'})

   chart.add_series({
      'name': 'Frequency',
      'categories': [worksheet_name, 0, 0, len(hist_eq), 0],
      'values':     [worksheet_name, 0, 1, len(hist_eq), 1]
   })

   chart.set_title({'name': chart_title})
   chart.set_y_axis({'name': 'Frequency'})
   chart.set_x_axis({
      'name': 'Equity Yield',
      'num_format': '0.00',
      'num_font': {'rotation': -45},
      'min_value': min(data) - 2,
      'max_value': max(data) + 2
   })

   chart.set_style(chart_style)
   chart.set_size({'width': 600, 'height': 400})
   worksheet.insert_chart('E2', chart)

def create_waar_graph(workbook, worksheet_name, data, chart_title, chart_style):
   bold = workbook.add_format({'bold': True})
   worksheet = workbook.add_worksheet(worksheet_name)

   bin_ranges = [round(x, 4) for x in np.linspace(min(data)-0.0001, max(data)+0.0001, 15)]
   hist, bins = np.histogram(data, bins=bin_ranges)

   worksheet.write_column('A1', [f"[{bins[i]}-{bins[i+1]}]" for i in range(len(bins)-1)], bold)
   worksheet.write_column('B1', hist)
   chart = workbook.add_chart({'type': 'column'})

   chart.add_series({
      'name': 'Frequency',
      'categories': [worksheet_name, 0, 0, len(hist), 0],
      'values': [worksheet_name, 0, 1, len(hist), 1]
   })

   chart.set_title({'name': chart_title})
   chart.set_y_axis({'name': 'Frequency'})
   chart.set_x_axis({
      'name': 'WA Adv Rate',
      'num_format': '0.00',
      'num_font': {'rotation': -45},
      'min_value': min(data) - 0.2,
      'max_value': max(data) + 0.2
   })

   chart.set_style(chart_style)
   chart.set_size({'width': 600, 'height': 400})
   worksheet.insert_chart('E2', chart)

def graphs(output_df, cases, trial_numbers):
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

   # ------------------------- GRAPHING OUTPUTS -------------------------- #
    workbook = xlsxwriter.Workbook('graphs.xlsx')

    # Set an Excel chart style.
    # 1 - grey / 2 - blue, red / 3 - blues / 4 - reds / 5  - greens / 6 - purples 
    # 7 - like a light blueish green / 8 - oranges / 9 - ew / 10 - blue, orangey red

    # ------------------------------- SWAPPED --------------------------------- #
    create_dcm_chart(workbook, "Deal Call Months", output_df['Deal Call Month'], "ALL Deal Call Months Frequency", 7)
    create_dcm_chart(workbook, "Deal Call Months Base", deal_call_months_dict['base'], "BASE Deal Call Months Frequency", 3)
    create_dcm_chart(workbook, "Deal Call Months Downside", deal_call_months_dict['downside'], "DOWNSIDE Deal Call Months Frequency", 4)
    create_dcm_chart(workbook, "Deal Call Months Upside", deal_call_months_dict['upside'], "UPSIDE Deal Call Months Frequency", 5)
    # --------------------------------- WEIGHTED AVERAGE COST OF FUNDS ------------------------------------ #
    create_wa_cof_chart(workbook, "WA Cost of Funds", output_df['WA COF'], "ALL WA Cost of Funds Frequency", 7)
    create_wa_cof_chart(workbook, "WA Cost of Funds Base", wa_cof_dict['base'], "BASE WA Cost of Funds Frequency", 3)
    create_wa_cof_chart(workbook, "WA Cost of Funds Downside", wa_cof_dict['downside'], "DOWNSIDE WA Cost of Funds Frequency", 4)
    create_wa_cof_chart(workbook, "WA Cost of Funds Upside", wa_cof_dict['upside'], "UPSIDE WA Cost of Funds Frequency", 5)
    # --------------------------------- PROJECTED EQUITY YIELD ------------------------------------ #
    create_equity_yield_graph(workbook, "Proj Equity Yield", output_df['Projected Equity Yield'], "ALL Hypothetical Equity Yield Frequency", 7)
    create_equity_yield_graph(workbook, "Proj Equity Yield Base", equity_yield_dict['base'], "BASE Hypothetical Equity Yield Frequency", 3)
    create_equity_yield_graph(workbook, "Proj Equity Yield Downside", equity_yield_dict['downside'], "DOWNSIDE Hypothetical Equity Yield Frequency", 4)
    create_equity_yield_graph(workbook, "Proj Equity Yield Upside", equity_yield_dict['upside'], "UPSIDE Hypothetical Equity Yield Frequency", 5)
    # -------------------------------- WA ADVANCE RATE  ------------------------------ #
    create_waar_graph(workbook, "WA Adv Rate", output_df['WA Adv Rate'], "ALL WA Adv Rate Frequency", 7)
    create_waar_graph(workbook, "WA Adv Rate Base", adv_rate_dict['base'], "BASE WA Adv Rate Frequency", 3)
    create_waar_graph(workbook, "WA Adv Rate Downside", adv_rate_dict['downside'], "DOWNSIDE WA Adv Rate Frequency", 4)
    create_waar_graph(workbook, "WA Adv Rate Upside", adv_rate_dict['upside'], "UPSIDE WA Adv Rate Frequency", 5)
    # -------------------------------- CLOSE WORKBOOK  ------------------------------ #
    workbook.close()