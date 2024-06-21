from http import HTTPStatus

from modular_sdk.models.tenant import Tenant
from routes.route import Route

from commons import NextToken
from commons.constants import Endpoint, HTTPMethod, Permission
from commons.lambda_response import ResponseFactory, build_response
from commons.log_helper import get_logger
from lambdas.modular_api_handler.processors.abstract_processor import (
    AbstractCommandProcessor,
)
from services import SERVICE_PROVIDER
from services.customer_mutator_service import CustomerMutatorService
from services.tenant_mutator_service import TenantMutatorService
from validators.request import BaseModel, TenantPost, TenantQuery
from validators.response import MessageModel, TenantResponse, TenantsResponse
from validators.utils import validate_kwargs

_LOG = get_logger(__name__)


class TenantProcessor(AbstractCommandProcessor):
    def __init__(self, customer_service: CustomerMutatorService,
                 tenant_service: TenantMutatorService):
        self.customer_service: CustomerMutatorService = customer_service
        self.tenant_service: TenantMutatorService = tenant_service

    @classmethod
    def build(cls) -> 'TenantProcessor':
        return cls(
            customer_service=SERVICE_PROVIDER.customer_service,
            tenant_service=SERVICE_PROVIDER.tenant_service
        )

    @classmethod
    def routes(cls) -> tuple[Route, ...]:
        return (
            cls.route(
                Endpoint.TENANTS,
                HTTPMethod.GET,
                'query',
                response=(HTTPStatus.OK, TenantsResponse, None),
                permission=Permission.TENANT_DESCRIBE
            ),
            cls.route(
                Endpoint.TENANTS_NAME,
                HTTPMethod.GET,
                'get',
                summary='Queries a specific tenant',
                description='Either tenant name or tenant account id can be used to retrieve a tenant',
                response=(HTTPStatus.OK, TenantResponse, None),
                permission=Permission.TENANT_DESCRIBE
            ),
            cls.route(
                Endpoint.TENANTS,
                HTTPMethod.POST,
                'create',
                response=[(HTTPStatus.CREATED, TenantResponse, None),
                          (HTTPStatus.CONFLICT, MessageModel, 'Tenant already exists')],
                description='Creates a new tenant',
                permission=Permission.TENANT_CREATE
            ),
            cls.route(
                Endpoint.TENANTS_NAME_ACTIVATE,
                HTTPMethod.POST,
                'activate',
                response=(HTTPStatus.OK, TenantResponse, None),
                description='Activates an existing tenant',
                permission=Permission.TENANT_ACTIVATE
            ),
            cls.route(
                Endpoint.TENANTS_NAME_DEACTIVATE,
                HTTPMethod.POST,
                'deactivate',
                response=(HTTPStatus.OK, TenantResponse, None),
                description='Deactivates an existing tenant',
                permission=Permission.TENANT_DEACTIVATE
            ),
            cls.route(
                Endpoint.TENANTS_NAME,
                HTTPMethod.DELETE,
                'delete',
                summary='Guarantees that tenant is completely removed from the DB',
                response=(HTTPStatus.NO_CONTENT, None, None),
                permission=Permission.TENANT_DELETE
            ),
        )

    @validate_kwargs
    def query(self, event: TenantQuery):
        cursor = self.tenant_service.i_get_tenant_by_customer(
            customer_id=event.customer_id,
            active=event.is_active,
            cloud=event.cloud.value if event.cloud else None,
            limit=event.limit,
            last_evaluated_key=NextToken.from_input(event.next_token).value,
        )
        items = list(cursor)

        return ResponseFactory().items(
            it=map(self.tenant_service.get_dto, items),
            next_token=NextToken(cursor.last_evaluated_key)
        ).build()

    def _get_tenant(self, name: str, customer_id: str) -> Tenant | None:
        item = self.tenant_service.get(name)
        if not item:
            item = next(self.tenant_service.i_get_by_acc(
                acc=name, limit=1
            ), None)
        if not item or item.customer_name != customer_id:
            return
        return item

    @validate_kwargs
    def get(self, event: BaseModel, name: str):
        tenant = self._get_tenant(name, event.customer_id)
        if not tenant:
            raise ResponseFactory(HTTPStatus.NOT_FOUND).default().exc()
        return build_response(content=self.tenant_service.get_dto(tenant))

    @validate_kwargs
    def create(self, event: TenantPost):
        name = event.name
        acc = event.account_id
        if self.tenant_service.get(tenant_name=name):
            _LOG.warning(f'Tenant with name \'{name}\' already exist.')
            raise ResponseFactory(HTTPStatus.CONFLICT).message(
                f'Tenant with name \'{name}\' already exist.'
            ).exc()

        by_acc = next(self.tenant_service.i_get_by_acc(
            acc=acc, limit=1
        ), None)
        if by_acc:
            _LOG.warning(f'Tenant with account id \'{acc}\' already exist.')
            raise ResponseFactory(HTTPStatus.CONFLICT).message(
                f'Tenant with account id \'{acc}\' already exist.'
            ).exc()

        _LOG.debug('Creating tenant')
        tenant = self.tenant_service.create(
            tenant_name=name,
            display_name=event.display_name,
            customer_name=event.customer_id,
            cloud=event.cloud,
            acc=acc,
            is_active=True,
            read_only=event.read_only,
            contacts={
                'primary_contacts': list(event.primary_contacts),
                'secondary_contacts': list(event.secondary_contacts),
                'tenant_manager_contacts': list(event.tenant_manager_contacts),
                'default_owner': event.default_owner
            }
        )
        _LOG.debug('Saving tenant')
        self.tenant_service.save(tenant=tenant)
        return build_response(
            content=self.tenant_service.get_dto(tenant),
            code=HTTPStatus.CREATED
        )

    @validate_kwargs
    def activate(self, event: BaseModel, name: str):
        tenant = self._get_tenant(name, event.customer_id)
        if not tenant:
            raise ResponseFactory(HTTPStatus.NOT_FOUND).default().exc()
        self.tenant_service.activate(tenant)
        return build_response(content=self.tenant_service.get_dto(tenant))

    @validate_kwargs
    def deactivate(self, event: BaseModel, name: str):
        tenant = self._get_tenant(name, event.customer_id)
        if not tenant:
            raise ResponseFactory(HTTPStatus.NOT_FOUND).default().exc()
        self.tenant_service.deactivate(tenant)
        return build_response(content=self.tenant_service.get_dto(tenant))

    @validate_kwargs
    def delete(self, event: BaseModel, name: str):
        tenant = self._get_tenant(name, event.customer_id)

        if not tenant:
            _LOG.warning(f'Tenant {name} did not exist before')
            return build_response(code=HTTPStatus.NO_CONTENT)

        _LOG.debug(f'Deactivating tenant \'{name}\'')
        self.tenant_service.remove(tenant)
        return build_response(code=HTTPStatus.NO_CONTENT)
