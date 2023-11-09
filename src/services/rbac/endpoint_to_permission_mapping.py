GET_METHOD = 'GET'
POST_METHOD = 'POST'
PATCH_METHOD = 'PATCH'
DELETE_METHOD = 'DELETE'

ENDPOINT_PERMISSION_MAPPING = {
    '/customers/': {
        GET_METHOD: 'modular:customer:describe_customer',
        POST_METHOD: 'modular:customer:create_customer',
        PATCH_METHOD: 'modular:customer:update_customer',
        DELETE_METHOD: 'modular:customer:remove_customer',
    },
    '/applications/': {
        GET_METHOD: 'modular:application:describe_application',
        POST_METHOD: 'modular:application:create_application',
        PATCH_METHOD: 'modular:application:update_application',
        DELETE_METHOD: 'modular:application:remove_application',
    },
    '/parents/': {
        GET_METHOD: 'modular:parent:describe_parent',
        POST_METHOD: 'modular:parent:create_parent',
        PATCH_METHOD: 'modular:parent:update_parent',
        DELETE_METHOD: 'modular:parent:remove_parent',
    },
    '/tenants/': {
        GET_METHOD: 'modular:tenant:describe_tenant',
        POST_METHOD: 'modular:tenant:create_tenant',
        PATCH_METHOD: 'modular:tenant:update_tenant',
        DELETE_METHOD: 'modular:tenant:remove_tenant',
    },
    '/regions/': {
        GET_METHOD: 'modular:region:describe_region',
        POST_METHOD: 'modular:region:create_region',
        PATCH_METHOD: 'modular:region:update_region',
        DELETE_METHOD: 'modular:region:remove_region',
    },
    '/tenants/regions/': {
        GET_METHOD: 'modular:tenant:describe_region',
        POST_METHOD: 'modular:tenant:create_region',
        PATCH_METHOD: 'modular:tenant:update_region',
        DELETE_METHOD: 'modular:tenant:remove_region',
    },
    '/policies/': {
        GET_METHOD: 'modular:iam:describe_policy',
        POST_METHOD: 'modular:iam:create_policy',
        PATCH_METHOD: 'modular:iam:update_policy',
        DELETE_METHOD: 'modular:iam:remove_policy',
    },
    '/roles/': {
        GET_METHOD: 'modular:iam:describe_role',
        POST_METHOD: 'modular:iam:create_role',
        PATCH_METHOD: 'modular:iam:update_role',
        DELETE_METHOD: 'modular:iam:remove_role',
    },
    '/signup/': {
        POST_METHOD: None,
    },
    '/signin/': {
        POST_METHOD: None
    },
}
