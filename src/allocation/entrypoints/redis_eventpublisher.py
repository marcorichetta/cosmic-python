import json
import logging
from dataclasses import asdict

import redis

from allocation import config
from allocation.domain import events

r = redis.Redis(**config.get_redis_host_and_port())


def publish(channel, event: events.Event):
    try:
        logging.debug("publishing %s to %s", event, channel)
        r.publish(channel, json.dumps(asdict(event)))  # type: ignore
    except Exception:  # pylint: disable=broad-except
        logging.exception("Failed to publish %s to %s", event, channel)
