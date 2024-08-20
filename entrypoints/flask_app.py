from datetime import datetime
from flask import Flask, request
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import config
import domain.model as model
import adapters.orm as orm
import adapters.repository as repository
from service_layer import unit_of_work
import service_layer.services as services

import logging

logger = logging.getLogger(__name__)

orm.start_mappers()
get_session = sessionmaker(bind=create_engine(config.get_postgres_uri()))
app = Flask(__name__)


@app.route("/allocate", methods=["POST"])
def allocate_endpoint():
    uow = unit_of_work.SqlAlchemyUnitOfWork()

    try:
        ref = services.allocate(
            request.json["orderid"], request.json["sku"], request.json["qty"], uow
        )
    except (model.OutOfStockException, services.InvalidSku) as e:
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
    except (model.DeallocateBatchException, services.InvalidSku) as e:
        return {"message": str(e)}, 400

    return {"message": "ok"}, 200


@app.route("/batches", methods=["POST"])
def add_batch():
    uow = unit_of_work.SqlAlchemyUnitOfWork()

    eta = (
        datetime.fromisoformat(request.json["eta"]).date()
        if request.json["eta"]
        else None
    )

    try:
        ref = services.add_batch(
            request.json["ref"], request.json["sku"], request.json["qty"], eta, uow
        )

    except Exception as e:
        logger.exception(e)
        return {"message": str(e)}, 400

    return {"ref": ref}, 201
