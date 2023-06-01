# ------------------------ VARIOUS TRANCHE OPERATIONS ------------------------ #
class Tranche:
    def __init__(self, name, rating, size, spread, offered, price):
        self.__name = name
        self.__rating = rating
        self.__size = size
        self.__spread = spread
        self.__offered = offered
        self.__price = price

    def get_name(self):
        return self.__get_name
    
    def get_rating(self):
        return self.__rating

    def get_size(self):
        return self.__size

    def get_spread(self):
        return self.__spread

    def get_offered(self):
        return self.__offered

    def get_price(self):
        return self.__price

    def update_size(self, value):
        d=""
      # formulas

row_index = 1
tranche_instances = []

while True:
    tranche_data = df.loc[row_index, ['Rating', 'Offered', 'Size', 'Spread (bps)', 'Price']]

    if tranche_data.empty:
        break

tranche_instance = Tranche(
    tranche_data['Rating'],
    tranche_data['Size'],
    tranche_data['Spread (bps)'],
    tranche_data['Offered'],
    tranche_data['Price']
)

tranche_instances.append(tranche_instance)

row_index =+ 1