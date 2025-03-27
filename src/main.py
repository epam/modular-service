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
from typing import Any, Callable, Literal

import pymongo
from modular_sdk.commons.constants import Cloud, Env as ModularSDKEnv, DBBackend
from modular_sdk.models.pynamongo.indexes_creator import IndexesCreator

from commons import dereference_json
from commons.__version__ import __version__
from commons.constants import (
    PRIVATE_KEY_SECRET_NAME,
    Env,
    HTTPMethod,
    Permission,
)
from commons.log_helper import setup_logging
from commons.regions import AWS_REGIONS


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


logging.config.dictConfig(
    {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'console_formatter': {'format': '%(levelname)s - %(message)s'}
        },
        'handlers': {
            'console_handler': {
                'class': 'logging.StreamHandler',
                'formatter': 'console_formatter',
            }
        },
        'loggers': {
            '__main__': {'level': 'DEBUG', 'handlers': ['console_handler']},
            'modular_sdk': {'level': 'INFO', 'handlers': ['console_handler']},
        },
    }
)


_LOG = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Modular service main CLI endpoint'
    )
    # -- top level sub-parser
    sub_parsers = parser.add_subparsers(
        dest=ACTION_DEST, required=True, help='Available actions'
    )

    # generate-openapi
    parser_open_api = sub_parsers.add_parser(
        GENERATE_OPENAPI_ACTION, help='Generates Open API spec for API'
    )
    parser_open_api.add_argument(
        '-f',
        '--filename',
        type=Path,
        required=True,
        help='Filename where to write spec',
    )
    _ = sub_parsers.add_parser(
        ACTIVATE_REGIONS_ACTION, help='Activates global regions'
    )

    # run
    parser_run = sub_parsers.add_parser(RUN_ACTION, help='Run on-prem server')
    parser_run.add_argument(
        '-g',
        '--gunicorn',
        action='store_true',
        default=False,
        help='Specify the flag is you want to run the server via Gunicorn',
    )
    parser_run.add_argument(
        '-nw',
        '--workers',
        type=int,
        required=False,
        help='Number of gunicorn workers. Must be specified only '
        'if --gunicorn flag is set',
    )
    parser_run.add_argument(
        '--host',
        default=DEFAULT_HOST,
        type=str,
        help='IP address where to run the server',
    )
    parser_run.add_argument(
        '--port',
        default=DEFAULT_PORT,
        type=int,
        help='IP Port to run the server on',
    )

    # init-vault
    _ = sub_parsers.add_parser(INIT_VAULT_ACTION, help='Init token in vault')

    # init
    _ = sub_parsers.add_parser(
        CREATE_SYSTEM_USER_ACTION,
        help='Creates a system user that can perform actions on behalf of '
        'other users',
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
        help='Updates api definition insider deployment_resources.json',
    )
    return parser


class ActionHandler(ABC):
    @abstractmethod
    def __call__(self, **kwargs): ...


class InitVault(ABC):
    def __call__(self):
        from services import SP

        if not SP.environment_service.is_docker():
            _LOG.warning(
                'Not onprem (set env MODULAR_SERVICE_MODE=docker). ' 'Exiting'
            )
            exit(1)
        ssm = SP.ssm
        if not ssm.is_secrets_engine_enabled():
            _LOG.info('Enabling secrets engine')
            ssm.enable_secrets_engine()
        else:
            _LOG.info('Vault engine has been already enabled')
        if ssm.get_parameter(PRIVATE_KEY_SECRET_NAME):
            _LOG.info('Token inside Vault already exists. Skipping...')
            return

        ssm.put_parameter(
            name=PRIVATE_KEY_SECRET_NAME, value=self.generate_private_key()
        )
        print('Token was set to Vault')

    @staticmethod
    def generate_private_key(
        kty: Literal['EC', 'RSA'] = 'EC', crv='P-521', size: int = 4096
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
        return base64.b64encode(
            key.export_to_pem(private_key=True, password=None)
        ).decode()  # type: ignore


class Run(ActionHandler):
    def __call__(
        self,
        host: str = DEFAULT_HOST,
        port: int = DEFAULT_PORT,
        gunicorn: bool = False,
        workers: int | None = None,
    ):
        from onprem.app import OnPremApiBuilder

        self._host = host
        self._port = port

        setup_logging()

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
                'timeout': 60,
                'max_requests': 512,
                'max_requests_jitter': 64,
            }
            CustodianGunicornApplication(app, options).run()
        else:
            app.run(host=host, port=port)


class CreateSystemUser(ActionHandler):
    @staticmethod
    def gen_password(digits: int = 20) -> str:
        chars = string.ascii_letters + string.digits
        while True:
            password = ''.join(secrets.choice(chars) for _ in range(digits))
            if (
                any(c.islower() for c in password)
                and any(c.isupper() for c in password)
                and sum(c.isdigit() for c in password) >= 3
            ):
                break
        return password

    def __call__(self):
        from services import SP

        cl = SP.users_client
        if cl.does_user_exist(SYSTEM_USER):
            _LOG.info('System user already exists')
            return
        password = Env.SYSTEM_USER_PASSWORD.get()
        from_env = bool(password)
        if not from_env:
            password = self.gen_password()
        cl.signup_user(username=SYSTEM_USER, password=password, is_system=True)
        if not from_env:
            print(f'System ({SYSTEM_USER}) password: {password}')
        else:
            print(f'System ({SYSTEM_USER}) was created')


class CreateIndexes(ActionHandler):
    @staticmethod
    def models() -> tuple:
        from models.policy import Policy
        from models.role import Role
        from models.user import User

        return Policy, Role, User

    @staticmethod
    def modular_sdk_models() -> tuple:
        from modular_sdk.models.application import Application
        from modular_sdk.models.customer import Customer
        from modular_sdk.models.customer_settings import CustomerSettings
        from modular_sdk.models.execution_trace import ExecutionTrace
        from modular_sdk.models.heartbeat import Heartbeat
        from modular_sdk.models.job import Job as ModularJob
        from modular_sdk.models.operation_mode import OperationMode
        from modular_sdk.models.parent import Parent
        from modular_sdk.models.region import RegionModel

        # from modular_sdk.models.setting import Setting
        from modular_sdk.models.tenant import Tenant
        from modular_sdk.models.tenant_settings import TenantSettings

        return (
            Application,
            Customer,
            CustomerSettings,
            ExecutionTrace,
            Heartbeat,
            ModularJob,
            OperationMode,
            Parent,
            RegionModel,
            Tenant,
            TenantSettings,
        )

    def __call__(self):
        _LOG.debug('Going to sync indexes with code')
        from models import PynamoDBToPymongoAdapterSingleton
        from modular_sdk.models.pynamongo.models import ModularBaseModel

        if Env.is_docker():
            creator = IndexesCreator(db=PynamoDBToPymongoAdapterSingleton.get_instance().mongo_database)
            for model in self.models():
                _LOG.info(f'Going to sync indexes for {model.Meta.table_name}')
                creator.sync(model)
        if ModularSDKEnv.DB_BACKEND.get() == DBBackend.MONGO:
            creator = IndexesCreator(db=ModularBaseModel.mongo_adapter().mongo_database)
            for model in self.modular_sdk_models():
                _LOG.info(f'Going to ensure indexes for {model.Meta.table_name}')
                creator.ensure(
                    model,
                    primary_index_unique=False,
                    hash_key_order=pymongo.ASCENDING,
                    range_key_order=pymongo.ASCENDING
                )


class GenerateOpenApi(ActionHandler):
    def __call__(self, filename: Path):
        from lambdas.modular_api_handler.handler import HANDLER
        from services.openapi_spec_generator import OpenApiGenerator

        if filename.is_dir():
            _LOG.error('Please, provide path to file')
            exit(1)
        generator = OpenApiGenerator(
            title='Modular service API',
            description='Modular service rest API',
            url=f'http://{DEFAULT_HOST}:{DEFAULT_PORT}',
            stages='dev',  # todo get from somewhere
            version=__version__,
            endpoints=HANDLER.iter_endpoint(),
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
        api = data.setdefault(
            self.api_name,
            {
                'resource_type': 'api_gateway',
                'deploy_stage': 'dev',
                'resources': {},
                'dependencies': [],
                'models': {},
            },
        )
        resources = api.setdefault('resources', {})
        for endpoint in HANDLER.iter_endpoint():
            method_data = resources.setdefault(
                endpoint.path,
                {'policy_statement_singleton': True, 'enable_cors': True},
            ).setdefault(
                endpoint.method.value,
                {
                    'enable_proxy': True,
                    'integration_type': 'lambda',
                    'lambda_alias': '${lambdas_alias_name}',
                    'authorization_type': 'authorizer'
                    if endpoint.auth
                    else 'NONE',
                    'lambda_name': self.lambda_name,
                },
            )
            method_data.pop('method_request_models', None)
            method_data.pop('responses', None)
            method_data.pop('method_request_parameters', None)
            if model := endpoint.request_model:
                match endpoint.method:
                    case HTTPMethod.GET:
                        params = {}
                        for name, info in model.model_fields.items():
                            params[f'method.request.querystring.{name}'] = (
                                info.is_required()
                            )
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
                            'schema': schema,
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
        from modular_sdk.models.region import RegionModel

        from services import SP

        if ModularSDKEnv.DB_BACKEND.get() == DBBackend.DYNAMO:
            _LOG.warning(
                'Regions won`t be activated because modular sdk '
                'is saas mode'
            )
            # TODO: this is probably a kludge
            return
        if '+srv' in ModularSDKEnv.MONGO_URI.get('mongo://') or ModularSDKEnv.MONGO_SRV.get():
            _LOG.warning(
                'Regions won`t be activated because modular sdk is using '
                'external Mongo cluster'
            )
            # TODO: this is definitely a kludge
            return
        rs = SP.region_service
        for region in AWS_REGIONS:
            if rs.get_region(region_name=region):
                continue
            _LOG.debug(f'Activation {region}')
            # rs.create is too expensive
            rs.save(
                RegionModel(
                    region_id=str(uuid.uuid4()),
                    maestro_name=region,
                    native_name=region,
                    cloud=Cloud.AWS.value,
                    is_active=True,
                )
            )
        _LOG.info('Regions were created')


def main(args: list[str] | None = None):
    parser = build_parser()
    arguments = parser.parse_args(args)
    key = tuple(
        getattr(arguments, dest)
        for dest in ALL_NESTING
        if hasattr(arguments, dest)
    )
    mapping: dict[tuple[str, ...], Callable] = {
        (RUN_ACTION,): Run(),
        (INIT_VAULT_ACTION,): InitVault(),
        (CREATE_SYSTEM_USER_ACTION,): CreateSystemUser(),
        (CREATE_INDEXES_ACTION,): CreateIndexes(),
        (GENERATE_OPENAPI_ACTION,): GenerateOpenApi(),
        (DUMP_PERMISSIONS_ACTION,): DumpPermissions(),
        (UPDATE_DEPLOYMENT_RESOURCES_ACTION,): UpdateDeploymentResources(),
        (ACTIVATE_REGIONS_ACTION,): ActivateRegions(),
    }
    func = mapping.get(key) or (lambda **kwargs: _LOG.error('Hello'))
    for dest in ALL_NESTING:
        if hasattr(arguments, dest):
            delattr(arguments, dest)
    try:
        func(**vars(arguments))
    except Exception as e:
        _LOG.error(f'Unexpected exception occurred: {e}')
        exit(1)  # some connection errors for entrypoint.sh


if __name__ == '__main__':
    main()
