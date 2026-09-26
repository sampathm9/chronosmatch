# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
# cython: cdivision=True

from libc.stdlib cimport malloc, free
from libc.stdint cimport uint64_t, int64_t
from libc.stddef cimport size_t


cdef struct OrderNode:
    uint64_t order_id
    uint64_t timestamp_ns
    uint64_t quantity
    int64_t price
    OrderNode* next


cdef struct PriceLevel:
    int64_t price
    OrderNode* head
    OrderNode* tail
    PriceLevel* next


cdef class OrderBook:

    cdef PriceLevel* bids
    cdef PriceLevel* asks

    cdef uint64_t trade_count
    cdef int64_t last_trade_price

    def __cinit__(self):
        self.bids = NULL
        self.asks = NULL
        self.trade_count = 0
        self.last_trade_price = 0

    def __dealloc__(self):
        self._free_side(self.bids)
        self._free_side(self.asks)

    cdef void _free_orders(self, OrderNode* node):
        cdef OrderNode* nxt

        while node != NULL:
            nxt = node.next
            free(node)
            node = nxt

    cdef void _free_side(self, PriceLevel* level):
        cdef PriceLevel* nxt

        while level != NULL:
            nxt = level.next
            self._free_orders(level.head)
            free(level)
            level = nxt

    cdef PriceLevel* _find_level(
        self,
        PriceLevel* side,
        int64_t price
    ):
        cdef PriceLevel* current = side

        while current != NULL:
            if current.price == price:
                return current

            current = current.next

        return NULL

    cdef PriceLevel* _create_level(
        self,
        int64_t price
    ):
        cdef PriceLevel* level

        level = <PriceLevel*>malloc(sizeof(PriceLevel))

        if level == NULL:
            raise MemoryError()

        level.price = price
        level.head = NULL
        level.tail = NULL
        level.next = NULL

        return level

    cdef void _append_order(
        self,
        PriceLevel* level,
        uint64_t order_id,
        uint64_t timestamp_ns,
        int64_t price,
        uint64_t quantity
    ):
        cdef OrderNode* order

        order = <OrderNode*>malloc(sizeof(OrderNode))

        if order == NULL:
            raise MemoryError()

        order.order_id = order_id
        order.timestamp_ns = timestamp_ns
        order.price = price
        order.quantity = quantity
        order.next = NULL

        if level.tail == NULL:
            level.head = order
            level.tail = order
        else:
            level.tail.next = order
            level.tail = order

    cdef void _insert_bid(
        self,
        uint64_t order_id,
        uint64_t timestamp_ns,
        int64_t price,
        uint64_t quantity
    ):
        cdef PriceLevel* level
        cdef PriceLevel* current
        cdef PriceLevel* previous

        level = self._find_level(self.bids, price)

        if level != NULL:
            self._append_order(
                level,
                order_id,
                timestamp_ns,
                price,
                quantity
            )
            return

        level = self._create_level(price)

        if self.bids == NULL:
            self.bids = level
            return

        if price > self.bids.price:
            level.next = self.bids
            self.bids = level
            return

        previous = self.bids
        current = self.bids.next

        while current != NULL and current.price > price:
            previous = current
            current = current.next

        level.next = current
        previous.next = level

    cdef void _insert_ask(
        self,
        uint64_t order_id,
        uint64_t timestamp_ns,
        int64_t price,
        uint64_t quantity
    ):
        cdef PriceLevel* level
        cdef PriceLevel* current
        cdef PriceLevel* previous

        level = self._find_level(self.asks, price)

        if level != NULL:
            self._append_order(
                level,
                order_id,
                timestamp_ns,
                price,
                quantity
            )
            return

        level = self._create_level(price)

        if self.asks == NULL:
            self.asks = level
            return

        if price < self.asks.price:
            level.next = self.asks
            self.asks = level
            return

        previous = self.asks
        current = self.asks.next

        while current != NULL and current.price < price:
            previous = current
            current = current.next

        level.next = current
        previous.next = level

    cdef void _remove_bid_level(self):
        cdef PriceLevel* old

        if self.bids == NULL:
            return

        old = self.bids
        self.bids = old.next

        self._free_orders(old.head)
        free(old)

    cdef void _remove_ask_level(self):
        cdef PriceLevel* old

        if self.asks == NULL:
            return

        old = self.asks
        self.asks = old.next

        self._free_orders(old.head)
        free(old)

    cpdef add(
        self,
        uint64_t order_id,
        int side,
        int64_t price,
        uint64_t quantity,
        uint64_t timestamp_ns
    ):
        """
        side:
            1 = BUY
            2 = SELL

        Returns:
            Python list of trades.

        The matching state itself is maintained entirely
        through C structs and pointers.
        """

        cdef uint64_t remaining = quantity
        cdef OrderNode* resting
        cdef uint64_t fill
        cdef int64_t trade_price

        cdef list trades = []

        # BUY
        if side == 1:

            while (
                remaining > 0
                and self.asks != NULL
                and price >= self.asks.price
            ):

                resting = self.asks.head
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
                        fill
                    )
                )

                self.trade_count += 1
                self.last_trade_price = trade_price

                remaining -= fill
                resting.quantity -= fill

                if resting.quantity == 0:
                    self.asks.head = resting.next

                    if self.asks.head == NULL:
                        self.asks.tail = NULL

                    free(resting)

                    if self.asks.head == NULL:
                        self._remove_ask_level()

            if remaining > 0:
                self._insert_bid(
                    order_id,
                    timestamp_ns,
                    price,
                    remaining
                )

        # SELL
        elif side == 2:

            while (
                remaining > 0
                and self.bids != NULL
                and price <= self.bids.price
            ):

                resting = self.bids.head
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
                        fill
                    )
                )

                self.trade_count += 1
                self.last_trade_price = trade_price

                remaining -= fill
                resting.quantity -= fill

                if resting.quantity == 0:
                    self.bids.head = resting.next

                    if self.bids.head == NULL:
                        self.bids.tail = NULL

                    free(resting)

                    if self.bids.head == NULL:
                        self._remove_bid_level()

            if remaining > 0:
                self._insert_ask(
                    order_id,
                    timestamp_ns,
                    price,
                    remaining
                )

        return trades

    cpdef top(self):
        cdef int64_t best_bid = 0
        cdef int64_t best_ask = 0

        if self.bids != NULL:
            best_bid = self.bids.price

        if self.asks != NULL:
            best_ask = self.asks.price

        return (
            best_bid,
            best_ask,
            self.trade_count,
            self.last_trade_price
        )