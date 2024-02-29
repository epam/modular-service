from datetime import datetime
from http import HTTPStatus

from modular_sdk.commons.constants import ApplicationType, ParentType, \
    ParentScope, Cloud
from pydantic import BaseModel
from typing_extensions import TypedDict


class ErrorData(TypedDict):
    location: list[str]
    message: str


class Customer(TypedDict):
    name: str
    display_name: str
    admins: list[str]
    is_active: bool


class Application(TypedDict):
    application_id: str
    created_by: str
    customer_id: str
    description: str
    is_deleted: bool
    meta: dict  # todo make more specific?
    secret: str
    type: ApplicationType


class Parent(TypedDict):
    application_id: str
    created_at: datetime
    created_by: str
    customer_id: str
    description: str
    is_deleted: bool
    meta: dict  # todo make more specific?
    parent_id: str
    scope: ParentScope
    type: ParentType


class Policy(TypedDict):
    name: str
    permissions: list[str]


class Region(TypedDict):
    maestro_name: str
    native_name: str
    cloud: str
    region_id: str
    is_active: bool

    availability_zones: list[str]
    fields: dict
    region_abbreviation: str
    billing_mix_mode: bool
    billing_disabled: bool
    is_hardware: bool
    is_hidden: bool
    is_deprecated: bool
    is_unreachable: bool


class Role(TypedDict):
    name: str
    policies: list[str]
    resource: list[str]


class TenantContacts(TypedDict):
    primary_contacts: list[str]
    secondary_contacts: list[str]
    tenant_manager_contacts: list[str]
    default_owner: str | None


class Tenant(TypedDict):
    name: str
    account_id: str
    activation_date: datetime
    cloud: Cloud
    contacts: TenantContacts
    customer_name: str
    display_name: str
    display_name_to_lower: str  # really, for what?
    is_active: bool
    read_only: bool
    regions: list[str]


class TenantSetting(TypedDict):
    tenant_name: str
    key: str
    value: dict | list | str | int | float | None


# responses
class CustomersResponse(BaseModel):
    items: list[Customer]


class CustomerResponse(BaseModel):
    data: Customer


class TenantsResponse(BaseModel):
    items: list[Tenant]
    next_token: str | None


class TenantResponse(BaseModel):
    data: Tenant


class RolesResponse(BaseModel):
    items: list[Role]


class PoliciesResponse(BaseModel):
    items: list[Policy]


class ParentsResponse(BaseModel):
    items: list[Parent]


class ApplicationsResponse(BaseModel):
    items: list[Application]
    next_token: str | None


class ApplicationResponse(BaseModel):
    data: Application


class RegionsResponse(BaseModel):
    items: list[Region]


class SignInResponse(BaseModel):
    access_token: str


class TenantSettingsResponse(BaseModel):
    items: list[TenantSetting]
    next_token: str | None


class TenantSettingResponse(BaseModel):
    data: TenantSetting


class MessageModel(BaseModel):
    message: str


class ErrorsModel(BaseModel):
    """
    400 Validation error
    """
    errors: list[ErrorData]


common_responses = (
    (HTTPStatus.BAD_REQUEST, ErrorsModel, 'Validation error'),
    (HTTPStatus.UNAUTHORIZED, MessageModel, 'Invalid credentials'),
    (HTTPStatus.FORBIDDEN, MessageModel, 'Cannot access the resource'),
    (HTTPStatus.INTERNAL_SERVER_ERROR, MessageModel, 'Server error'),
    (HTTPStatus.SERVICE_UNAVAILABLE, MessageModel,
     'Service is temporarily unavailable'),
    (HTTPStatus.GATEWAY_TIMEOUT, MessageModel,
     'Gateway 30s timeout is reached')
)
