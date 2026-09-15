from chronosmatch.engine.order_book import OrderBook

def test_buy_sell_match():
    book = OrderBook()
    book.add(1, 2, 100_000, 10, 1)
    trades = book.add(2, 1, 100_000, 5, 2)
    assert trades == [(1, 2, 100_000, 5)]
    assert book.top()[2] == 1
