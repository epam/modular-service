from typing import Final

from commons.constants import HTTPMethod, Endpoint

ENDPOINT_PERMISSION_MAPPING: Final[dict] = {
    Endpoint.APPLICATIONS: {
        HTTPMethod.GET: 'application:describe_application',
        HTTPMethod.POST: 'application:create_application',
        HTTPMethod.PATCH: 'application:update_application',
        HTTPMethod.DELETE: 'application:remove_application',
    },
    Endpoint.CUSTOMERS: {
        HTTPMethod.GET: 'customer:describe_customer',
        HTTPMethod.POST: 'customer:create_customer',
        HTTPMethod.PATCH: 'customer:update_customer',
        HTTPMethod.DELETE: 'customer:remove_customer',
    },
    Endpoint.PARENTS: {
        HTTPMethod.GET: 'parent:describe_parent',
        HTTPMethod.POST: 'parent:create_parent',
        HTTPMethod.PATCH: 'parent:update_parent',
        HTTPMethod.DELETE: 'parent:remove_parent',
    },
    Endpoint.TENANTS: {
        HTTPMethod.GET: 'tenant:describe_tenant',
        HTTPMethod.POST: 'tenant:create_tenant',
        HTTPMethod.PATCH: 'tenant:update_tenant',
        HTTPMethod.DELETE: 'tenant:remove_tenant',
    },
    Endpoint.REGIONS: {
        HTTPMethod.GET: 'region:describe_region',
        HTTPMethod.POST: 'region:create_region',
        HTTPMethod.PATCH: 'region:update_region',
        HTTPMethod.DELETE: 'region:remove_region',
    },
    Endpoint.TENANTS_REGIONS: {
        HTTPMethod.GET: 'tenant:describe_region',
        HTTPMethod.POST: 'tenant:create_region',
        HTTPMethod.PATCH: 'tenant:update_region',
        HTTPMethod.DELETE: 'tenant:remove_region',
    },
    Endpoint.POLICIES: {
        HTTPMethod.GET: 'iam:describe_policy',
        HTTPMethod.POST: 'iam:create_policy',
        HTTPMethod.PATCH: 'iam:update_policy',
        HTTPMethod.DELETE: 'iam:remove_policy',
    },
    Endpoint.ROLES: {
        HTTPMethod.GET: 'iam:describe_role',
        HTTPMethod.POST: 'iam:create_role',
        HTTPMethod.PATCH: 'iam:update_role',
        HTTPMethod.DELETE: 'iam:remove_role',
    },
    Endpoint.SIGNUP: {
        HTTPMethod.POST: None,
    },
    Endpoint.SIGNIN: {
        HTTPMethod.POST: None
    },
}

ALL_PERMISSIONS = {
    permission for method_data in ENDPOINT_PERMISSION_MAPPING.values()
    for permission in method_data.values()
}
ALL_PERMISSIONS.discard(None)
