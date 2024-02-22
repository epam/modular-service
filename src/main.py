from abc import ABC, abstractmethod
import argparse
import base64
import logging
import logging.config
import multiprocessing
import os
from pathlib import Path
import secrets
import string
from typing import Callable, Literal, TYPE_CHECKING

from commons.__version__ import __version__
from commons.constants import Env, PRIVATE_KEY_SECRET_NAME

# NOTE, all imports are inside corresponding methods in order to make
# CLI more or less fast
if TYPE_CHECKING:
    from models import BaseModel
    from bottle import Bottle

DEFAULT_HOST = '0.0.0.0'
DEFAULT_PORT = 8000
DEFAULT_NUMBER_OF_WORKERS = (multiprocessing.cpu_count() * 2) + 1
DEFAULT_ON_PREM_API_LINK = f'http://{DEFAULT_HOST}:{str(DEFAULT_PORT)}/caas'
DEFAULT_API_GATEWAY_NAME = 'custodian-as-a-service-api'
DEFAULT_SWAGGER_PREFIX = '/api/doc'

ACTION_DEST = 'action'
ENV_ACTION_DEST = 'env_action'
ALL_NESTING: tuple[str, ...] = (ACTION_DEST, ENV_ACTION_DEST)  # important

RUN_ACTION = 'run'
GENERATE_OPENAPI_ACTION = 'generate-openapi'
INIT_VAULT_ACTION = 'init-vault'
CREATE_INDEXES_ACTION = 'create-indexes'
INIT_ACTION = 'init'


def get_logger():
    config = {
        'version': 1,
        'disable_existing_loggers': True
    }
    logging.config.dictConfig(config)
    logger = logging.getLogger()
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger


_LOG = get_logger()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Modular service main CLI endpoint'
    )
    # -- top level sub-parser
    sub_parsers = parser.add_subparsers(dest=ACTION_DEST, required=True,
                                        help='Available actions')

    # generate-openapi
    parser_open_api = sub_parsers.add_parser(
        GENERATE_OPENAPI_ACTION,
        help='Generates Open API spec for API'
    )
    parser_open_api.add_argument(
        '-f', '--filename', type=Path, required=True,
        help='Filename where to write spec'
    )

    # run
    parser_run = sub_parsers.add_parser(RUN_ACTION, help='Run on-prem server')
    parser_run.add_argument(
        '-g', '--gunicorn', action='store_true', default=False,
        help='Specify the flag is you want to run the server via Gunicorn')
    parser_run.add_argument(
        '-nw', '--workers', type=int, required=False,
        help='Number of gunicorn workers. Must be specified only '
             'if --gunicorn flag is set'
    )
    parser_run.add_argument(
        '-sw', '--swagger', action='store_true', default=False,
        help='Specify the flag is you want to enable swagger'
    )
    parser_run.add_argument(
        '-swp', '--swagger-prefix', type=str, default=DEFAULT_SWAGGER_PREFIX,
        help='Swagger path prefix, (default: %(default)s)'
    )
    parser_run.add_argument('--host', default=DEFAULT_HOST, type=str,
                            help='IP address where to run the server')
    parser_run.add_argument('--port', default=DEFAULT_PORT, type=int,
                            help='IP Port to run the server on')

    # init-vault
    _ = sub_parsers.add_parser(INIT_VAULT_ACTION, help='Init token in vault')

    # init
    parser_init = sub_parsers.add_parser(
        INIT_ACTION, help='Creates admin policy, role and user'
    )
    parser_init.add_argument('--username', required=True, type=str,
                             help='Admin username')

    # create-indexes
    _ = sub_parsers.add_parser(
        CREATE_INDEXES_ACTION, help='Creates indexes for mongo'
    )
    return parser


class ActionHandler(ABC):
    @abstractmethod
    def __call__(self, **kwargs):
        ...


class InitVault(ABC):
    def __call__(self):
        from services import SP
        ssm = SP.ssm
        if ssm.enable_secrets_engine():
            _LOG.info('Vault engine was enabled')
        else:
            _LOG.info('Vault engine has been already enabled')
        if ssm.get_parameter(PRIVATE_KEY_SECRET_NAME):
            _LOG.info('Token inside Vault already exists. Skipping...')
            return

        ssm.put_parameter(
            name=PRIVATE_KEY_SECRET_NAME,
            value=self.generate_private_key()
        )
        print('Token was set to Vault')

    @staticmethod
    def generate_private_key(kty: Literal['EC', 'RSA'] = 'EC',
                             crv='P-521', size: int = 4096,
                             ) -> str:
        """
        Generates a private key and exports PEM to str encoding it to base64
        :param kty:
        :param crv:
        :param size:
        :return:
        """
        from jwcrypto import jwk
        match kty:
            case 'EC':
                key = jwk.JWK.generate(kty=kty, crv=crv)
            case _:  # RSA
                key = jwk.JWK.generate(kty=kty, size=size)
        return base64.b64encode(key.export_to_pem(private_key=True,
                                                  password=None)).decode()  # type: ignore


class Run(ActionHandler):
    def _init_swagger(self, app: 'Bottle', prefix: str) -> None:
        from swagger_ui import api_doc
        from services.openapi_spec_generator import OpenApiGenerator
        url = f'http://{self._host}:{self._port}'
        # TODO get from handlers
        generator = OpenApiGenerator(
            title='Modular service API',
            description='Modular service rest API',
            url=url,
            stages='dev',
            version=__version__,
            endpoints=[]
        )
        if not prefix.startswith('/'):
            prefix = f'/{prefix}'
        api_doc(
            app,
            config=generator.generate(),
            url_prefix=prefix,
            title='Rule engine'
        )
        _LOG.info(f'Serving swagger on {url + prefix}')

    def __call__(self, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT,
                 gunicorn: bool = False, workers: int | None = None,
                 swagger: bool = False,
                 swagger_prefix: str = DEFAULT_SWAGGER_PREFIX):
        from onprem.app import OnPremApiBuilder
        self._host = host
        self._port = port

        if not gunicorn and workers:
            _LOG.warning(
                '--workers is ignored because you are not running Gunicorn'
            )

        os.environ[Env.SERVICE_MODE] = 'docker'

        app = OnPremApiBuilder().build()
        if swagger:
            self._init_swagger(app, swagger_prefix)

        if gunicorn:
            workers = workers or DEFAULT_NUMBER_OF_WORKERS
            from onprem.app_gunicorn import CustodianGunicornApplication
            options = {
                'bind': f'{host}:{port}',
                'workers': workers,
            }
            CustodianGunicornApplication(app, options).run()
        else:
            app.run(host=host, port=port)


class Init(ActionHandler):
    @staticmethod
    def gen_password(digits: int = 20) -> str:
        allowed_punctuation = ''.join(
            set(string.punctuation) - {'"', "'", "!"})
        chars = string.ascii_letters + string.digits + allowed_punctuation
        while True:
            password = ''.join(
                secrets.choice(chars) for _ in range(digits)) + '='
            if (any(c.islower() for c in password)
                    and any(c.isupper() for c in password)
                    and sum(c.isdigit() for c in password) >= 3):
                break
        return password

    def __call__(self, username: str):
        from models.policy import Policy
        from models.role import Role
        from services.rbac.endpoint_to_permission_mapping import \
            ALL_PERMISSIONS
        from services import SP

        Policy(
            name='admin_policy',
            permissions=list(ALL_PERMISSIONS)
        ).save()
        Role(
            name='admin_role',
            policies=['admin_policy']
        ).save()

        user_service = SP.user_service
        password = self.gen_password()
        user_service.save(
            username=username,
            password=password,
            role='admin_role'
        )
        print(password)


class CreateIndexes(ActionHandler):
    @staticmethod
    def convert_index(key_schema: dict) -> str | list[tuple]:
        if len(key_schema) == 1:
            _LOG.info('Only hash key found for the index')
            return key_schema[0]['AttributeName']
        elif len(key_schema) == 2:
            _LOG.info('Both hash and range keys found for the index')
            result = [None, None]
            for key in key_schema:
                if key['KeyType'] == 'HASH':
                    _i = 0
                elif key['KeyType'] == 'RANGE':
                    _i = 1
                else:
                    raise ValueError(f'Unknown key type: {key["KeyType"]}')
                result[_i] = (key['AttributeName'], -1)  # descending
            return result
        else:
            raise ValueError(f'Unknown key schema: {key_schema}')

    def create_indexes_for_model(self, model: type['BaseModel']):
        table_name = model.Meta.table_name
        collection = model.mongodb_handler().mongodb.collection(table_name)
        collection.drop_indexes()

        hash_key = getattr(model._hash_key_attribute(), 'attr_name', None)
        range_key = getattr(model._range_key_attribute(), 'attr_name', None)
        _LOG.info(f'Creating main indexes for \'{table_name}\'')
        if hash_key and range_key:
            collection.create_index([(hash_key, 1),
                                     (range_key, 1)],
                                    name='main')
        elif hash_key:
            collection.create_index(hash_key, name='main')
        else:
            _LOG.error(f'Table \'{table_name}\' has no hash_key and range_key')

        indexes = model._get_schema()  # GSIs & LSIs,  # only PynamoDB 5.2.1+
        gsi = indexes.get('global_secondary_indexes')
        lsi = indexes.get('local_secondary_indexes')
        if gsi:
            _LOG.info(f'Creating global indexes for \'{table_name}\'')
            for i in gsi:
                index_name = i['index_name']
                _LOG.info(f'Processing index \'{index_name}\'')
                collection.create_index(
                    self.convert_index(i['key_schema']), name=index_name)
                _LOG.info(f'Index \'{index_name}\' was created')
            _LOG.info(f'Global indexes for \'{table_name}\' were created!')
        if lsi:
            pass  # write this part if at least one LSI is used

    def __call__(self):
        from models.policy import Policy
        from models.role import Role
        from models.user import User
        for model in (Policy, Role, User):
            self.create_indexes_for_model(model)


def main(args: list[str] | None = None):
    parser = build_parser()
    arguments = parser.parse_args(args)
    key = tuple(
        getattr(arguments, dest) for dest in ALL_NESTING
        if hasattr(arguments, dest)
    )
    mapping: dict[tuple[str, ...], Callable] = {
        (RUN_ACTION,): Run(),
        (INIT_VAULT_ACTION,): InitVault(),
        (INIT_ACTION,): Init(),
        (CREATE_INDEXES_ACTION,): CreateIndexes()
    }
    func = mapping.get(key) or (lambda **kwargs: _LOG.error('Hello'))
    for dest in ALL_NESTING:
        if hasattr(arguments, dest):
            delattr(arguments, dest)
    from dotenv import load_dotenv
    load_dotenv(verbose=True)
    func(**vars(arguments))


if __name__ == '__main__':
    main()
