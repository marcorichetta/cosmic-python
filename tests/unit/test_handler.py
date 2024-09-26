from datetime import date
from unittest import mock

import pytest

from allocation.adapters import repository
from allocation.domain import events
from allocation.service_layer import handlers, messagebus
from allocation.service_layer.unit_of_work import AbstractUnitOfWork


class FakeRepository(repository.AbstractRepository):
    def __init__(self, products):
        super().__init__()
        self._products = set(products)

    def add(self, product):
        self._products.add(product)

    def get(self, sku):
        return next((p for p in self._products if p.sku == sku), None)

    def get_by_batchref(self, ref: str):
        return next(
            (
                prod
                for prod in self._products
                for batch in prod.batches
                if batch.reference == ref
            )
        )


class FakeUnitOfWork(AbstractUnitOfWork):
    def __init__(self, *args, **kwargs):
        self.products = repository.TrackingRepository(FakeRepository([]))
        self.committed = False

    def _commit(self):
        self.committed = True

    def rollback(self):
        pass


class TestAddBatch:
    def test_for_new_product(self):
        uow = FakeUnitOfWork()
        messagebus.handle(events.BatchCreated("b1", "CRUNCHY-ARMCHAIR", 100, None), uow)

        assert uow.products.get("CRUNCHY-ARMCHAIR") is not None
        assert uow.committed

    def test_for_existing_product(self):
        uow = FakeUnitOfWork()
        messagebus.handle(events.BatchCreated("b1", "GARISH-RUG", 100, None), uow)
        messagebus.handle(events.BatchCreated("b2", "GARISH-RUG", 99, None), uow)
        assert "b2" in [b.reference for b in uow.products.get("GARISH-RUG").batches]


class TestChangeBatchQuantity:
    def test_changes_available_quantity(self):
        uow = FakeUnitOfWork()
        sku = "CRUNCHY-ARMCHAIR"
        messagebus.handle(events.BatchCreated("b1", sku, 100, None), uow)

        [batch] = uow.products.get(sku).batches
        assert batch.available_quantity == 100

        messagebus.handle(events.BatchQuantityChanged("b1", 50), uow)

        assert batch.available_quantity == 50

    def test_reallocates_if_necessary(self):
        uow = FakeUnitOfWork()
        sku = "INDIFFERENT-TABLE"
        event_history = [
            events.BatchCreated("batch1", sku, 50, None),
            events.BatchCreated("batch2", sku, 50, date.today()),
            events.AllocationRequired("order1", sku, 20),  # batch1 == 30
            events.AllocationRequired("order2", sku, 20),  # batch1 == 10
        ]
        for e in event_history:
            messagebus.handle(e, uow)
        [batch1, batch2] = uow.products.get(sku).batches

        assert batch1.available_quantity == 10
        assert batch2.available_quantity == 50

        messagebus.handle(events.BatchQuantityChanged("batch1", 25), uow)

        # order1 or order2 will be deallocated, so we'll have 25 - 20
        assert batch1.available_quantity == 5
        # and 20 will be reallocated to the next batch
        assert batch2.available_quantity == 30


class TestAllocate:
    def test_allocate_returns_allocation(self):
        uow = FakeUnitOfWork()
        messagebus.handle(events.BatchCreated("b1", "COMPLICATED-LAMP", 100, None), uow)
        result = messagebus.handle(
            events.AllocationRequired("o1", "COMPLICATED-LAMP", 10), uow
        )

        assert result.pop(0) == "b1"

    def test_allocate_errors_for_invalid_sku(self):
        uow = FakeUnitOfWork()

        messagebus.handle(events.BatchCreated("b1", "AREALSKU", 100, None), uow)

        with pytest.raises(handlers.InvalidSku, match="Invalid sku NONEXISTENTSKU"):
            messagebus.handle(
                events.AllocationRequired("o1", "NONEXISTENTSKU", 10), uow
            )

    def test_allocate_commits(self):
        uow = FakeUnitOfWork()
        messagebus.handle(events.BatchCreated("b1", "OMINOUS-MIRROR", 100, None), uow)
        messagebus.handle(events.AllocationRequired("o1", "OMINOUS-MIRROR", 10), uow)
        assert uow.committed


def test_sends_email_on_out_of_stock_error():
    uow = FakeUnitOfWork()
    sku = "POPULAR-CURTAINS"
    messagebus.handle(events.BatchCreated("b1", sku, 9, None), uow)

    with mock.patch("allocation.adapters.email.send_mail") as mock_send_mail:
        messagebus.handle(events.AllocationRequired("o1", sku, 10), uow)
        assert mock_send_mail.call_args == mock.call(
            "stock@made.com",
            f"Out of stock for {sku}",
        )
