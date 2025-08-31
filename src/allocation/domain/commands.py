from dataclasses import dataclass
from datetime import date
from typing import Optional


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
