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


def allocate(line: OrderLine, repo: AbstractRepository, session) -> str:
    """Allocates an orderline from available batches"""

    batches = repo.list()
    if not is_valid_sku(line.sku, batches):
        raise InvalidSku(f"Invalid sku {line.sku}")
    batchref = model.allocate(line, batches)
    session.commit()
    return batchref


def deallocate(line: OrderLine, repo: AbstractRepository, session) -> None:
    """Deallocates a previously allocated orderline"""

    batches = repo.list()
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
