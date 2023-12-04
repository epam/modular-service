import click

from group import cli_response, ViewCommand
from service.constants import (
    PARAM_NAME, PARAM_PERMISSIONS, PARAM_ID, CLOUD_PROVIDERS
)


@click.group(name='region')
def region():
    """Manages Region Entity"""


@region.command(cls=ViewCommand, name='describe')
@click.option('--maestro_name', '-n', type=str,
              help='Region name.', required=False)
@cli_response(attributes_order=[PARAM_NAME, PARAM_ID, PARAM_PERMISSIONS])
def describe(maestro_name=None):
    """
    Describes Region.
    """
    from service.initializer import init_configuration
    return init_configuration().region_get(maestro_name=maestro_name)


@region.command(cls=ViewCommand, name='activate')
@click.option('--maestro_name', '-mn', type=str,
              help='Region name.', required=True)
@click.option('--native_name', '-nn', type=str,
              help='Native region name.', required=True)
@click.option('--cloud', '-c', type=click.Choice(CLOUD_PROVIDERS),
              required=True, help='Region cloud')
@click.option('--region_id', '-rid', type=str,
              help='Region id.', required=False)
@cli_response(attributes_order=[PARAM_NAME, PARAM_ID, PARAM_PERMISSIONS])
def activate(maestro_name, native_name, cloud, region_id=None):
    """
    Activates Region.
    """
    from service.initializer import init_configuration
    return init_configuration().region_post(
        maestro_name=maestro_name, native_name=native_name, cloud=cloud,
        region_id=region_id)


@region.command(cls=ViewCommand, name='delete')
@click.option('--maestro_name', '-n', type=str,
              help='Region name.', required=True)
@cli_response(attributes_order=[PARAM_NAME, PARAM_ID, PARAM_PERMISSIONS])
def delete(maestro_name=None):
    """
    Deletes Region.
    """
    from service.initializer import init_configuration
    return init_configuration().region_delete(maestro_name=maestro_name)
