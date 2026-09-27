class Bot:

    def __init__(self, name, initial_cash, products):

        self.name = name

        self._initial_cash = initial_cash
        self._cash = initial_cash
        self._inventory = {symbol: 0 for symbol in products}

        self._active_orders = set()

        self._market_pnl = 0
        self._market_pnl_history = [(0, 0)]

        self._true_pnl = 0
        self._true_pnl_history = [(0, 0)]

        self._last_market_price = {symbol: None for symbol in products}

    def get_cash(self):
        return self._cash

    def get_position(self, product):
        return self._inventory[product]

    def get_inventory(self):
        return self._inventory.copy()

    def get_active_orders(self):
        return self._active_orders.copy()

    def place_order(self, exchange, product, side, price, qty):

        # Exchange creates the ID and performs immediate matching
        order_id, trades = exchange.add_order(product, side, price, qty)

        # Add it before processing trades so immediate fills are recognized
        self._active_orders.add(order_id)

        self.process_trades(exchange, product, trades)

        return order_id

    def cancel_order(self, exchange, product, order_id):

        # Bot can only cancel one of its own orders
        if order_id not in self._active_orders:
            return

        exchange.cancel(product, order_id)
        self._active_orders.discard(order_id)

    def modify_order(self, exchange, product, order_id, new_price, new_qty):

        if order_id not in self._active_orders:
            return []

        # MODIFY may generate immediate trades
        trades = exchange.modify(product, order_id, new_price, new_qty)

        self.process_trades(exchange, product, trades)

        # If the modified order disappeared, it was cancelled or fully filled
        if exchange.get_order(order_id) is None:
            self._active_orders.discard(order_id)

        return trades

    def process_trades(self, exchange, product, trades):

        for buy_id, sell_id, price, qty in trades:

            # Trade price is public information
            self._last_market_price[product] = price

            if buy_id in self._active_orders:
                self._inventory[product] += qty
                self._cash -= price * qty

            if sell_id in self._active_orders:
                self._inventory[product] -= qty
                self._cash += price * qty

        # Remove orders that are no longer active on the Exchange
        for order_id in list(self._active_orders):
            if exchange.get_order(order_id) is None:
                self._active_orders.discard(order_id)

    def update_pnl(self, exchange, time):

        current_wealth = self._cash

        for symbol, qty in self._inventory.items():

            # No position -> valuation of that product is irrelevant
            if qty == 0:
                continue

            snapshot = exchange.get_snapshot(symbol)
            price = None

            if snapshot is not None:
                best_bid, bid_qty, best_ask, ask_qty, spread = snapshot

                # Mid-price uses only public market information
                if best_bid is not None and best_ask is not None:
                    price = (best_bid + best_ask) / 2

            # If no mid exists, use the latest public trade price we observed
            if price is None:
                price = self._last_market_price[symbol]

            # In normal play, a bot cannot have inventory without having traded,
            # so there should normally be a last market price available.
            if price is not None:
                current_wealth += qty * price

        self._market_pnl = current_wealth - self._initial_cash
        self._market_pnl_history.append((time, self._market_pnl))

    def get_pnl(self):
        # This is the PnL the bot/player is allowed to see
        return self._market_pnl

    def get_pnl_history(self):
        return self._market_pnl_history.copy()

    def _update_true_pnl(self, products, time):

        # INTERNAL SIMULATION METHOD.
        # Strategies should never use this because it contains hidden information.
        current_wealth = self._cash

        for symbol, qty in self._inventory.items():
            true_value = products[symbol].get_fair_value()
            current_wealth += qty * true_value

        self._true_pnl = current_wealth - self._initial_cash
        self._true_pnl_history.append((time, self._true_pnl))

    def _get_true_pnl(self):
        # Internal evaluation only
        return self._true_pnl

    def observe(self, market_state):
        # Subclasses will use this to process information they are allowed to see
        pass

    def decide(self, exchange, market_state):
        # Subclasses implement their trading strategy here
        pass