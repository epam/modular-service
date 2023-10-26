import click

from modular_service_admin_cli.group import cli_response, ViewCommand
from modular_service_admin_cli.service.config import create_configuration, clean_up_configuration, \
    save_token
from modular_service_admin_cli.group.policy import policy
from modular_service_admin_cli.group.role import role
from modular_service_admin_cli.group.customer import customer
from modular_service_admin_cli.group.application import application
from modular_service_admin_cli.group.parent import parent
from modular_service_admin_cli.group.tenant import tenant
from modular_service_admin_cli.group.region import region
from modular_service_admin_cli.group.mode import mode
from modular_service_admin_cli.version import __version__


@click.group()
@click.version_option(__version__)
def modularadmin():
    """The main click's group to accumulate all the CLI commands"""


@modularadmin.command(cls=ViewCommand, name='configure')
@click.option('--api_link', '-api', type=str,
              required=True,
              help='Link to the Madular API host.')
@cli_response(check_api_adapter=False)
def configure(api_link):
    """
    Configures modularadmin tool to work with Modular API.
    """
    response = create_configuration(api_link=api_link)
    return {'message': response}


@modularadmin.command(cls=ViewCommand, name='login')
@click.option('--username', '-u', type=str,
              required=True,
              help='Modular user username.')
@click.option('--password', '-p', type=str,
              required=True, hide_input=True, prompt=True,
              help='Modular user password.')
@cli_response()
def login(username: str, password: str):
    """
    Authenticates user to work with Modular API.
    """
    from service.initializer import ADAPTER_SDK

    response = ADAPTER_SDK.login(username=username, password=password)

    if isinstance(response, dict):
        return response

    response = save_token(access_token=response)
    return {'message': response}


@modularadmin.command(cls=ViewCommand, name='cleanup')
@cli_response(check_api_adapter=False)
def cleanup():
    """
    Removes all the configuration data related to the tool.
    """
    response = clean_up_configuration()
    return {'message': response}


modularadmin.add_command(policy)
modularadmin.add_command(role)
modularadmin.add_command(customer)
modularadmin.add_command(application)
modularadmin.add_command(parent)
modularadmin.add_command(tenant)
modularadmin.add_command(region)
modularadmin.add_command(mode)
