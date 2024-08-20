import pytest
from service_layer import unit_of_work
from tests.integration.test_repository import insert_batch


def test_rolls_back_uncommited_work_by_default(session_factory):
    uow = unit_of_work.SqlAlchemyUnitOfWork(session_factory)
    with uow:
        insert_batch(uow.session, "batch1", "ITEM-1", 100, None)

    new_session = session_factory()
    rows = list(new_session.execute('SELECT * FROM "batches"'))
    assert rows == []


def test_rolls_back_on_error(session_factory):
    class CustomException(Exception):
        ...

    uow = unit_of_work.SqlAlchemyUnitOfWork(session_factory)
    with pytest.raises(CustomException):
        with uow:
            insert_batch(uow.session, "batch1", "ITEM-1", 100, None)
            raise CustomException()

    new_session = session_factory()
    rows = list(new_session.execute('SELECT * FROM "batches"'))
    assert rows == []
