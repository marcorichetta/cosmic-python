from datetime import date, timedelta
import pytest
from domain.model import allocate, OrderLine, Batch, OutOfStockException

today = date.today()
tomorrow = today + timedelta(days=1)
later = tomorrow + timedelta(days=10)


def test_prefers_current_stock_batches_to_shipments():
    in_stock_batch = Batch("in_stock", "CLOCK", 100, eta=None)
    shipment_batch = Batch("in_shipment", "CLOCK", 100, eta=tomorrow)
    line = OrderLine("REF-1", "CLOCK", 10)

    allocate(line, [in_stock_batch, shipment_batch])

    assert in_stock_batch.available_quantity == 90
    assert shipment_batch.available_quantity == 100


def test_prefers_earlier_batches():
    earliest = Batch("in_stock", "CLOCK", 100, eta=today)
    medium = Batch("in_stock", "CLOCK", 100, eta=tomorrow)
    latest = Batch("in_stock", "CLOCK", 100, eta=later)
    line = OrderLine("REF-1", "CLOCK", 10)

    allocate(line, [latest, earliest, medium])

    assert earliest.available_quantity == 90
    assert medium.available_quantity == 100
    assert latest.available_quantity == 100


def test_returns_allocated_batch_ref():
    in_stock_batch = Batch("in_stock", "POSTER", 100, eta=None)
    shipment_batch = Batch("in_stock", "POSTER", 100, eta=tomorrow)
    line = OrderLine("REF-1", "POSTER", 10)

    allocation = allocate(line, [in_stock_batch, shipment_batch])
    assert allocation == in_stock_batch.reference


def test_raises_out_of_stock_exception_if_cannot_allocate():
    batch = Batch("batch1", "SMALL-FORK", 10, eta=today)
    allocate(OrderLine("order1", "SMALL-FORK", 10), [batch])

    with pytest.raises(OutOfStockException, match="SMALL-FORK"):
        allocate(OrderLine("order2", "SMALL-FORK", 1), [batch])