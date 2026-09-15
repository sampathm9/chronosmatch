import argparse
import multiprocessing as mp
import os
import time

from chronosmatch.ipc.ring_buffer import create_ring
from chronosmatch.simulator.market_firehose import run_producer
from chronosmatch.engine.consumer import run_consumer

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--orders", type=int, default=100_000)
    parser.add_argument("--capacity", type=int, default=262_144)
    parser.add_argument("--symbol", default="MOCK")
    args = parser.parse_args()

    path = os.path.abspath("chronosmatch.mmap")
    create_ring(path, args.capacity)

    db_path = os.path.abspath("chronosmatch.db")

    producer = mp.Process(
        target=run_producer,
        args=(path, args.capacity, args.orders, args.symbol),
        name="market-producer",
    )
    consumer = mp.Process(
        target=run_consumer,
        args=(path, args.capacity, args.orders, db_path),
        name="matching-engine",
    )

    print("=" * 60)
    print("                 CHRONOSMATCH")
    print("=" * 60)
    print(f"Orders        : {args.orders:,}")
    print(f"Ring capacity : {args.capacity:,}")
    print("IPC           : mmap + struct")
    print("Engine        : Cython")
    print("Ledger        : SQLite")
    print()

    started = time.perf_counter()
    consumer.start()
    producer.start()
    producer.join()
    consumer.join()
    elapsed = time.perf_counter() - started

    print()
    print("=" * 60)
    print("                 RUN COMPLETE")
    print("=" * 60)
    print(f"Wall time     : {elapsed:.6f} s")
    print(f"Input rate    : {args.orders / elapsed:,.0f} orders/sec")
    print(f"Ledger        : {db_path}")
    print("=" * 60)

if __name__ == "__main__":
    mp.freeze_support()
    main()
