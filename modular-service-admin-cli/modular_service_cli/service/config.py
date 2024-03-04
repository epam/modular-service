from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed
from itertools import chain
from pathlib import Path
from typing import Generator, TYPE_CHECKING

from botocore.credentials import JSONFileCache

from modular_service_cli.service.logger import get_logger

if TYPE_CHECKING:
    from modular_cli_sdk.services.credentials_manager import (
        AbstractCredentialsManager)

SYSTEM_LOG = get_logger(__name__)
Json = dict | list | float | int | str | bool


class AbstractConfig(ABC):
    @property
    @abstractmethod
    def api_link(self) -> str | None:
        ...

    @api_link.setter
    @abstractmethod
    def api_link(self, value):
        ...

    @property
    @abstractmethod
    def access_token(self) -> str | None:
        ...

    @access_token.setter
    @abstractmethod
    def access_token(self, value):
        ...

    @abstractmethod
    def items(self) -> Generator[tuple[str, Json], None, None]:
        ...

    @abstractmethod
    def clear(self):
        ...

    @abstractmethod
    def set(self, key: str, value: Json):
        ...

    @abstractmethod
    def update(self, dct: dict):
        ...


class OnDiskModularServiceConfig(JSONFileCache, AbstractConfig):
    CACHE_DIR = Path.home() / '.modular_service_admin_cli'

    def __init__(self, prefix: str = 'root', working_dir: Path = CACHE_DIR):
        super().__init__(working_dir=str(working_dir / prefix))

    def get(self, cache_key: str) -> Json | None:
        if cache_key in self:
            return self[cache_key]

    def set(self, key: str, value: Json):
        self[key] = value

    def update(self, dct: dict):
        for key, value in dct.items():
            self.set(key, value)

    @property
    def api_link(self) -> str | None:
        return self.get('api_link')

    @api_link.setter
    def api_link(self, value: str):
        self['api_link'] = value

    @api_link.deleter
    def api_link(self):
        if 'api_link' in self:
            del self['api_link']

    @property
    def access_token(self) -> str | None:
        return self.get('access_token')

    @access_token.setter
    def access_token(self, value: str):
        self['access_token'] = value

    @access_token.deleter
    def access_token(self):
        if 'access_token' in self:
            del self['access_token']

    @classmethod
    def public_config_params(cls) -> list[property]:
        return [
            cls.api_link,
        ]

    @classmethod
    def private_config_params(cls) -> list[property]:
        return [
            cls.access_token,
        ]

    def items(self, private: bool = False) -> Generator[tuple[str, Json], None, None]:
        lst = self.public_config_params()
        if private:
            lst += self.private_config_params()
        with ThreadPoolExecutor() as executor:  # it reads a lot of files
            futures = {
                executor.submit(prop.fget, self): prop.fget.__name__
                for prop in lst
            }
            for future in as_completed(futures):
                yield futures[future], future.result()

    def clear(self):
        it = chain(self.public_config_params(), self.private_config_params())
        with ThreadPoolExecutor() as executor:
            for prop in it:
                executor.submit(prop.fdel, self)


class ModularCliSdkConfig(AbstractConfig):
    """
    For integration with modular cli sdk
    """
    __slots__ = '_credentials_manager', '_config_dict'

    def __init__(self, credentials_manager: 'AbstractCredentialsManager'):
        self._credentials_manager = credentials_manager
        self._config_dict = {}

    @property
    def config_dict(self) -> dict:
        from modular_cli_sdk.commons.exception import \
            ModularCliSdkBaseException
        # in order to be able to use other classes from this module
        # without cli_sdk installed
        if not self._config_dict:
            try:
                SYSTEM_LOG.info('Getting creds from credentials manager')
                self._config_dict = self._credentials_manager.extract()
            except ModularCliSdkBaseException:
                pass
        return self._config_dict

    def set(self, key: str, value: Json) -> None:
        config_dict = self.config_dict
        config_dict[key] = value
        self._credentials_manager.store(config_dict)

    def update(self, dct: dict) -> None:
        config_dict = self.config_dict
        config_dict.update(dct)
        self._credentials_manager.store(config_dict)

    @property
    def api_link(self) -> str | None:
        return self.config_dict.get('api_link')

    @api_link.setter
    def api_link(self, value: str):
        self.set('api_link', value)

    @property
    def access_token(self) -> str | None:
        return self.config_dict.get('access_token')

    @access_token.setter
    def access_token(self, value: str):
        self.set('access_token', value)

    def items(self) -> Generator[tuple[str, Json], None, None]:
        yield 'api_link', self.api_link

    def clear(self):
        self._credentials_manager.clean_up()
