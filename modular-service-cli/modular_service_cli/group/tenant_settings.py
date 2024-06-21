import json

import click

from modular_service_cli.group import (
    ApiResponse,
    ContextObj,
    ViewCommand,
    build_limit_option,
    build_next_token_option,
    cli_response,
)

attributes_order = 'key', 'value', 'tenant_name'


@click.group(name='settings')
def settings():
    """Manages Tenant Setting Entity"""


@settings.command(cls=ViewCommand, name='describe')
@click.option('--tenant_name', '-name', type=str, required=True,
              help='Tenant name to describe.')
@build_limit_option()
@build_next_token_option()
@click.option('--key', '-k', type=str, required=False,
              help='Setting key to filter based on')
@cli_response(attributes_order=attributes_order)
def describe(ctx: ContextObj, tenant_name, limit, next_token, key,
             customer_id):
    """
    Describes Tenant settings
    """
    return ctx.api_client.get_tenant_settings(
        name=tenant_name,
        limit=limit,
        next_token=next_token,
        key=key,
        customer_id=customer_id
    )


@settings.command(cls=ViewCommand, name='put')
@click.option('--tenant_name', '-tn', type=str, required=True,
              help='Tenant name to activate.')
@click.option('--key', '-k', type=str, required=True,
              help='Setting key to filter based on')
@click.option('--value', '-v', type=str, required=True,
              help='Path to a JSON file that contains setting value')
@cli_response(attributes_order=attributes_order)
def put(ctx: ContextObj, tenant_name, key, value):
    """
    Set tenant setting
    """
    try:
        with open(value, 'r') as fp:
            data = json.load(fp)
    except FileNotFoundError:
        return ApiResponse.build(f'File {value} not found')
    except json.JSONDecodeError:
        return ApiResponse.build(f'File {value} contains invalid JSON')
    except Exception:
        return ApiResponse.build(f'Could not load file {value}')
    return ctx.api_client.put_tenant_settings(
        name=tenant_name,
        key=key,
        value=data
    )
