from http import HTTPStatus
import inspect
from typing import Generator

from pydantic import BaseModel
from routes import Mapper
from routes.route import Route

from commons import RequestContext
from commons.abstract_lambda import (
    AbstractEventProcessor,
    ApiGatewayEventProcessor,
    EventProcessorLambdaHandler,
    ProcessedEvent,
)
from commons.constants import Endpoint, HTTPMethod, Permission, REQUEST_METHOD_WSGI_ENV
from commons.lambda_response import ResponseFactory
from commons.log_helper import get_logger
from lambdas.modular_api_handler.processors.abstract_processor import (
    AbstractCommandProcessor,
)
from lambdas.modular_api_handler.processors.application_processor import (
    ApplicationProcessor,
)
from lambdas.modular_api_handler.processors.customer_processor import CustomerProcessor
from lambdas.modular_api_handler.processors.parent_processor import ParentProcessor
from lambdas.modular_api_handler.processors.policies_processor import PolicyProcessor
from lambdas.modular_api_handler.processors.region_processor import RegionProcessor
from lambdas.modular_api_handler.processors.role_processor import RoleProcessor
from lambdas.modular_api_handler.processors.health_processor import HealthCheckProcessor
from lambdas.modular_api_handler.processors.tenant_in_region_processor import (
    TenantRegionProcessor,
)
from lambdas.modular_api_handler.processors.users_processor import UsersProcessor
from lambdas.modular_api_handler.processors.tenant_processor import TenantProcessor
from lambdas.modular_api_handler.processors.tenant_settings_processor import (
    TenantSettingsProcessor,
)
from lambdas.modular_api_handler.processors.swagger_processor import SwaggerProcessor
from services.customer_mutator_service import CustomerMutatorService
from services import SP
from services.openapi_spec_generator import EndpointInfo
from services.rbac_service import RBACService
from validators.response import MessageModel, common_responses

_LOG = get_logger('modular_api_handler')


class RestrictCustomerEventProcessor(AbstractEventProcessor):
    """
    Each user has its own customer but a system user should be able to
    perform actions on behalf of any customer. Every request model has
    customer_id attribute that is used by handlers to manage entities of
    that customer. This processor inserts user's customer to each event body.
    Allows to provide customer_id only for system users
    """
    __slots__ = '_cs',

    # TODO organize this collection somehow else
    can_work_without_customer_id = {
        (Endpoint.CUSTOMERS, HTTPMethod.GET),
        (Endpoint.CUSTOMERS, HTTPMethod.POST),
        (Endpoint.CUSTOMERS_NAME, HTTPMethod.GET),
        (Endpoint.CUSTOMERS_NAME, HTTPMethod.PATCH),
        (Endpoint.CUSTOMERS_NAME_ACTIVATE, HTTPMethod.POST),
        (Endpoint.CUSTOMERS_NAME_DEACTIVATE, HTTPMethod.POST),

        (Endpoint.REGIONS, HTTPMethod.GET),
        (Endpoint.REGIONS, HTTPMethod.POST),
        (Endpoint.REGIONS, HTTPMethod.DELETE),

        (Endpoint.USERS_WHOAMI, HTTPMethod.GET),
        (Endpoint.USERS_RESET_PASSWORD, HTTPMethod.POST),
        (Endpoint.USERS, HTTPMethod.GET),
        (Endpoint.USERS_USERNAME, HTTPMethod.PATCH),
        (Endpoint.USERS_USERNAME, HTTPMethod.DELETE),
        (Endpoint.USERS_USERNAME, HTTPMethod.GET),
    }

    def __init__(self, customer_service: CustomerMutatorService):
        self._cs = customer_service

    def __call__(self, event: ProcessedEvent) -> ProcessedEvent:
        if not event['cognito_user_id']:
            # endpoint without auth
            return event
        if event['is_system']:
            # is system user is making a request it should provide customer_id
            # as a parameter to make a request on his behalf.
            if (event['resource'], event['method']) in self.can_work_without_customer_id:  # noqa
                return event
            cid = (event['query'].get('customer_id')
                   or event['body'].get('customer_id'))
            if not cid:
                raise ResponseFactory(HTTPStatus.BAD_REQUEST).message(
                    'Please, provide customer_id param to make a request on '
                    'his behalf'
                ).exc()
            if not self._cs.get(cid):
                raise ResponseFactory(HTTPStatus.BAD_REQUEST).message(
                    f'Customer {cid} does not exist. You cannot make a request'
                    f' on his behalf'
                ).exc()
            return event
        match event['method']:
            case HTTPMethod.GET:
                event['query']['customer_id'] = event['cognito_customer']
            case _:
                event['body']['customer_id'] = event['cognito_customer']
        return event


class CheckPermissionEventProcessor(AbstractEventProcessor):
    """
    Processor that restricts rbac permission
    """
    __slots__ = ('_rs', '_mapping')

    def __init__(self, rbac_service: RBACService,
                 mapping: dict[tuple[Endpoint, HTTPMethod], Permission | None]):
        self._rs = rbac_service
        self._mapping = mapping

    def __call__(self, event: ProcessedEvent) -> ProcessedEvent:
        if event['is_system']:
            return event
        username = event['cognito_username']
        if not username:
            return event
        if not event['resource']:
            _LOG.warning('A request for not known resource')
            return event
        permission = self._mapping.get((event['resource'], event['method']))
        if not permission:
            _LOG.info('No permission exist for endpoint, allowing')
            return event
        # if cognito_username exists, cognito_customer & cognito_user_role
        # exist as well
        if not self._rs.is_allowed(event['cognito_customer'], event['cognito_user_role'], permission):
            _LOG.info('Not allowed to access')
            raise ResponseFactory(HTTPStatus.FORBIDDEN).message(
                f'You don\'t have the necessary permission: {permission}'
            ).exc()  # todo maybe return missing permission in a separate key
        event['permission'] = permission
        return event


class ModularApiHandler(EventProcessorLambdaHandler):
    controller_classes = (
        PolicyProcessor,
        RoleProcessor,
        CustomerProcessor,
        TenantProcessor,
        TenantRegionProcessor,
        ApplicationProcessor,
        ParentProcessor,
        RegionProcessor,
        TenantSettingsProcessor,
        HealthCheckProcessor,
        SwaggerProcessor,
        UsersProcessor
    )
    __slots__ = ('_mapper', '_controllers', 'processors')

    def __init__(self):
        self._mapper: Mapper | None = None
        self._controllers: dict[str, AbstractCommandProcessor] = {}

        self.processors = (
            ApiGatewayEventProcessor(),
            RestrictCustomerEventProcessor(
                customer_service=SP.customer_service
            ),
            CheckPermissionEventProcessor(
                rbac_service=SP.rbac_service,
                mapping=self._build_permissions_mapping()
            )
        )

    def _build_permissions_mapping(self) -> dict[tuple[Endpoint, HTTPMethod], Permission | None]:
        res = {}
        for route in self.mapper.matchlist:
            route: Route
            kargs = route._kargs
            for method in route.conditions['method']:
                if isinstance(method, str):
                    method = HTTPMethod(method.upper())
                path = Endpoint(route.routepath)  # should always match
                res[(path, method)] = kargs.get('_permission')
        return res

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
        to_pop = ('_summary', '_description', '_responses', '_require_auth', 
                  '_permission')
        for k in to_pop:
            match_result.pop(k, None)
        # it's expected that the mapper is configured properly because
        # if it is, there could be no KeyError
        handler = self._controllers[controller].get_action_handler(action)
        match method:
            case HTTPMethod.GET:
                body = event['query']
            case _:
                body = event['body']
        params = dict(event=body, **match_result)
        sign = inspect.signature(handler)
        if '_pe' in sign.parameters:
            # if you need to access raw event data inside event
            _LOG.debug('Expanding handler payload with raw event')
            params['_pe'] = event
        return handler(**params)

    def iter_endpoint(self) -> Generator[EndpointInfo, None, None]:
        """
        For swagger. The collection of EndpointInfo(s) can be hardcoded or
        generated some other way. I think this is quite convenient. Just add
        a new endpoint and it will automatically appear in swagger
        :return:
        """
        for route in self.mapper.matchlist:
            route: Route
            kargs = route._kargs
            controller, action = kargs['controller'], kargs['action']
            handler = self._controllers[controller].get_action_handler(action)
            annotations = handler.__annotations__
            req = annotations.get('event')
            if not isinstance(req, type) or not issubclass(req, BaseModel):
                req = None

            # expanding responses with common ones
            responses = kargs.get('_responses') or []
            existing = {r[0] for r in responses}
            for code, model, description in common_responses:
                if code in existing:
                    continue
                responses.append((code, model, description))
            if '{' in route.routepath and HTTPStatus.NOT_FOUND not in existing:
                responses.append(
                    (HTTPStatus.NOT_FOUND, MessageModel, 'Entity is not found')
                )
            responses.sort(key=lambda x: x[0])

            for method in route.conditions['method']:
                yield EndpointInfo(
                    path=route.routepath,
                    method=method if isinstance(method, HTTPMethod) else HTTPMethod(method.upper()),
                    summary=kargs.get('_summary'),
                    description=kargs.get('_description'),
                    request_model=req,
                    responses=responses,
                    auth=kargs['_require_auth']
                )


HANDLER = ModularApiHandler()


def lambda_handler(event: dict, context: RequestContext):
    return HANDLER.lambda_handler(event=event, context=context)
