import click

from modular_service_cli.group import ContextObj
from modular_service_cli.group import cli_response, ViewCommand
from modular_service_cli.group.application import application
from modular_service_cli.group.customer import customer
from modular_service_cli.group.policy import policy
from modular_service_cli.group.region import region
from modular_service_cli.group.role import role
from modular_service_cli.group.tenant import tenant
from modular_service_cli.group.users import users
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
@click.option('--api_link', '-api', type=str, required=True,
              help='Link to the Modular API host.')
@cli_response(check_access_token=False, check_api_link=False)
def configure(ctx: ContextObj, api_link: str, **kwargs):
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
def login(ctx: ContextObj, username: str, password: str, **kwargs):
    """
    Authenticates user to work with Modular API.
    """
    resp = ctx.api_client.login(username=username, password=password)
    if resp.exc or not resp.ok:
        return resp
    # check_version_compatibility(resp.api_version)

    ctx.config.access_token = resp.data['access_token']
    if rt := resp.data.get('refresh_token'):
        ctx.config.refresh_token = rt
    resp.data = {'message': 'Logged in successfully'}
    # if rt := resp.data.get('refresh_token'):
    #     ctx['config'].refresh_token = rt
    return resp


@modularservice.command(cls=ViewCommand, name='signup')
@click.option('--username', '-u', type=str, required=True,
              help='Modular user username.')
@click.option('--password', '-p', type=str,
              required=True, hide_input=True, prompt=True,
              help='Modular user password.')
@click.option('--customer_name', '-cn', type=str,
              required=True,
              help='Customer name to sign up this user for')
@click.option('--customer_display_name', '-dn', type=str, required=True,
              help='Customer display name')
@click.option('--customer_admin', '-ca', multiple=True, type=str,
              required=True,
              help='List of admin emails attached to customer.')
@cli_response(check_access_token=False)
def signup(ctx: ContextObj, username, password, customer_name,
           customer_display_name, customer_admin, customer_id):
    """
    Signs up a new user
    """
    return ctx.api_client.signup(
        username=username,
        password=password,
        customer_name=customer_name,
        customer_display_name=customer_display_name,
        customer_admins=customer_admin
    )


@modularservice.command(cls=ViewCommand, name='cleanup')
@cli_response(check_access_token=False, check_api_link=False)
def cleanup(ctx: ContextObj, **kwargs):
    """
    Removes all the configuration data related to the tool.
    """
    ctx.config.clear()
    return ApiResponse.build('Configuration was cleaned')


modularservice.add_command(policy)
modularservice.add_command(role)
modularservice.add_command(customer)
modularservice.add_command(application)
modularservice.add_command(tenant)
modularservice.add_command(region)
modularservice.add_command(users)
