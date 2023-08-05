import abc
from typing import Optional

from sqlalchemy.engine import Result

import model


class AbstractRepository(abc.ABC):
    """Simplest abstract repository"""

    # Python will refuse to let you instantiate a class that does not implement
    # all the abstractmethods defined in its parent class.
    @abc.abstractmethod
    def add(self, batch: model.Batch):
        raise NotImplementedError

    # An alternative to look into is PEP 544 protocols. These give you typing without
    # the possibility of inheritance, which "prefer composition over inheritance" fans
    # will particularly like.
    @abc.abstractmethod
    def get(self, reference) -> model.Batch:
        raise NotImplementedError


class SqlRepository(AbstractRepository):
    def __init__(self, session):
        self.session = session

    def add(self, batch: model.Batch):
        """Inserts a Batch with his allocated OrderLines"""

        # update if batch already exists
        if batch_id := self._get_batch_by_id(batch.reference):
            self._insert_allocations(batch, *batch_id)
            return

        batch_id = self._insert_batch(batch)
        self._insert_allocations(batch, *batch_id)

    def _insert_allocations(self, batch: model.Batch, batch_id: int):
        for line in batch._allocations:
            print("Processing {0} allocations".format(len(batch._allocations)))
            self._insert_order_line(line)

            print(f"Allocating order line {line.order_reference}")
            self.session.execute(
                """INSERT INTO allocations(orderline_id, batch_id)
                SELECT id as orderline_id, :batch_id as batch_id FROM order_lines WHERE orderid = :orderid
                """,
                {
                    "orderid": line.order_reference,
                    "batch_id": batch_id,
                },
            )

    def _insert_order_line(self, line: model.OrderLine):
        print("Inserting line {0}".format(line.order_reference))

        self.session.execute(
            "INSERT INTO order_lines (orderid, sku, qty) VALUES (:orderline_id, :sku, :qty)",
            {
                "orderline_id": line.order_reference,
                "sku": line.sku,
                "qty": line.quantity,
            },
        )

    def _insert_batch(self, batch) -> tuple[int]:
        try:
            result: Result = self.session.execute(
                """
                INSERT INTO batches(reference, sku, eta, _purchased_quantity)
                VALUES (:reference, :sku, :eta, :_purchased_quantity)
                RETURNING id
                """,
                {
                    "reference": batch.reference,
                    "sku": batch.sku,
                    "eta": batch.eta,
                    "_purchased_quantity": batch._purchased_quantity,
                },
            )

            batch_id = result.fetchone()
            return batch_id

        except Exception as exc:
            print("Error inserting batch", exc)
            raise Exception from exc

    def get(self, reference) -> model.Batch:
        [[sku, _purchased_quantity, eta]] = self.session.execute(
            "SELECT sku, _purchased_quantity, eta FROM batches WHERE reference=:reference",
            dict(reference=reference),
        )

        batch = model.Batch(reference, sku, _purchased_quantity, eta)

        for line in self._get_order_lines(reference):
            batch.allocate(line)

        return batch

    def _get_batch_by_id(self, reference: str):
        """Gets batch by reference. Returns database Id or None"""

        result: Result = self.session.execute(
            "SELECT id FROM batches WHERE reference = :reference",
            {"reference": reference},
        )

        return result.fetchone()

    def _get_order_lines(self, reference) -> list[model.OrderLine]:
        rows = list(
            self.session.execute(
                "SELECT orderid, order_lines.sku, order_lines.qty"
                " FROM allocations"
                " JOIN order_lines ON allocations.orderline_id = order_lines.id"
                " JOIN batches ON allocations.batch_id = batches.id"
                " WHERE batches.reference = :batchid",
                dict(batchid=reference),
            )
        )

        order_lines = [model.OrderLine(*row) for row in rows]
        return order_lines
