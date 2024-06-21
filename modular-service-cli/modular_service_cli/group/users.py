import click

from modular_service_cli.group import ContextObj, ViewCommand, cli_response


@click.group(name='users')
def users():
    """Manage Modular Service users"""


@users.command(cls=ViewCommand, name='change_password')
@click.option('--password', '-p', type=str,
              required=True, hide_input=True, prompt=True,
              help='New password for your user')
@cli_response()
def change_password(ctx: ContextObj, password, customer_id):
    """
    Changes password for your user
    """
    return ctx.api_client.reset_password(
        new_password=password,
        customer_id=customer_id
    )
