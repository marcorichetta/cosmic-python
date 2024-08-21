import pytest
import domain.model as model
import adapters.repository as repository
import service_layer.services as services
from service_layer.unit_of_work import AbstractUnitOfWork


class FakeRepository(repository.AbstractRepository):
    def __init__(self, batches):
        self._batches = set(batches)

    def add(self, batch):
        self._batches.add(batch)

    def get(self, sku):
        return next((p for p in self._batches if p.sku == sku), None)

    def list(self):
        return list(self._batches)

    @staticmethod
    def for_batch(ref: str, sku: str, qty: int, eta=None):
        return FakeRepository([model.Batch(ref, sku, qty, eta)])


class FakeUnitOfWork(AbstractUnitOfWork):
    def __init__(self, *args, **kwargs):
        self.products = FakeRepository([])
        self.committed = False

    def commit(self):
        self.committed = True

    def rollback(self):
        pass


def test_add_batch_for_new_product():
    uow = FakeUnitOfWork()
    services.add_batch("b1", "CRUNCHY-ARMCHAIR", 100, None, uow)
    assert uow.products.get("CRUNCHY-ARMCHAIR") is not None
    assert uow.committed


def test_add_batch_for_existing_product():
    uow = FakeUnitOfWork()
    services.add_batch("b1", "GARISH-RUG", 100, None, uow)
    services.add_batch("b2", "GARISH-RUG", 99, None, uow)
    assert "b2" in [b.reference for b in uow.products.get("GARISH-RUG").batches]


def test_allocate_returns_allocation():
    uow = FakeUnitOfWork()
    services.add_batch("b1", "COMPLICATED-LAMP", 100, None, uow)
    result = services.allocate("o1", "COMPLICATED-LAMP", 10, uow)
    assert result == "b1"


def test_allocate_errors_for_invalid_sku():
    uow = FakeUnitOfWork()

    services.add_batch("b1", "AREALSKU", 100, None, uow)

    with pytest.raises(services.InvalidSku, match="Invalid sku NONEXISTENTSKU"):
        services.allocate("o1", "NONEXISTENTSKU", 10, uow)


def test_allocate_commits():
    uow = FakeUnitOfWork()
    services.add_batch("b1", "OMINOUS-MIRROR", 100, None, uow)
    services.allocate("o1", "OMINOUS-MIRROR", 10, uow)
    assert uow.committed


def test_deallocate_decrements_available_quantity():
    uow = FakeUnitOfWork()
    services.add_batch("b1", "BLUE-PLINTH", 100, None, uow)

    services.allocate("o1", "BLUE-PLINTH", 10, uow)
    batch = uow.products.get(reference="b1")
    assert batch.available_quantity == 90
    services.deallocate("o1", "BLUE-PLINTH", 10, uow)
    assert batch.available_quantity == 100


def test_deallocate_decrements_correct_quantity():
    uow = FakeUnitOfWork()

    # Add two different batches
    services.add_batch("b1", "RED-PLINTH", 100, None, uow)
    services.add_batch("b2", "BLUE-PLINTH", 100, None, uow)

    # Allocate one line
    services.allocate("o1", "BLUE-PLINTH", 10, uow)

    # Check that we decrement the BLUE-PLINTH line
    b2 = uow.products.get(reference="b2")
    assert b2.available_quantity == 90
    services.deallocate("o1", "BLUE-PLINTH", 10, uow)
    assert b2.available_quantity == 100


def test_trying_to_deallocate_unallocated_batch():
    uow = FakeUnitOfWork()

    with pytest.raises(
        model.DeallocateBatchException, match="unallocated batch for sku BLUE-PLINTH"
    ):
        services.deallocate("o1", "BLUE-PLINTH", 10, uow)


def test_add_batch():
    uow = FakeUnitOfWork()

    services.add_batch("b1", "CRUNCHY-ARMCHAIR", 100, None, uow)
    assert uow.products.get("b1") is not None
