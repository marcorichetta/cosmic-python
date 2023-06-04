from datetime import date, timedelta
import pytest

from model import Batch, OrderLine, OutOfStock, allocate

today = date.today()
tomorrow = today + timedelta(days=1)
later = tomorrow + timedelta(days=10)


def make_batch_and_line(sku: str, batch_qty: int, line_qty: int):
    batch = Batch(reference="batch-001", sku=sku, quantity=batch_qty, eta=today)
    line = OrderLine(order_reference="order-001", sku=sku, quantity=line_qty)
    return batch, line


def test_allocating_to_a_batch_reduces_the_available_quantity():
    batch, line = make_batch_and_line("SMALL_TABLE", 20, 2)

    batch.allocate(line)

    assert batch.available_quantity == 18


def test_can_allocate_if_available_greater_than_required():
    large_batch, small_line = make_batch_and_line("SMALL_TABLE", 20, 2)

    large_batch.can_allocate(small_line)


def test_can_allocate_if_available_equal_to_required():
    batch, line = make_batch_and_line("SMALL_TABLE", 20, 20)

    assert batch.can_allocate(line)


def test_cannot_allocate_if_available_smaller_than_required():
    small_batch, large_line = make_batch_and_line("SMALL_TABLE", 2, 20)

    assert small_batch.can_allocate(large_line) is False


def test_cannot_allocate_if_skus_do_not_match():
    batch = Batch("batch-001", "SMALL_TABLE", 10, eta=None)
    different_sku_line = OrderLine("order-001", "LARGE_HADRON_COLLIDER", 5)

    assert batch.can_allocate(different_sku_line) is False


def test_can_only_deallocate_allocated_lines():
    batch, unallocated_line = make_batch_and_line("DECORATIVE-TRINKET", 20, 2)
    batch.deallocate(unallocated_line)
    assert batch.available_quantity == 20


def test_allocation_is_idempotent():
    batch, line = make_batch_and_line("ANGULAR-DESK", 20, 2)
    batch.allocate(line)
    batch.allocate(line)
    assert batch.available_quantity == 18


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
    batch, line = make_batch_and_line("SHOES", 10, 10)
    allocate(line, [batch])

    with pytest.raises(OutOfStock, match="SHOES"):
        allocate(OrderLine("Order-2", "SHOES", 1), [batch])
