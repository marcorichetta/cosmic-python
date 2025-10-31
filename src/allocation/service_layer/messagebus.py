import logging
from typing import Callable, Union

from tenacity import RetryError, Retrying, stop_after_attempt, wait_exponential

from allocation.domain import commands, events
from allocation.service_layer import unit_of_work

logger = logging.getLogger(__name__)

Message = Union[events.Event, commands.Command]


class MessageBus:
    def __init__(
        self,
        uow: unit_of_work.AbstractUnitOfWork,
        event_handlers: dict[type[events.Event], list[Callable]],
        command_handlers: dict[type[commands.Command], Callable],
    ) -> None:
        self.uow = uow
        self.event_handlers = event_handlers
        self.command_handlers = command_handlers

    def handle(self, message: Message):
        """Entrypoint for event handling. It creates a queue, passes the events to their
        respective handlers and finally collects new events to repeat the process
        """
        # Using self.queue like this is not thread-safe,
        # which might be a problem if you’re using threads,
        # because the bus instance is global in the Flask app context.
        self.queue = [message]
        while self.queue:
            message = self.queue.pop(0)
            match message:
                case events.Event():
                    # Fire and forget events
                    self.handle_event(message)
                case commands.Command():
                    # We care about the result of commands
                    self.handle_command(message)
                case _:
                    raise Exception(f"{message} was not an Event or Command")

    def handle_event(
        self,
        event: events.Event,
    ):
        for handler in self.event_handlers[type(event)]:
            try:
                for attempt in Retrying(
                    stop=stop_after_attempt(3), wait=wait_exponential()
                ):
                    with attempt:
                        logger.debug(
                            "Handling event %s with handler %s", event, handler
                        )
                        handler(event)
                        self.queue.extend(self.uow.collect_new_events())
            except RetryError as retry_failure:
                logger.error(
                    "Failed to handle event %s times, giving up!",
                    retry_failure.last_attempt.attempt_number,
                )

                continue

    def handle_command(
        self,
        command: commands.Command,
    ):
        logger.debug("Handling command %s", command)
        try:
            handler = self.command_handlers[type(command)]
            handler(command)
            self.queue.extend(self.uow.collect_new_events())
        except Exception:
            logger.exception("Exception handling command %s", command)
            raise
