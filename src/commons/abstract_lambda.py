from abc import abstractmethod, ABC
from typing import Optional
import json

from commons import build_response, deep_get, RESPONSE_BAD_REQUEST_CODE
from commons.log_helper import get_logger

_LOG = get_logger(__name__)

ACTION_PARAM = 'action'
PARAM_HTTP_METHOD = 'http_method'


class AbstractEventProcessor(ABC):
    def __init__(self, event: Optional[dict] = None):
        self._event = event or {}  # the crudest event we can get

    @property
    def event(self) -> dict:
        return self._event

    @event.setter
    def event(self, value: dict):
        self._event = value

    @abstractmethod
    def process(self) -> dict:
        """
        Returns somehow changed dict.
        :return: dict
        """


class NullEventProcessor(AbstractEventProcessor):
    """
    Makes nothing with an incoming event
    """

    def process(self) -> dict:
        return self._event


class ApiGatewayEventProcessor(AbstractEventProcessor):
    """
    Should somehow process or/and validated event in case we decide
    to use API Gateway.
    Returns an event in such a format:
    {
        'path': '/path/without/stage',
        'method': 'POST',
        'body': {
            'one': 'two'
        }
    }
    """

    def process(self) -> dict:
        event = self._event
        path = deep_get(event, ['requestContext', 'resourcePath'])
        method = event.get('httpMethod')
        assert path and method, 'Invalid lambda proxy integration event'
        try:
            body = json.loads(event.get('body') or '{}')
        except json.JSONDecodeError as e:
            return build_response(code=RESPONSE_BAD_REQUEST_CODE,
                                  content=f'Invalid request body: \'{e}\'')
        body.update(event.get('queryStringParameters') or {})
        #  body.update(event.get('pathParameters') or {})
        return {
            'path': path,
            'method': method,
            'body': body
        }
