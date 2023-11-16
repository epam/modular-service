from setuptools import find_packages, setup
from __version__ import __version__

setup(
    name='modular_service',
    version=__version__,
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'certifi==2023.7.22',
        'charset-normalizer==3.3.2',
        'click==7.1.2',
        'colorama==0.4.5',
        'idna==3.4',
        'pika==1.0.0b1',
        'PyYAML==6.0.1',
        'requests==2.31.0',
        'tabulate==0.9.0',
        'urllib3==1.26.16',
        'modular-cli-sdk>=2.0.0,<3.0.0'
    ],
    entry_points='''
        [console_scripts]
        modular_service=group.modularservice:modularservice
    '''
)
