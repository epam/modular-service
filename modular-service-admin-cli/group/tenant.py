import click
from group import cli_response, ViewCommand
from group.tenant_regions import region
from service.constants import (
    PARAM_NAME, PARAM_PERMISSIONS, PARAM_ID, CLOUD_PROVIDERS
)


@click.group(name='tenant')
def tenant():
    """Manages Parent Entity"""


@tenant.command(cls=ViewCommand, name='describe')
@click.option('--tenant_name', '-name', type=str,
              help='Tenant name to describe.')
@cli_response(attributes_order=[PARAM_NAME, PARAM_ID, PARAM_PERMISSIONS])
def describe(tenant_name=None):
    """
    Describes Tenant.
    """
    from service.initializer import init_configuration
    return init_configuration().tenant_get(tenant_name=tenant_name)


@tenant.command(cls=ViewCommand, name='activate')
@click.option('--name', '-n', type=str, required=True,
              help='Tenant name to activate.')
@click.option('--display_name', '-dn', type=str, required=True,
              help='Tenant display name.')
@click.option('--customer', '-cust', type=str, required=True,
              help='Customer name to attach tenant.')
@click.option('--cloud', '-c', type=click.Choice(CLOUD_PROVIDERS),
              required=True, help='Tenant cloud')
@click.option('--read_only', '-ro', is_flag=True, required=False,
              default=False, help='Mark tenant as read only')
@cli_response(attributes_order=[PARAM_NAME, PARAM_ID, PARAM_PERMISSIONS])
def activate(name, display_name, customer, cloud, read_only):
    """
    Activates Tenant.
    """
    from service.initializer import init_configuration
    return init_configuration().tenant_post(
        tenant_name=name,
        display_name=display_name,
        customer=customer,
        cloud=cloud,
        read_only=read_only
    )


@tenant.command(cls=ViewCommand, name='deactivate')
@click.option('--tenant_name', '-n', type=str, required=True,
              help='Tenant name to deactivate.')
@cli_response(attributes_order=[PARAM_NAME, PARAM_ID, PARAM_PERMISSIONS])
def deactivate(tenant_name=None):
    """
    Deactivates Tenant.
    """
    from service.initializer import init_configuration
    return init_configuration().tenant_delete(tenant_name=tenant_name)


tenant.add_command(region)
