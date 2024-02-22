import json
import math
import uuid
from datetime import datetime
from functools import reduce
from types import NoneType
from typing import Any


def get_iso_timestamp():
    return datetime.now().isoformat()


def validate_params(event, required_params_list):
    """
    Checks if all required parameters present in lambda payload.
    :param event: the lambda payload
    :param required_params_list: list of the lambda required parameters
    :return: bad request response if some parameter[s] is/are missing,
        otherwise - none
    """
    # TODO remove


class RequestContext:
    __slots__ = ('aws_request_id', 'function_name')

    def __init__(self, request_id: str | None = None):
        self.aws_request_id: str = request_id or str(uuid.uuid4())
        self.function_name: str = 'modular-api-handler'  # currently only one

    @staticmethod
    def get_remaining_time_in_millis():
        return math.inf


def deep_get(dct: dict, path: list | tuple) -> Any:
    """
    >>> d = {'a': {'b': 1}}
    >>> deep_get(d, ('a', 'b'))
    1
    >>> deep_get(d, (1, 'two'))
    None
    """
    return reduce(
        lambda d, key: d.get(key, None) if isinstance(d, dict) else None,
        path, dct
    )


def deep_set(dct: dict, path: tuple, item: Any):
    if len(path) == 1:
        dct[path[0]] = item
    else:
        subdict = dct.get(path[0], None)
        if not isinstance(subdict, dict):
            dct[path[0]] = {}
        deep_set(dct[path[0]], path[1:], item)


def dereference_json(obj: dict) -> None:
    """
    Changes the given dict in place de-referencing all $ref. Does not support
    files and http references. If you need them, better use jsonref
    lib. Works only for dict as root object.
    Note that it does not create new objects but only replaces {'$ref': ''}
    with objects that ref(s) are referring to, so:
    - works really fast, 20x faster than jsonref, at least relying on my
      benchmarks;
    - changes your existing object;
    - can reference the same object multiple times so changing some arbitrary
      values afterward can change object in multiple places.
    Though, it's perfectly fine in case you need to dereference obj, dump it
    to file and forget
    :param obj:
    :return:
    """

    def _inner(o):
        if isinstance(o, (str, int, float, bool, NoneType)):
            return
        # dict or list
        if isinstance(o, dict):
            for k, v in o.items():
                if isinstance(v, dict) and isinstance(v.get('$ref'), str):
                    _path = v['$ref'].strip('#/').split('/')
                    o[k] = deep_get(obj, _path)
                else:
                    _inner(v)
        else:  # isinstance(o, list)
            for i, v in enumerate(o):
                if isinstance(v, dict) and isinstance(v.get('$ref'), str):
                    _path = v['$ref'].strip('#/').split('/')
                    o[i] = deep_get(obj, _path)
                else:
                    _inner(v)

    _inner(obj)


class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


def secured_params() -> tuple:
    return (
        'refresh_token', 'id_token', 'password', 'authorization', 'secret',
        'private_key', 'private_key_id', 'Authorization', 'Authentication'
    )


# todo remove
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


def urljoin(*args: str) -> str:
    """
    Joins all the parts with one "/"
    :param args:
    :return:
    """
    return '/'.join(map(lambda x: str(x).strip('/'), args))
