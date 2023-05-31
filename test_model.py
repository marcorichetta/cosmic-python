from datetime import date, timedelta
import pytest

from model import Batch, OrderLine

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


def test_prefers_warehouse_batches_to_shipments():
    pytest.fail("todo")


def test_prefers_earlier_batches():
    pytest.fail("todo")
