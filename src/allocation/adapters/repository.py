from typing import Protocol, Set

from allocation.domain import model


class AbstractRepository(Protocol):
    """Simplest abstract repository"""

    def add(self, product: model.Product): ...

    def get(self, sku) -> model.Product: ...


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
