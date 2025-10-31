import inspect
from typing import Callable

from allocation.adapters import notifications, orm
from allocation.entrypoints import redis_eventpublisher
from allocation.service_layer import handlers, messagebus, unit_of_work


def bootstrap(
    start_orm: bool = True,
    uow: unit_of_work.AbstractUnitOfWork | None = None,
    notifications_provider: notifications.AbstractNotifications | None = None,
    publish: Callable = redis_eventpublisher.publish,
) -> messagebus.MessageBus:
    """
    We want our bootstrap script to do the following:
    Declare default dependencies but allow us to override them
    Do the "init" stuff that we need to get our app started
    Inject all the dependencies into our handlers
    Give us back the core object for our app, the message bus
    """

    if start_orm:
        orm.start_mappers()

    if not uow:
        uow = unit_of_work.SqlAlchemyUnitOfWork()

    if not notifications_provider:
        notifications_provider = notifications.EmailNotifications()

    dependencies = {
        "uow": uow,
        "notifications": notifications_provider,
        "publish": publish,
    }
    injected_event_handlers = {
        event_type: [
            inject_dependencies(handler, dependencies) for handler in event_handlers
        ]
        for event_type, event_handlers in handlers.EVENT_HANDLERS.items()
    }

    injected_command_handlers = {
        command_type: inject_dependencies(handler, dependencies)
        for command_type, handler in handlers.COMMAND_HANDLERS.items()
    }

    return messagebus.MessageBus(
        uow=uow,
        event_handlers=injected_event_handlers,
        command_handlers=injected_command_handlers,
    )


def inject_dependencies(handler, dependencies):
    """
    Inject dependencies into a message handler function.

    This function performs dependency injection by inspecting a handler's signature
    and providing only the dependencies that match the handler's parameter names.

    Read: https://www.cosmicpython.com/book/chapter_13_dependency_injection.html > Even-More-Manual DI with Less Magic
    """
    params = inspect.signature(handler).parameters
    deps = {
        name: dependency for name, dependency in dependencies.items() if name in params
    }
    return lambda message: handler(message, **deps)
