def get_date_array(starting_date):
    date = starting_date.split("/")
    # ["MM", "DD", "YYYY"]
    date = list(map(int,date))
    # [MM, DD, YYYY]
    if date[2] % 4 == 0:
      return [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    else: 
      return [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    
print(get_date_array("01/02/2003"))