import operator

import click

from modular_service_cli.group import (
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
              type=click.Choice(map(operator.attrgetter('value'), ApplicationType)), 
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


# @application.command(cls=ViewCommand, name='add')
# @click.option('--application_type', '-at',
#               type=click.Choice(AVAILABLE_APPLICATION_TYPES),
#               required=True, help='Application type')
# @click.option('--customer', '-c', type=str, required=True,
#               help='Customer name to link application')
# @click.option('--description', '-d', type=str, required=True,
#               help='Application description.')
# @click.option('--meta', default=None, help='Application meta JSON string.')
# @cli_response(attributes_order=[PARAM_NAME, PARAM_ID, PARAM_PERMISSIONS])
# def add(application_type, customer, description=None, meta=None):
#     """
#     Describes Application.
#     """
#     from service.initializer import init_configuration
#     return init_configuration().application_post(
#         application_type=application_type,
#         customer_id=customer,
#         description=description,
#         meta=meta)


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
