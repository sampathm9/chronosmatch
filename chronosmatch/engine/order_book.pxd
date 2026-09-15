cdef class OrderBook:
    cpdef list add(self, long long order_id, unsigned char side,
                   long long price, unsigned int quantity,
                   unsigned long long timestamp_ns)
    cpdef tuple top(self)
