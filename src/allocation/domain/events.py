from dataclasses import dataclass


class Event:
    """Base class for Domain Events"""

    pass


@dataclass
class OutOfStock(Event):
    sku: str
