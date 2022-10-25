from dataclasses import dataclass
from datetime import date
from decimal import Decimal


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
    eta: date

    def allocate(self, line: OrderLine) -> None:
        self.quantity -= line.quantity

    @property
    def available_quantity(self) -> int:
        return self.quantity
