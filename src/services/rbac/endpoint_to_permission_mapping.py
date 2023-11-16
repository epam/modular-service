GET_METHOD = 'GET'
POST_METHOD = 'POST'
PATCH_METHOD = 'PATCH'
DELETE_METHOD = 'DELETE'

ENDPOINT_PERMISSION_MAPPING = {
    '/applications/': {
        GET_METHOD: 'application:describe_application',
        POST_METHOD: 'application:create_application',
        PATCH_METHOD: 'application:update_application',
        DELETE_METHOD: 'application:remove_application',
    },
    '/customers/': {
        GET_METHOD: 'customer:describe_customer',
        POST_METHOD: 'customer:create_customer',
        PATCH_METHOD: 'customer:update_customer',
        DELETE_METHOD: 'customer:remove_customer',
    },
    '/parents/': {
        GET_METHOD: 'parent:describe_parent',
        POST_METHOD: 'parent:create_parent',
        PATCH_METHOD: 'parent:update_parent',
        DELETE_METHOD: 'parent:remove_parent',
    },
    '/tenants/': {
        GET_METHOD: 'tenant:describe_tenant',
        POST_METHOD: 'tenant:create_tenant',
        PATCH_METHOD: 'tenant:update_tenant',
        DELETE_METHOD: 'tenant:remove_tenant',
    },
    '/regions/': {
        GET_METHOD: 'region:describe_region',
        POST_METHOD: 'region:create_region',
        PATCH_METHOD: 'region:update_region',
        DELETE_METHOD: 'region:remove_region',
    },
    '/tenants/regions/': {
        GET_METHOD: 'tenant:describe_region',
        POST_METHOD: 'tenant:create_region',
        PATCH_METHOD: 'tenant:update_region',
        DELETE_METHOD: 'tenant:remove_region',
    },
    '/policies/': {
        GET_METHOD: 'iam:describe_policy',
        POST_METHOD: 'iam:create_policy',
        PATCH_METHOD: 'iam:update_policy',
        DELETE_METHOD: 'iam:remove_policy',
    },
    '/roles/': {
        GET_METHOD: 'iam:describe_role',
        POST_METHOD: 'iam:create_role',
        PATCH_METHOD: 'iam:update_role',
        DELETE_METHOD: 'iam:remove_role',
    },
    '/signup/': {
        POST_METHOD: None,
    },
    '/signin/': {
        POST_METHOD: None
    },
}
