from __future__ import annotations
from datetime import date
from typing import Optional

import domain.model as model
from domain.model import OrderLine
from adapters.repository import AbstractRepository
from service_layer.unit_of_work import AbstractUnitOfWork


class InvalidSku(Exception):
    pass


def is_valid_sku(sku, batches):
    return sku in {b.sku for b in batches}


def allocate(orderid: str, sku: str, qty: int, uow: AbstractUnitOfWork) -> str:
    """Allocates an orderline from available batches"""

    with uow:
        batches = uow.batches.list()
        if not is_valid_sku(sku, batches):
            raise InvalidSku(f"Invalid sku {sku}")

        line = OrderLine(orderid, sku, qty)
        ref = model.allocate(line, batches)
        uow.commit()

    return ref


def deallocate(orderid: str, sku: str, qty: int, uow: AbstractUnitOfWork) -> None:
    """Deallocates a previously allocated orderline"""

    with uow:
        batches = uow.batches.list()

        line = OrderLine(orderid, sku, qty)
        model.deallocate(line, batches)
        uow.commit()


def add_batch(
    reference: str,
    sku: str,
    quantity: int,
    eta: Optional[date],
    uow: AbstractUnitOfWork,
) -> None:
    """Creates a new Batch and saves it to the repository"""

    with uow:
        batch = model.Batch(reference, sku, quantity, eta)
        uow.batches.add(batch)
        uow.commit()
