import pytest

from tests.e2e.api_client import APIClient
from tests.random_refs import random_batchref, random_orderid, random_sku


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.usefixtures("postgres_db")
@pytest.mark.usefixtures("restart_api")
def test_happy_path_returns_201_and_allocated_batch(api_client):
    sku, othersku = random_sku(), random_sku("other")
    earlybatch = random_batchref("1")
    laterbatch = random_batchref("2")
    otherbatch = random_batchref("3")

    api_client.post_to_add_batch(laterbatch, sku, 100, "2011-01-02")
    api_client.post_to_add_batch(earlybatch, sku, 100, "2011-01-01")
    api_client.post_to_add_batch(otherbatch, othersku, 100, None)

    r = api_client.post_to_allocate(random_orderid(), sku, 3)

    assert r.status_code == 201
    assert r.json()["ref"] == earlybatch


@pytest.mark.usefixtures("restart_api")
def test_unhappy_path_returns_400_and_error_message(api_client):
    unknown_sku, orderid = random_sku(), random_orderid()
    r = api_client.post_to_allocate(orderid, unknown_sku, 20)
    assert r.status_code == 400
    assert r.json()["message"] == f"Invalid sku {unknown_sku}"
