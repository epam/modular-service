import urllib.error
import urllib.request
from typing import Callable, TypeVar

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
