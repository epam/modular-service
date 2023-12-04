import click

from group import cli_response, ViewCommand
from service.config import (
    create_configuration, clean_up_configuration, save_token
)
from group.policy import policy
from group.role import role
from group.customer import customer
from group.application import application
from group.parent import parent
from group.tenant import tenant
from group.region import region
from group.mode import mode
from importlib.metadata import version as lib_version


@click.group()
@click.version_option(lib_version('modular_service'), '-v', '--version')
def modularservice():
    """The main click's group to accumulate all the CLI commands"""


@modularservice.command(cls=ViewCommand, name='configure')
@click.option('--api_link', '-api', type=str,
              required=True,
              help='Link to the Modular API host.')
@cli_response(check_api_adapter=False)
def configure(api_link):
    """
    Configures modularadmin tool to work with Modular API.
    """
    response = create_configuration(api_link=api_link)
    return {'message': response}


@modularservice.command(cls=ViewCommand, name='login')
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
    from service.initializer import init_configuration

    response = init_configuration().login(username=username, password=password)

    if isinstance(response, dict):
        return response

    response = save_token(access_token=response)
    return {'message': response}


@modularservice.command(cls=ViewCommand, name='cleanup')
@cli_response(check_api_adapter=False)
def cleanup():
    """
    Removes all the configuration data related to the tool.
    """
    response = clean_up_configuration()
    return {'message': response}


modularservice.add_command(policy)
modularservice.add_command(role)
modularservice.add_command(customer)
modularservice.add_command(application)
modularservice.add_command(parent)
modularservice.add_command(tenant)
modularservice.add_command(region)
modularservice.add_command(mode)
