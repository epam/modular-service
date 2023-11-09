from datetime import datetime
from uuid import uuid4
from typing import Union, Iterable, Optional, Any
from commons.constants import (
    PARAM_MESSAGE, PARAM_ITEMS, PASSWORD_ATTR, ID_TOKEN_ATTR, REFRESH_TOKEN_ATTR
)
import json
from functools import reduce

from commons.exception import ApplicationException

RESPONSE_BAD_REQUEST_CODE = 400
RESPONSE_UNAUTHORIZED = 401
RESPONSE_FORBIDDEN_CODE = 403
RESPONSE_RESOURCE_NOT_FOUND_CODE = 404
RESPONSE_CONFLICT_CODE = 409
RESPONSE_OK_CODE = 200
RESPONSE_INTERNAL_SERVER_ERROR = 500
RESPONSE_NOT_IMPLEMENTED = 501
RESPONSE_SERVICE_UNAVAILABLE_CODE = 503

MISSING_PARAMETER_ERROR_PATTERN = '{0} must be specified'


def build_response(content: Union[str, dict, list, Iterable],
                   code: int = RESPONSE_OK_CODE, meta: Optional[dict] = None):
    meta = meta or {}
    _body = {
        **meta
    }
    if isinstance(content, str):
        _body.update({PARAM_MESSAGE: content})
    elif isinstance(content, dict) and content:
        _body.update({PARAM_ITEMS: [content, ]})
    elif isinstance(content, list):
        _body.update({PARAM_ITEMS: content})
    elif isinstance(content, Iterable):
        _body.update({PARAM_ITEMS: list(content)})
    else:
        _body.update({PARAM_ITEMS: []})

    if 200 <= code <= 206:
        return {
            'statusCode': code,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': '*'
            },
            'isBase64Encoded': False,
            'multiValueHeaders': {},
            'body': json.dumps(_body)
        }
    raise ApplicationException(
        code=code,
        content=content
    )


def raise_error_response(code, content):
    raise ApplicationException(code=code, content=content)


def assert_param_is_not_none(parameter, parameter_name,
                             raise_if_none=True):
    if not parameter and raise_if_none:
        return build_response(
            code=RESPONSE_BAD_REQUEST_CODE,
            content=MISSING_PARAMETER_ERROR_PATTERN.format(parameter_name))


def get_iso_timestamp():
    return datetime.now().isoformat()


def get_missing_parameters(event, required_params_list):
    missing_params_list = []
    for param in required_params_list:
        if event.get(param) is None:
            missing_params_list.append(param)
    return missing_params_list


def validate_params(event, required_params_list):
    """
    Checks if all required parameters present in lambda payload.
    :param event: the lambda payload
    :param required_params_list: list of the lambda required parameters
    :return: bad request response if some parameter[s] is/are missing,
        otherwise - none
    """
    missing_params_list = get_missing_parameters(event, required_params_list)

    if missing_params_list:
        raise_error_response(RESPONSE_BAD_REQUEST_CODE,
                             'Bad Request. The following parameters '
                             'are missing: {0}'.format(missing_params_list))


class LambdaContext:
    aws_request_id: str = 'mock'
    function_name: str

    def __init__(self):
        self.aws_request_id = str(uuid4())


def generate_id():
    return str(uuid4())


def deep_get(dct: dict, path: Union[list, tuple]) -> Any:
    """
    >>> d = {'a': {'b': 1}}
    >>> deep_get(d, ('a', 'b'))
    1
    >>> deep_get(d, (1, 'two'))
    None
    """
    return reduce(
        lambda d, key: d.get(key, None) if isinstance(d, dict) else None,
        path, dct)


def deep_set(dct: dict, path: tuple, item: Any):
    if len(path) == 1:
        dct[path[0]] = item
    else:
        subdict = dct.get(path[0], None)
        if not isinstance(subdict, dict):
            dct[path[0]] = {}
        deep_set(dct[path[0]], path[1:], item)


class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


def reformat_request_path(request_path: str) -> str:
    """
    /hello -> /hello/
    hello/ -> /hello/
    hello -> /hello/
    """
    if not request_path.startswith('/'):
        request_path = '/' + request_path
    if not request_path.endswith('/'):
        request_path += '/'
    return request_path


def secured_params() -> tuple:
    return (
        'refresh_token', 'id_token', 'password', 'authorization', 'secret',
        'AWS_SECRET_ACCESS_KEY', 'AWS_SESSION_TOKEN', 'git_access_secret',
        'api_key', 'AZURE_CLIENT_ID', 'AZURE_CLIENT_SECRET',
        'GOOGLE_APPLICATION_CREDENTIALS', 'private_key', 'private_key_id',
        'Authorization', 'Authentication', 'client_email'
    )


def secure_event(event: dict, secured_keys=secured_params()):
    result_event = {}
    if not isinstance(event, dict):
        return event
    for key, value in event.items():
        if key in secured_keys:
            result_event[key] = '*****'
        elif isinstance(value, dict):
            result_event[key] = secure_event(value, secured_keys)
        elif isinstance(value, list):
            result_event[key] = []
            for item in value:
                result_event[key].append(secure_event(item, secured_keys))
        elif isinstance(value, str):
            try:
                result_event[key] = json.dumps(
                    secure_event(json.loads(value), secured_keys)
                )
            except ValueError:
                result_event[key] = value
        else:
            result_event[key] = value

    return result_event
