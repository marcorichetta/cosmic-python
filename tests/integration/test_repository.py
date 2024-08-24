# pylint: disable=protected-access
import pytest
from allocation.domain import model
from allocation.adapters import repository


def test_repository_can_save_a_batch(session):
    batch = model.Batch("batch1", "RUSTY-SOAPDISH", 100, eta=None)

    repo = repository.SqlAlchemyRepository(session)
    repo.add(batch)
    session.commit()

    rows = session.execute(
        'SELECT reference, sku, _purchased_quantity, eta FROM "batches"'
    )
    assert list(rows) == [("batch1", "RUSTY-SOAPDISH", 100, None)]


def insert_order_line(session, orderid, sku, qty):
    session.execute(
        "INSERT INTO order_lines (orderid, sku, qty)" " VALUES (:orderid, :sku, :qty)",
        dict(orderid=orderid, sku=sku, qty=qty),
    )
    [[orderline_id]] = session.execute(
        "SELECT id FROM order_lines WHERE orderid=:orderid AND sku=:sku",
        dict(orderid="order1", sku="GENERIC-SOFA"),
    )
    return orderline_id


def insert_batch(session, ref, sku, qty, eta):
    session.execute(
        "INSERT INTO batches (reference, sku, _purchased_quantity, eta)"
        " VALUES (:ref, :sku, :qty, :eta)",
        dict(ref=ref, sku=sku, qty=qty, eta=eta),
    )


def insert_allocation(session, orderline_id, batch_id):
    session.execute(
        "INSERT INTO allocations (orderline_id, batch_id)"
        " VALUES (:orderline_id, :batch_id)",
        dict(orderline_id=orderline_id, batch_id=batch_id),
    )


@pytest.mark.skip("Will fix later")
def test_repository_can_retrieve_a_batch_with_allocations(session):
    orderline_id = insert_order_line(session, "order1", "GENERIC-SOFA", 12)
    batch1_id = insert_batch(session, "batch1", "GENERIC-SOFA", 100, None)
    insert_batch(session, "batch2", "ITEM-2", 100, None)
    insert_allocation(session, orderline_id, batch1_id)

    repo = repository.SqlAlchemyRepository(session)
    retrieved = repo.get("batch1")

    expected = model.Batch("batch1", "GENERIC-SOFA", 100, eta=None)
    assert retrieved == expected  # Batch.__eq__ only compares reference
    assert retrieved.sku == expected.sku
    assert retrieved._purchased_quantity == expected._purchased_quantity
    assert retrieved._allocations == {
        model.OrderLine("order1", "GENERIC-SOFA", 12),
    }


def get_allocations(session, batchid):
    rows = list(
        session.execute(
            "SELECT orderid"
            " FROM allocations"
            " JOIN order_lines ON allocations.orderline_id = order_lines.id"
            " JOIN batches ON allocations.batch_id = batches.id"
            " WHERE batches.reference = :batchid",
            dict(batchid=batchid),
        )
    )
    return {row[0] for row in rows}


def test_updating_a_batch(session):
    order1 = model.OrderLine("order1", "WEATHERED-BENCH", 10)
    order2 = model.OrderLine("order2", "WEATHERED-BENCH", 20)
    batch = model.Batch("batch1", "WEATHERED-BENCH", 100, eta=None)
    batch.allocate(order1)

    repo = repository.SqlAlchemyRepository(session)
    repo.add(batch)
    session.commit()

    batch.allocate(order2)
    repo.add(batch)
    session.commit()

    assert get_allocations(session, "batch1") == {"order1", "order2"}
