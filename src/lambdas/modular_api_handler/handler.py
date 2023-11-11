from typing import Optional, Dict, Type, List

from routes import Mapper
from functools import cached_property

from commons import RESPONSE_RESOURCE_NOT_FOUND_CODE, LambdaContext
from commons.abstract_lambda import EventProcessorLambdaHandler, \
    ApiGatewayEventProcessor
from commons.constants import REQUEST_METHOD_WSGI_ENV
from commons.exception import ApplicationException
from commons.log_helper import get_logger
from lambdas.modular_api_handler.processors.abstract_processor import \
    AbstractCommandProcessor
from lambdas.modular_api_handler.processors.application_processor import \
    ApplicationProcessor
from lambdas.modular_api_handler.processors.customer_processor import \
    CustomerProcessor
from lambdas.modular_api_handler.processors.parent_processor import \
    ParentProcessor
from lambdas.modular_api_handler.processors.policies_processor import \
    PolicyProcessor
from lambdas.modular_api_handler.processors.region_processor import \
    RegionProcessor
from lambdas.modular_api_handler.processors.role_processor import RoleProcessor
from lambdas.modular_api_handler.processors.signin_processor import \
    SignInProcessor
from lambdas.modular_api_handler.processors.signup_processor import \
    SignUpProcessor
from lambdas.modular_api_handler.processors.tenant_in_region_processor import \
    TenantRegionProcessor
from lambdas.modular_api_handler.processors.tenant_processor import \
    TenantProcessor
from services.abstract_api_handler_lambda import AbstractApiHandlerLambda

_LOG = get_logger('ModularApiHandler')

SIGNIN_ACTION = 'signin'
SIGNUP_ACTION = 'signup'
POLICY_ACTION = 'policy'
ROLE_ACTION = 'role'
CUSTOMER_ACTION = 'customer'
TENANT_ACTION = 'tenant'
TENANT_REGION_ACTION = 'tenant_region'
APPLICATION_ACTION = 'application'
PARENT_ACTION = 'parent'
REGION_ACTION = 'region'


class ModularApiHandler(AbstractApiHandlerLambda):
    event_processor = ApiGatewayEventProcessor()

    def __init__(self):
        self._mapper: Optional[Mapper] = None

        self._controllers: Dict[str, AbstractCommandProcessor] = {}

    def get_controller(self, controller_class: Type[AbstractCommandProcessor]
                       ) -> AbstractCommandProcessor:
        name = controller_class.controller_name()
        if name not in self._controllers:
            self._controllers[name] = controller_class.build()
        return self._controllers[name]

    @cached_property
    def controller_classes(self) -> List[Type[AbstractCommandProcessor]]:
        return [
            SignUpProcessor,
            SignInProcessor,
            PolicyProcessor,
            RoleProcessor,
            CustomerProcessor,
            TenantProcessor,
            TenantRegionProcessor,
            ApplicationProcessor,
            ParentProcessor,
            RegionProcessor
        ]

    def _build_mapper(self) -> Mapper:
        mapper = Mapper()
        for controller_class in self.controller_classes:
            controller = self.get_controller(controller_class)
            mapper.extend(controller.routes())
        return mapper

    @property
    def mapper(self) -> Mapper:
        if not self._mapper:
            _LOG.debug('Building mapper')
            self._mapper = self._build_mapper()
            _LOG.debug('Mapper was built')
        return self._mapper

    def validate_request(self, event: dict) -> dict:
        pass

    def handle_request(self, event: dict, context: LambdaContext):
        path, method = event.get('path'), event.get('method')
        match_result = self.mapper.match(
            path, {REQUEST_METHOD_WSGI_ENV: method})
        if not match_result:
            raise ApplicationException(
                code=RESPONSE_RESOURCE_NOT_FOUND_CODE,
                content=f'{method} {path} not found'
            )
        controller = match_result.pop('controller')
        action = match_result.pop('action')
        # it's expected that the mapper is configured properly because
        # if it is, there could be no KeyError
        handler = self._controllers[controller].get_action_handler(action)
        # give the handler kwargs
        return handler(event=event['body'], **match_result)


HANDLER = ModularApiHandler()


def lambda_handler(event: dict, context: LambdaContext):
    return HANDLER.lambda_handler(event=event, context=context)
