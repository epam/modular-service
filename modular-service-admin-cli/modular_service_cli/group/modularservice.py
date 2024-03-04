import click

from modular_service_cli.group import ContextObj
from modular_service_cli.group import cli_response, ViewCommand
# from modular_service_cli.group.application import application
# from modular_service_cli.group.customer import customer
# from modular_service_cli.group.mode import mode
# from modular_service_cli.group.parent import parent
# from modular_service_cli.group.policy import policy
# from modular_service_cli.group.region import region
from modular_service_cli.group.role import role
# from modular_service_cli.group.tenant import tenant
from modular_service_cli.service.api_client import ApiResponse
from modular_service_cli.service.utils import validate_api_link
from modular_service_cli.version import __version__


@click.group()
@click.version_option(__version__)
def modularservice():
    """
    Cli to manage modular entities
    """


@modularservice.command(cls=ViewCommand, name='configure')
@click.option('--api_link', '-api', type=str,
              required=True,
              help='Link to the Modular API host.')
@cli_response(check_access_token=False, check_api_link=False)
def configure(ctx: ContextObj, api_link: str):
    """
    Configures modularadmin tool to work with Modular API.
    """
    if message := validate_api_link(api_link):
        return ApiResponse.build(message)
    ctx.config.api_link = api_link
    return ApiResponse.build('Api link was configured!')


@modularservice.command(cls=ViewCommand, name='login')
@click.option('--username', '-u', type=str, required=True,
              help='Modular user username.')
@click.option('--password', '-p', type=str,
              required=True, hide_input=True, prompt=True,
              help='Modular user password.')
@cli_response(check_access_token=False)
def login(ctx: ContextObj, username: str, password: str):
    """
    Authenticates user to work with Modular API.
    """
    resp = ctx.api_client.login(username=username, password=password)
    if resp.exc or not resp.ok:
        return resp
    # check_version_compatibility(resp.api_version)

    ctx.config.access_token = resp.data['access_token']
    # if rt := resp.data.get('refresh_token'):
    #     ctx['config'].refresh_token = rt
    return ApiResponse.build('Logged in successfully')


@modularservice.command(cls=ViewCommand, name='cleanup')
@cli_response(check_access_token=False, check_api_link=False)
def cleanup(ctx: ContextObj):
    """
    Removes all the configuration data related to the tool.
    """
    ctx.config.clear()
    return ApiResponse.build('Configuration was cleaned')


# modularservice.add_command(policy)
modularservice.add_command(role)
# modularservice.add_command(customer)
# modularservice.add_command(application)
# modularservice.add_command(parent)
# modularservice.add_command(tenant)
# modularservice.add_command(region)
# modularservice.add_command(mode)
