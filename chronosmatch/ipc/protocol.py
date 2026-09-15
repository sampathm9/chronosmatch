import struct

# Q=order id, B=side, q=price ticks, I=quantity, Q=timestamp.
ORDER_STRUCT = struct.Struct("<QBqIQ")
ORDER_SIZE = ORDER_STRUCT.size

BUY = 1
SELL = 2

def pack_order(order_id, side, price_ticks, quantity, timestamp_ns):
    return ORDER_STRUCT.pack(order_id, side, price_ticks, quantity, timestamp_ns)

def unpack_order(data):
    return ORDER_STRUCT.unpack(data)
