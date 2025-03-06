import click

from modular_service_cli.group import (
    ContextObj,
    ViewCommand,
    build_limit_option,
    build_next_token_option,
    cli_response,
)

attributes_order = 'name', 'display_name', 'admins', 'is_active'


@click.group(name='customer')
def customer():
    """Manages Customer Entity"""


@customer.command(cls=ViewCommand, name='describe')
@click.option('--name', '-n', type=str,
              help='Customer name to describe.')
@build_limit_option()
@build_next_token_option()
@click.option('--is_active', '-act', type=bool, 
              help='Whether to return active or deactivated customers')
@cli_response(attributes_order=attributes_order)
def describe(ctx: ContextObj, name, limit, next_token, is_active, 
             customer_id):
    """
    Describes Customer.
    """
    if name:
        return ctx.api_client.get_customer(name, customer_id=customer_id)
    return ctx.api_client.query_customer(
        limit=limit,
        next_token=next_token,
        is_active=is_active,
        customer_id=customer_id
    )


@customer.command(cls=ViewCommand, name='add')
@click.option('--name', '-n', type=str, required=True,
              help='Customer name')
@click.option('--display_name', '-dn', type=str, required=True,
              help='Customer display name')
@click.option('--admin', '-a', multiple=True, type=str,
              help='List of admin emails attached to customer.')
@cli_response(attributes_order=attributes_order)
def add(ctx: ContextObj, name, display_name, admin, customer_id):
    """
    Adds Customer.
    """
    return ctx.api_client.create_customer(
        name=name,
        display_name=display_name,
        admins=admin,
        customer_id=customer_id
    )


@customer.command(cls=ViewCommand, name='update')
@click.option('--name', '-n', type=str, required=True,
              help='Customer name')
@click.option('--admin', '-a', multiple=True,
              required=True,
              help='List of admin emails attached to customer.')
@cli_response(attributes_order=attributes_order)
def update(ctx: ContextObj, name, admin, customer_id):
    """
    Updates Customer.
    """
    return ctx.api_client.patch_customer(
        name=name,
        admins=admin,
        customer_id=customer_id
    )


@customer.command(cls=ViewCommand, name='activate')
@click.option('--name', '-n', type=str, required=True,
              help='Customer name')
@cli_response(attributes_order=attributes_order)
def activate(ctx: ContextObj, name, customer_id):
    """
    Activates an existing customer
    """
    return ctx.api_client.activate_customer(
        name=name,
        customer_id=customer_id
    )


@customer.command(cls=ViewCommand, name='deactivate')
@click.option('--name', '-n', type=str, required=True,
              help='Customer name')
@cli_response(attributes_order=attributes_order)
def deactivate(ctx: ContextObj, name, customer_id):
    """
    Deactivates an existing customer
    """
    return ctx.api_client.deactivate_customer(
        name=name,
        customer_id=customer_id
    )
