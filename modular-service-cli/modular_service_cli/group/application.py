import json
import operator

import click

from modular_service_cli.group import (
    ApiResponse,
    ContextObj,
    ViewCommand,
    build_limit_option,
    build_next_token_option,
    cli_response,
)
from modular_service_cli.service.constants import ApplicationType

attributes_order = 'application_id', 'type', 'description',


@click.group(name='application')
def application():
    """Manages Application Entity"""


@application.command(cls=ViewCommand, name='describe')
@click.option('--application_id', '-aid', type=str,
              help='Application id to describe.')
@build_limit_option()
@build_next_token_option()
@click.option('--type', '-t',
              type=click.Choice(tuple(map(operator.attrgetter('value'), ApplicationType))),
              help='Application type to filter applications')
@cli_response(attributes_order=attributes_order)
def describe(ctx: ContextObj, application_id, limit, next_token, type,
             customer_id):
    """
    Describes Application.
    """
    if application_id:
        return ctx.api_client.get_application(application_id,
                                              customer_id=customer_id)
    return ctx.api_client.query_application(
        customer_id=customer_id,
        limit=limit,
        next_token=next_token,
        type=type
    )


@application.command(cls=ViewCommand, name='create_aws_role')
@click.option('--role_name', '-rn', type=str, required=True,
              help='AWS Role name')
@click.option('--account_id', '-aid', type=str, required=True,
              help='AWS Account id.')
@click.option('--description', '-d', type=str, required=True,
              help='Application description.')
@cli_response(attributes_order=attributes_order)
def create_aws_role(ctx: ContextObj, role_name, account_id, description,
                    customer_id):
    """
    Creates Application with type AWS_ROLE
    """
    return ctx.api_client.create_application_aws_role(
        description=description,
        role_name=role_name,
        account_id=account_id,
        customer_id=customer_id
    )


@application.command(cls=ViewCommand, name='create_aws_credentials')
@click.option('--access_key_id', '-ak', type=str, required=True,
              help='AWS Access key')
@click.option('--secret_access_key', '-sk', type=str, required=True,
              help='AWS Secret Access key')
@click.option('--session_token', '-st', type=str, required=False,
              help='AWS Session token key')
@click.option('--default_region', '-dr', type=str, default='us-east-1',
              help='AWS region to use by default')
@click.option('--description', '-d', type=str, required=True,
              help='Application description.')
@cli_response(attributes_order=attributes_order)
def create_aws_credentials(ctx: ContextObj, **kwargs):
    """
    Creates Application with type AWS_CREDENTIALS
    """
    return ctx.api_client.create_application_aws_credentials(**kwargs)


@application.command(cls=ViewCommand, name='create_azure_credentials')
@click.option('--client_id', '-cid', type=str, required=True,
              help='AZURE Client id')
@click.option('--tenant_id', '-tid', type=str, required=True,
              help='AZURE Tenant id')
@click.option('--api_key', '-ak', type=str, required=True,
              help='AZURE api key')
@click.option('--description', '-d', type=str, required=True,
              help='Application description.')
@cli_response(attributes_order=attributes_order)
def create_azure_credentials(ctx: ContextObj, **kwargs):
    """
    Creates Application with type AZURE_CREDENTIALS
    """
    return ctx.api_client.create_application_azure_credentials(**kwargs)


@application.command(cls=ViewCommand, name='create_azure_certificate')
@click.option('--client_id', '-cid', type=str, required=True,
              help='AZURE Client id')
@click.option('--tenant_id', '-tid', type=str, required=True,
              help='AZURE Tenant id')
@click.option('--certificate', '-cert', type=str, required=True,
              help='Base64 encoded azure certificate')
@click.option('--password', '-p', type=str, required=False,
              help='Password from the certificate')
@click.option('--description', '-d', type=str, required=True,
              help='Application description.')
@cli_response(attributes_order=attributes_order)
def create_azure_certificate(ctx: ContextObj, **kwargs):
    """
    Creates Application with type AZURE_CERTIFICATE
    """
    return ctx.api_client.create_application_azure_certificate(**kwargs)


@application.command(cls=ViewCommand, name='create_gcp_service_account')
@click.option('--path', '-p', type=str, required=True,
              help='Path to JSON file with GCP service account creds')
@click.option('--description', '-d', type=str, required=True,
              help='Application description.')
@cli_response(attributes_order=attributes_order)
def create_gcp_service_account(ctx: ContextObj, path, description,
                               customer_id):
    """
    Creates Application with type GCP_SERVICE_ACCOUNT
    """
    try:
        with open(path, 'r') as fp:
            data = json.load(fp)
    except FileNotFoundError:
        return ApiResponse.build(f'File {path} not found')
    except json.JSONDecodeError:
        return ApiResponse.build(f'File {path} contains invalid JSON')
    except Exception:
        return ApiResponse.build(f'Could not load file {path}')
    return ctx.api_client.create_application_gcp_service_account(
        description=description,
        customer_id=customer_id,
        credentials=data
    )


@application.command(cls=ViewCommand, name='update')
@click.option('--application_id', '-aid', type=str, required=True,
              help='Application id to update')
@click.option('--description', '-d', type=str, required=True,
              help='Application description.')
@cli_response(attributes_order=attributes_order)
def update(ctx: ContextObj, application_id, description, customer_id):
    """
    Updates Application.
    """
    return ctx.api_client.patch_application(
        id=application_id,
        description=description,
        customer_id=customer_id
    )


@application.command(cls=ViewCommand, name='delete')
@click.option('--application_id', '-aid', type=str, required=True,
              help='Application id to describe.')
@cli_response()
def deactivate(ctx: ContextObj, application_id, customer_id):
    """
    Deactivates Application.
    """
    return ctx.api_client.delete_application(
        id=application_id,
        customer_id=customer_id
    )
