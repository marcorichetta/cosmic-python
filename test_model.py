from datetime import date, timedelta
import pytest

from model import Batch, NotAvailableError, OrderLine

today = date.today()
tomorrow = today + timedelta(days=1)
later = tomorrow + timedelta(days=10)


def test_allocating_to_a_batch_reduces_the_available_quantity():
    batch = Batch(reference="batch-001", sku="SMALL-TABLE", quantity=20, eta=today)
    line = OrderLine(order_reference="order-ref", sku="SMALL-TABLE", quantity=2)

    batch.allocate(line)

    assert batch.available_quantity == 18


def test_can_allocate_if_available_greater_than_required():
    batch = Batch(reference="batch-001", sku="SMALL-TABLE", quantity=20, eta=today)

    assert batch.available_quantity == 20

    line = OrderLine(order_reference="order-ref", sku="SMALL-TABLE", quantity=19)

    batch.allocate(line)

    # Succesfully allocated
    assert batch.available_quantity == 1


def test_cannot_allocate_if_available_smaller_than_required():
    batch = Batch(reference="batch-001", sku="SMALL-TABLE", quantity=20, eta=today)
    line = OrderLine(order_reference="order-ref", sku="SMALL-TABLE", quantity=21)

    with pytest.raises(NotAvailableError):
        batch.allocate(line)


def test_can_allocate_if_available_equal_to_required():
    batch = Batch(reference="batch-001", sku="SMALL-TABLE", quantity=20, eta=today)
    line = OrderLine(order_reference="order-ref", sku="SMALL-TABLE", quantity=20)

    batch.allocate(line)
    assert batch.available_quantity == 0


def test_prefers_warehouse_batches_to_shipments():
    pytest.fail("todo")


def test_prefers_earlier_batches():
    pytest.fail("todo")
