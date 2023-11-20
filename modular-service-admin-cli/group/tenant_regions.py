import click

from group import cli_response, ViewCommand
from service.constants import (PARAM_NAME, PARAM_PERMISSIONS, PARAM_ID)


@click.group(name='regions')
def regions():
    """Manages Tenant Region Entity"""


@regions.command(cls=ViewCommand, name='describe')
@click.option('--tenant_name', '-name', type=str, required=True,
              help='Tenant name to describe.')
@cli_response(attributes_order=[PARAM_NAME, PARAM_ID, PARAM_PERMISSIONS])
def describe(tenant_name):
    """
    Describes Tenant region.
    """
    from service.initializer import init_configuration
    return init_configuration().tenant_region_get(tenant_name=tenant_name)


@regions.command(cls=ViewCommand, name='activate')
@click.option('--tenant_name', '-tn', type=str, required=True,
              help='Tenant name to activate.')
@click.option('--region_name', '-rn', type=str, required=True,
              help='Region Maestro name to activate.')
@cli_response(attributes_order=[PARAM_NAME, PARAM_ID, PARAM_PERMISSIONS])
def activate(tenant_name, region_name):
    """
    Activates region in tenant.
    """
    from service.initializer import init_configuration
    return init_configuration().tenant_region_post(
        tenant_name=tenant_name, region_name=region_name)


@regions.command(cls=ViewCommand, name='deactivate')
@click.option('--tenant_name', '-tn', type=str, required=True,
              help='Tenant name to activate.')
@click.option('--region_name', '-rn', type=str, required=True,
              help='Region Maestro name to activate.')
@cli_response(attributes_order=[PARAM_NAME, PARAM_ID, PARAM_PERMISSIONS])
def deactivate(tenant_name, region_name):
    """
    Deactivates region in tenant.
    """
    from service.initializer import init_configuration
    return init_configuration().tenant_region_delete(
        tenant_name=tenant_name, region_name=region_name)
