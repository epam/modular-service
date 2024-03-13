from modular_sdk.services.ssm_service import VaultSSMClient

from commons.log_helper import get_logger
from services.environment_service import EnvironmentService

_LOG = get_logger(__name__)


class ModularVaultSSMClient(VaultSSMClient):
    """
    Our custom Vault ssm client because we use different envs
    """
    mount_point = 'kv'
    key = 'data'

    def __init__(self, environment_service: EnvironmentService):
        super().__init__()
        self._env = environment_service

    def _init_client(self) -> None:
        import hvac
        _LOG.info('Initializing hvac client')
        self._client = hvac.Client(
            url=self._env.vault_endpoint(),
            token=self._env.vault_token()
        )

    def enable_secrets_engine(self, mount_point=None) -> bool:
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
