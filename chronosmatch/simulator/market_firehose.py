import asyncio
import random
import time

from chronosmatch.ipc.protocol import BUY, SELL, ORDER_SIZE, pack_order
from chronosmatch.ipc.ring_buffer import RingWriter

async def firehose(writer, count, symbol):
    base_price = 100_000

    for order_id in range(1, count + 1):
        side = BUY if order_id % 2 else SELL
        if random.random() < 0.15:
            side = BUY if random.random() < 0.5 else SELL

        if side == BUY:
            price_ticks = base_price + random.randint(-20, 5)
        else:
            price_ticks = base_price + random.randint(-5, 20)

        quantity = random.randint(1, 100)
        timestamp_ns = time.perf_counter_ns()

        writer.write(
            pack_order(
                order_id, side, price_ticks, quantity, timestamp_ns
            )
        )

        if order_id % 1000 == 0:
            await asyncio.sleep(0)

def run_producer(path, capacity, count, symbol):
    writer = RingWriter(path, capacity, ORDER_SIZE)
    try:
        asyncio.run(firehose(writer, count, symbol))
        writer.write(pack_order(0, 0, 0, 0, time.perf_counter_ns()))
    finally:
        writer.close()
