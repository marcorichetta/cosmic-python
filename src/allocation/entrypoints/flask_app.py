import logging
from datetime import datetime

from flask import Flask, jsonify, request

from allocation import bootstrap, views
from allocation.domain import commands
from allocation.service_layer import handlers, unit_of_work

logger = logging.getLogger(__name__)

app = Flask(__name__)
bus = bootstrap.bootstrap()


@app.route("/batches", methods=["POST"])
def add_batch():
    eta = request.json["eta"]
    if eta is not None:
        eta = datetime.fromisoformat(eta).date()

    try:
        cmd = commands.CreateBatch(
            request.json["ref"], request.json["sku"], request.json["qty"], eta
        )

        results = bus.handle(cmd)
        reference = results[0] if results else None

    except Exception as e:
        logger.exception(e)
        return {"message": str(e)}, 400

    return {"batchref": reference}, 201


@app.route("/allocate", methods=["POST"])
def allocate():
    uow = unit_of_work.SqlAlchemyUnitOfWork()

    try:
        cmd = commands.Allocate(
            request.json["orderid"],
            request.json["sku"],
            request.json["qty"],
        )

        results = bus.handle(cmd)
        batchref = results.pop(0)
    except handlers.InvalidSku as e:
        return {"message": str(e)}, 400

    return {"batchref": batchref}, 202


@app.route("/allocations/<orderid>", methods=["GET"])
def allocations_view(orderid: str):
    uow = unit_of_work.SqlAlchemyUnitOfWork()

    result = views.allocations(orderid, uow)
    if not result:
        return {"message": "not found"}, 404

    return jsonify(result), 200
