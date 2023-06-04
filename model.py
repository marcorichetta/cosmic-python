from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import List, Optional


class OutOfStock(Exception):
    ...


@dataclass
class Product:
    sku: str


"""
Whenever we have a business concept that has data but no identity, we often choose to
represent it using the Value Object pattern. A value object is any domain object that is
uniquely identified by the data it holds; we usually make them immutable:
"""


@dataclass(frozen=True)
class OrderLine:
    order_reference: str
    sku: str
    quantity: int


class Batch:
    def __init__(self, reference: str, sku: str, quantity: int, eta: Optional[date]):
        self.reference = reference
        self.sku = sku
        self.eta = eta
        self._purchased_quantity = quantity
        self._allocations = set()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Batch):
            return False
        return other.reference == self.reference

    # you shouldn’t modify __hash__ without also modifying __eq__
    # https://hynek.me/articles/hashes-and-equality/
    def __hash__(self) -> int:
        return hash(self.reference)

    # NOTE: We use Python mechanisms to adapt our models instead of creating specific methods for it.
    def __gt__(self, other):
        if self.eta is None:
            return False
        if other.eta is None:
            return True
        return self.eta > other.eta

    def allocate(self, line: OrderLine) -> None:
        if self.can_allocate(line):
            self._allocations.add(line)

    def deallocate(self, line: OrderLine) -> None:
        if line in self._allocations:
            self._allocations.remove(line)

    def can_allocate(self, line: OrderLine) -> bool:
        return self.sku == line.sku and self.available_quantity >= line.quantity

    @property
    def allocated_quantity(self) -> int:
        return sum(line.quantity for line in self._allocations)

    @property
    def available_quantity(self) -> int:
        return self._purchased_quantity - self.allocated_quantity


def allocate(line: OrderLine, batches: List[Batch]) -> str:
    """Assigns one `Batch` to an OrderLine given some priorities
    - it prefers Batches in stock over ones on shipment.
    - it prefers earlier Batches.

    Returns:
        str: allocated Batch reference
    """

    try:
        batch: Batch = next(b for b in sorted(batches) if b.can_allocate(line))
        batch.allocate(line)
        return batch.reference
    except StopIteration:
        raise OutOfStock(f"Out of stock for sku {line.sku}")
