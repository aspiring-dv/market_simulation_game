class Product:

    def __init__(self, name, symbol, tick_size, initial_fair_value):

        self.name = name
        self.symbol = symbol
        self.tick_size = tick_size
        self.fair_value = initial_fair_value
        self.fair_value_history = [(0, initial_fair_value)]

    def get_fair_value(self):
        return self.fair_value

    def set_fair_value(self, new_value, time):
        self.fair_value = new_value
        self.fair_value_history.append((time, new_value))

    def is_valid_price(self, price):
        if price <= 0:
            return False
        x = price / self.tick_size
        return abs(x - round(x)) < 1e-9

    def round_price(self, price):
        return self.tick_size * round(price / self.tick_size)

    def get_fair_value_history(self):
        return self.fair_value_history