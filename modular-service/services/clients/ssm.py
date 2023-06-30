import json

import boto3
from botocore.client import ClientError

from commons.log_helper import get_logger

_LOG = get_logger(__name__)


class SSMClient:
    def __init__(self, region):
        self._region = region
        self._client = None

    @property
    def client(self):
        if not self._client:
            _LOG.info('Initializing ssm client')
            self._client = boto3.client('ssm', self._region)
        return self._client

    def get_secret_value(self, secret_name):
        try:
            response = self.client.get_parameter(
                Name=secret_name,
                WithDecryption=True
            )
            value_str = response['Parameter']['Value']
            try:
                return json.loads(value_str)
            except json.decoder.JSONDecodeError:
                return value_str
        except ClientError as e:
            error_code = e.response['Error']['Code']
            _LOG.error(f'Can\'t get secret for name \'{secret_name}\', '
                       f'error code: \'{error_code}\'')

    def get_secret_values(self, secret_names: list):
        try:
            response = self.client.get_parameters(
                Names=secret_names,
                WithDecryption=True)
            parameters = {item.get('Name'): item.get('Value') for item in
                          response.get('Parameters')}
            return parameters
        except ClientError as e:
            error_code = e.response['Error']['Code']
            _LOG.error(f'Can\'t get secret for names \'{secret_names}\', '
                       f'error code: \'{error_code}\'')

    def create_secret(self, secret_name: str, secret_value: str,
                      secret_type='SecureString'):
        try:
            if isinstance(secret_value, (list, dict)):
                secret_value = json.dumps(secret_value)
            self.client.put_parameter(
                Name=secret_name,
                Value=secret_value,
                Overwrite=True,
                Type=secret_type)
        except ClientError as e:
            error_code = e.response['Error']['Code']
            _LOG.error(f'Can\'t get secret for name \'{secret_name}\', '
                       f'error code: \'{error_code}\'')

    def delete_parameter(self, secret_name: str):
        try:
            self.client.delete_parameter(Name=secret_name)
        except ClientError as e:
            error_code = e.response['Error']['Code']
            _LOG.error(f'Can\'t delete secret name \'{secret_name}\', '
                       f'error code: \'{error_code}\'')
