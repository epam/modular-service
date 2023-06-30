import hvac
from hvac.exceptions import InvalidPath

MOUNT_POINT = 'kv'


class SSMToVaultAdapter:
    def __init__(self, vault_connection):
        self.vault_conn: hvac = vault_connection

    def describe_params(self, name=None):
        try:
            response = self.vault_conn.secrets.kv.v2.read_secret_metadata(
                path=name, mount_point=MOUNT_POINT)
        except InvalidPath:
            return False
        return response.get('data')

    def get_secret_value(self, secret_name):
        try:
            response = self.vault_conn.secrets.kv.v2.read_secret_version(
                path=secret_name, mount_point=MOUNT_POINT)
        except InvalidPath:
            return
        return response.get('data').get('data').get(
            'data') if response else None

    def create_secret(self, secret_name, secret_value):
        return self.vault_conn.secrets.kv.v2.create_or_update_secret(
            path=secret_name,
            secret={'data': secret_value},
            mount_point=MOUNT_POINT)

    def delete_parameter(self, secret_name):
        return self.vault_conn.secrets.kv.v2.delete_latest_version_of_secret(
            path=secret_name, mount_point=MOUNT_POINT)

    def delete_parameters(self, names):
        for name in names:
            self.vault_conn.secrets.kv.v2.delete_latest_version_of_secret(
                path=name, mount_point=MOUNT_POINT)

    def list_parameters(self):
        response = self.vault_conn.secrets.kv.v2.list_secrets(
            path='', mount_point=MOUNT_POINT)
        if response and response['data'] and response['data']['keys']:
            return response['data']['keys']

    def get_secret_values(self, secret_names):
        # todo implement
        pass
