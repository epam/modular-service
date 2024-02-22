import uuid
from datetime import datetime, timezone

from modular_sdk.commons.constants import Cloud, ParentType, ParentScope, \
    ApplicationType
from pydantic import BaseModel as BaseModelPydantic, ConfigDict, Field, \
    model_validator, field_validator
from typing_extensions import Self


class BaseModel(BaseModelPydantic):
    model_config = ConfigDict(
        coerce_numbers_to_str=True,
        populate_by_name=True
    )


class CustomerPost(BaseModel):
    name: str
    display_name: str
    admins: list[str] = Field(default_factory=list)


class CustomerGet(BaseModel):
    name: str = Field(None)


class CustomerPatch(BaseModel):
    name: str
    admins: set[str]
    override: bool


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


class TenantGet(BaseModel):
    name: str = Field(None)


class TenantPost(BaseModel):
    name: str
    display_name: str
    tenant_customer: str
    cloud: Cloud
    acc: str
    read_only: bool


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


class ApplicationGet(BaseModel):
    application_id: str = Field(None)


class ApplicationPost(BaseModel):
    type: ApplicationType
    customer_id: str
    description: str
    meta: dict = Field(default_factory=dict)  # todo specific validator


class ApplicationPatch(BaseModel):
    application_id: str


class ApplicationDelete(BaseModel):
    application_id: str
