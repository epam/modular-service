from http import HTTPStatus
from typing import Generator

from commons.constants import Endpoint, HTTPMethod
from services.openapi_spec_generator import EndpointInfo
from validators.response import *
from validators.request import *

data: tuple[EndpointInfo, ...] = (
    # applications
    EndpointInfo(
        path=Endpoint.APPLICATIONS,
        method=HTTPMethod.GET,
        summary=None,
        description=None,
        request_model=ApplicationGet,
        responses=[(HTTPStatus.OK, ApplicationsResponse, None)],
        auth=True,
    ),
    EndpointInfo(
        path=Endpoint.APPLICATIONS,
        method=HTTPMethod.POST,
        summary=None,
        description=None,
        request_model=ApplicationPost,
        responses=[(HTTPStatus.OK, ApplicationsResponse, None)],
        auth=True,
    ),
    EndpointInfo(
        path=Endpoint.APPLICATIONS,
        method=HTTPMethod.PATCH,
        summary=None,
        description=None,
        request_model=ApplicationPatch,
        responses=[(HTTPStatus.OK, ApplicationsResponse, None)],
        auth=True,
    ),
    EndpointInfo(
        path=Endpoint.APPLICATIONS,
        method=HTTPMethod.DELETE,
        summary=None,
        description=None,
        request_model=ApplicationDelete,
        responses=[(HTTPStatus.OK, MessageModel, None)],
        auth=True,
    ),

    # customers
    EndpointInfo(
        path=Endpoint.CUSTOMERS,
        method=HTTPMethod.GET,
        summary=None,
        description=None,
        request_model=CustomerGet,
        responses=[(HTTPStatus.OK, CustomersResponse, None)],
        auth=True,
    ),
    EndpointInfo(
        path=Endpoint.CUSTOMERS,
        method=HTTPMethod.POST,
        summary=None,
        description=None,
        request_model=CustomerPost,
        responses=[(HTTPStatus.OK, CustomersResponse, None)],
        auth=True,
    ),
    EndpointInfo(
        path=Endpoint.CUSTOMERS,
        method=HTTPMethod.PATCH,
        summary=None,
        description=None,
        request_model=CustomerPatch,
        responses=[(HTTPStatus.OK, CustomersResponse, None)],
        auth=True,
    ),

    # parents
    EndpointInfo(
        path=Endpoint.PARENTS,
        method=HTTPMethod.GET,
        summary=None,
        description=None,
        request_model=ParentGet,
        responses=[(HTTPStatus.OK, ParentsResponse, None)],
        auth=True,
    ),
    EndpointInfo(
        path=Endpoint.PARENTS,
        method=HTTPMethod.POST,
        summary=None,
        description=None,
        request_model=ParentPost,
        responses=[(HTTPStatus.OK, ParentsResponse, None)],
        auth=True,
    ),
    EndpointInfo(
        path=Endpoint.PARENTS,
        method=HTTPMethod.PATCH,
        summary=None,
        description=None,
        request_model=ParentPost,
        responses=[(HTTPStatus.OK, ParentsResponse, None)],
        auth=True,
    ),
    EndpointInfo(
        path=Endpoint.PARENTS,
        method=HTTPMethod.DELETE,
        summary=None,
        description=None,
        request_model=ParentDelete,
        responses=[(HTTPStatus.OK, ParentsResponse, None)],
        auth=True,
    ),

    # policies
    EndpointInfo(
        path=Endpoint.POLICIES,
        method=HTTPMethod.GET,
        summary=None,
        description=None,
        request_model=PolicyGet,
        responses=[(HTTPStatus.OK, PoliciesResponse, None)],
        auth=True,
    ),
    EndpointInfo(
        path=Endpoint.POLICIES,
        method=HTTPMethod.POST,
        summary=None,
        description=None,
        request_model=PolicyPost,
        responses=[(HTTPStatus.OK, PoliciesResponse, None)],
        auth=True,
    ),
    EndpointInfo(
        path=Endpoint.POLICIES,
        method=HTTPMethod.PATCH,
        summary=None,
        description=None,
        request_model=PolicyPatch,
        responses=[(HTTPStatus.OK, PoliciesResponse, None)],
        auth=True,
    ),
    EndpointInfo(
        path=Endpoint.POLICIES,
        method=HTTPMethod.DELETE,
        summary=None,
        description=None,
        request_model=PolicyDelete,
        responses=[(HTTPStatus.OK, MessageModel, None)],
        auth=True,
    ),
    # roles
    EndpointInfo(
        path=Endpoint.ROLES,
        method=HTTPMethod.GET,
        summary=None,
        description=None,
        request_model=RoleGet,
        responses=[(HTTPStatus.OK, RolesResponse, None)],
        auth=True,
    ),
    EndpointInfo(
        path=Endpoint.ROLES,
        method=HTTPMethod.POST,
        summary=None,
        description=None,
        request_model=RolePost,
        responses=[(HTTPStatus.OK, RolesResponse, None)],
        auth=True,
    ),
    EndpointInfo(
        path=Endpoint.ROLES,
        method=HTTPMethod.PATCH,
        summary=None,
        description=None,
        request_model=RolePatch,
        responses=[(HTTPStatus.OK, RolesResponse, None)],
        auth=True,
    ),
    EndpointInfo(
        path=Endpoint.ROLES,
        method=HTTPMethod.DELETE,
        summary=None,
        description=None,
        request_model=RoleDelete,
        responses=[(HTTPStatus.OK, MessageModel, None)],
        auth=True,
    ),
    # regions
    EndpointInfo(
        path=Endpoint.REGIONS,
        method=HTTPMethod.GET,
        summary=None,
        description=None,
        request_model=RegionGet,
        responses=[(HTTPStatus.OK, RegionsResponse, None)],
        auth=True,
    ),
    EndpointInfo(
        path=Endpoint.REGIONS,
        method=HTTPMethod.POST,
        summary=None,
        description=None,
        request_model=RegionPost,
        responses=[(HTTPStatus.OK, RegionsResponse, None)],
        auth=True,
    ),
    EndpointInfo(
        path=Endpoint.REGIONS,
        method=HTTPMethod.DELETE,
        summary=None,
        description=None,
        request_model=RegionDelete,
        responses=[(HTTPStatus.OK, MessageModel, None)],
        auth=True,
    ),
    # auth
    EndpointInfo(
        path=Endpoint.SIGNIN,
        method=HTTPMethod.POST,
        summary=None,
        description=None,
        request_model=SignInPost,
        responses=[(HTTPStatus.OK, SignInResponse, None)],
        auth=False,
    ),
    EndpointInfo(
        path=Endpoint.SIGNUP,
        method=HTTPMethod.POST,
        summary=None,
        description=None,
        request_model=SignUpPost,
        responses=[(HTTPStatus.OK, MessageModel, None)],
        auth=False,
    ),
    # tenant in region
    EndpointInfo(
        path=Endpoint.TENANTS_REGIONS,
        method=HTTPMethod.POST,
        summary=None,
        description=None,
        request_model=TenantRegionPost,
        responses=[(HTTPStatus.OK, RegionsResponse, None)],
        auth=True,
    ),
    EndpointInfo(
        path=Endpoint.TENANTS_REGIONS,
        method=HTTPMethod.GET,
        summary=None,
        description=None,
        request_model=TenantRegionGet,
        responses=[(HTTPStatus.OK, RegionsResponse, None)],
        auth=True,
    ),
    EndpointInfo(
        path=Endpoint.TENANTS_REGIONS,
        method=HTTPMethod.DELETE,
        summary=None,
        description=None,
        request_model=TenantRegionDelete,
        responses=[(HTTPStatus.OK, TenantsResponse, None)],
        auth=True,
    ),
    # tenants
    EndpointInfo(
        path=Endpoint.TENANTS,
        method=HTTPMethod.GET,
        summary=None,
        description=None,
        request_model=TenantGet,
        responses=[(HTTPStatus.OK, TenantsResponse, None)],
        auth=True,
    ),
    EndpointInfo(
        path=Endpoint.TENANTS,
        method=HTTPMethod.POST,
        summary=None,
        description=None,
        request_model=TenantPost,
        responses=[(HTTPStatus.OK, TenantsResponse, None)],
        auth=True,
    ),
    EndpointInfo(
        path=Endpoint.TENANTS,
        method=HTTPMethod.DELETE,
        summary=None,
        description=None,
        request_model=TenantDelete,
        responses=[(HTTPStatus.OK, TenantsResponse, None)],
        auth=True,
    ),
)

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


def iter_all() -> Generator[EndpointInfo, None, None]:
    """
    Extends data
    :return:
    """
    for endpoint in data:
        existing = {r[0] for r in endpoint.responses}
        for code, model, description in common_responses:
            if code in existing:
                continue
            endpoint.responses.append((code, model, description))
        if '{' in endpoint.path and HTTPStatus.NOT_FOUND not in existing:
            endpoint.responses.append((HTTPStatus.NOT_FOUND, MessageModel,
                                       'Entity is not found'))
        endpoint.responses.sort(key=lambda x: x[0])
        yield endpoint
