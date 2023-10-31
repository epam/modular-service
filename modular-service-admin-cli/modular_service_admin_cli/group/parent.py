import click

from modular_service_admin_cli.group import cli_response, ViewCommand
from modular_service_admin_cli.service.constants import (PARAM_NAME,
                                                         PARAM_PERMISSIONS,
                                                         PARAM_ID,
                                                         ALL_PARENT_TYPES)


@click.group(name='parent')
def parent():
    """Manages Parent Entity"""


@parent.command(cls=ViewCommand, name='describe')
@click.option('--parent_id', '-pid', type=str,
              help='Parent id to describe.')
@click.option('--application_id', '-aid', type=str,
              help='Application id to describe parents.')
@cli_response(attributes_order=[PARAM_NAME, PARAM_ID, PARAM_PERMISSIONS])
def describe(parent_id=None, application_id=None):
    """
    Describes Parent.
    """
    from modular_service_admin_cli.service.initializer import init_configuration
    return init_configuration().parent_get(
        parent_id=parent_id,
        application_id=application_id)


@parent.command(cls=ViewCommand, name='add')
@click.option('--application_id', '-aid', type=str, required=True,
              help='Application id to link parent.')
@click.option('--customer', '-c', type=str, required=True,
              help='Customer name to link parent.')
@click.option('--parent_type', '-pt',
              type=click.Choice(ALL_PARENT_TYPES),
              required=True, help='Parent type')
@click.option('--description', '-d', type=str,
              help='Parent description.')
@cli_response(attributes_order=[PARAM_NAME, PARAM_ID, PARAM_PERMISSIONS])
def add(application_id, customer, parent_type, description=None):
    """
    Adds Parent.
    """
    from modular_service_admin_cli.service.initializer import init_configuration
    return init_configuration().parent_post(
        application_id=application_id,
        customer=customer,
        parent_type=parent_type,
        description=description)


@parent.command(cls=ViewCommand, name='update')
@click.option('--parent_id', '-pid', type=str, required=True,
              help='Parent id to update.')
@click.option('--application_id', '-aid', type=str,
              help='Application id to link parent.')
@click.option('--parent_type', '-pt',
              type=click.Choice(ALL_PARENT_TYPES),
              help='Parent type')
@click.option('--description', '-d', type=str,
              help='Parent description.')
@cli_response(attributes_order=[PARAM_NAME, PARAM_ID, PARAM_PERMISSIONS])
def update(parent_id, application_id=None, parent_type=None, description=None):
    """
    Updates Parent.
    """
    from modular_service_admin_cli.service.initializer import init_configuration
    return init_configuration().parent_patch(
        parent_id=parent_id,
        application_id=application_id,
        parent_type=parent_type,
        description=description)


@parent.command(cls=ViewCommand, name='deactivate')
@click.option('--parent_id', '-pid', type=str,
              help='Parent id to deactivate.')
@cli_response(attributes_order=[PARAM_NAME, PARAM_ID, PARAM_PERMISSIONS])
def deactivate(parent_id):
    """
    Deactivates Parent.
    """
    from modular_service_admin_cli.service.initializer import init_configuration
    return init_configuration().parent_delete(
        parent_id=parent_id)
