import json
import logging

import redis

from allocation.adapters import orm
from allocation.domain import commands
from allocation.service_layer import messagebus, unit_of_work
from src.allocation import config

r = redis.Redis(**config.get_redis_host_and_port())


def main():
    """Executes on load and subscribes to Redis channel"""
    orm.start_mappers()
    pubsub = r.pubsub(ignore_subscribe_messages=True)
    pubsub.subscribe("change_batch_quantity")

    for message in pubsub.listen():
        handle_change_batch_quantity(message)


def handle_change_batch_quantity(message):
    logging.debug("handling %s", message)
    data = json.loads(message["data"])
    cmd = commands.ChangeBatchQuantity(
        reference=data["batchref"], quantity=data["quantity"]
    )
    messagebus.handle(cmd, uow=unit_of_work.SqlAlchemyUnitOfWork())
