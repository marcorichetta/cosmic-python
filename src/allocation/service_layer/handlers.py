from __future__ import annotations

from allocation.adapters import email
from allocation.domain import model
from allocation.domain.events import (
    AllocationRequired,
    BatchCreated,
    BatchQuantityChanged,
    OutOfStock,
)
from allocation.service_layer.unit_of_work import AbstractUnitOfWork


class InvalidSku(Exception):
    pass


def is_valid_sku(sku, batches):
    return sku in {b.sku for b in batches}


def add_batch(
    event: BatchCreated,
    uow: AbstractUnitOfWork,
) -> str:
    """Creates a new Batch and saves it to the repository

    Retuns:
        str: Batch reference
    """

    with uow:
        product = uow.products.get(sku=event.sku)
        if product is None:
            product = model.Product(sku=event.sku, batches=[])
            uow.products.add(product)
        batch = model.Batch(event.reference, event.sku, event.quantity, event.eta)
        product.batches.append(batch)
        uow.commit()
        return batch.reference


def allocate(
    event: AllocationRequired,
    uow: AbstractUnitOfWork,
) -> str:
    """Allocates an orderline from available batches"""
    line = model.OrderLine(event.orderid, event.sku, event.quantity)

    with uow:
        product = uow.products.get(sku=line.sku)
        if product is None:
            raise InvalidSku(f"Invalid sku {line.sku}")
        batchref = product.allocate(line)
        uow.commit()
        return batchref


def send_out_of_stock_notification(event: OutOfStock, uow: AbstractUnitOfWork):
    email.send_mail(
        "stock@made.com",
        f"Out of stock for {event.sku}",
    )


def change_batch_quantity(event: BatchQuantityChanged, uow: AbstractUnitOfWork):
    """Updates batch available quantity"""

    with uow:
        product = uow.products.get_by_batchref(event.reference)
        product.change_batch_quantity(event.reference, quantity=event.quantity)
        uow.commit()
