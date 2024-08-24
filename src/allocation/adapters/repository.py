import abc

from allocation.domain import model


class AbstractProductRepository(abc.ABC):
    """Simplest abstract repository"""

    # Python will refuse to let you instantiate a class that does not implement
    # all the abstractmethods defined in its parent class.
    @abc.abstractmethod
    def add(self, product: model.Product):
        raise NotImplementedError

    # An alternative to look into is PEP 544 protocols. These give you typing without
    # the possibility of inheritance, which "prefer composition over inheritance" fans
    # will particularly like.
    @abc.abstractmethod
    def get(self, sku) -> model.Product:
        raise NotImplementedError


class SqlAlchemyRepository(AbstractProductRepository):
    def __init__(self, session):
        self.session = session

    def add(self, product: model.Product):
        self.session.add(product)

    def get(self, sku):
        return self.session.query(model.Product).filter_by(sku=sku).first()

    def list(self):
        return self.session.query(model.Product).all()
