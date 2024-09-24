import click
from dateutil.parser import isoparse

from modular_service_cli.group import (
    ApiResponse,
    ContextObj,
    ViewCommand,
    build_limit_option,
    build_next_token_option,
    cli_response,
)

attributes_order = ('name', 'policies', 'expiration')


@click.group(name='role')
def role():
    """Manages Role Entity"""


@role.command(cls=ViewCommand, name='describe')
@click.option('--name', '-n', type=str, help='Role name to describe.')
@build_limit_option()
@build_next_token_option()
@cli_response(attributes_order=attributes_order)
def describe(ctx: ContextObj, name: str, limit: int, next_token: str,
             customer_id: str | None):
    """
    Describes roles.
    """
    if name:
        return ctx.api_client.get_role(name, customer_id=customer_id)
    return ctx.api_client.query_roles(
        limit=limit,
        next_token=next_token,
        customer_id=customer_id
    )


@role.command(cls=ViewCommand, name='add')
@click.option('--name', '-n', type=str, required=True, help='Role name')
@click.option('--policies', '-p', multiple=True, required=True,
              help='List of policies to attach to the role')
@click.option('--expiration', '-e', type=str,
              help='Expiration date, ISO 8601. '
                   'Example: 2024-03-05T11:10:52.482Z')
@cli_response(attributes_order=attributes_order)
def add(ctx: ContextObj, name: str, policies: tuple[str], expiration: str, 
        customer_id: str | None):
    """
    Creates the Role entity with the given name
    """
    if expiration:
        try:
            isoparse(expiration)
        except ValueError:
            return ApiResponse.build('Could not parse value from --expiration')
    return ctx.api_client.create_role(
        name=name,
        expiration=expiration,
        policies=policies,
        customer_id=customer_id
    )


@role.command(cls=ViewCommand, name='update')
@click.option('--name', '-n', type=str,
              help='Role name to modify', required=True)
@click.option('--attach_policy', '-a', multiple=True,
              help='List of policies to attach to the role')
@click.option('--detach_policy', '-d', multiple=True,
              help='List of policies to detach from role')
@click.option('--expiration', '-e', type=str,
              help='Expiration date, ISO 8601. Example: 2024-03-05T11:10:52.482Z')
@cli_response(attributes_order=attributes_order)
def update(ctx: ContextObj, name, attach_policy, detach_policy, expiration,
           customer_id):
    """
    Updates role configuration.
    """

    if not attach_policy and not detach_policy and not expiration:
        return ApiResponse.build(
            'Either --attach_policy or --detach_policy or --expiration must be provided'
        )
    if expiration:
        try:
            isoparse(expiration)
        except ValueError:
            return ApiResponse.build('Could not parse value from --expiration')
    return ctx.api_client.patch_role(
        name=name,
        expiration=expiration,
        policies_to_attach=attach_policy,
        policies_to_detach=detach_policy,
        customer_id=customer_id
    )


@role.command(cls=ViewCommand, name='delete')
@click.option('--name', '-n', type=str, required=True,
              help='Role name to delete')
@cli_response()
def delete(ctx: ContextObj, name, customer_id):
    """
    Deletes role.
    """
    return ctx.api_client.delete_role(name, customer_id=customer_id)
