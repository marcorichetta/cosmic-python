from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional


class NotAvailableError(Exception):
    ...


@dataclass
class Product:
    sku: str


@dataclass
class OrderLine:
    order_reference: str
    sku: str
    quantity: Decimal


@dataclass
class Batch:
    reference: str
    sku: str
    quantity: Decimal
    eta: Optional[date]

    def allocate(self, line: OrderLine) -> None:
        self.quantity -= line.quantity

        if self.quantity < 0:
            raise NotAvailableError

    @property
    def available_quantity(self) -> int:
        return self.quantity
