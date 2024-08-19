import pytest
import domain.model as model
import adapters.repository as repository
import service_layer.services as services


class FakeRepository(repository.AbstractRepository):
    def __init__(self, batches):
        self._batches = set(batches)

    def add(self, batch):
        self._batches.add(batch)

    def get(self, reference):
        return next(b for b in self._batches if b.reference == reference)

    def list(self):
        return list(self._batches)

    @staticmethod
    def for_batch(ref: str, sku: str, qty: int, eta=None):
        return FakeRepository([model.Batch(ref, sku, qty, eta)])


class FakeSession:
    committed = False

    def commit(self):
        self.committed = True


def test_allocate_returns_allocation():
    repo, session = FakeRepository([]), FakeSession()
    services.add_batch("b1", "COMPLICATED-LAMP", 100, None, repo, session)
    result = services.allocate("o1", "COMPLICATED-LAMP", 10, repo, session)
    assert result == "b1"


def test_allocate_errors_for_invalid_sku():
    repo, session = FakeRepository([]), FakeSession()
    services.add_batch("b1", "AREALSKU", 100, None, repo, session)

    with pytest.raises(services.InvalidSku, match="Invalid sku NONEXISTENTSKU"):
        services.allocate("o1", "NONEXISTENTSKU", 10, repo, FakeSession())


def test_commits():
    repo = FakeRepository.for_batch("b1", "OMINOUS-MIRROR", 100, eta=None)
    session = FakeSession()

    services.allocate("o1", "OMINOUS-MIRROR", 10, repo, session)
    assert session.committed is True


def test_deallocate_decrements_available_quantity():
    repo, session = FakeRepository([]), FakeSession()
    services.add_batch("b1", "BLUE-PLINTH", 100, None, repo, session)

    services.allocate("o1", "BLUE-PLINTH", 10, repo, session)
    batch = repo.get(reference="b1")
    assert batch.available_quantity == 90
    services.deallocate("o1", "BLUE-PLINTH", 10, repo, session)
    assert batch.available_quantity == 100


def test_deallocate_decrements_correct_quantity():
    repo, session = FakeRepository([]), FakeSession()

    # Add two different batches
    services.add_batch("b1", "RED-PLINTH", 100, None, repo, session)
    services.add_batch("b2", "BLUE-PLINTH", 100, None, repo, session)

    # Allocate one line
    services.allocate("o1", "BLUE-PLINTH", 10, repo, session)

    # Check that we decrement the BLUE-PLINTH line
    b2 = repo.get(reference="b2")
    assert b2.available_quantity == 90
    services.deallocate("o1", "BLUE-PLINTH", 10, repo, session)
    assert b2.available_quantity == 100


def test_trying_to_deallocate_unallocated_batch(caplog: pytest.LogCaptureFixture):
    repo, session = FakeRepository([]), FakeSession()

    with pytest.raises(
        model.DeallocateBatchException, match="unallocated batch for sku BLUE-PLINTH"
    ):
        services.deallocate("o1", "BLUE-PLINTH", 10, repo, session)


def test_add_batch():
    repo, session = FakeRepository([]), FakeSession()

    services.add_batch("b1", "CRUNCHY-ARMCHAIR", 100, None, repo, session)
    assert repo.get("b1") is not None
    assert session.committed
