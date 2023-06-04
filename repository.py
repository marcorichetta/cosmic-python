import abc
import model


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


class SqlRepository(AbstractRepository):
    def __init__(self, session):
        self.session = session

    def add(self, batch: model.Batch):
        # TODO - Find a better way of doing this
        query = f"INSERT INTO batches (reference, sku, _purchased_quantity, eta) VALUES ('{batch.reference}', '{batch.sku}', {batch._purchased_quantity}, {batch.eta if batch.eta else 'NULL'})"

        self.session.execute(query)

    def get(self, reference) -> model.Batch:
        # self.session.execute('SELECT ??
        ...
