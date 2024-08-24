from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from typing import Optional

import logging

logger = logging.getLogger()


class OutOfStock(Exception):
    ...


class DeallocateBatch(Exception):
    ...


@dataclass(unsafe_hash=True)
class OrderLine:
    """
    Whenever we have a business concept that has data but no identity, we often choose to
    represent it using the Value Object pattern. A value object is any domain object that is
    uniquely identified by the data it holds; we usually make them immutable."""

    orderid: str
    sku: str
    qty: int


class Batch:
    def __init__(self, reference: str, sku: str, quantity: int, eta: Optional[date]):
        self.reference = reference
        self.sku = sku
        self.eta = eta
        self._purchased_quantity = quantity
        self._allocations = set()  # type: Set[OrderLine]

    def __repr__(self) -> str:
        return f"Batch - Ref: {self.reference} - SKU: {self.sku}"

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
        return self.sku == line.sku and self.available_quantity >= line.qty

    @property
    def allocated_quantity(self) -> int:
        return sum(line.qty for line in self._allocations)

    @property
    def available_quantity(self) -> int:
        return self._purchased_quantity - self.allocated_quantity


class Product:
    """A product has a unique ID (sku) and also batches associated to it that can be allocated to OrderLines"""

    def __init__(
        self, sku: str, batches: list, version_number: int = 0, *args, **kwargs
    ):
        self.sku = sku
        self.batches = batches
        self.version_number = version_number

    def __repr__(self) -> str:
        return f"Product {self.sku}"

    def allocate(self, line: OrderLine) -> str:
        """Assigns one `Batch` to an OrderLine given some priorities
        - it prefers Batches in stock over ones on shipment.
        - it prefers earlier Batches.

        Returns:
            str: allocated Batch reference
        """

        try:
            batch: Batch = next(b for b in sorted(self.batches) if b.can_allocate(line))
            batch.allocate(line)
            self.version_number += 1
            return batch.reference
        except StopIteration:
            raise OutOfStock(f"Out of stock for sku {line.sku}") from None

    def deallocate(self, line: OrderLine):
        try:
            batch: Batch = next(b for b in self.batches if b.sku == line.sku)
            batch.deallocate(line)
        except StopIteration:
            raise DeallocateBatch(
                f"Attempting to deallocate an unallocated batch for sku {line.sku}"
            ) from None
