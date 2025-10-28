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

    def post_to_allocate(self, orderid, sku, qty, expect_success=True):
        url = config.get_api_url()
        r = requests.post(
            f"{url}/allocate", json={"orderid": orderid, "sku": sku, "qty": qty}
        )

        # Harry agrega un expect_success flag y assert que checkea esta condicion
        # Me llama la atención pero lo comento por si acaso
        # 201 El server creó un nuevo objeto
        # 202 El server acepta procesar la request
        if expect_success:
            assert r.status_code == 202

        return r
