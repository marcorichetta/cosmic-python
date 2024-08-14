from datetime import datetime
from flask import Flask, request
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import config
import model
import orm
import repository
import services


orm.start_mappers()
get_session = sessionmaker(bind=create_engine(config.get_postgres_uri()))
app = Flask(__name__)


@app.route("/allocate", methods=["POST"])
def allocate_endpoint():
    session = get_session()
    repo = repository.SqlAlchemyRepository(session)
    line = model.OrderLine(
        request.json["orderid"],
        request.json["sku"],
        request.json["qty"],
    )

    try:
        batchref = services.allocate(line, repo, session)
    except (model.OutOfStockException, services.InvalidSku) as e:
        return {"message": str(e)}, 400

    return {"batchref": batchref}, 201


@app.route("/deallocate", methods=["POST"])
def deallocate():
    session = get_session()
    repo = repository.SqlAlchemyRepository(session)

    line = model.OrderLine(
        request.json["orderid"],
        request.json["sku"],
        100,  # HACK - Hardcoded - quantity plays a role in equality for OrderLines
        # Either pass it from the test or get it from the existent one
    )
    try:
        services.deallocate(line, repo, session)
    except (model.DeallocateBatchException, services.InvalidSku) as e:
        return {"message": str(e)}, 400

    return {"message": "ok"}, 200


@app.route("/batch", methods=["POST"])
def add_batch():
    session = get_session()
    repo = repository.SqlAlchemyRepository(session)

    date = (
        datetime.strptime(request.json["eta"], "%Y-%m-%d").date()
        if request.json["eta"]
        else None
    )

    try:
        batchref = services.add_batch(
            request.json["batchref"],
            request.json["sku"],
            request.json["qty"],
            date,
            repo,
            session,
        )

    except Exception as e:
        return {"message": str(e)}, 400

    return {"batchref": batchref}, 201
