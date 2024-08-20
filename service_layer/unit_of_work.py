import abc

from adapters import repository
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import create_engine
import config

DEFAULT_SESSION_FACTORY = sessionmaker(bind=create_engine(config.get_postgres_uri()))


class AbstractUnitOfWork(abc.ABC):
    """The UoW handles the interaction with the DB and the service layer"""

    batches: repository.AbstractRepository

    def __enter__(self) -> "AbstractUnitOfWork":
        return self

    def __exit__(self, *args):
        self.rollback()

    @abc.abstractmethod
    def commit(self):
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
        self.batches = repository.SqlAlchemyRepository(self.session)
        return super().__enter__()

    def __exit__(self, *args):
        super().__exit__(*args)
        self.session.close()

    def commit(self):
        self.session.commit()

    def rollback(self):
        """It does not have effect if `commit()` has been called"""
        self.session.rollback()
