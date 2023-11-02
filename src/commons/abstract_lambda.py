from abc import abstractmethod, ABC
from typing import Optional
import json

from commons import ApplicationException, build_response, deep_get, \
    RESPONSE_BAD_REQUEST_CODE, LambdaContext
from commons.log_helper import get_logger
from modular_sdk.commons.exception import ModularException

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


class AbstractLambdaHandler(ABC):
    @abstractmethod
    def handle_request(self, event: dict, context: LambdaContext) -> dict:
        """
        Should be implemented. May raise TelegramBotException or any
        other kind of exception
        """

    @abstractmethod
    def lambda_handler(self, event: dict, context: LambdaContext) -> dict:
        """
        Main lambda's method that is executed
        """


class EventProcessorLambdaHandler(AbstractLambdaHandler):
    event_processor: AbstractEventProcessor

    @abstractmethod
    def handle_request(self, event: dict, context: LambdaContext) -> dict:
        ...

    def lambda_handler(self, event: dict, context: LambdaContext) -> dict:
        try:
            _LOG.debug(f'Starting request: {context.aws_request_id}')
            _LOG.debug(f'Request: {event}')
            if event.get('warm_up'):
                return build_response(code=200, content='Warmed up a bit')
            self.event_processor.event = event
            processed = self.event_processor.process()
            result = self.handle_request(event=processed, context=context)
            _LOG.debug(f'Response: {result}')
            return result
        except ModularException as e:
            _LOG.error(f'Exception occurred: {e}')
            return ApplicationException(code=e.code, content=e.content) \
                .response()
        except ApplicationException as e:
            _LOG.error(f'Application exception occurred: {e}')
            return e.response()
        except Exception as e:
            _LOG.error(f'Unexpected error occurred: {e}')
            return ApplicationException(
                code=500, content='Internal server error').response()
