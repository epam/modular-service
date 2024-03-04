import click

from modular_service_cli.group import ViewCommand, cli_response


@click.group(name='mode')
def mode():
    """
    Describes component operation mode
    """


@mode.command(cls=ViewCommand, name='get_mode')
@click.option('--application', '-app',
              type=str,
              help='Application name. If not specified - application name will '
                   'be retrieved from environment variable "application_name"')
@cli_response(check_api_adapter=False)
def get_mode(application):
    """
    Describes mode of the particular application
    """
    try:
        from modular_sdk.utils.operation_mode.generic import \
            ModularOperationModeManagerService
        return ModularOperationModeManagerService().get_mode(
            application_name=application)
    except ModuleNotFoundError:
        return {'message': "Not available in standalone mode"}
