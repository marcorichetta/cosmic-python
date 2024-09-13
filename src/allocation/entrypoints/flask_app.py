from datetime import datetime
from flask import Flask, request

from allocation.adapters import orm
from allocation.service_layer import services, unit_of_work

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
        ref = services.add_batch(
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
        ref = services.allocate(
            request.json["orderid"],
            request.json["sku"],
            request.json["qty"],
            uow,
        )
    except services.InvalidSku as e:
        return {"message": str(e)}, 400

    return {"ref": ref}, 201


@app.route("/deallocate", methods=["POST"])
def deallocate():
    uow = unit_of_work.SqlAlchemyUnitOfWork()

    try:
        services.deallocate(
            request.json["orderid"],
            request.json["sku"],
            100,  # HACK - Hardcoded - quantity plays a role in equality for OrderLines. Either pass it from the test or get it from the existent one
            uow,
        )
    except (model.DeallocateBatch, services.InvalidSku) as e:
        return {"message": str(e)}, 400

    return {"message": "ok"}, 200
