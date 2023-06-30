from setuptools import find_packages, setup
from modular_service_admin_cli.version import __version__

setup(
    name='modularadmin',
    version=__version__,
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'click==8.0.0',
        'PyYAML==5.4.1',
        'tabulate==0.8.9',
        'requests==2.25.1',
        'pika==1.0.0b1'
    ],
    entry_points='''
        [console_scripts]
        modularadmin=modular_service_admin_cli.modular_admin.modularadmin
    ''',
)
