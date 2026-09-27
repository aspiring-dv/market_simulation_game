import heapq

class Exchange:

    def __init__(self, products):

        self.next_order_id = 0
        self.products = products
        self.time = 0

        self.bid = {product: [] for product in products}
        self.ask = {product: [] for product in products}
        self.orders = {product: {} for product in products}

        self.trades = {product: [] for product in products}
        self.snapshots = {product: [] for product in products}

    def _execute_order(self, product, order_id, side, price, qty, version):

        bid = self.bid[product]
        ask = self.ask[product]
        orders = self.orders[product]

        new_trades = []

        if side == "B":

            while ask and qty > 0:

                pa, ta, oa, va = ask[0]

                if oa not in orders:
                    heapq.heappop(ask)
                    continue

                _, _, _, qa, v = orders[oa]

                if va != v:
                    heapq.heappop(ask)
                    continue

                if pa > price:
                    break

                heapq.heappop(ask)

                traded_qty = min(qty, qa)
                trade = (order_id, oa, pa, traded_qty)

                self.trades[product].append(trade)
                new_trades.append(trade)

                if qty >= qa:
                    qty -= qa
                    del orders[oa]

                else:
                    orders[oa][3] = qa - qty
                    qty = 0
                    heapq.heappush(ask, (pa, ta, oa, va))

            if qty > 0:
                heapq.heappush(bid, (-price, self.time, order_id, version))
                orders[order_id] = ["B", self.time, price, qty, version]


        elif side == "S":

            while bid and qty > 0:

                pb, tb, ob, vb = bid[0]
                pb = -pb

                if ob not in orders:
                    heapq.heappop(bid)
                    continue

                _, _, _, qb, v = orders[ob]

                if vb != v:
                    heapq.heappop(bid)
                    continue

                if pb < price:
                    break

                heapq.heappop(bid)

                traded_qty = min(qty, qb)
                trade = (ob, order_id, pb, traded_qty)

                self.trades[product].append(trade)
                new_trades.append(trade)

                if qty >= qb:
                    qty -= qb
                    del orders[ob]

                else:
                    orders[ob][3] = qb - qty
                    qty = 0
                    heapq.heappush(bid, (-pb, tb, ob, vb))

            if qty > 0:
                heapq.heappush(ask, (price, self.time, order_id, version))
                orders[order_id] = ["S", self.time, price, qty, version]

        return new_trades

    def add_order(self, product, side, price, qty):
        order_id = self.next_order_id
        self.next_order_id += 1

        self.time += 1
        version = self.time

        trades = self._execute_order(product, order_id, side, price, qty, version)
        self.record_snapshot(product)

        return order_id , trades

    def cancel(self, product, order_id):

        self.time += 1
        orders = self.orders[product]

        if order_id in orders:
            del orders[order_id]

        self.record_snapshot(product)

    def modify(self, product, order_id, new_price, new_qty):

        self.time += 1
        orders = self.orders[product]

        if order_id not in orders:
            self.record_snapshot(product)
            return []

        if new_qty <= 0:
            del orders[order_id]
            self.record_snapshot(product)
            return []

        side, t, price, qty, version = orders[order_id]

        # Same price + quantity decreases -> keep priority
        if new_price == price and new_qty <= qty:
            orders[order_id] = [side, t, price, new_qty, version]
            self.record_snapshot(product)
            return []

        # Otherwise lose priority and behave like a new incoming order
        del orders[order_id]

        version = self.time
        trades = self._execute_order(product, order_id, side, new_price, new_qty, version)

        self.record_snapshot(product)

        return trades

    def record_snapshot(self, product):

        bid = self.bid[product]
        ask = self.ask[product]
        orders = self.orders[product]

        while ask:
            pa, ta, oa, va = ask[0]

            if oa not in orders or orders[oa][4] != va:
                heapq.heappop(ask)
            else:
                break

        if ask:
            best_ask = ask[0][0]
            ask_qty = sum(qty for side, t, price, qty, v in orders.values() if side == "S" and price == best_ask)
        else:
            best_ask = None
            ask_qty = None


        while bid:
            pb, tb, ob, vb = bid[0]

            if ob not in orders or orders[ob][4] != vb:
                heapq.heappop(bid)
            else:
                break

        if bid:
            best_bid = -bid[0][0]
            bid_qty = sum(qty for side, t, price, qty, v in orders.values() if side == "B" and price == best_bid)
        else:
            best_bid = None
            bid_qty = None


        if best_bid is None or best_ask is None:
            spread = None
        else:
            spread = best_ask - best_bid

        snapshot = (best_bid, bid_qty, best_ask, ask_qty, spread)

        self.snapshots[product].append(snapshot)

        return snapshot

    def get_snapshot(self, product):

        if not self.snapshots[product]:
            return None

        return self.snapshots[product][-1]