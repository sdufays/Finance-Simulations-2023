import xlsxwriter

workbook = xlsxwriter.Workbook('chart_scatter.xlsx')

worksheet = workbook.add_worksheet()

bold = workbook.add_format({'bold': 1})

headings = ['Number of Sims', 'Deal Call Months']

"""
for scenario in scenarios:
      # chnage 10 to number of simulation runs per scenario 
      # i think 10 needs to be made into a variable so that whatever number is in that variable 
      # can be inputed into the data list below
      for _ in range(10):
          run_simulation(scenario)"""
   
num_of_runs = 10

data = [
    list(range(1, num_of_runs + 1)), # this is my x-axis
    [80, 80, 100, 60, 50, 100], # this is one batch of data aka the y-axis
    # i need this one to be deal call months which is in main
    # does that mean this code should go in sim test?
    # yes
    # TODO: integrate this into sim test
]

worksheet.write_row('A1', headings, bold)
   
# Write a column of data starting from 
# 'A2', 'B2', 'C2' respectively .
worksheet.write_column('A2', data[0])
worksheet.write_column('B2', data[1])

# here we create a scatter chart object .
chart1 = workbook.add_chart({'type': 'scatter'})

chart1.add_series({
    'name':       ['Deal Call Months', 0, 1],
    'categories': ['Deal Call Months', 1, 0, 6, 0], # x axis values placement ['Sheet name', first_row, first_column, last_row, last_column]
    'values':     ['Deal Call Months', 1, 1, 6, 1], # y axis values placement ['Sheet name', first_row, first_column, last_row, last_column]
})

# Add a chart title 
chart1.set_title ({'name': 'Results of CLO Simulation'})
   
# Add x-axis label
chart1.set_x_axis({'name': 'Sim Number'})
   
# Add y-axis label
chart1.set_y_axis({'name': 'Deal Call Month'})
   
# Set an Excel chart style.
# 1 - grey
# 2 - blue, red
# 3 - blues
# 4 - reds
# 5 - greens
# 6 - purples
# 7 - like a light blueish green
# 8 - oranges
# 9 - ew
# 10 - blue, orangey red
chart1.set_style(6)

# add chart to the worksheet 
# the top-left corner of a chart 
# is anchored to cell E2 . 
worksheet.insert_chart('E2', chart1)

# TODO: i need a summary kind of thing to go near
# so user can specify month they are looking for the deal to be called
# and then it prints how many times it was called as well as shows it in the graph
   
# Finally, close the Excel file 
# via the close() method. 
workbook.close()