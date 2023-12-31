from datetime import datetime

import click
from modular_service_admin_cli.group import cli_response, cast_to_list, ViewCommand
from modular_service_admin_cli.service.constants import (PARAM_NAME,
                                                         PARAM_POLICIES,
                                                         PARAM_EXPIRATION)


@click.group(name='role')
def role():
    """Manages Role Entity"""


@role.command(cls=ViewCommand, name='describe')
@click.option('--name', '-n', type=str, help='Role name to describe.')
@cli_response(attributes_order=[PARAM_NAME, PARAM_POLICIES, PARAM_EXPIRATION])
def describe(name=None):
    """
    Describes roles.
    """
    from modular_service_admin_cli.service.initializer import init_configuration
    return init_configuration().role_get(role_name=name)


@role.command(cls=ViewCommand, name='add')
@click.option('--name', '-n', type=str, required=True, help='Role name')
@click.option('--policies', '-p', multiple=True,
              required=True,
              help='List of policies to attach to the role')
@click.option('--expiration', '-e', type=str,
              help='Expiration date, ISO 8601. Example: 2021-08-01T15:30:00')
@cli_response(attributes_order=[PARAM_NAME, PARAM_POLICIES, PARAM_EXPIRATION])
def add(name, policies, expiration):
    """
    Creates the Role entity with the given name
    """
    from modular_service_admin_cli.service.initializer import init_configuration

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
    from modular_service_admin_cli.service.initializer import init_configuration

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
    from modular_service_admin_cli.service.initializer import init_configuration
    return init_configuration().role_delete(role_name=name)
