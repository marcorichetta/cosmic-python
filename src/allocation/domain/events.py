from dataclasses import dataclass
from datetime import date
from typing import Optional


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
