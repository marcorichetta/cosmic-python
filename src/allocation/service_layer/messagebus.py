import logging
from typing import Callable, Dict, List, Type, Union

from tenacity import RetryError, Retrying, stop_after_attempt, wait_exponential

from allocation.domain import commands, events
from allocation.service_layer import handlers
from allocation.service_layer.unit_of_work import AbstractUnitOfWork

logger = logging.getLogger(__name__)

Message = Union[events.Event, commands.Command]


def handle(message: Message, uow: AbstractUnitOfWork):
    """Entrypoint for event handling. It creates a queue, passes the events to their
    respective handlers and finally collects new events to repeat the process
    """
    results = []
    queue = [message]
    while queue:
        message = queue.pop(0)
        match message:
            case events.Event():
                # Fire and forget events
                handle_event(message, queue, uow)
            case commands.Command():
                # We care about the result of commands
                result = handle_command(message, queue, uow)
                results.append(result)
            case _:
                raise Exception(f"{message} was not an Event or Command")
    return results


def handle_event(
    event: events.Event,
    queue: List[Message],
    uow: AbstractUnitOfWork,
):
    for handler in EVENT_HANDLERS[type(event)]:
        try:
            for attempt in Retrying(
                stop=stop_after_attempt(3), wait=wait_exponential()
            ):
                with attempt:
                    logger.debug("Handling event %s with handler %s", event, handler)
                    handler(event, uow)
                    queue.extend(uow.collect_new_events())
        except RetryError as retry_failure:
            logger.error(
                "Failed to handle event %s times, giving up!",
                retry_failure.last_attempt.attempt_number,
            )

            continue


def handle_command(
    command: commands.Command,
    queue: List[Message],
    uow: AbstractUnitOfWork,
):
    logger.debug("Handling command %s", command)
    try:
        handler = COMMAND_HANDLERS[type(command)]
        result = handler(command, uow)
        queue.extend(uow.collect_new_events())
        return result
    except Exception:
        logger.exception("Exception handling command %s", command)
        raise


EVENT_HANDLERS: Dict[Type[events.Event], List[Callable]] = {
    events.BatchCreated: [handlers.add_batch],
    events.BatchQuantityChanged: [handlers.change_batch_quantity],
    events.AllocationRequired: [handlers.allocate],
    events.OutOfStock: [handlers.send_out_of_stock_notification],
}

COMMAND_HANDLERS: Dict[Type[commands.Command], Callable] = {
    commands.Allocate: handlers.allocate,
    commands.CreateBatch: handlers.add_batch,
    commands.ChangeBatchQuantity: handlers.change_batch_quantity,
}
