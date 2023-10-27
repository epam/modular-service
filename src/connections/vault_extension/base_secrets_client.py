import os

from commons.log_helper import get_logger
from services.clients.ssm import SSMClient

_LOG = get_logger(__name__)

SERVICE_MODE = os.getenv('service_mode')
is_docker = SERVICE_MODE == 'docker'

if is_docker:
    import hvac
    from connections.vault_extension.ssm_to_vault_adapter import \
        SSMToVaultAdapter

    vault_token = os.environ['VAULT_TOKEN']
    vault_url = os.environ['VAULT_URL']
    vault_port = os.environ['VAULT_SERVICE_SERVICE_PORT']

    vault_connection_url = f'http://{vault_url}:{vault_port}'
    client = hvac.Client(url=vault_connection_url, token=vault_token)
    VAULT_HANDLER = SSMToVaultAdapter(vault_connection=client)


class BaseSecretsClient(SSMClient):
    is_docker = SERVICE_MODE == 'docker'

    def __init__(self, region=None):
        super().__init__(region)

    def get_secret_value(self, secret_name):
        if self.is_docker:
            return VAULT_HANDLER.get_secret_value(secret_name=secret_name)
        return super().get_secret_value(secret_name)

    def create_secret(self, secret_name, secret_value,
                      secret_type='SecureString'):
        if self.is_docker:
            return VAULT_HANDLER.create_secret(secret_name=secret_name,
                                               secret_value=secret_value)
        return super().create_secret(secret_name, secret_value, secret_type)

    def delete_parameter(self, secret_name):
        if self.is_docker:
            return VAULT_HANDLER.delete_parameter(secret_name=secret_name)
        return super().delete_parameter(secret_name=secret_name)
