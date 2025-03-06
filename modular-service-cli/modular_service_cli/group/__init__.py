import json
import os
import sys
import urllib.error
from abc import ABC, abstractmethod
from datetime import timezone
from functools import reduce, wraps
from http import HTTPStatus
from itertools import islice
from pathlib import Path
from typing import Any, Callable, Literal, TypedDict, cast

import click
from dateutil.parser import isoparse
from tabulate import tabulate

from modular_service_cli.service.api_client import (
    ApiResponse,
    ModularServiceApiClient
)
from modular_service_cli.service.config import (
    AbstractConfig,
    ModularCliSdkConfig,
    OnDiskModularServiceConfig,
)
from modular_service_cli.service.constants import (
    DATA_ATTR,
    ERRORS_ATTR,
    ITEMS_ATTR,
    MESSAGE_ATTR,
    NEXT_TOKEN_ATTR,
    NO_CONTENT_RESPONSE_MESSAGE,
    NO_ITEMS_TO_DISPLAY_RESPONSE_MESSAGE,
)
from modular_service_cli.service.logger import get_logger, write_verbose_logs

CredentialsProvider = None
try:
    from modular_cli_sdk.services.credentials_manager import (
        CredentialsProvider
    )
except ImportError:
    pass

_LOG = get_logger(__name__)

REVERT_TO_JSON_MESSAGE = 'The command`s response is pretty huge and the ' \
                         'result table structure can be broken.\n' \
                         'Do you want to show the response in the JSON format?'

COLUMN_OVERFLOW = 'Column has overflown, within the table representation.'


class ColumnOverflow(Exception):
    __slots__ = 'table', 'message'

    def __init__(self, table: str, message: str = COLUMN_OVERFLOW):
        self.table = table
        self.message = message


class ContextObj:
    __slots__ = 'config', 'api_client'

    def __init__(self, config: AbstractConfig,
                 api_client: ModularServiceApiClient):
        self.config: AbstractConfig = config
        self.api_client: ModularServiceApiClient = api_client


class cli_response:  # noqa
    __slots__ = ('_attributes_order', '_check_api_link', '_check_access_token')

    def __init__(self, attributes_order: tuple[str, ...] = (),
                 check_api_link: bool = True,
                 check_access_token: bool = True):
        self._attributes_order = attributes_order
        self._check_api_link = check_api_link
        self._check_access_token = check_access_token

    @staticmethod
    def to_exit_code(code: HTTPStatus | None) -> int:
        if not code:
            return 1
        if 200 <= code < 400:
            return 0
        return 1

    @staticmethod
    def update_context(ctx: click.Context):
        """
        Updates the given (current) click context's obj with api
        client instance and config instance
        :param ctx:
        :return:
        """
        if CredentialsProvider:
            _LOG.debug('Cli sdk is installed. Using its credentials provider')
            config = ModularCliSdkConfig(
                credentials_manager=CredentialsProvider(
                    module_name='modular-service-cli', context=ctx
                ).credentials_manager
            )
        else:
            _LOG.warning(
                'Could not import modular_cli_sdk. Using standard '
                'config instead of the one provided by cli skd'
            )
            m3_username = None
            if isinstance(ctx.obj, dict):
                m3_username = ctx.obj.get('modular_admin_username')
            if isinstance(m3_username, str):  # basically if not None
                # modular
                config = OnDiskModularServiceConfig(prefix=m3_username)
            else:
                # standard
                config = OnDiskModularServiceConfig()

        ctx.obj = ContextObj(
            config=config,
            api_client=ModularServiceApiClient(config)
        )

    def _check_context(self, ctx: click.Context):
        """
        May raise click.UsageError
        :param ctx:
        :return:
        """
        obj: ContextObj = cast(ContextObj, ctx.obj)
        config = obj.config
        if self._check_api_link and not config.api_link:
            raise click.UsageError(
                'Modular service API link is not configured. '
                'Run \'modular-service configure\' and try again.'
            )
        if self._check_access_token and not config.access_token:
            raise click.UsageError(
                'Modular access token not found. '
                'Run \'modular-service login\' to receive the token'
            )

    def __call__(self, func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            modular_mode = False
            if Path(__file__).parents[
                3].name == 'modules':  # TODO check some other way
                modular_mode = True

            json_view = kwargs.pop('json')
            verbose = kwargs.pop('verbose')
            if verbose:
                write_verbose_logs()

            ctx = cast(click.Context, click.get_current_context())
            self.update_context(ctx)
            try:
                self._check_context(ctx)
                resp: ApiResponse = click.pass_obj(func)(*args, **kwargs)
            except click.ClickException as e:
                _LOG.info('Click exception has occurred')
                resp = ApiResponse.build(e.format_message())
            except Exception as e:
                _LOG.exception('Unexpected error has occurred')
                resp = ApiResponse.build(str(e))

            if modular_mode:
                _LOG.info('The cli is installed as a module. '
                          'Returning m3 modular cli response')
                formatted = ModularResponseProcessor().format(resp)
                return json.dumps(formatted, separators=(',', ':'))

            if not json_view:  # table view

                _LOG.info('Returning table view')
                prepared = TableResponseProcessor().format(resp)
                trace_id = resp.trace_id
                next_token = (resp.data or {}).get(NEXT_TOKEN_ATTR)

                try:
                    printer = TablePrinter(
                        attributes_order=self._attributes_order
                    )
                    table = printer.print(prepared)
                except ColumnOverflow as ce:

                    _LOG.info(f'Awaiting user to respond to - {ce!r}.')
                    to_revert = click.prompt(
                        REVERT_TO_JSON_MESSAGE,
                        type=click.Choice(('y', 'n'))
                    )
                    if to_revert == 'n':
                        table = ce.table
                    else:
                        table, json_view = None, True

                if table:
                    if verbose:
                        click.echo(f'Trace id: \'{trace_id}\'')
                    if next_token:
                        click.echo(f'Next token: \'{next_token}\'')
                    click.echo(table)
                    _LOG.info(f'Finished request: \'{trace_id}\'')

            if json_view:
                _LOG.info('Returning json view')
                data = JsonResponseProcessor().format(resp)
                click.echo(json.dumps(data, indent=2))
            sys.exit(self.to_exit_code(resp.code))

        return wrapper


class ResponseProcessor(ABC):
    @abstractmethod
    def format(self, resp: ApiResponse) -> Any:
        """
        Returns a dict that can be printed or used for printing
        :param resp:
        :return:
        """


class JsonResponseProcessor(ResponseProcessor):
    """
    Processes the json before it can be printed
    """

    def format(self, resp: ApiResponse) -> dict:
        if resp.code == HTTPStatus.NO_CONTENT:
            return {MESSAGE_ATTR: NO_CONTENT_RESPONSE_MESSAGE}
        elif isinstance(resp.exc, json.JSONDecodeError):
            return {MESSAGE_ATTR: f'Invalid JSON received: {resp.exc.msg}'}
        elif isinstance(resp.exc, urllib.error.URLError):
            return {MESSAGE_ATTR: f'Cannot send a request: {resp.exc.reason}'}
        return resp.data or {}


class TableResponseProcessor(JsonResponseProcessor):
    """
    Processes the json before it can be converted to table and printed
    """

    def format(self, resp: ApiResponse) -> list[dict]:
        dct = super().format(resp)
        if data := dct.get(DATA_ATTR):
            return [data]
        if errors := dct.get(ERRORS_ATTR):
            return errors
        if items := dct.get(ITEMS_ATTR):
            return items
        if ITEMS_ATTR in dct and not dct.get(ITEMS_ATTR):  # empty
            return [{MESSAGE_ATTR: NO_ITEMS_TO_DISPLAY_RESPONSE_MESSAGE}]
        return [dct]


class ModularResponseProcessor(JsonResponseProcessor):
    modular_table_title = 'Custodian as a service'

    class ModularResponse(TypedDict, total=False):
        code: HTTPStatus
        status: Literal['SUCCESS']
        table_title: str
        items: list[str] | None
        message: str | None

    def format(self, resp: ApiResponse) -> ModularResponse:
        base = {
            'code': resp.code,
            'status': 'SUCCESS',
            'table_title': self.modular_table_title,
        }
        dct = super().format(resp)
        if data := dct.get(DATA_ATTR):
            base[ITEMS_ATTR] = [data]
        elif errors := dct.get(ERRORS_ATTR):
            base[ITEMS_ATTR] = errors
        elif dct.get(ITEMS_ATTR):
            base.update(dct)
        elif ITEMS_ATTR in dct:  # empty
            base[MESSAGE_ATTR] = NO_ITEMS_TO_DISPLAY_RESPONSE_MESSAGE
        elif message := dct.get(MESSAGE_ATTR):
            base[MESSAGE_ATTR] = message
        else:
            base[ITEMS_ATTR] = [dct]
        return base


class TablePrinter:
    __slots__ = '_format', '_datetime_format', '_items_per_column', '_order'

    default_datetime_format: str = '%A, %B %d, %Y %I:%M:%S %p'

    def __init__(self, format: str = 'pretty',
                 datetime_format: str = default_datetime_format,
                 items_per_column: int | None = None,
                 attributes_order: tuple[str, ...] = ()):
        self._format = format
        self._datetime_format = datetime_format
        self._items_per_column = items_per_column
        if attributes_order:
            self._order = {x: i for i, x in enumerate(attributes_order)}
        else:
            self._order = None

    def prepare_value(self, value: str | list | dict | None) -> str:
        """
        Makes the given value human-readable. Should be applied only for
        table view since it can reduce the total amount of useful information
        within the value in favor of better view.
        :param value:
         items per column.
        :return:
        """
        if not value and not isinstance(value, (int, bool)):
            return '—'

        limit = self._items_per_column
        to_limit = limit is not None
        f = self.prepare_value

        # todo, maybe use just list comprehensions instead of iterators
        match value:
            case list():
                i_recurse = map(f, value)
                result = ', '.join(islice(i_recurse, limit))
                if to_limit and len(value) > limit:
                    result += f'... ({len(value)})'  # or len(value) - limit
                return result
            case dict():
                i_prepare = (
                    f'{f(value=k)}: {f(value=v)}'
                    for k, v in islice(value.items(), limit)
                )
                result = reduce(lambda a, b: f'{a}; {b}', i_prepare)
                if to_limit and len(value) > limit:
                    result += f'... ({len(value)})'
                return result
            case str():
                try:
                    obj = isoparse(value)
                    # we assume that everything from the server is UTC even
                    # if it is a naive object
                    obj.replace(tzinfo=timezone.utc)
                    return obj.astimezone().strftime(self._datetime_format)
                except ValueError:
                    return value
            case _:  # bool, int
                return str(value)

    def print(self, data: list[dict]) -> str:
        """
        Raises on overflow
        :param data:
        :return:
        """
        if order := self._order:
            def key(tpl):
                return order.get(tpl[0], 4096)  # just some big int

            formatted = self._items_table([
                dict(sorted(dct.items(), key=key)) for dct in data
            ])
        else:
            formatted = self._items_table(data)

        overflow = formatted.index('\n') > os.get_terminal_size().columns
        if overflow:
            raise ColumnOverflow(table=formatted)
        return formatted

    def _items_table(self, items: list[dict]) -> str:
        prepare_value = self.prepare_value

        rows, title_to_key = [], {}

        for entry in items:
            for key in entry:
                title = key.replace('_', ' ').capitalize()  # title
                if title not in title_to_key:
                    title_to_key[title] = key

        for entry in items:
            rows.append([
                prepare_value(value=entry.get(key))
                for key in title_to_key.values()
            ])

        return tabulate(
            rows, headers=list(title_to_key),
            tablefmt=self._format
        )


class ViewCommand(click.core.Command):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.params.append(
            click.core.Option(('--json',), is_flag=True,
                              help='Response as a JSON'))
        self.params.append(
            click.core.Option(('--verbose',), is_flag=True,
                              help='Save detailed information to '
                                   'the log file'))
        self.params.append(
            click.core.Option(('--customer_id', '-cid'), type=str,
                              required=False, hidden=True)
        )


def build_limit_option(**kwargs) -> Callable:
    params = dict(
        type=click.IntRange(min=1, max=50),
        default=10, show_default=True,
        help='Number of records to show'
    )
    params.update(kwargs)
    return click.option('--limit', '-l', **params)


def build_next_token_option(**kwargs) -> Callable:
    params = dict(
        type=str, required=False,
        help='Token to start record-pagination from'
    )
    params.update(kwargs)
    return click.option('--next_token', '-nt', **params)
