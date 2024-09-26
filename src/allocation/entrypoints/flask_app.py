from datetime import datetime
from flask import Flask, request

from allocation.adapters import orm
from allocation.service_layer import handlers, unit_of_work

import logging

logger = logging.getLogger(__name__)

app = Flask(__name__)
orm.start_mappers()


@app.route("/batches", methods=["POST"])
def add_batch():
    uow = unit_of_work.SqlAlchemyUnitOfWork()

    eta = request.json["eta"]
    if eta is not None:
        eta = datetime.fromisoformat(eta).date()

    try:
        ref = handlers.add_batch(
            request.json["ref"], request.json["sku"], request.json["qty"], eta, uow
        )

    except Exception as e:
        logger.exception(e)
        return {"message": str(e)}, 400

    return {"ref": ref}, 201


@app.route("/allocate", methods=["POST"])
def allocate():
    uow = unit_of_work.SqlAlchemyUnitOfWork()

    try:
        ref = handlers.allocate(
            request.json["orderid"],
            request.json["sku"],
            request.json["qty"],
            uow,
        )
    except handlers.InvalidSku as e:
        return {"message": str(e)}, 400

    return {"ref": ref}, 201
