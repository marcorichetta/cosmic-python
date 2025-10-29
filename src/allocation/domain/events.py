from dataclasses import dataclass
from datetime import date
from typing import Optional

# Events are used to broadcast information about something that has happened in the domain.
# They can trigger commands
# They can fail silently


class Event:
    """Base class for Domain Events"""

    pass


@dataclass
class OutOfStock(Event):
    sku: str


@dataclass
class BatchCreated(Event):
    """Captures the batch creation event"""

    reference: str
    sku: str
    quantity: int
    eta: Optional[date] = None


@dataclass
class AllocationRequired(Event):
    orderid: str
    sku: str
    quantity: int


@dataclass
class BatchQuantityChanged(Event):
    reference: str
    quantity: int


@dataclass
class Allocated(Event):
    orderid: str
    sku: str
    quantity: int
    batchref: str


@dataclass
class Deallocated(Event):
    orderid: str
    sku: str
    quantity: int
