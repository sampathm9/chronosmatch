cdef class OrderBook:
    cdef dict bids
    cdef dict asks
    cdef long long trade_count
    cdef long long last_trade_price

    def __cinit__(self):
        self.bids = {}
        self.asks = {}
        self.trade_count = 0
        self.last_trade_price = 0

    cpdef list add(self, long long order_id, unsigned char side,
                   long long price, unsigned int quantity,
                   unsigned long long timestamp_ns):
        cdef list trades = []
        cdef unsigned int fill
        cdef object price_key
        cdef object queue
        cdef object resting
        cdef long long trade_price
        cdef unsigned int remaining = quantity

        if side == 1:
            while remaining > 0 and self.asks:
                price_key = min(self.asks.keys())
                if price_key > price:
                    break

                queue = self.asks[price_key]
                while remaining > 0 and queue:
                    resting = queue[0]
                    fill = remaining if remaining < resting[2] else resting[2]
                    trade_price = price_key
                    trades.append((resting[0], order_id, trade_price, fill))
                    self.trade_count += 1
                    self.last_trade_price = trade_price
                    remaining -= fill
                    resting[2] -= fill
                    if resting[2] == 0:
                        queue.pop(0)

                if not queue:
                    del self.asks[price_key]

            if remaining > 0:
                self.bids.setdefault(price, []).append(
                    [order_id, timestamp_ns, remaining]
                )

        elif side == 2:
            while remaining > 0 and self.bids:
                price_key = max(self.bids.keys())
                if price_key < price:
                    break

                queue = self.bids[price_key]
                while remaining > 0 and queue:
                    resting = queue[0]
                    fill = remaining if remaining < resting[2] else resting[2]
                    trade_price = price_key
                    trades.append((resting[0], order_id, trade_price, fill))
                    self.trade_count += 1
                    self.last_trade_price = trade_price
                    remaining -= fill
                    resting[2] -= fill
                    if resting[2] == 0:
                        queue.pop(0)

                if not queue:
                    del self.bids[price_key]

            if remaining > 0:
                self.asks.setdefault(price, []).append(
                    [order_id, timestamp_ns, remaining]
                )

        return trades

    cpdef tuple top(self):
        cdef object bid = max(self.bids.keys()) if self.bids else None
        cdef object ask = min(self.asks.keys()) if self.asks else None
        return bid, ask, self.trade_count, self.last_trade_price
