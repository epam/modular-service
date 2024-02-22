import json
import re
from abc import ABC, abstractmethod
from functools import cached_property
from secrets import token_hex

import boto3
from botocore.exceptions import ClientError

from commons.log_helper import get_logger
from services.environment_service import EnvironmentService

_LOG = get_logger(__name__)
Json = list | dict | str | None
SSM_NOT_AVAILABLE = re.compile(r'[^a-zA-Z0-9\/_.-]')


class AbstractSSMClient(ABC):
    @classmethod
    def allowed_name(cls, name: str) -> str:
        """
        Keeps only allowed symbols
        """
        return str(re.sub(SSM_NOT_AVAILABLE, '-', name))

    @classmethod
    def generate_name(cls, prefix: str = 'cloud-mentor.',
                      suffix: str = '',
                      name: str | None = None) -> str:
        name = name or token_hex(10)
        return cls.allowed_name(f'{prefix}{name}{suffix}')

    @abstractmethod
    def get_parameter(self, name: str) -> Json | None:
        """
        Gets raw value of parameter from ssm parameter store
        :param name:
        :return:
        """

    @abstractmethod
    def put_parameter(self, name: str, value: Json) -> bool:
        ...

    @abstractmethod
    def delete_parameter(self, name: str) -> bool:
        ...

    def enable_secrets_engine(self, mount_point=None):
        pass

    def is_secrets_engine_enabled(self, mount_point=None) -> bool:
        return True


class SSMClient(AbstractSSMClient):
    """
    Sync client
    """

    @cached_property
    def client(self):
        _LOG.info('Initializing boto3 ssm client')
        return boto3.client('ssm')

    def get_parameter(self, name: str) -> Json:
        try:
            _LOG.info(f'Getting {name} from SSM')
            val = self.client.get_parameter(
                Name=name, WithDecryption=True
            )['Parameter']['Value']
            try:
                return json.loads(val)
            except json.JSONDecodeError:
                return val
        except ClientError as e:
            _LOG.exception('Error occurred trying to get parameter')
            return

    def put_parameter(self, name: str, value: Json) -> bool:
        if isinstance(value, (list, dict)):
            value = json.dumps(value, separators=(",", ":"),
                               sort_keys=True)
        try:
            self.client.put_parameter(
                Name=name,
                Value=value,
                Overwrite=True,
                Type='SecureString'
            )
            return True
        except ClientError as e:
            _LOG.exception('Could not put parameter')
            return False

    def delete_parameter(self, name: str) -> bool:
        try:
            self.client.delete_parameter(Name=name)
            return True
        except ClientError as e:
            _LOG.exception('Could not delete parameter')
            return False


class VaultSSMClient(AbstractSSMClient):
    mount_point = 'kv'
    key = 'data'

    def __init__(self, environment_service: EnvironmentService):
        self._env = environment_service

    def _init_client(self):
        import hvac
        _LOG.info('Initializing hvac client')
        return hvac.Client(
            url=self._env.vault_endpoint(),
            token=self._env.vault_token()
        )

    @cached_property
    def client(self):
        return self._init_client()

    def get_parameter(self, name: str) -> str | dict | list | None:
        try:
            response = self.client.secrets.kv.v2.read_secret_version(
                path=name, mount_point=self.mount_point) or {}
        except Exception:  # hvac.InvalidPath
            return
        return response.get('data', {}).get('data', {}).get(self.key)

    def put_parameter(self, name: str, value: Json) -> bool:
        self.client.secrets.kv.v2.create_or_update_secret(
            path=name,
            secret={self.key: value},
            mount_point=self.mount_point
        )
        return True

    def delete_parameter(self, name: str) -> bool:
        return bool(self.client.secrets.kv.v2.delete_metadata_and_all_versions(
            path=name, mount_point=self.mount_point)
        )

    def enable_secrets_engine(self, mount_point=None):
        try:
            self.client.sys.enable_secrets_engine(
                backend_type='kv',
                path=(mount_point or self.mount_point),
                options={'version': 2}
            )
            return True
        except Exception:  # hvac.exceptions.InvalidRequest
            return False  # already exists

    def is_secrets_engine_enabled(self, mount_point=None) -> bool:
        mount_points = self.client.sys.list_mounted_secrets_engines()
        target_point = mount_point or self.mount_point
        return f'{target_point}/' in mount_points
