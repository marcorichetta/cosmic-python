import requests

from allocation import config


class APIClient:
    def post_to_add_batch(self, ref, sku, qty, eta):
        url = config.get_api_url()
        r = requests.post(
            f"{url}/batches",
            json={"ref": ref, "sku": sku, "qty": qty, "eta": eta},
        )
        assert r.status_code == 201
        return r

    def post_to_allocate(self, orderid, sku, qty):
        url = config.get_api_url()
        r = requests.post(
            f"{url}/allocate", json={"orderid": orderid, "sku": sku, "qty": qty}
        )
        assert r.status_code == 201
        return r
