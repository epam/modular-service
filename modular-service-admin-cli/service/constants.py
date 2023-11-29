PARAM_NAME = 'name'
PARAM_DISPLAY_NAME = 'display_name'
PARAM_PERMISSIONS = 'permissions'
PARAM_PERMISSIONS_ADMIN = 'permissions_admin'
PARAM_EXPIRATION = 'expiration'
PARAM_POLICIES = 'policies'
PARAM_VERSION = 'version'
PARAM_CLOUD = 'cloud'
PARAM_SUBMITTED_AT = 'submitted_at'
PARAM_CREATED_AT = 'created_at'
PARAM_STARTED_AT = 'started_at'
PARAM_STOPPED_AT = 'stopped_at'
PARAM_ACTIVE = 'active'
PARAM_ACTION = 'action'
PARAM_ADMINS = 'admins'
PARAM_OVERRIDE = 'override'
PARAM_APPLICATION_ID = 'application_id'
PARAM_TENANT_NAME = 'tenant_name'
PARAM_READ_ONLY = 'read_only'
PARAM_TENANT_CUSTOMER = 'tenant_customer'
PARAM_TYPE = 'type'
PARAM_CUSTOMER_ID = 'customer_id'
PARAM_DESCRIPTION = 'description'
PARAM_PARENT_ID = 'parent_id'
PARAM_MAESTRO_NAME = 'maestro_name'
PARAM_NATIVE_NAME = 'native_name'
PARAM_REGION_ID = 'region_id'
PARAM_ACC = 'acc'

AWS_ROLE = 'AWS_ROLE'
AWS_CREDENTIALS = 'AWS_CREDENTIALS'
AZURE_CREDENTIALS = 'AZURE_CREDENTIALS'
AZURE_ENROLMENT = 'AZURE_ENROLMENT'
GCP_COMPUTE_ACCOUNT = 'GCP_COMPUTE_ACCOUNT'
GCP_SERVICE_ACCOUNT = 'GCP_SERVICE_ACCOUNT'
CUSTODIAN_TYPE = 'CUSTODIAN'

AVAILABLE_APPLICATION_TYPES = [
    AWS_ROLE, AWS_CREDENTIALS, AZURE_CREDENTIALS, AZURE_ENROLMENT,
    GCP_COMPUTE_ACCOUNT, GCP_SERVICE_ACCOUNT, CUSTODIAN_TYPE
]

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
CUSTODIAN_CUSTOMER = 'CUSTODIAN_CUSTOMER'
ALL_PARENT_TYPES = [AWS_MANAGEMENT, AWS_ATHENA, AWS_COST_EXPLORER,
                    AZURE_ENTERPRISE_BILLING, AZURE_USAGE_DETAILS,
                    AZURE_RATE_CARDS, AZURE_CSP_BILLING, AZURE_CSP_PARTNER,
                    AZURE_MANAGEMENT, AZURE_AD_SSO, GCP_BILLING_SERVICE,
                    GCP_SECURITY, GCP_MANAGEMENT, CUSTODIAN_CUSTOMER]

AZURE_CLOUD = 'AZURE'
YANDEX_CLOUD = 'YANDEX'
GOOGLE_CLOUD = 'GOOGLE'
AWS_CLOUD = 'AWS'
OPENSTACK_CLOUD = 'OPEN_STACK'
CSA_CLOUD = 'CSA'
HWU_CLOUD = 'HARDWARE'
ENTERPRISE_CLOUD = 'ENTERPRISE'
EXOSCALE_CLOUD = 'EXOSCALE'
WORKSPACE_CLOUD = 'WORKSPACE'
AOS_CLOUD = 'AOS'
VSPHERE_CLOUD = 'VSPHERE'
VMWARE_CLOUD = 'VMWARE'  # VCloudDirector group
NUTANIX_CLOUD = 'NUTANIX'

CLOUD_PROVIDERS = [AZURE_CLOUD, GOOGLE_CLOUD, AWS_CLOUD, OPENSTACK_CLOUD,
                   HWU_CLOUD, EXOSCALE_CLOUD, CSA_CLOUD, YANDEX_CLOUD,
                   WORKSPACE_CLOUD, ENTERPRISE_CLOUD, AOS_CLOUD, VSPHERE_CLOUD,
                   VMWARE_CLOUD, NUTANIX_CLOUD]


PARAM_USERNAME = 'username'
PARAM_PASSWORD = 'password'
API_POLICY = 'policies'
API_ROLE = 'roles'
API_CUSTOMER = 'customers'
API_TENANT = 'tenants'
API_REGION = 'regions'
API_APPLICATION = 'applications'
API_PARENT = 'parents'
API_TENANT_REGION = 'tenants/regions'
API_SIGNIN = 'signin'


PARAM_ID = '_id'
PARAM_JOB_ID = 'id'

PARAM_TENANT = 'tenant'
PARAM_ACTION = 'action'
PARAM_BODY = 'body'

PARAM_CUSTOMER = 'customer'
PARAM_REGION = 'region'


PARAM_REPORT_TYPE = 'report_type'
REPORT_RESIZE = 'instance_shape'
REPORT_DOWNLOAD = 'download'

POLICIES_TO_ATTACH = 'policies_to_attach'
POLICIES_TO_DETACH = 'policies_to_detach'

PERMISSIONS_TO_ATTACH = 'permissions_to_attach'
PERMISSIONS_TO_DETACH = 'permissions_to_detach'

PARAM_API_VERSION = 'api_version'

ALL = 'ALL'
DISABLED = 'DISABLED'
SPECIFIC = 'SPECIFIC'
AVAILABLE_PARENT_SCOPES = (ALL, DISABLED, SPECIFIC)
AVAILABLE_CLOUDS = ('AWS', 'AZURE', 'GOOGLE')
META = 'meta'
SCOPE = 'scope'


