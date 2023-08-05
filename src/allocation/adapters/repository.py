import abc
from allocation.domain import model

from sqlalchemy.engine import Result


class AbstractRepository(abc.ABC):
    """Simplest abstract repository"""

    # Python will refuse to let you instantiate a class that does not implement
    # all the abstractmethods defined in its parent class.
    @abc.abstractmethod
    def add(self, batch: model.Batch):
        raise NotImplementedError

    # An alternative to look into is PEP 544 protocols. These give you typing without
    # the possibility of inheritance, which "prefer composition over inheritance" fans
    # will particularly like.
    @abc.abstractmethod
    def get(self, reference) -> model.Batch:
        raise NotImplementedError


class SqlAlchemyRepository(AbstractRepository):
    def __init__(self, session):
        self.session = session

    def add(self, batch):
        self.session.add(batch)

    def get(self, reference):
        return self.session.query(model.Batch).filter_by(reference=reference).one()

    def list(self):
        return self.session.query(model.Batch).all()
