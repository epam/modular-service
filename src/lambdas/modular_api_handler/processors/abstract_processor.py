from abc import abstractmethod
from http import HTTPStatus
from typing import Callable

from routes.route import Route

from commons.constants import Endpoint, HTTPMethod, Permission
from commons.log_helper import get_logger
from pydantic import BaseModel

_LOG = get_logger(__name__)


class AbstractCommandProcessor:
    Resp = tuple[HTTPStatus, type[BaseModel] | None, str | None]

    @classmethod
    def controller_name(cls) -> str:
        return cls.__name__

    @classmethod
    @abstractmethod
    def routes(cls) -> tuple[Route, ...]:
        """
        Must return a list of routes. See how it's built in some controller
        :return: List[Route]
        """

    def get_action_handler(self, action: str) -> Callable | None:
        """
        By default, returns class method with the same name as action.
        :return: Callable
        """
        return getattr(self, action, None)

    @classmethod
    def build(cls) -> 'AbstractCommandProcessor':
        _LOG.info(f'Building {cls.__name__} controller')
        return cls()

    @classmethod
    def route(cls, path: Endpoint, method: tuple[HTTPMethod, ...] | HTTPMethod,
              action: str, permission: Permission | None,
              summary: str | None = None,
              description: str | None = None,
              response: list[Resp] | Resp = (HTTPStatus.OK, None, None),
              require_auth: bool = True
              ) -> Route:
        """
        Just auxiliary method
        :param path:
        :param method:
        :param action: name of method to be executed for this route
        :param permission: target permission for this route, should be 
        explicitly set to None in case we want this endpoint to be 
        require no permissions
        :param summary:
        :param description:
        :param response: list of tuples with three elements: code, optional
        model and optional response description
        :param require_auth:
        :return:
        """
        if isinstance(method, HTTPMethod):
            method = (method,)
        if isinstance(response, tuple):
            response = [response]
        return Route(
            name=None,
            routepath=path.value,
            controller=cls.controller_name(),
            action=action,
            conditions={'method': method},
            # custom kwargs
            _summary=summary,
            _description=description,
            _responses=response,
            _require_auth=require_auth,
            _permission=permission
        )
