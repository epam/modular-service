from abc import abstractmethod
from typing import Callable
from routes.route import Route

from commons.log_helper import get_logger

_LOG = get_logger(__name__)


class AbstractCommandProcessor:
    @classmethod
    def controller_name(cls) -> str:
        return cls.__name__

    @classmethod
    @abstractmethod
    def routes(cls) -> list[Route]:
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
