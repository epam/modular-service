from typing import MutableMapping, Mapping

from commons.constants import Env


class EnvironmentService:
    def __init__(self, source: MutableMapping):
        self._env = source

    def update(self, source: Mapping):
        self._env.update(source)

    def aws_region(self) -> str:
        return (self._env.get('AWS_REGION')
                or self._env.get('AWS_DEFAULT_REGION') or 'us-east-1')

    def is_docker(self) -> bool:
        return self._env.get(Env.SERVICE_MODE) == 'docker'

    def user_pool_name(self) -> str | None:
        return self._env.get(Env.COGNITO_USER_POOL_NAME)

    def user_pool_id(self) -> str | None:
        return self._env.get(Env.COGNITO_USER_POOL_ID)

    def _ensure_env(self, name: Env) -> str:
        val = self._env.get(name)
        if not val:
            raise RuntimeError(f'Env {val} is required')
        return val

    def vault_endpoint(self) -> str:
        return self._ensure_env(Env.VAULT_ENDPOINT)

    def vault_token(self) -> str:
        return self._ensure_env(Env.VAULT_TOKEN)

    def mongo_uri(self) -> str:
        return self._ensure_env(Env.MONGO_URI)

    def mongo_database(self) -> str:
        return self._ensure_env(Env.MONGO_DATABASE)

    def is_external_ssm(self) -> bool:
        """
        modular tables can be placed in another aws account. So, should we use
        SSM parameter store from their account or from ours? By default - ours
        :return:
        """
        env = str(self._env.get(Env.EXTERNAL_SSM)).lower()
        return env in ('y', 'yes', 'true')
