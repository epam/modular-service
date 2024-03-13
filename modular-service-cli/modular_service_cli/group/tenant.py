import operator

import click

from modular_service_cli.group import (
    ContextObj,
    ViewCommand,
    build_limit_option,
    build_next_token_option,
    cli_response,
)
from modular_service_cli.group.tenant_regions import regions
from modular_service_cli.group.tenant_settings import settings
from modular_service_cli.service.constants import Cloud


attributes_order = 'name', 'display_name', 'cloud', 'account_id', 


@click.group(name='tenant')
def tenant():
    """Manages Parent Entity"""


@tenant.command(cls=ViewCommand, name='describe')
@click.option('--tenant_name', '-name', type=str, 
              help='Tenant name to describe.')
@build_limit_option()
@build_next_token_option()
@click.option('--cloud', '-c', 
              type=click.Choice(map(operator.attrgetter('value'), Cloud)), 
              help='Cloud to filter tenants by')
@click.option('--is_active', '-act', type=bool, 
              help='Whether to query only active tenants')
@cli_response(attributes_order=attributes_order)
def describe(ctx: ContextObj, tenant_name, limit, next_token, cloud, 
             is_active, customer_id):
    """
    Describes Tenant.
    """
    if tenant_name:
        return ctx.api_client.get_tenant(tenant_name, customer_id=customer_id)
    return ctx.api_client.query_tenants(
        customer_id=customer_id,
        limit=limit,
        next_token=next_token,
        cloud=cloud,
        is_active=is_active
    )


@tenant.command(cls=ViewCommand, name='create')
@click.option('--name', '-n', type=str, required=True,
              help='Tenant name to activate.')
@click.option('--display_name', '-dn', type=str, required=True,
              help='Tenant display name.')
@click.option('--cloud', '-c', type=click.Choice(map(operator.attrgetter('value'), Cloud)),
              required=True, help='Tenant cloud')
@click.option('--account_id', '-acc', required=True,
              help='Tenant account ID')
@click.option('--read_only', '-ro', is_flag=True, 
              help='Mark tenant as read only')
@click.option('--primary_contacts', type=str, multiple=True, required=True,
              help='Main contacts')
@click.option('--secondary_contacts', type=str, multiple=True, required=True,
              help='Secondaty contacts')
@click.option('--tenant_manager_contacts', type=str, multiple=True, 
              required=True)
@click.option('--default_owner', type=str, required=True)
@cli_response(attributes_order=attributes_order)
def create(ctx: ContextObj, name, display_name, cloud, account_id, read_only,
           primary_contacts, secondary_contacts, tenant_manager_contacts, 
           default_owner, customer_id):
    """
    Activates Tenant.
    """
    return ctx.api_client.create_tenant(
        name=name,
        display_name=display_name,
        cloud=cloud,
        account_id=account_id,
        read_only=read_only,
        primary_contacts=primary_contacts,
        secondary_contacts=secondary_contacts,
        tenant_manager_contacts=tenant_manager_contacts,
        default_owner=default_owner,
        customer_id=customer_id
    )


@tenant.command(cls=ViewCommand, name='delete')
@click.option('--tenant_name', '-n', type=str, required=True,
              help='Tenant name to deactivate.')
@cli_response(attributes_order=attributes_order)
def delete(ctx: ContextObj, tenant_name, customer_id):
    """
    Deactivates Tenant.
    """
    return ctx.api_client.delete_tenant(tenant_name, customer_id=customer_id)


@tenant.command(cls=ViewCommand, name='activate')
@click.option('--tenant_name', '-n', type=str, required=True,
              help='Tenant name')
@cli_response(attributes_order=attributes_order)
def activate(ctx: ContextObj, tenant_name, customer_id):
    """
    Activates an existing tenant
    """
    return ctx.api_client.activate_tenant(
        name=tenant_name,
        customer_id=customer_id
    )


@tenant.command(cls=ViewCommand, name='deactivate')
@click.option('--tenant_name', '-n', type=str, required=True,
              help='Tenant name')
@cli_response(attributes_order=attributes_order)
def deactivate(ctx: ContextObj, tenant_name, customer_id):
    """
    Deactivates an existing tenant
    """
    return ctx.api_client.deactivate_tenant(
        name=tenant_name,
        customer_id=customer_id
    )

tenant.add_command(regions)
tenant.add_command(settings)
