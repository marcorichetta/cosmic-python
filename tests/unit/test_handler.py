from datetime import date
from unittest import mock

import pytest

from allocation import bootstrap
from allocation.adapters import repository
from allocation.domain import commands, model
from allocation.service_layer import handlers
from allocation.service_layer.unit_of_work import AbstractUnitOfWork


class FakeRepository(repository.AbstractRepository):
    def __init__(self, products):
        super().__init__()
        self._products = set(products)

    def add(self, product):
        self._products.add(product)

    def get(self, sku) -> model.Product | None:
        return next((p for p in self._products if p.sku == sku), None)

    def get_by_batchref(self, batchref: str):
        return next(
            (
                prod
                for prod in self._products
                for batch in prod.batches
                if batch.reference == batchref
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


def bootstrap_test_app():
    return bootstrap.bootstrap(
        start_orm=False,  # We don't need an ORM for these tests
        uow=FakeUnitOfWork(),
        send_mail=lambda *args: None,
        publish=lambda *args: None,
    )


class TestAddBatch:
    bus = bootstrap_test_app()

    def test_for_new_product(self):
        self.bus.handle(commands.CreateBatch("b1", "CRUNCHY-ARMCHAIR", 100, None))

        assert self.bus.uow.products.get("CRUNCHY-ARMCHAIR") is not None
        assert self.bus.uow.committed

    def test_for_existing_product(self):
        self.bus.handle(commands.CreateBatch("b1", "GARISH-RUG", 100, None))
        self.bus.handle(commands.CreateBatch("b2", "GARISH-RUG", 99, None))
        assert "b2" in [
            b.reference for b in self.bus.uow.products.get("GARISH-RUG").batches
        ]


class TestChangeBatchQuantity:
    bus = bootstrap_test_app()

    def test_changes_available_quantity(self):
        sku = "CRUNCHY-ARMCHAIR"
        self.bus.handle(commands.CreateBatch("b1", sku, 100, None))

        [batch] = self.bus.uow.products.get(sku).batches
        assert batch.available_quantity == 100

        self.bus.handle(commands.ChangeBatchQuantity("b1", 50))

        assert batch.available_quantity == 50

    def test_reallocates_if_necessary(self):
        sku = "INDIFFERENT-TABLE"
        history = [
            commands.CreateBatch("batch1", sku, 50, None),
            commands.CreateBatch("batch2", sku, 50, date.today()),
            commands.Allocate("order1", sku, 20),  # batch1 == 30
            commands.Allocate("order2", sku, 20),  # batch1 == 10
        ]
        for message in history:
            self.bus.handle(message)
        [batch1, batch2] = self.bus.uow.products.get(sku).batches

        assert batch1.available_quantity == 10
        assert batch2.available_quantity == 50

        self.bus.handle(commands.ChangeBatchQuantity("batch1", 25))

        # order1 or order2 will be deallocated, so we'll have 25 - 20
        assert batch1.available_quantity == 5
        # and 20 will be reallocated to the next batch
        assert batch2.available_quantity == 30


class TestAllocate:
    bus = bootstrap_test_app()

    def test_allocate_returns_allocation(self):
        self.bus.handle(commands.CreateBatch("b1", "COMPLICATED-LAMP", 100, None))
        result = self.bus.handle(commands.Allocate("o1", "COMPLICATED-LAMP", 10))

        assert result.pop(0) == "b1"

    def test_allocate_errors_for_invalid_sku(self):
        self.bus.handle(commands.CreateBatch("b1", "AREALSKU", 100, None))

        with pytest.raises(handlers.InvalidSku, match="Invalid sku NONEXISTENTSKU"):
            self.bus.handle(commands.Allocate("o1", "NONEXISTENTSKU", 10))

    def test_allocate_commits(self):
        self.bus.handle(commands.CreateBatch("b1", "OMINOUS-MIRROR", 100, None))
        self.bus.handle(commands.Allocate("o1", "OMINOUS-MIRROR", 10))
        assert self.bus.uow.committed

    def test_sends_email_on_out_of_stock_error(self):
        sku = "POPULAR-CURTAINS"
        self.bus.handle(commands.CreateBatch("b1", sku, 9, None))

        with mock.patch("allocation.adapters.email.send") as mock_send_mail:
            self.bus.handle(commands.Allocate("o1", sku, 10))
            assert mock_send_mail.call_args == mock.call(
                "stock@made.com",
                f"Out of stock for {sku}",
            )
