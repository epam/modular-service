import base64
import binascii
from datetime import datetime, timezone
from typing_extensions import Self, TypedDict
import uuid

import boto3
from botocore.exceptions import ClientError
from modular_sdk.commons.constants import (
    ApplicationType,
    Cloud,
    ParentScope,
    ParentType,
)
from pydantic import (
    BaseModel as BaseModelPydantic,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)
from pydantic.json_schema import SkipJsonSchema


class BaseModel(BaseModelPydantic):
    model_config = ConfigDict(
        coerce_numbers_to_str=True,
        populate_by_name=True
    )


class BasePaginationModel(BaseModel):
    limit: int = Field(50, le=50)
    next_token: str = Field(None)


class CustomerPost(BaseModel):
    name: str
    display_name: str
    admins: set[str] = Field(default_factory=set)


class CustomerQuery(BasePaginationModel):
    is_active: bool = Field(None)


class CustomerPatch(BaseModel):
    admins: set[str]


class PolicyGet(BaseModel):
    name: str = Field(None)


class PolicyPost(BaseModel):
    name: str
    permissions: set[str] = Field(default_factory=set)
    permissions_admin: bool = False

    @model_validator(mode='after')
    def _(self) -> Self:
        if not self.permissions_admin and not self.permissions:
            raise ValueError('Provide either permissions or permissions_admin')
        return self


class PolicyPatch(BaseModel):
    name: str
    permissions: set[str] = Field(default_factory=set)
    permissions_to_attach: set[str] = Field(default_factory=set)
    permissions_to_detach: set[str] = Field(default_factory=set)

    @model_validator(mode='after')
    def _(self) -> Self:
        if not any((self.permissions, self.permissions_to_detach,
                    self.permissions_to_detach)):
            raise ValueError(
                'Provide at permissions or permissions_to_attach or permissions_to_detach')
        return self


class PolicyDelete(BaseModel):
    name: str


class RoleGet(BaseModel):
    name: str


class RolePost(BaseModel):
    name: str
    expiration: datetime
    policies: set[str]

    @field_validator('expiration')
    @classmethod
    def _(cls, expiration: datetime) -> datetime:
        expiration.astimezone(timezone.utc)
        if expiration < datetime.now(tz=timezone.utc):
            raise ValueError('Expiration date has already passed')
        return expiration


class RolePatch(BaseModel):
    name: str
    expiration: datetime

    policies_to_attach: set[str] = Field(default_factory=set)
    policies_to_detach: set[str] = Field(default_factory=set)

    @field_validator('expiration')
    @classmethod
    def _(cls, expiration: datetime) -> datetime:
        expiration.astimezone(timezone.utc)
        if expiration < datetime.now(tz=timezone.utc):
            raise ValueError('Expiration date has already passed')
        return expiration


class RoleDelete(BaseModel):
    name: str


class SignInPost(BaseModel):
    username: str
    password: str


class SignUpPost(BaseModel):
    username: str
    password: str
    role: str


class TenantQuery(BasePaginationModel):
    customer_id: str
    cloud: Cloud = Field(None)
    is_active: bool = Field(None)


class TenantPost(BaseModel):
    name: str
    display_name: str
    customer_id: str
    cloud: Cloud
    account_id: str
    read_only: bool
    primary_contacts: set[str] = Field(default_factory=set)
    secondary_contacts: set[str] = Field(default_factory=set)
    tenant_manager_contacts: set[str] = Field(default_factory=set)
    default_owner: str = Field(None)


class TenantDelete(BaseModel):
    name: str


class RegionGet(BaseModel):
    maestro_name: str = Field(None)


class RegionPost(BaseModel):
    maestro_name: str
    native_name: str
    cloud: str
    region_id: str = Field(default_factory=lambda: str(uuid.uuid4()))


class RegionDelete(BaseModel):
    maestro_name: str


class TenantRegionGet(BaseModel):
    tenant: str


class TenantRegionPost(BaseModel):
    tenant: str
    region: str


class TenantRegionDelete(BaseModel):
    tenant: str
    region: str


class ParentGet(BaseModel):
    parent_id: str = Field(None)
    application_id: str = Field(None)


class ParentPost(BaseModel):
    application_id: str
    type: ParentType
    customer_id: str
    description: str
    meta: dict = Field(default_factory=dict)  # todo specific validator
    cloud: Cloud
    tenant: str
    scope: ParentScope


class ParentPatch(BaseModel):
    parent_id: str
    application_id: str = Field(None)
    # todo rewrite patch


class ParentDelete(BaseModel):
    parent_id: str


class ApplicationQuery(BasePaginationModel):
    customer_id: str
    type: ApplicationType = Field(None)
    is_deleted: bool = Field(None)


class ApplicationPatch(BaseModel):
    description: str


class ApplicationPostAWSRole(BaseModel):
    customer_id: str
    description: str
    role_name: str
    account_id: str = Field(None)


class ApplicationPostAWSCredentials(BaseModel):
    customer_id: str
    description: str
    access_key_id: str
    secret_access_key: str
    session_token: str = Field(None)
    default_region: str = 'us-east-1'
    account_id: SkipJsonSchema[str] = Field(None)  # derived from creds

    @model_validator(mode='after')
    def _(self) -> Self:
        cl = boto3.client(
            'sts',
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.secret_access_key,
            aws_session_token=self.session_token
        )
        try:
            resp = cl.get_caller_identity()
        except ClientError:
            raise ValueError(
                'could not get caller identity with provided creds'
            )
        self.account_id = resp['Account']
        return self


class ApplicationPostAZURECredentials(BaseModel):
    customer_id: str
    description: str
    client_id: str
    tenant_id: str
    api_key: str


class ApplicationPostAZURECertificate(BaseModel):
    customer_id: str
    description: str
    client_id: str
    tenant_id: str
    certificate: str = Field(description='Base64 encoded certificate')
    password: str = Field(None, description='Password from the certificate')

    @model_validator(mode='after')
    def _(self) -> Self:
        try:
            base64.b64decode(self.certificate)
        except binascii.Error:
            raise ValueError('could not b64 decode the provided certificate')
        return self


class GOOGLECredentialsRaw1(TypedDict):
    type: str
    project_id: str
    private_key_id: str
    private_key: str
    client_email: str
    client_id: str
    auth_uri: str
    token_uri: str
    auth_provider_x509_cert_url: str
    client_x509_cert_url: str


class ApplicationPostGCPServiceAccount(BaseModel):
    customer_id: str
    description: str
    credentials: GOOGLECredentialsRaw1


class ApplicationDelete(BaseModel):
    application_id: str


class TenantSettingQuery(BasePaginationModel):
    key: str = Field(
        None,
        description='Note that a tenant can have only one setting for a '
                    'specific key. So in case you provide this value either '
                    'an empty list of a list with one element is returned'
    )


class TenantSettingPut(BaseModel):
    key: str
    value: dict | list | str | int | float | None
