import json

import click

from modular_service_cli.group import (
    ContextObj,
    ViewCommand,
    build_limit_option,
    build_next_token_option,
    cli_response,
)
from modular_service_cli.service.api_client import ApiResponse


attributes_order = ('name', 'permissions')


@click.group(name='policy')
def policy():
    """Manages Policy Entity"""


@policy.command(cls=ViewCommand, name='describe')
@click.option('--policy_name', '-name', type=str,
              help='Policy name to describe.')
@build_limit_option()
@build_next_token_option()
@cli_response(attributes_order=attributes_order)
def describe(ctx: ContextObj, policy_name, limit, next_token, customer_id):
    """
    Describes policies.
    """
    if policy_name:
        return ctx.api_client.get_policy(policy_name, customer_id=customer_id)
    return ctx.api_client.query_policies(
        limit=limit,
        next_token=next_token,
        customer_id=customer_id
    )


@policy.command(cls=ViewCommand, name='add')
@click.option('--policy_name', '-name', type=str, required=True,
              help='Policy name to create')
@click.option('--permission', '-p', multiple=True,
              required=False,
              help='List of permissions to attach to the policy')
@click.option('--permissions_admin', '-padm', is_flag=True, required=False,
              help='Adds all admin permissions')
@click.option('--path_to_permissions', '-path', required=False,
              help='Path to .json file that contains list of permissions to '
                   'attach to the policy')
@cli_response(attributes_order=attributes_order)
def add(ctx: ContextObj, policy_name, permission, permissions_admin,
        path_to_permissions, customer_id):
    """
    Creates policy.
    """
    permissions = list(permission)
    if path_to_permissions:
        try:
            with open(path_to_permissions, 'r') as fp:
                data = json.load(fp)
        except FileNotFoundError:
            return ApiResponse.build(f'File {path_to_permissions} not found')
        except json.JSONDecodeError:
            return ApiResponse.build(f'File {path_to_permissions} contains invalid JSON')
        except Exception:
            return ApiResponse.build(f'Could not load file {path_to_permissions}')
        if not isinstance(data, list) and not all([isinstance(i, str) for i in data]):
            return ApiResponse.build('File should contain list of strings')
        permissions.extend(data) 

    return ctx.api_client.create_policy(
        name=policy_name,
        permissions=permissions,
        permissions_admin=permissions_admin,
        customer_id=customer_id
    )


@policy.command(cls=ViewCommand, name='update')
@click.option('--policy_name', '-name', type=str, required=True)
@click.option('--attach_permission', '-a', multiple=True,
              required=False,
              help='Names of permissions to attach to the policy')
@click.option('--detach_permission', '-d', multiple=True,
              required=False,
              help='Names of permissions to detach from the policy')
@cli_response(attributes_order=attributes_order)
def update(ctx: ContextObj, policy_name, attach_permission,
           detach_permission, customer_id):
    """
    Updates list of permissions attached to the policy.
    """

    if not attach_permission and not detach_permission:
        return ApiResponse.build('Provide either --attach_permission or --detach_permission')

    return ctx.api_client.patch_policy(
        name=policy_name,
        permissions_to_attach=attach_permission,
        permissions_to_detach=detach_permission,
        customer_id=customer_id
    )


@policy.command(cls=ViewCommand, name='delete')
@click.option('--policy_name', '-name', type=str, required=True,
              help='Policy name to delete')
@cli_response()
def delete(ctx: ContextObj, policy_name, customer_id):
    """
    Deletes policy.
    """
    return ctx.api_client.delete_policy(policy_name, customer_id=customer_id)
