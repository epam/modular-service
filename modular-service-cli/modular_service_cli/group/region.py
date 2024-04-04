import operator

import click

from modular_service_cli.group import ContextObj, ViewCommand, cli_response
from modular_service_cli.service.constants import Cloud


attributes_order = 'maestro_name', 'native_name', 'cloud', 'is_active'


@click.group(name='region')
def region():
    """Manages Region Entity"""


@region.command(cls=ViewCommand, name='describe')
@click.option('--maestro_name', '-n', type=str,
              help='Region name.', required=False)
@cli_response(attributes_order=attributes_order)
def describe(ctx: ContextObj, maestro_name, customer_id):
    """
    Describes Region.
    """
    if maestro_name:
        return ctx.api_client.get_region(maestro_name)
    return ctx.api_client.query_regions()


@region.command(cls=ViewCommand, name='activate')
@click.option('--maestro_name', '-mn', type=str,
              help='Region name.', required=True)
@click.option('--native_name', '-nn', type=str,
              help='Native region name.', required=True)
@click.option('--cloud', '-c', type=click.Choice(tuple(map(operator.attrgetter('value'), Cloud))),
              required=True, help='Region cloud')
@click.option('--region_id', '-rid', type=str,
              help='Region id.', required=False)
@cli_response(attributes_order=attributes_order)
def activate(ctx: ContextObj, maestro_name, native_name, cloud, region_id, 
             customer_id):
    """
    Activates Region.
    """
    return ctx.api_client.create_region(
        maestro_name=maestro_name,
        native_name=native_name,
        cloud=cloud,
        region_id=region_id
    )


@region.command(cls=ViewCommand, name='delete')
@click.option('--maestro_name', '-n', type=str,
              help='Region name.', required=True)
@cli_response(attributes_order=attributes_order)
def delete(ctx: ContextObj, maestro_name, customer_id):
    """
    Deletes Region.
    """
    return ctx.api_client.delete_region(maestro_name)
