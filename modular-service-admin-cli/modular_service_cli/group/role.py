from datetime import datetime

import click
from modular_service_cli.group import cli_response, ViewCommand, ContextObj, build_limit_option, build_next_token_option

from modular_service_cli.service.constants import (PARAM_NAME, PARAM_POLICIES, PARAM_EXPIRATION)


@click.group(name='role')
def role():
    """Manages Role Entity"""


@role.command(cls=ViewCommand, name='describe')
@click.option('--name', '-n', type=str, help='Role name to describe.')
@build_limit_option()
@build_next_token_option()
@cli_response(attributes_order=[PARAM_NAME, PARAM_POLICIES, PARAM_EXPIRATION])
def describe(ctx: ContextObj, name: str, limit: int, next_token: str,
             customer_id: str | None):
    """
    Describes roles.
    """
    if name:
        return ctx.api_client.get_role(name)
    return ctx.api_client.query_role(
        limit=limit,
        next_token=next_token,
        customer_id=customer_id
    )


@role.command(cls=ViewCommand, name='add')
@click.option('--name', '-n', type=str, required=True, help='Role name')
@click.option('--policies', '-p', multiple=True,
              required=True,
              help='List of policies to attach to the role')
@click.option('--expiration', '-e', type=str, required=True,
              help='Expiration date, ISO 8601. Example: 2021-08-01T15:30:00')
@cli_response(attributes_order=[PARAM_NAME, PARAM_POLICIES, PARAM_EXPIRATION])
def add(name, policies, expiration):
    """
    Creates the Role entity with the given name
    """
    from service.initializer import init_configuration

    policies = cast_to_list(policies)
    if expiration:
        try:
            expiration = datetime.fromisoformat(expiration).isoformat()
        except ValueError:
            return {'message': f'Invalid value for the \'expiration\' '
                               f'parameter: {expiration}'}
    return init_configuration().role_post(role_name=name,
                                 policies=policies,
                                 expiration=expiration)


@role.command(cls=ViewCommand, name='update')
@click.option('--name', '-n', type=str,
              help='Role name to modify', required=True)
@click.option('--attach_policy', '-a', multiple=True,
              help='List of policies to attach to the role')
@click.option('--detach_policy', '-d', multiple=True,
              help='List of policies to detach from role')
@click.option('--expiration', '-e', type=str, required=False,
              help='Expiration date, ISO 8601. Example: 2021-08-01T15:30:00')
@cli_response(attributes_order=[PARAM_NAME, PARAM_POLICIES, PARAM_EXPIRATION])
def update(name, attach_policy, detach_policy, expiration):
    """
    Updates role configuration.
    """
    from service.initializer import init_configuration

    if not attach_policy and not detach_policy:
        return {'message': 'At least one of the following arguments must be '
                           'provided: attach_policy, detach_policy'}

    attach_policies = cast_to_list(attach_policy)
    detach_policies = cast_to_list(detach_policy)
    if expiration:
        try:
            expiration = datetime.fromisoformat(expiration).isoformat()
        except ValueError:
            return {'message': f'Invalid value for the \'expiration\' '
                               f'parameter: {expiration}'}

    return init_configuration().role_patch(
        role_name=name,
        expiration=expiration,
        attach_policies=attach_policies,
        detach_policies=detach_policies)


@role.command(cls=ViewCommand, name='delete')
@click.option('--name', '-n', type=str, required=True,
              help='Role name to delete')
@cli_response()
def delete(name):
    """
    Deletes role.
    """
    from service.initializer import init_configuration
    return init_configuration().role_delete(role_name=name)
