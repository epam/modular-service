from abc import ABC, abstractmethod
from http import HTTPStatus
import json
from typing import TypedDict

from modular_sdk.commons.exception import ModularException

from commons import RequestContext, deep_get
from commons.constants import Endpoint, HTTPMethod, Permission
from commons.lambda_response import ApplicationException, LambdaOutput, ResponseFactory
from commons.log_helper import get_logger, hide_secret_values

_LOG = get_logger(__name__)


class AbstractEventProcessor(ABC):
    __slots__ = ()

    @abstractmethod
    def __call__(self, event: dict) -> dict:
        """
        Returns somehow changed dict
        """


class NullEventProcessor(AbstractEventProcessor):
    """
    Makes nothing with an incoming event
    """

    def __call__(self, event: dict) -> dict:
        return event


class ProcessedEvent(TypedDict):
    method: HTTPMethod
    resource: Endpoint | None  # our resource if it can be matched: /jobs/{id}
    path: str  # real path without stage: /jobs/123
    fullpath: str  # full real path with stage /dev/jobs/123
    cognito_username: str | None
    cognito_customer: str | None
    cognito_user_id: str | None
    cognito_user_role: str | None
    permission: Permission | None
    is_system: bool
    body: dict  # maybe better str in order not to bind to json
    query: dict
    path_params: dict


class ApiGatewayEventProcessor(AbstractEventProcessor):
    def __call__(self, event: dict) -> ProcessedEvent:
        try:
            body = json.loads(event.get('body') or '{}')
        except json.JSONDecodeError as e:
            raise ResponseFactory(HTTPStatus.BAD_REQUEST).message(
                f'Invalid request body: \'{e}\''
            ).exc()
        rc = event.get('requestContext') or {}
        return {
            'method': HTTPMethod(event['httpMethod']),
            'resource': Endpoint.match(rc['resourcePath']),
            'path': event['path'],
            'fullpath': rc['path'],
            'cognito_username': deep_get(rc, ('authorizer', 'claims',
                                              'cognito:username')),
            'cognito_customer': deep_get(rc, ('authorizer', 'claims',
                                              'custom:customer')),
            'cognito_user_id': deep_get(rc, ('authorizer', 'claims', 'sub')),
            'cognito_user_role': deep_get(rc, ('authorizer', 'claims',
                                               'custom:role')),
            'permission': None,  # will be set later
            'is_system': deep_get(rc, ('authorizer', 'claims', 
                                       'custom:is_system')) or False,
            'body': body,
            'query': dict(event.get('queryStringParameters') or {}),
            'path_params': dict(event.get('pathParameters') or {})
        }


class RestrictCustomerEventProcessor(AbstractEventProcessor):
    """
    Each user has its own customer but a system user should be able to 
    perform actions on behalf of any customer. Every request model has 
    customer_id attribute that is used by handlers to manage entities of 
    that customer. This processor inserts user's customer to each event body.
    Allows to provide customer_id only for system users
    """
    def __call__(self, event: ProcessedEvent) -> ProcessedEvent:
        if not event['cognito_user_id']:
            # endpoint without auth
            return event
        if event['is_system']:
            return event
        match event['method']:
            case HTTPMethod.GET:
                event['query']['customer_id'] = event['cognito_customer']
            case _:
                event['body']['customer_id'] = event['cognito_customer']
        return event


class AbstractLambdaHandler(ABC):
    @abstractmethod
    def handle_request(self, event: ProcessedEvent, context: RequestContext
                       ) -> LambdaOutput:
        """
        Should be implemented. May raise TelegramBotException or any
        other kind of exception
        """

    @abstractmethod
    def lambda_handler(self, event: dict, context: RequestContext
                       ) -> LambdaOutput:
        """
        Main lambda's method that is executed
        """


class EventProcessorLambdaHandler(AbstractLambdaHandler):
    processors: tuple[AbstractEventProcessor, ...] = ()

    @abstractmethod
    def handle_request(self, event: ProcessedEvent,
                       context: RequestContext) -> LambdaOutput:
        ...

    def lambda_handler(self, event: dict, context: RequestContext
                       ) -> LambdaOutput:
        _LOG.info(f'Starting request: {context.aws_request_id}')
        # This is the only place where we print the event. Do not print it
        # somewhere else
        _LOG.debug('Incoming event')
        _LOG.debug(json.dumps(hide_secret_values(event)))

        try:
            for processor in self.processors:
                event = processor(event)
            return self.handle_request(event=event, context=context)
        except ApplicationException as e:
            _LOG.warning(f'Application exception occurred: {e}')
            return e.build()
        except ModularException as e:
            _LOG.warning('Modular exception occurred', exc_info=True)
            return ResponseFactory(int(e.code)).message(e.content).build()
        except Exception:  # noqa
            _LOG.exception('Unexpected exception occurred')
            return ResponseFactory(
                HTTPStatus.INTERNAL_SERVER_ERROR
            ).default().build()
