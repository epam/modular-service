#!/usr/local/bin/python
from abc import ABC, abstractmethod
import argparse
import base64
from functools import cached_property
import json
import logging
import logging.config
import multiprocessing
import os
from pathlib import Path
import secrets
import string
import sys
from typing import Any, Callable, Literal, TYPE_CHECKING
import urllib.error
import urllib.request

from commons import dereference_json
from commons.__version__ import __version__
from commons.constants import Env, HTTPMethod, PRIVATE_KEY_SECRET_NAME, Permission

# NOTE, all imports are inside corresponding methods in order to make cli faster
if TYPE_CHECKING:
    from models import BaseModel
    from bottle import Bottle

DEFAULT_HOST = '0.0.0.0'
DEFAULT_PORT = 8040
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
DUMP_PERMISSIONS_ACTION = 'dump-permissions'
CREATE_SYSTEM_USER_ACTION = 'create-system-user'
UPDATE_DEPLOYMENT_RESOURCES_ACTION = 'update-deployment-resources'

SYSTEM_USER = 'system_user'


logging.config.dictConfig({
    'version': 1,
    'formatters': {
        'console_formatter': {'format': '%(levelname)s - %(message)s'},
    },
    'handlers': {
        'console_handler': {
            'class': 'logging.StreamHandler',
            'formatter': 'console_formatter'
        },
    },
    'loggers': {
        '__main__': {'level': 'DEBUG', 'handlers': ['console_handler']},
    }
})


_LOG = logging.getLogger(__name__)



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
    _ = sub_parsers.add_parser(
        CREATE_SYSTEM_USER_ACTION,
        help='Creates a system user that can perform actions on behalf of '
             'other users'
    )

    # create-indexes
    _ = sub_parsers.add_parser(
        CREATE_INDEXES_ACTION, help='Creates indexes for mongo'
    )
    _ = sub_parsers.add_parser(
        DUMP_PERMISSIONS_ACTION, help='Dumps all the available permission'
    )
    _ = sub_parsers.add_parser(
        UPDATE_DEPLOYMENT_RESOURCES_ACTION,
        help='Updates api definition insider deployment_resources.json'
    )
    return parser


class ActionHandler(ABC):
    @abstractmethod
    def __call__(self, **kwargs):
        ...


class InitVault(ABC):
    def __call__(self):
        from services import SP
        if not SP.environment_service.is_docker():
            _LOG.warning('Not onprem (set env MODULAR_SERVICE_MODE=docker). '
                         'Exiting')
            exit(1)
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

    def _resolve_urls(self) -> set[str]:
        """
        Builds some additional urls for swagger ui
        :return:
        """
        urls = {f'http://127.0.0.1:{self._port}'}
        try:
            with urllib.request.urlopen(
                    'http://169.254.169.254/latest/meta-data/public-ipv4',
                    timeout=1) as resp:
                urls.add(f'http://{resp.read().decode()}:{self._port}')
        except urllib.error.URLError:
            _LOG.warning('Cannot resolve public-ipv4 from instance metadata')
        return urls

    def _init_swagger(self, app: 'Bottle', prefix: str, stage: str) -> None:
        """
        :param app:
        :param prefix: prefix for swagger UI
        :param stage: stage where all endpoints are, the same as API gw
        :return:
        """
        from swagger_ui import api_doc
        from services.openapi_spec_generator import OpenApiGenerator
        from lambdas.modular_api_handler.handler import HANDLER

        # from validators import registry
        url = f'http://{self._host}:{self._port}'
        urls = self._resolve_urls()
        urls.add(url)
        generator = OpenApiGenerator(
            title='Modular service API',
            description='Modular service rest API',
            url=list(urls),
            stages=stage,
            version=__version__,
            endpoints=HANDLER.iter_endpoint()
        )
        if not prefix.startswith('/'):
            prefix = f'/{prefix}'
        api_doc(
            app,
            config=generator.generate(),
            url_prefix=prefix,
            title='Modular service'
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

        stage = 'dev'  # todo get from somewhere
        app = OnPremApiBuilder().build(stage)
        if swagger:
            self._init_swagger(app, swagger_prefix, stage)

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


class CreateSystemUser(ActionHandler):
    @staticmethod
    def gen_password(digits: int = 20) -> str:
        chars = string.ascii_letters + string.digits
        while True:
            password = ''.join(
                secrets.choice(chars) for _ in range(digits))
            if (any(c.islower() for c in password)
                    and any(c.isupper() for c in password)
                    and sum(c.isdigit() for c in password) >= 3):
                break
        return password

    def __call__(self):
        from services import SP
        if SP.user_service.client.is_user_exists(SYSTEM_USER):
            _LOG.info('System user already exists')
            return
        password = os.getenv(Env.SYSTEM_USER_PASSWORD)
        from_env = bool(password)
        if not from_env:
            password = self.gen_password()
        SP.user_service.save(
            username=SYSTEM_USER,
            password=password,
            is_system=True
        )
        if not from_env:
            print(f'System ({SYSTEM_USER}) password: {password}')
        else:
            print(f'System ({SYSTEM_USER}) was created')


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

    def create_indexes_for_model(self, model: 'BaseModel'):
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
        from modular_sdk.models.application import Application
        from modular_sdk.models.customer import Customer
        from modular_sdk.models.job import Job as ModularJob
        from modular_sdk.models.region import RegionModel
        from modular_sdk.models.tenant import Tenant
        from modular_sdk.models.tenant_settings import TenantSettings
        from modular_sdk.models.parent import Parent
        models = (
            Policy, Role, User,
            Application, Customer, ModularJob, RegionModel, Tenant,
            TenantSettings, Parent
        )
        for model in models:
            self.create_indexes_for_model(model)


class GenerateOpenApi(ActionHandler):
    def __call__(self, filename: Path):
        from services.openapi_spec_generator import OpenApiGenerator
        from lambdas.modular_api_handler.handler import HANDLER
        if filename.is_dir():
            _LOG.error('Please, provide path to file')
            exit(1)
        generator = OpenApiGenerator(
            title='Modular service API',
            description='Modular service rest API',
            url=f'http://{DEFAULT_HOST}:{DEFAULT_PORT}',
            stages='dev',  # todo get from somewhere
            version=__version__,
            endpoints=HANDLER.iter_endpoint()
        )
        with open(filename, 'w') as file:
            json.dump(generator.generate(), file, separators=(',', ':'))
        _LOG.info(f'Spec was written to {filename}')


class DumpPermissions(ActionHandler):
    def __call__(self):
        json.dump(sorted(Permission.iter_all()), sys.stdout, indent=2)


class UpdateDeploymentResources(ActionHandler):
    api_name = 'modular-api'
    lambda_name = 'modular-api-handler'  # only one now

    @cached_property
    def deployment_resources(self) -> Path:
        return Path(__file__).parent / 'deployment_resources.json'

    def __call__(self):
        from lambdas.modular_api_handler.handler import HANDLER
        filename = self.deployment_resources
        if filename.is_file() and filename.exists():
            with open(filename, 'r') as file:
                data = json.load(file)
        else:
            data = {}
        api = data.setdefault(self.api_name, {
            'resource_type': 'api_gateway',
            'deploy_stage': 'dev',
            'resources': {},
            'dependencies': [],
            'models': {}
        })
        resources = api.setdefault('resources', {})
        for endpoint in HANDLER.iter_endpoint():
            method_data = resources.setdefault(endpoint.path, {
                'policy_statement_singleton': True,
                'enable_cors': True,
            }).setdefault(endpoint.method.value, {
                'enable_proxy': True,
                'integration_type': 'lambda',
                'lambda_alias': '${lambdas_alias_name}',
                'authorization_type': 'authorizer' if endpoint.auth else 'NONE',
                'lambda_name': self.lambda_name
            })
            method_data.pop('method_request_models', None)
            method_data.pop('responses', None)
            method_data.pop('method_request_parameters', None)
            if model := endpoint.request_model:
                match endpoint.method:
                    case HTTPMethod.GET:
                        params = {}
                        for name, info in model.model_fields.items():
                            params[f'method.request.querystring.{name}'] = info.is_required()
                        method_data['method_request_parameters'] = params
                    case _:
                        name = model.__name__
                        method_data['method_request_models'] = {
                            'application/json': name
                        }
                        schema = model.model_json_schema()
                        dereference_json(schema)
                        schema.pop('$defs', None)
                        api.setdefault('models', {})[name] = {
                            'content_type': 'application/json',
                            'schema': schema
                        }
            responses = []
            for st, m, _ in endpoint.responses:
                resp: dict[str, Any] = {'status_code': str(st.value)}
                if m:
                    resp['response_models'] = {'application/json': m.__name__}
                responses.append(resp)
            method_data['responses'] = responses

        with open(filename, 'w') as file:
            json.dump(data, file, indent=2)
        _LOG.info(f'{filename} has been updated')


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
        (CREATE_SYSTEM_USER_ACTION,): CreateSystemUser(),
        (CREATE_INDEXES_ACTION,): CreateIndexes(),
        (GENERATE_OPENAPI_ACTION,): GenerateOpenApi(),
        (DUMP_PERMISSIONS_ACTION,): DumpPermissions(),
        (UPDATE_DEPLOYMENT_RESOURCES_ACTION, ): UpdateDeploymentResources()
    }
    func = mapping.get(key) or (lambda **kwargs: _LOG.error('Hello'))
    for dest in ALL_NESTING:
        if hasattr(arguments, dest):
            delattr(arguments, dest)
    from dotenv import load_dotenv
    load_dotenv(verbose=True)
    try:
        func(**vars(arguments))
    except Exception as e:
        _LOG.error(f'Unexpected exception occurred: {e}')
        exit(1)  # some connection errors for entrypoint.sh


if __name__ == '__main__':
    main()
