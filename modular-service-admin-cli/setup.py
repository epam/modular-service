from setuptools import find_packages, setup
from modular_service_cli.version import __version__

setup(
    name='modular-service-cli',
    version=__version__,
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "click==7.1.2",
        "tabulate==0.9.0",
        "boto3==1.26.80",
        "python-dateutil==2.8.2",
        "modular-cli-sdk[hvac]==2.0.0",
    ],
    entry_points='''
        [console_scripts]
        modular-service=modular_service_cli.group.modularservice:modularservice
    '''
)
