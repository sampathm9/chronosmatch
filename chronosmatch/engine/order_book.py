class OrderNode:
    """A single resting order in the order book."""

    __slots__ = (
        "order_id",
        "timestamp_ns",
        "quantity",
        "price",
    )

    def __init__(
        self,
        order_id,
        timestamp_ns,
        price,
        quantity,
    ):
        self.order_id = order_id
        self.timestamp_ns = timestamp_ns
        self.price = price
        self.quantity = quantity


class PriceLevel:
    """All resting orders at one price."""

    __slots__ = (
        "price",
        "orders",
    )

    def __init__(self, price):
        self.price = price
        self.orders = []


class OrderBook:
    """
    Pure-Python implementation of the ChronosMatch OrderBook.

    Side:
        1 = BUY
        2 = SELL

    add() returns:
        [
            (
                resting_order_id,
                incoming_order_id,
                trade_price,
                fill_quantity
            ),
            ...
        ]

    top() returns:
        (
            best_bid,
            best_ask,
            trade_count,
            last_trade_price
        )
    """

    def __init__(self):
        # Price levels are maintained in sorted order.
        #
        # bids: highest price first
        # asks: lowest price first
        self.bids = []
        self.asks = []

        self.trade_count = 0
        self.last_trade_price = 0

    def _find_level(self, side, price):
        """Find a price level on the specified side."""

        levels = self.bids if side == 1 else self.asks

        for level in levels:
            if level.price == price:
                return level

        return None

    def _create_level(self, price):
        return PriceLevel(price)

    def _append_order(
        self,
        level,
        order_id,
        timestamp_ns,
        price,
        quantity,
    ):
        """
        Append an order to the end of a price level.

        This preserves FIFO time priority.
        """

        order = OrderNode(
            order_id=order_id,
            timestamp_ns=timestamp_ns,
            price=price,
            quantity=quantity,
        )

        level.orders.append(order)

    def _insert_bid(
        self,
        order_id,
        timestamp_ns,
        price,
        quantity,
    ):
        """Insert a resting BUY order at the correct price level."""

        level = self._find_level(1, price)

        if level is not None:
            self._append_order(
                level,
                order_id,
                timestamp_ns,
                price,
                quantity,
            )
            return

        level = self._create_level(price)

        # Highest bid first.
        index = 0

        while index < len(self.bids):
            if self.bids[index].price < price:
                break

            index += 1

        self.bids.insert(index, level)

        self._append_order(
            level,
            order_id,
            timestamp_ns,
            price,
            quantity,
        )

    def _insert_ask(
        self,
        order_id,
        timestamp_ns,
        price,
        quantity,
    ):
        """Insert a resting SELL order at the correct price level."""

        level = self._find_level(2, price)

        if level is not None:
            self._append_order(
                level,
                order_id,
                timestamp_ns,
                price,
                quantity,
            )
            return

        level = self._create_level(price)

        # Lowest ask first.
        index = 0

        while index < len(self.asks):
            if self.asks[index].price > price:
                break

            index += 1

        self.asks.insert(index, level)

        self._append_order(
            level,
            order_id,
            timestamp_ns,
            price,
            quantity,
        )

    def _remove_bid_level(self):
        """Remove the best bid price level."""

        if not self.bids:
            return

        self.bids.pop(0)

    def _remove_ask_level(self):
        """Remove the best ask price level."""

        if not self.asks:
            return

        self.asks.pop(0)

    def add(
        self,
        order_id,
        side,
        price,
        quantity,
        timestamp_ns,
    ):
        """
        Add an order and immediately match it against resting liquidity.

        side:
            1 = BUY
            2 = SELL

        Returns:
            Python list of trades.
        """

        remaining = quantity
        trades = []

        # ---------------------------------------------------------
        # BUY
        # ---------------------------------------------------------

        if side == 1:

            while (
                remaining > 0
                and self.asks
                and price >= self.asks[0].price
            ):
                level = self.asks[0]

                # FIFO: always match the oldest order first.
                resting = level.orders[0]

                trade_price = resting.price

                if remaining < resting.quantity:
                    fill = remaining
                else:
                    fill = resting.quantity

                trades.append(
                    (
                        resting.order_id,
                        order_id,
                        trade_price,
                        fill,
                    )
                )

                self.trade_count += 1
                self.last_trade_price = trade_price

                remaining -= fill
                resting.quantity -= fill

                # Resting order completely filled.
                if resting.quantity == 0:

                    level.orders.pop(0)

                    if not level.orders:
                        self._remove_ask_level()

            # Unfilled BUY quantity becomes resting liquidity.
            if remaining > 0:
                self._insert_bid(
                    order_id,
                    timestamp_ns,
                    price,
                    remaining,
                )

        # ---------------------------------------------------------
        # SELL
        # ---------------------------------------------------------

        elif side == 2:

            while (
                remaining > 0
                and self.bids
                and price <= self.bids[0].price
            ):
                level = self.bids[0]

                # FIFO: always match the oldest order first.
                resting = level.orders[0]

                trade_price = resting.price

                if remaining < resting.quantity:
                    fill = remaining
                else:
                    fill = resting.quantity

                trades.append(
                    (
                        resting.order_id,
                        order_id,
                        trade_price,
                        fill,
                    )
                )

                self.trade_count += 1
                self.last_trade_price = trade_price

                remaining -= fill
                resting.quantity -= fill

                # Resting order completely filled.
                if resting.quantity == 0:

                    level.orders.pop(0)

                    if not level.orders:
                        self._remove_bid_level()

            # Unfilled SELL quantity becomes resting liquidity.
            if remaining > 0:
                self._insert_ask(
                    order_id,
                    timestamp_ns,
                    price,
                    remaining,
                )

        return trades

    def top(self):
        """
        Return the current top-of-book and trade statistics.

        Returns:
            (
                best_bid,
                best_ask,
                trade_count,
                last_trade_price
            )
        """

        best_bid = 0
        best_ask = 0

        if self.bids:
            best_bid = self.bids[0].price

        if self.asks:
            best_ask = self.asks[0].price

        return (
            best_bid,
            best_ask,
            self.trade_count,
            self.last_trade_price,
        )
