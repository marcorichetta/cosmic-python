from typing import Protocol, Set

from allocation.adapters import orm
from allocation.domain import model


class AbstractRepository(Protocol):
    """Simplest abstract repository"""

    # seen: Set[model.Product]

    def add(self, product: model.Product): ...

    def get(self, sku: str) -> model.Product: ...

    def get_by_batchref(self, ref: str) -> model.Product: ...


class TrackingRepository:
    """
    Implementation of a repository that tracks "seen" products.
    """

    seen: Set[model.Product]

    def __init__(self, repo: AbstractRepository):
        self.seen = set()
        self._repo = repo

    def add(self, product: model.Product):
        self._repo.add(product)
        self.seen.add(product)

    def get(self, sku) -> model.Product:
        product = self._repo.get(sku)
        if product:
            self.seen.add(product)
        return product

    def get_by_batchref(self, ref: str) -> model.Product:
        product = self._repo.get_by_batchref(ref)
        if product:
            self.seen.add(product)
        return product


class SqlAlchemyRepository:
    """
    Repository that interacts with the DB using SQLAlchemy
    """

    def __init__(self, session):
        super().__init__()
        self.session = session

    def add(self, product: model.Product):
        self.session.add(product)

    def get(self, sku):
        return self.session.query(model.Product).filter_by(sku=sku).first()

    def get_by_batchref(self, batchref: str):
        """Gets a Product based on a batch reference"""
        return (
            self.session.query(model.Product)
            .join(model.Batch)
            .filter(orm.batches.c.reference == batchref)
            .first()
        )
