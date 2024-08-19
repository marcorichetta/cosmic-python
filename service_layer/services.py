from __future__ import annotations
from datetime import date
from typing import Optional

import domain.model as model
from domain.model import OrderLine
from adapters.repository import AbstractRepository


class InvalidSku(Exception):
    pass


def is_valid_sku(sku, batches):
    return sku in {b.sku for b in batches}


def allocate(
    orderid: str, sku: str, qty: int, repo: AbstractRepository, session
) -> str:
    """Allocates an orderline from available batches"""

    batches = repo.list()
    if not is_valid_sku(sku, batches):
        raise InvalidSku(f"Invalid sku {sku}")

    line = OrderLine(orderid, sku, qty)
    ref = model.allocate(line, batches)
    session.commit()
    return ref


def deallocate(
    orderid: str, sku: str, qty: int, repo: AbstractRepository, session
) -> None:
    """Deallocates a previously allocated orderline"""

    batches = repo.list()

    line = OrderLine(orderid, sku, qty)
    model.deallocate(line, batches)
    session.commit()


def add_batch(
    reference: str,
    sku: str,
    quantity: int,
    eta: Optional[date],
    repo: AbstractRepository,
    session,
) -> None:
    """Creates a new Batch and saves it to the repository"""

    batch = model.Batch(reference, sku, quantity, eta)
    repo.add(batch)
    session.commit()
