from dataclasses import dataclass
from datetime import date
from typing import Optional


# Commands are used to express the intent to do something in the domain.
# The system reacts to commands
# If they fail, we raise an exception
class Command:
    pass


@dataclass
class Allocate(Command):
    orderid: str
    sku: str
    quantity: int


@dataclass
class CreateBatch(Command):
    reference: str
    sku: str
    quantity: int
    eta: Optional[date] = None


@dataclass
class ChangeBatchQuantity(Command):
    reference: str
    quantity: int
