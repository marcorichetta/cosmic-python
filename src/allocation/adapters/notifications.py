import abc
import smtplib

import apprise

from allocation import config
from allocation.config import ADMIN_EMAIL, DISCORD_WEBHOOK_ID, DISCORD_WEBHOOK_TOKEN

DEFAULT_HOST = config.get_email_host_and_port()["host"]
DEFAULT_PORT = config.get_email_host_and_port()["port"]


class AbstractNotifications(abc.ABC):
    @abc.abstractmethod
    def send(self, destination, message):
        raise NotImplementedError


class EmailNotifications(AbstractNotifications):
    def __init__(self, smtp_host=DEFAULT_HOST, port=DEFAULT_PORT):
        self.server = smtplib.SMTP(host=smtp_host, port=port)
        self.server.noop()

    def send(self, destination, message):
        msg = f"Subject: Allocation Service notification\n{message}"
        self.server.sendmail(from_addr=ADMIN_EMAIL, to_addrs=[destination], msg=msg)


class DiscordNotifications(AbstractNotifications):
    def __init__(
        self, webhook_id=DISCORD_WEBHOOK_ID, webhook_token=DISCORD_WEBHOOK_TOKEN
    ):
        self.url = f"discord://{webhook_id}/{webhook_token}/"

        self.appriseProvider = apprise.Apprise()
        self.appriseProvider.add(self.url)

    def send(self, destination, message):
        self.appriseProvider.notify(
            body="Successful Allocation @everyone", title="Hola"
        )
