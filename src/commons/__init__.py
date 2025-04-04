import base64
import binascii
import json
import math
import uuid
from functools import reduce
from typing import Any

from typing_extensions import Self


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
        match o:
            case str() | int() | float() | bool() | None:
                return
            case dict():
                for k, v in o.items():
                    if isinstance(v, dict) and isinstance(v.get('$ref'), str):
                        _path = v['$ref'].strip('#/').split('/')
                        o[k] = deep_get(obj, _path)
                    else:
                        _inner(v)
            case _:  # list()
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


def urljoin(*args: str) -> str:
    """
    Joins all the parts with one "/"
    :param args:
    :return:
    """
    return '/'.join(map(lambda x: str(x).strip('/'), args))


class NextToken:
    __slots__ = ('_lak',)

    def __init__(self, lak: dict | int | None = None):
        """
        Wrapper over dynamodb last_evaluated_key and pymongo offset
        :param lak:
        """
        self._lak = lak

    def __json__(self) -> str | None:
        """
        Handled only inside commons.lambda_response
        :return:
        """
        if not self:
            return
        # TODO encrypt
        return base64.urlsafe_b64encode(
            json.dumps(self._lak, separators=(',', ':')).encode()
        ).decode()

    @property
    def value(self) -> dict | int | None:
        return self._lak

    @classmethod
    def from_input(cls, s: str | None = None) -> Self:
        if not s or not isinstance(s, str):
            return cls()
        decoded = None
        try:
            decoded = json.loads(base64.urlsafe_b64decode(s).decode())
        except (binascii.Error, json.JSONDecodeError):
            pass
        except Exception:  # noqa
            pass
        return cls(decoded)

    def __bool__(self) -> bool:
        return not not self._lak  # 0 and empty dict are None
