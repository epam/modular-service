import click

from group import cli_response, cast_to_list, ViewCommand
from service.constants import (
    PARAM_NAME, PARAM_PERMISSIONS, PARAM_ID, PARAM_DISPLAY_NAME, PARAM_ADMINS
)


@click.group(name='customer')
def customer():
    """Manages Customer Entity"""


@customer.command(cls=ViewCommand, name='describe')
@click.option('--name', '-n', type=str,
              help='Customer name to describe.')
@cli_response(attributes_order=[PARAM_NAME, PARAM_ID, PARAM_PERMISSIONS])
def describe(name=None):
    """
    Describes Customer.
    """
    from service.initializer import init_configuration
    return init_configuration().customer_get(name=name)


@customer.command(cls=ViewCommand, name='add')
@click.option('--name', '-n', type=str, required=True,
              help='Customer name')
@click.option('--display_name', '-dn', type=str, required=True,
              help='Customer display name')
@click.option('--admin', '-a', multiple=True,
              required=False,
              help='List of admin emails attached to customer.')
@cli_response(attributes_order=[PARAM_NAME, PARAM_DISPLAY_NAME, PARAM_ADMINS])
def add(name, display_name, admin):
    """
    Adds Customer.
    """
    from service.initializer import init_configuration
    admin_emails = cast_to_list(admin)
    return init_configuration().customer_post(name=name, display_name=display_name,
                                     admins=admin_emails)


@customer.command(cls=ViewCommand, name='update')
@click.option('--name', '-n', type=str, required=True,
              help='Customer name')
@click.option('--admin', '-a', multiple=True,
              required=True,
              help='List of admin emails attached to customer.')
@click.option('--override', '-o', is_flag=True, required=False,
              help='Override existing admin emails')
@cli_response(attributes_order=[PARAM_NAME, PARAM_DISPLAY_NAME, PARAM_ADMINS])
def update(name, admin, override):
    """
    Updates Customer.
    """
    from service.initializer import init_configuration
    admin_emails = cast_to_list(admin)
    return init_configuration().customer_patch(name=name,
                                      admins=admin_emails, override=override)
