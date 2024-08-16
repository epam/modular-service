#!/usr/local/bin/python
import argparse
import base64
import json
import logging.config
import multiprocessing
import os
import secrets
import string
import sys
import uuid
from abc import ABC, abstractmethod
from functools import cached_property
from pathlib import Path
from typing import Any, Callable, Literal, TYPE_CHECKING, Generator, cast

import pymongo
from pymongo.operations import IndexModel
from modular_sdk.commons.constants import Cloud

from commons import dereference_json
from commons.__version__ import __version__
from commons.constants import Env, HTTPMethod, PRIVATE_KEY_SECRET_NAME, \
    Permission
from commons.regions import AWS_REGIONS

# NOTE, all imports are inside corresponding methods in order to make cli faster
if TYPE_CHECKING:
    from models import BaseModel

DEFAULT_HOST = '0.0.0.0'
DEFAULT_PORT = 8040
DEFAULT_NUMBER_OF_WORKERS = (multiprocessing.cpu_count() * 2) + 1
DEFAULT_ON_PREM_API_LINK = f'http://{DEFAULT_HOST}:{str(DEFAULT_PORT)}/caas'
DEFAULT_API_GATEWAY_NAME = 'custodian-as-a-service-api'

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
ACTIVATE_REGIONS_ACTION = 'activate-regions'

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
    _ = sub_parsers.add_parser(
        ACTIVATE_REGIONS_ACTION,
        help='Activates global regions'
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

    def __call__(self, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT,
                 gunicorn: bool = False, workers: int | None = None):
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
    main_index_name = 'main'
    hash_key_order = pymongo.ASCENDING
    range_key_order = pymongo.DESCENDING

    @staticmethod
    def models() -> tuple:
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
        return (
            Policy, Role, User,
            Application, Customer, ModularJob, RegionModel, Tenant,
            TenantSettings, Parent
        )

    @staticmethod
    def _get_hash_range(model: 'BaseModel') -> tuple[str, str | None]:
        h, r = None, None
        for attr in model.get_attributes().values():
            if attr.is_hash_key:
                h = attr.attr_name
            if attr.is_range_key:
                r = attr.attr_name
        return cast(str, h), r

    @staticmethod
    def _iter_indexes(model: 'BaseModel'
                      ) -> Generator[tuple[str, str, str | None], None, None]:
        """
        Yields tuples: (index name, hash_key, range_key) indexes of the given
        model. Currently, only global secondary indexes are used so this
        implementation wasn't tested with local ones. Uses private PynamoDB
        API because cannot find public methods that can help
        """
        for index in model._indexes.values():
            name = index.Meta.index_name
            h, r = None, None
            for attr in index.Meta.attributes.values():
                if attr.is_hash_key:
                    h = attr.attr_name
                if attr.is_range_key:
                    r = attr.attr_name
            yield name, cast(str, h), r

    def _iter_all_indexes(self, model: 'BaseModel'
                          ) -> Generator[tuple[str, str, str | None], None, None]:
        yield self.main_index_name, *self._get_hash_range(model)
        yield from self._iter_indexes(model)

    @staticmethod
    def _exceptional_indexes() -> tuple[str, ...]:
        return '_id_',

    def ensure_indexes(self, model: 'BaseModel'):
        table_name = model.Meta.table_name
        _LOG.info(f'Going to check indexes for {table_name}')
        collection = model.mongodb_handler().mongodb.collection(table_name)
        existing = collection.index_information()
        for name in self._exceptional_indexes():
            existing.pop(name, None)
        needed = {}
        for name, h, r in self._iter_all_indexes(model):
            needed[name] = [(h, self.hash_key_order)]
            if r:
                needed[name].append((r, self.range_key_order))
        to_create = []
        to_delete = set()
        for name, data in existing.items():
            if name not in needed:
                to_delete.add(name)
                continue
            # name in needed so maybe the index is valid, and we must keep it
            # or the index has changed, and we need to re-create it
            if data.get('key', []) != needed[name]:  # not valid
                to_delete.add(name)
                to_create.append(IndexModel(
                    keys=needed[name],
                    name=name
                ))
            needed.pop(name)
        for name, keys in needed.items():  # all that left must be created
            to_create.append(IndexModel(
                keys=keys,
                name=name
            ))
        for name in to_delete:
            _LOG.info(f'Going to remove index: {name}')
            collection.drop_index(name)
        if to_create:
            _message = ','.join(
                json.dumps(i.document,
                           separators=(',', ':')) for i in to_create
            )
            _LOG.info(f'Going to create indexes: {_message}')
            collection.create_indexes(to_create)

    def __call__(self):
        _LOG.debug('Going to sync indexes with code')
        for model in self.models():
            self.ensure_indexes(model)


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


class ActivateRegions(ActionHandler):
    def __call__(self):
        from services import SP
        from modular_sdk.models.region import RegionModel
        rs = SP.region_service
        for region in AWS_REGIONS:
            if rs.get_region(region_name=region):
                continue
            _LOG.debug(f'Activation {region}')
            # rs.create is too expensive
            rs.save(RegionModel(
                region_id=str(uuid.uuid4()),
                maestro_name=region,
                native_name=region,
                cloud=Cloud.AWS.value,
                is_active=True
            ))
        _LOG.info('Regions were created')


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
        (UPDATE_DEPLOYMENT_RESOURCES_ACTION, ): UpdateDeploymentResources(),
        (ACTIVATE_REGIONS_ACTION, ): ActivateRegions()
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
