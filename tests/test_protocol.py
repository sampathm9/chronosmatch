from chronosmatch.ipc.protocol import pack_order, unpack_order, BUY

def test_order_roundtrip():
    raw = pack_order(123, BUY, 100250, 10, 999)
    assert unpack_order(raw) == (123, BUY, 100250, 10, 999)
