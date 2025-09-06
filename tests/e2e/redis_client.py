import json

import redis

from allocation import config


class RedisClient:
    def __init__(self):
        self._redis = redis.Redis(**config.get_redis_host_and_port())

    def publish_message(self, channel, message):
        self._redis.publish(channel, json.dumps(message))

    def subscribe_to(self, channel):
        pubsub = self._redis.pubsub()
        pubsub.subscribe(channel)
        confirmation = pubsub.get_message(timeout=3)
        assert confirmation["type"] == "subscribe"  # type: ignore
        return pubsub
