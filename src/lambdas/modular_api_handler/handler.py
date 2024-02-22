from http import HTTPStatus

from routes import Mapper

from commons import RequestContext
from commons.abstract_lambda import ApiGatewayEventProcessor, \
    CheckPermissionEventProcessor, EventProcessorLambdaHandler, ProcessedEvent
from commons.constants import REQUEST_METHOD_WSGI_ENV, HTTPMethod
from commons.lambda_response import ResponseFactory
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

_LOG = get_logger('modular_api_handler')


class ModularApiHandler(EventProcessorLambdaHandler):
    processors = (
        ApiGatewayEventProcessor(),
        CheckPermissionEventProcessor()
    )
    controller_classes = (
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
    )
    __slots__ = ('_mapper', '_controllers')

    def __init__(self):
        self._mapper: Mapper | None = None
        self._controllers: dict[str, AbstractCommandProcessor] = {}

    def get_controller(self, controller_class: type[AbstractCommandProcessor]
                       ) -> AbstractCommandProcessor:
        name = controller_class.controller_name()
        if name not in self._controllers:
            self._controllers[name] = controller_class.build()
        return self._controllers[name]

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

    def handle_request(self, event: ProcessedEvent, context: RequestContext):
        path, method = event['path'], event['method']
        match_result = self.mapper.match(
            path, {REQUEST_METHOD_WSGI_ENV: method}
        )
        if not match_result:
            raise ResponseFactory(HTTPStatus.NOT_FOUND).message(
                f'{method} {path} not found'
            ).exc()
        controller = match_result.pop('controller')
        action = match_result.pop('action')
        # it's expected that the mapper is configured properly because
        # if it is, there could be no KeyError
        handler = self._controllers[controller].get_action_handler(action)
        # give the handler kwargs
        # TODO insert other kwargs if needed
        match method:
            case HTTPMethod.GET:
                body = event['query']
            case _:
                body = event['body']
        return handler(event=body, **match_result)


HANDLER = ModularApiHandler()


def lambda_handler(event: dict, context: RequestContext):
    return HANDLER.lambda_handler(event=event, context=context)
