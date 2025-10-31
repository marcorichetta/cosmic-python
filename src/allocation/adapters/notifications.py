import abc
import smtplib

from allocation import config

DEFAULT_HOST = config.get_email_host_and_port()["host"]
DEFAULT_PORT = config.get_email_host_and_port()["port"]
ADMIN_EMAIL = "allocations@example.com"


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
