import click

from modular_service_admin_cli.group import cli_response, ViewCommand
from modular_service_admin_cli.service.constants import (PARAM_NAME,
                                                         PARAM_PERMISSIONS,
                                                         PARAM_ID,
                                                         AVAILABLE_APPLICATION_TYPES)


@click.group(name='application')
def application():
    """Manages Application Entity"""


@application.command(cls=ViewCommand, name='describe')
@click.option('--application_id', '-aid', type=str,
              help='Application id to describe.')
@cli_response(attributes_order=[PARAM_NAME, PARAM_ID, PARAM_PERMISSIONS])
def describe(application_id=None):
    """
    Describes Application.
    """
    from modular_service_admin_cli.service.initializer import init_configuration
    return init_configuration().application_get(application_id=application_id)


@application.command(cls=ViewCommand, name='add')
@click.option('--application_type', '-at',
              type=click.Choice(AVAILABLE_APPLICATION_TYPES),
              required=True, help='Application type')
@click.option('--customer', '-c', type=str, required=True,
              help='Customer name to link application')
@click.option('--description', '-d', type=str, required=True,
              help='Application description.')
@cli_response(attributes_order=[PARAM_NAME, PARAM_ID, PARAM_PERMISSIONS])
def add(application_type, customer, description=None):
    """
    Describes Application.
    """
    from modular_service_admin_cli.service.initializer import init_configuration
    return init_configuration().application_post(
        application_type=application_type,
        customer_id=customer,
        description=description)


@application.command(cls=ViewCommand, name='update')
@click.option('--application_id', '-aid', type=str, required=True,
              help='Application id to update')
@click.option('--application_type', '-at',
              type=click.Choice(AVAILABLE_APPLICATION_TYPES),
              required=False, help='Application type')
@click.option('--customer', '-c', type=str, required=False,
              help='Customer name to link application')
@click.option('--description', '-d', type=str,
              help='Application description.')
@cli_response(attributes_order=[PARAM_NAME, PARAM_ID, PARAM_PERMISSIONS])
def update(application_id, application_type=None, customer=None,
           description=None):
    """
    Updates Application.
    """
    from modular_service_admin_cli.service.initializer import init_configuration
    return init_configuration().application_patch(
        application_id=application_id,
        application_type=application_type,
        customer_id=customer,
        description=description)


@application.command(cls=ViewCommand, name='deactivate')
@click.option('--application_id', '-aid', type=str, required=True,
              help='Application id to describe.')
@cli_response(attributes_order=[PARAM_NAME, PARAM_ID, PARAM_PERMISSIONS])
def deactivate(application_id):
    """
    Deactivates Application.
    """
    from modular_service_admin_cli.service.initializer import init_configuration
    return init_configuration().application_delete(application_id=application_id)
