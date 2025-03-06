from http import HTTPStatus

from modular_sdk.services.tenant_settings_service import TenantSettingsService
from routes.route import Route

from commons import NextToken
from commons.constants import Endpoint, HTTPMethod, Permission
from commons.lambda_response import ResponseFactory, build_response
from lambdas.modular_api_handler.processors.abstract_processor import (
    AbstractCommandProcessor,
)
from services import SP
from modular_sdk.models.tenant import Tenant
from services.tenant_mutator_service import TenantMutatorService
from validators.request import TenantSettingQuery, TenantSettingPut
from validators.response import TenantSettingsResponse
from validators.utils import validate_kwargs


class TenantSettingsProcessor(AbstractCommandProcessor):
    def __init__(self, tenant_settings_service: TenantSettingsService,
                 tenant_service: TenantMutatorService):
        self._tss = tenant_settings_service
        self._ts = tenant_service

    @classmethod
    def build(cls) -> 'TenantSettingsProcessor':
        return cls(
            tenant_settings_service=SP.modular.tenant_settings_service(),
            tenant_service=SP.tenant_service
        )

    @classmethod
    def routes(cls) -> tuple[Route, ...]:
        return (
            cls.route(
                Endpoint.TENANTS_NAME_SETTINGS,
                HTTPMethod.GET,
                'query',
                summary='List settings all settings for this tenant',
                response=(HTTPStatus.OK, TenantSettingsResponse, None),
                permission=Permission.TENANT_SETTING_DESCRIBE
            ),
            cls.route(
                Endpoint.TENANTS_NAME_SETTINGS,
                HTTPMethod.PUT,
                'put',
                summary='Put some setting value',
                response=(HTTPStatus.OK, TenantSettingsResponse, None),
                permission=Permission.TENANT_SETTING_SET
            ),
        )

    def _get_tenant(self, name: str, customer_id: str) -> Tenant | None:
        item = self._ts.get(name)
        if not item:
            item = next(self._ts.i_get_by_acc(acc=name, limit=1), None)
        if not item or item.customer_name != customer_id:
            return
        return item

    @validate_kwargs
    def query(self, event: TenantSettingQuery, name: str):
        name = name.upper()
        tenant = self._get_tenant(name, event.customer_id)
        if not tenant:
            raise ResponseFactory(HTTPStatus.NOT_FOUND).message(
                'Tenant not found'
            ).exc()
        cursor = self._tss.i_get_by_tenant(
            tenant=tenant.name,
            key=event.key,
            limit=event.limit,
            last_evaluated_key=NextToken.from_input(event.next_token).value,
        )
        items = list(cursor)

        return ResponseFactory().items(
            it=map(self._tss.get_dto, items),
            next_token=NextToken(cursor.last_evaluated_key)
        ).build()

    @validate_kwargs
    def put(self, event: TenantSettingPut, name: str):
        name = name.upper()
        tenant = self._get_tenant(name, event.customer_id)
        if not tenant:
            raise ResponseFactory(HTTPStatus.NOT_FOUND).message(
                'Tenant not found'
            ).exc()
        ts = self._tss.create(
            tenant_name=tenant.name,
            key=event.key,
            value=event.value
        )
        self._tss.save(ts)
        return build_response(self._tss.get_dto(ts))
