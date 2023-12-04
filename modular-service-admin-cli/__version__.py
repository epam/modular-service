__version__ = '2.0.6'

import sys
from distutils.version import LooseVersion


def check_version_compatibility(api_version):
    if not api_version:
        print('Modular API did not return the version number!')
        return
    cli_version = LooseVersion(__version__)
    api_version = LooseVersion(api_version)
    if cli_version > api_version:
        print(f'Consider that you modularadmin version {cli_version} is '
              f'higher than the API version {api_version}')
        return
    if cli_version.version[0] < api_version.version[0]:  # Major
        print(f'CLI major version {cli_version} is lower than '
              f'the API version {api_version}. Please, update the CLI',
              file=sys.stderr)
        sys.exit(1)
    if cli_version.version[1] < api_version.version[1]:  # Minor
        print(f'CLI Minor version {cli_version} is lower than the '
              f'API version {api_version}. Some features may not '
              f'work. Consider updating the CLI')
