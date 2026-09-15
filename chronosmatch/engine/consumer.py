import sqlite3
import time

from chronosmatch.ipc.protocol import unpack_order
from chronosmatch.ipc.ring_buffer import RingReader
from chronosmatch.engine.order_book import OrderBook

def init_db(path):
    conn = sqlite3.connect(path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            buy_order_id INTEGER,
            sell_order_id INTEGER,
            price_ticks INTEGER,
            quantity INTEGER,
            engine_latency_ns INTEGER,
            created_ns INTEGER
        )
    """)
    conn.commit()
    return conn

def run_consumer(path, capacity, expected_orders, db_path):
    reader = RingReader(path)
    conn = init_db(db_path)
    book = OrderBook()

    count = 0
    total_latency = 0
    max_latency = 0
    started = time.perf_counter()

    try:
        while True:
            payload = reader.read()
            order_id, side, price, quantity, producer_ts = unpack_order(payload)

            if order_id == 0:
                break

            engine_start = time.perf_counter_ns()
            trades = book.add(order_id, side, price, quantity, producer_ts)
            engine_end = time.perf_counter_ns()

            latency = engine_end - producer_ts
            total_latency += latency
            max_latency = max(max_latency, latency)
            count += 1

            for buy_id, sell_id, trade_price, fill in trades:
                conn.execute(
                    "INSERT INTO trades "
                    "(buy_order_id,sell_order_id,price_ticks,quantity,"
                    "engine_latency_ns,created_ns) VALUES (?,?,?,?,?,?)",
                    (buy_id, sell_id, trade_price, fill,
                     engine_end - engine_start, time.time_ns()),
                )

            if count % 10_000 == 0:
                conn.commit()
    finally:
        conn.commit()
        conn.close()
        reader.close()

    elapsed = time.perf_counter() - started
    avg_us = (total_latency / count / 1000.0) if count else 0
    top_bid, top_ask, trades, last_price = book.top()

    print()
    print("--------------- MATCHING ENGINE ----------------")
    print(f"Orders processed : {count:,}")
    print(f"Trades matched   : {trades:,}")
    print(f"Throughput       : {count / elapsed:,.0f} orders/sec")
    print(f"Avg E2E latency  : {avg_us:.2f} us")
    print(f"Max E2E latency  : {max_latency / 1000.0:.2f} us")
    print(f"Best bid         : {top_bid / 1000.0 if top_bid is not None else '-'}")
    print(f"Best ask         : {top_ask / 1000.0 if top_ask is not None else '-'}")
    print(f"Last trade       : {last_price / 1000.0 if last_price else '-'}")
    print("-------------------------------------------------")
