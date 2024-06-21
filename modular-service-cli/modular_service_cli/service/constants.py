from enum import Enum


# from http import HTTPMethod  # python3.11+


class HTTPMethod(str, Enum):
    HEAD = 'HEAD'
    GET = 'GET'
    POST = 'POST'
    PATCH = 'PATCH'
    DELETE = 'DELETE'
    PUT = 'PUT'


class Endpoint(str, Enum):
    ROLES = '/roles'
    SIGNUP = '/signup'
    SIGNIN = '/signin'
    TENANTS = '/tenants'
    REGIONS = '/regions'
    PARENTS = '/parents'
    REFRESH = '/refresh'
    POLICIES = '/policies'
    CUSTOMERS = '/customers'
    ROLES_NAME = '/roles/{name}'
    APPLICATIONS = '/applications'
    TENANTS_NAME = '/tenants/{name}'
    REGIONS_NAME = '/regions/{name}'  # maestro name
    POLICIES_NAME = '/policies/{name}'
    CUSTOMERS_NAME = '/customers/{name}'
    APPLICATIONS_ID = '/applications/{id}'
    USERS_RESET_PASSWORD = '/users/reset-password'
    TENANTS_NAME_REGIONS = '/tenants/{name}/regions'
    APPLICATIONS_AWS_ROLE = '/applications/aws-role'
    TENANTS_NAME_SETTINGS = '/tenants/{name}/settings'
    TENANTS_NAME_ACTIVATE = '/tenants/{name}/activate'
    TENANTS_NAME_DEACTIVATE = '/tenants/{name}/deactivate'
    CUSTOMERS_NAME_ACTIVATE = '/customers/{name}/activate'
    CUSTOMERS_NAME_DEACTIVATE = '/customers/{name}/deactivate'
    APPLICATIONS_AWS_CREDENTIALS = '/applications/aws-credentials'
    APPLICATIONS_AZURE_CREDENTIALS = '/applications/azure-credentials'
    APPLICATIONS_AZURE_CERTIFICATE = '/applications/azure-certificate'
    APPLICATIONS_GCP_SERVICE_ACCOUNT = '/applications/gcp-service-account'


class ApplicationType(str, Enum):
    AWS_ROLE = 'AWS_ROLE'
    AWS_CREDENTIALS = 'AWS_CREDENTIALS'
    AZURE_CREDENTIALS = 'AZURE_CREDENTIALS'
    AZURE_CERTIFICATE = 'AZURE_CERTIFICATE'
    AZURE_ENROLMENT = 'AZURE_ENROLMENT'
    GCP_COMPUTE_ACCOUNT = 'GCP_COMPUTE_ACCOUNT'
    GCP_SERVICE_ACCOUNT = 'GCP_SERVICE_ACCOUNT'
    CUSTODIAN = 'CUSTODIAN'
    CUSTODIAN_LICENSES = 'CUSTODIAN_LICENSES'
    RIGHTSIZER = 'RIGHTSIZER'
    RIGHTSIZER_LICENSES = 'RIGHTSIZER_LICENSES'
    RABBITMQ = 'RABBITMQ'
    DEFECT_DOJO = 'DEFECT_DOJO'
    K8S_KUBE_CONFIG = 'K8S_KUBE_CONFIG'


class ParentType(str, Enum):
    AWS_ATHENA = 'AWS_ATHENA'
    AZURE_AD_SSO = 'AZURE_AD_SSO'
    GCP_SECURITY = 'GCP_SECURITY'
    AWS_MANAGEMENT = 'AWS_MANAGEMENT'
    GCP_MANAGEMENT = 'GCP_MANAGEMENT'
    AZURE_RATE_CARDS = 'AZURE_RATE_CARDS'
    AZURE_MANAGEMENT = 'AZURE_MANAGEMENT'
    AWS_COST_EXPLORER = 'AWS_COST_EXPLORER'
    AZURE_CSP_BILLING = 'AZURE_CSP_BILLING'
    AZURE_CSP_PARTNER = 'AZURE_CSP_PARTNER'
    AZURE_USAGE_DETAILS = 'AZURE_USAGE_DETAILS'
    GCP_BILLING_SERVICE = 'GCP_BILLING_SERVICE'
    AZURE_ENTERPRISE_BILLING = 'AZURE_ENTERPRISE_BILLING'
    CUSTODIAN = 'CUSTODIAN'
    CUSTODIAN_ACCESS = 'CUSTODIAN_ACCESS'
    CUSTODIAN_LICENSES = 'CUSTODIAN_LICENSES'
    RIGHTSIZER_PARENT = 'RIGHTSIZER'
    RIGHTSIZER_LICENSES_PARENT = 'RIGHTSIZER_LICENSES'
    SIEM_DEFECT_DOJO = 'SIEM_DEFECT_DOJO'
    PLATFORM_K8S = 'PLATFORM_K8S'


class ParentScope(str, Enum):
    ALL = 'ALL'
    DISABLED = 'DISABLED'
    SPECIFIC = 'SPECIFIC'


class Cloud(str, Enum):
    AZURE = 'AZURE'
    YANDEX = 'YANDEX'
    GOOGLE = 'GOOGLE'
    AWS = 'AWS'
    OPENSTACK = 'OPEN_STACK'
    CSA = 'CSA'
    HWU = 'HARDWARE'
    ENTERPRISE = 'ENTERPRISE'
    EXOSCALE = 'EXOSCALE'
    WORKSPACE = 'WORKSPACE'
    AOS = 'AOS'
    VSPHERE = 'VSPHERE'
    VMWARE = 'VMWARE'  # VCloudDirector group
    NUTANIX = 'NUTANIX'


DATA_ATTR = 'data'
ITEMS_ATTR = 'items'
ERRORS_ATTR = 'errors'
MESSAGE_ATTR = 'message'
NEXT_TOKEN_ATTR = 'next_token'

LAMBDA_INVOCATION_TRACE_ID_HEADER = 'Lambda-Invocation-Trace-Id'
SERVER_VERSION_HEADER = 'Accept-Version'

# responses
NO_ITEMS_TO_DISPLAY_RESPONSE_MESSAGE = 'No items to display'
NO_CONTENT_RESPONSE_MESSAGE = 'Request is successful. No content returned'
