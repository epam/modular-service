import click

from modular_service_cli.group import ContextObj, ViewCommand, cli_response


attributes_order = 'maestro_name', 'native_name', 'cloud', 'is_active'


@click.group(name='regions')
def regions():
    """Manages Tenant Region Entity"""


@regions.command(cls=ViewCommand, name='describe')
@click.option('--tenant_name', '-name', type=str, required=True,
              help='Tenant name to describe.')
@cli_response(attributes_order=attributes_order)
def describe(ctx: ContextObj, tenant_name, customer_id):
    """
    Describes Tenant region.
    """
    return ctx.api_client.get_tenant_regions(tenant_name, 
                                             customer_id=customer_id)


@regions.command(cls=ViewCommand, name='activate')
@click.option('--tenant_name', '-tn', type=str, required=True,
              help='Tenant name to activate.')
@click.option('--region_name', '-rn', type=str, required=True,
              help='Region Maestro name to activate.')
@cli_response(attributes_order=attributes_order)
def activate(ctx: ContextObj, tenant_name, region_name, customer_id):
    """
    Activates region in tenant.
    """
    return ctx.api_client.add_tenant_region(
        name=tenant_name,
        region=region_name,
        customer_id=customer_id
    )


@regions.command(cls=ViewCommand, name='deactivate')
@click.option('--tenant_name', '-tn', type=str, required=True,
              help='Tenant name to activate.')
@click.option('--region_name', '-rn', type=str, required=True,
              help='Region Maestro name to activate.')
@cli_response()
def deactivate(ctx: ContextObj, tenant_name, region_name, customer_id):
    """
    Deactivates region in tenant.
    """
    return ctx.api_client.delete_tenant_region(
        name=tenant_name,
        region=region_name,
        customer_id=customer_id
    )
