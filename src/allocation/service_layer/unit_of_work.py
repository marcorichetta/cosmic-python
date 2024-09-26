import abc
from typing import Protocol

from allocation.adapters import repository
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import create_engine
import allocation.config as config

DEFAULT_SESSION_FACTORY = sessionmaker(
    bind=create_engine(
        config.get_postgres_uri(),
        isolation_level="REPEATABLE READ",  # https://www.postgresql.org/docs/12/transaction-iso.html#XACT-REPEATABLE-READ
    )
)


class AbstractUnitOfWork(Protocol):
    """The UoW handles the interaction with the DB and the service layer"""

    products: repository.AbstractRepository

    def __enter__(self) -> "AbstractUnitOfWork":
        return self

    def __exit__(self, *args):
        self.rollback()

    def commit(self):
        self._commit()

    def collect_new_events(self):
        """Collects events from products and makes them available (yield)

        Yields:
            Event: dispatched by a product
        """
        for product in self.products.seen:
            while product.events:
                yield product.events.pop(0)

    @abc.abstractmethod
    def _commit(self):
        """Commit changes to be saved in our repository"""
        raise NotImplementedError

    @abc.abstractmethod
    def rollback(self):
        """Rollback changes."""
        raise NotImplementedError


class SqlAlchemyUnitOfWork(AbstractUnitOfWork):
    def __init__(self, session_factory=DEFAULT_SESSION_FACTORY):
        self.session_factory = session_factory

    def __enter__(self):
        self.session = self.session_factory()
        self.products = repository.TrackingRepository(
            repository.SqlAlchemyRepository(self.session)
        )
        return super().__enter__()

    def __exit__(self, *args):
        super().__exit__(*args)
        self.session.close()

    def _commit(self):
        self.session.commit()

    def rollback(self):
        """It does not have effect if `commit()` has been called"""
        self.session.rollback()
