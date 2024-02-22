from http import HTTPStatus
from typing import Generator

from commons.constants import Endpoint, HTTPMethod
from services.openapi_spec_generator import EndpointInfo
from validators.response import *

data: tuple[EndpointInfo, ...] = (
    # applications
    EndpointInfo(
        path=Endpoint.APPLICATIONS,
        method=HTTPMethod.GET,
        summary=None,
        description=None,
        request_model=None,
        responses=[(HTTPStatus.OK, ApplicationsResponse, None)],
        auth=True,
    ),
    EndpointInfo(
        path=Endpoint.APPLICATIONS,
        method=HTTPMethod.POST,
        summary=None,
        description=None,
        request_model=None,
        responses=[(HTTPStatus.OK, ApplicationsResponse, None)],
        auth=True,
    ),
    EndpointInfo(
        path=Endpoint.APPLICATIONS,
        method=HTTPMethod.PATCH,
        summary=None,
        description=None,
        request_model=None,
        responses=[(HTTPStatus.OK, ApplicationsResponse, None)],
        auth=True,
    ),
    EndpointInfo(
        path=Endpoint.APPLICATIONS,
        method=HTTPMethod.DELETE,
        summary=None,
        description=None,
        request_model=None,
        responses=[(HTTPStatus.OK, MessageModel, None)],
        auth=True,
    ),

    # customers
    EndpointInfo(
        path=Endpoint.CUSTOMERS,
        method=HTTPMethod.GET,
        summary=None,
        description=None,
        request_model=None,
        responses=[(HTTPStatus.OK, CustomersResponse, None)],
        auth=True,
    ),
    EndpointInfo(
        path=Endpoint.CUSTOMERS,
        method=HTTPMethod.POST,
        summary=None,
        description=None,
        request_model=None,
        responses=[(HTTPStatus.OK, CustomersResponse, None)],
        auth=True,
    ),
    EndpointInfo(
        path=Endpoint.CUSTOMERS,
        method=HTTPMethod.PATCH,
        summary=None,
        description=None,
        request_model=None,
        responses=[(HTTPStatus.OK, CustomersResponse, None)],
        auth=True,
    ),

    # parents
    EndpointInfo(
        path=Endpoint.PARENTS,
        method=HTTPMethod.GET,
        summary=None,
        description=None,
        request_model=None,
        responses=[(HTTPStatus.OK, ParentsResponse, None)],
        auth=True,
    ),
    EndpointInfo(
        path=Endpoint.PARENTS,
        method=HTTPMethod.POST,
        summary=None,
        description=None,
        request_model=None,
        responses=[(HTTPStatus.OK, ParentsResponse, None)],
        auth=True,
    ),
    EndpointInfo(
        path=Endpoint.PARENTS,
        method=HTTPMethod.PATCH,
        summary=None,
        description=None,
        request_model=None,
        responses=[(HTTPStatus.OK, ParentsResponse, None)],
        auth=True,
    ),
    EndpointInfo(
        path=Endpoint.PARENTS,
        method=HTTPMethod.DELETE,
        summary=None,
        description=None,
        request_model=None,
        responses=[(HTTPStatus.OK, ParentsResponse, None)],
        auth=True,
    ),

    # policies
    EndpointInfo(
        path=Endpoint.POLICIES,
        method=HTTPMethod.GET,
        summary=None,
        description=None,
        request_model=None,
        responses=[(HTTPStatus.OK, PoliciesResponse, None)],
        auth=True,
    ),
    EndpointInfo(
        path=Endpoint.POLICIES,
        method=HTTPMethod.POST,
        summary=None,
        description=None,
        request_model=None,
        responses=[(HTTPStatus.OK, PoliciesResponse, None)],
        auth=True,
    ),
    EndpointInfo(
        path=Endpoint.POLICIES,
        method=HTTPMethod.PATCH,
        summary=None,
        description=None,
        request_model=None,
        responses=[(HTTPStatus.OK, PoliciesResponse, None)],
        auth=True,
    ),
    EndpointInfo(
        path=Endpoint.POLICIES,
        method=HTTPMethod.DELETE,
        summary=None,
        description=None,
        request_model=None,
        responses=[(HTTPStatus.OK, MessageModel, None)],
        auth=True,
    ),
    # roles
    EndpointInfo(
        path=Endpoint.ROLES,
        method=HTTPMethod.GET,
        summary=None,
        description=None,
        request_model=None,
        responses=[(HTTPStatus.OK, RolesResponse, None)],
        auth=True,
    ),
    EndpointInfo(
        path=Endpoint.ROLES,
        method=HTTPMethod.POST,
        summary=None,
        description=None,
        request_model=None,
        responses=[(HTTPStatus.OK, RolesResponse, None)],
        auth=True,
    ),
    EndpointInfo(
        path=Endpoint.ROLES,
        method=HTTPMethod.PATCH,
        summary=None,
        description=None,
        request_model=None,
        responses=[(HTTPStatus.OK, RolesResponse, None)],
        auth=True,
    ),
    EndpointInfo(
        path=Endpoint.ROLES,
        method=HTTPMethod.DELETE,
        summary=None,
        description=None,
        request_model=None,
        responses=[(HTTPStatus.OK, MessageModel, None)],
        auth=True,
    ),
    # regions
    EndpointInfo(
        path=Endpoint.REGIONS,
        method=HTTPMethod.GET,
        summary=None,
        description=None,
        request_model=None,
        responses=[(HTTPStatus.OK, RegionsResponse, None)],
        auth=True,
    ),
    EndpointInfo(
        path=Endpoint.REGIONS,
        method=HTTPMethod.POST,
        summary=None,
        description=None,
        request_model=None,
        responses=[(HTTPStatus.OK, RegionsResponse, None)],
        auth=True,
    ),
    EndpointInfo(
        path=Endpoint.REGIONS,
        method=HTTPMethod.DELETE,
        summary=None,
        description=None,
        request_model=None,
        responses=[(HTTPStatus.OK, MessageModel, None)],
        auth=True,
    ),
    # auth
    EndpointInfo(
        path=Endpoint.SIGNIN,
        method=HTTPMethod.POST,
        summary=None,
        description=None,
        request_model=None,
        responses=[(HTTPStatus.OK, SignInResponse, None)],
        auth=False,
    ),
    EndpointInfo(
        path=Endpoint.SIGNUP,
        method=HTTPMethod.POST,
        summary=None,
        description=None,
        request_model=None,
        responses=[(HTTPStatus.OK, MessageModel, None)],
        auth=False,
    ),
    # tenant in region
    EndpointInfo(
        path=Endpoint.TENANTS_REGIONS,
        method=HTTPMethod.POST,
        summary=None,
        description=None,
        request_model=None,
        responses=[(HTTPStatus.OK, RegionsResponse, None)],
        auth=True,
    ),
    EndpointInfo(
        path=Endpoint.TENANTS_REGIONS,
        method=HTTPMethod.GET,
        summary=None,
        description=None,
        request_model=None,
        responses=[(HTTPStatus.OK, RegionsResponse, None)],
        auth=True,
    ),
    EndpointInfo(
        path=Endpoint.TENANTS_REGIONS,
        method=HTTPMethod.DELETE,
        summary=None,
        description=None,
        request_model=None,
        responses=[(HTTPStatus.OK, TenantsResponse, None)],
        auth=True,
    ),
    # tenants
    EndpointInfo(
        path=Endpoint.TENANTS,
        method=HTTPMethod.GET,
        summary=None,
        description=None,
        request_model=None,
        responses=[(HTTPStatus.OK, TenantsResponse, None)],
        auth=True,
    ),
    EndpointInfo(
        path=Endpoint.TENANTS,
        method=HTTPMethod.POST,
        summary=None,
        description=None,
        request_model=None,
        responses=[(HTTPStatus.OK, TenantsResponse, None)],
        auth=True,
    ),
    EndpointInfo(
        path=Endpoint.TENANTS,
        method=HTTPMethod.DELETE,
        summary=None,
        description=None,
        request_model=None,
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
