import mmap
import struct
import time

MAGIC = b"CHRMATCH1"
HEADER_STRUCT = struct.Struct("<8sQQQQ")
HEADER_SIZE = HEADER_STRUCT.size

def create_ring(path, capacity, record_size=29):
    total = HEADER_SIZE + capacity * record_size
    with open(path, "wb") as f:
        f.truncate(total)
    with open(path, "r+b") as f:
        mm = mmap.mmap(f.fileno(), 0)
        mm[:HEADER_SIZE] = HEADER_STRUCT.pack(
            MAGIC, capacity, record_size, 0, 0
        )
        mm.flush()
        mm.close()

class RingWriter:
    def __init__(self, path, capacity, record_size):
        self.file = open(path, "r+b")
        self.mm = mmap.mmap(self.file.fileno(), 0)
        self.capacity = capacity
        self.record_size = record_size

    def write(self, payload):
        while True:
            magic, cap, size, write_seq, read_seq = HEADER_STRUCT.unpack(
                self.mm[:HEADER_SIZE]
            )
            if write_seq - read_seq < cap:
                slot = write_seq % cap
                offset = HEADER_SIZE + slot * size
                self.mm[offset:offset + size] = payload
                self.mm[:HEADER_SIZE] = HEADER_STRUCT.pack(
                    magic, cap, size, write_seq + 1, read_seq
                )
                return
            time.sleep(0)

    def close(self):
        self.mm.flush()
        self.mm.close()
        self.file.close()

class RingReader:
    def __init__(self, path):
        self.file = open(path, "r+b")
        self.mm = mmap.mmap(self.file.fileno(), 0)

    def read(self):
        while True:
            magic, cap, size, write_seq, read_seq = HEADER_STRUCT.unpack(
                self.mm[:HEADER_SIZE]
            )
            if read_seq < write_seq:
                slot = read_seq % cap
                offset = HEADER_SIZE + slot * size
                payload = self.mm[offset:offset + size]
                self.mm[:HEADER_SIZE] = HEADER_STRUCT.pack(
                    magic, cap, size, write_seq, read_seq + 1
                )
                return payload
            time.sleep(0)

    def close(self):
        self.mm.close()
        self.file.close()
