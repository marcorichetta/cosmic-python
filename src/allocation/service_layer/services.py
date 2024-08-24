from __future__ import annotations
from typing import Optional
from datetime import date

from allocation.domain import model
from allocation.service_layer.unit_of_work import AbstractUnitOfWork


class InvalidSku(Exception):
    pass


def is_valid_sku(sku, batches):
    return sku in {b.sku for b in batches}


def add_batch(
    reference: str,
    sku: str,
    quantity: int,
    eta: Optional[date],
    uow: AbstractUnitOfWork,
):
    """Creates a new Batch and saves it to the repository"""

    with uow:
        product = uow.products.get(sku=sku)
        if product is None:
            product = model.Product(sku=sku, batches=[])
            uow.products.add(product)
        batch = model.Batch(reference, sku, quantity, eta)

        product.batches.append(batch)
        uow.commit()


def allocate(
    orderid: str,
    sku: str,
    qty: int,
    uow: AbstractUnitOfWork,
) -> str:
    """Allocates an orderline from available batches"""
    line = model.OrderLine(orderid, sku, qty)

    with uow:
        product = uow.products.get(sku=line.sku)
        if product is None:
            raise InvalidSku(f"Invalid sku {line.sku}")

        batchref = product.allocate(line)
        uow.commit()

    return batchref


def deallocate(orderid: str, sku: str, qty: int, uow: AbstractUnitOfWork) -> None:
    """Deallocates a previously allocated orderline"""

    with uow:
        batches = uow.products.list()

        line = model.OrderLine(orderid, sku, qty)
        model.Product.deallocate(line, batches)
        uow.commit()
