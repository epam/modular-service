import base64
import json
import time
from typing import Callable, TypeVar
import urllib.error
import urllib.request

from urllib3.exceptions import LocationParseError
from urllib3.util import parse_url


def urljoin(*args: str) -> str:
    """
    This method somehow differs from urllib.parse.urljoin. See:
    >>> urljoin('one', 'two', 'three')
    'one/two/three'
    >>> urljoin('one/', '/two/', '/three/')
    'one/two/three'
    >>> urljoin('https://example.com/', '/prefix', 'path/to/service')
    'https://example.com/prefix/path/to/service'
    :param args: list of string
    :return:
    """
    return '/'.join(map(lambda x: str(x).strip('/'), args))


def sifted(data: dict) -> dict:
    """
    >>> sifted({'k': 'value', 'k1': None, 'k2': '', 'k3': 0, 'k4': False})
    {'k': 'value', 'k3': 0, 'k4': False}
    :param data:
    :return:
    """
    return {k: v for k, v in data.items() if isinstance(v, (bool, int)) or v}


def validate_api_link(url: str) -> str | None:
    url = url.lstrip()

    if "://" in url and not url.lower().startswith("http"):
        return 'Invalid API link: not supported scheme'
    try:
        scheme, auth, host, port, path, query, fragment = parse_url(url)
    except LocationParseError as e:
        return 'Invalid API link'
    if not scheme:
        return 'Invalid API link: missing scheme'
    if not host:
        return 'Invalid API link: missing host'
    try:
        req = urllib.request.Request(url)
        urllib.request.urlopen(req)
    except urllib.error.HTTPError as e:
        pass
    except urllib.error.URLError as e:
        return 'Invalid API link: cannot make a request'


RT = TypeVar('RT')  # return type
ET = TypeVar('ET', bound=Exception)  # exception type


def catch(func: Callable[[], RT], exception: type[ET] = Exception
          ) -> tuple[RT | None, ET | None]:
    """
    Calls the provided function and catches the desired exception.
    Seems useful to me :) ?
    :param func:
    :param exception:
    :return:
    """
    try:
        return func(), None
    except exception as e:
        return None, e


class JWTToken:
    """
    A simple wrapper over jwt token
    """
    EXP_THRESHOLD = 300  # in seconds
    __slots__ = '_token', '_exp_threshold'

    def __init__(self, token: str, exp_threshold: int = EXP_THRESHOLD):
        self._token = token
        self._exp_threshold = exp_threshold

    @property
    def raw(self) -> str:
        return self._token

    @property
    def payload(self) -> dict | None:
        try:
            return json.loads(
                base64.b64decode(self._token.split('.')[1] + '==').decode()
            )
        except Exception:
            return

    def is_expired(self) -> bool:
        p = self.payload
        if not p:
            return True
        exp = p.get('exp')
        if not exp:
            return False
        return exp < time.time() + self._exp_threshold

