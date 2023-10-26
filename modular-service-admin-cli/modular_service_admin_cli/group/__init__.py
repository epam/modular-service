import json
from collections import OrderedDict
from functools import wraps
from pathlib import Path

import click
from requests.models import Response
import requests.exceptions
from tabulate import tabulate

from modular_service_admin_cli.service.logger import get_logger, get_user_logger

MODULAR_ADMIN = 'modules'
SUCCESS_STATUS = 'SUCCESS'
FAILED_STATUS = 'FAILED'
STATUS_ATTR = 'status'
CODE_ATTR = 'code'
TABLE_TITLE_ATTR = 'table_title'

SYSTEM_LOG = get_logger('modular_admin_cli.group')
USER_LOG = get_user_logger('user')


def cli_response(attributes_order=None, check_api_adapter=True):
    def internal(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            modular_mode = False
            if Path(__file__).parents[3].name == MODULAR_ADMIN:
                modular_mode = True

            json_view = kwargs['json']
            del kwargs['json']

            if check_api_adapter:
                from service.initializer import ADAPTER_SDK
                response = func(*args, **kwargs) if ADAPTER_SDK else {
                    'message': f'API link is not '
                               f'configured. Run \'configure\' command and '
                               f'try again.'
                }
            else:
                response = func(*args, **kwargs)
            response = parse_response(response, modular_mode)
            response = order_response(response, attributes_order)
            if not response.get('items') and not response.get('message'):
                response = {'message': 'No items to display'}
            if json_view or modular_mode:
                output = form_json_view(response=response)
            else:
                output = form_table_view(response=response)
            if modular_mode:
                return output
            click.echo(output)

        return wrapper

    return internal


def parse_response(response: Response, modular_mode=False) -> dict:
    """Expands response for modularadmin"""
    code = 400
    if not isinstance(response, dict):
        code = response.status_code
        try:
            response = response.json()
        except requests.exceptions.JSONDecodeError as e:
            SYSTEM_LOG.error(f'Error occurred while loading '
                             f'response json: {e}')
            code = 500
            response = {
                'message': 'Malformed response obtained. Please contact '
                           'support team for assistance.'
            }

    if modular_mode:
        response[CODE_ATTR] = code
        response[STATUS_ATTR] = SUCCESS_STATUS
        response[TABLE_TITLE_ATTR] = 'Modular'
    return response


class ViewCommand(click.core.Command):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.params.append(
            click.core.Option(('--json',), is_flag=True,
                              help='Response as a JSON'))


def form_table_view(response):
    message = response.get('message')
    if message:
        # error
        return tabulate([[message]], headers=['Message'], tablefmt='pretty')

    items = response.get('items')
    if all(isinstance(item, str) for item in items):
        items = [{'value': item} for item in items]
    keys = []
    for entry in items:
        entry_keys = list(entry.keys())
        [keys.append(key) for key in entry_keys if key not in keys]
    values = {__response_view(key): list() for key in keys}
    for entry in items:
        for key in keys:
            values[__response_view(key)].append(entry.get(key))
    return tabulate(values, headers="keys", tablefmt='pretty')


def form_json_view(response):
    return json.dumps(response, indent=4)


def cast_to_list(input):
    if type(input) == tuple:
        list_item = list(input)
    elif type(input) == str:
        list_item = [input]
    else:
        list_item = input
    return list_item


def order_response(response, attributes_order):
    if not response.get('items') or not attributes_order:
        return response
    ordered_items = []
    for item in response.get('items', []):
        # sort item attributes by provided priority list
        # the lesser attribute index, the more priority
        # (values will be printed closer to the left side of table)
        key = lambda x: attributes_order.index(x[0]) \
            if x[0] in attributes_order else 100 + ord(
            x[0][0].lower())  # 100 - just some big int
        ordered_items.append(OrderedDict(sorted(item.items(), key=key)))
    response['items'] = ordered_items
    return response


def __response_view(key):
    key = key.replace('_', ' ')
    key = key.capitalize()
    return key
