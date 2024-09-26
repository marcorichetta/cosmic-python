import logging
from datetime import datetime

from flask import Flask, request

from allocation.adapters import orm
from allocation.domain import events
from allocation.service_layer import handlers, messagebus, unit_of_work

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
        event = events.BatchCreated(
            request.json["ref"], request.json["sku"], request.json["qty"], eta
        )

        [reference] = messagebus.handle(event, uow)

    except Exception as e:
        logger.exception(e)
        return {"message": str(e)}, 400

    return {"ref": reference}, 201


@app.route("/allocate", methods=["POST"])
def allocate():
    uow = unit_of_work.SqlAlchemyUnitOfWork()

    try:
        event = events.AllocationRequired(
            request.json["orderid"],
            request.json["sku"],
            request.json["qty"],
        )
        results = messagebus.handle(event, uow)
        ref = results.pop(0)
    except handlers.InvalidSku as e:
        return {"message": str(e)}, 400

    return {"ref": ref}, 201
