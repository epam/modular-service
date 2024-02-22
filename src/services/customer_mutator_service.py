from commons.log_helper import get_logger
from modular_sdk.commons import ModularException, RESPONSE_BAD_REQUEST_CODE
from modular_sdk.models.customer import Customer
from modular_sdk.services.customer_service import CustomerService

_LOG = get_logger(__name__)


class CustomerMutatorService(CustomerService):

    def create(self, name: str, display_name: str, admins: list):
        _LOG.debug(f'Checking if customer with name \'{name}\' exist')
        existing_customer = self.get(name=name)
        if existing_customer:
            _LOG.debug(f'Customer with name \'{name}\' already exist')
            raise ModularException(
                code=RESPONSE_BAD_REQUEST_CODE,
                content=f'Customer with name {name} already exists'
            )
        _LOG.debug(f'Creating customer with name \'{name}\', '
                   f'display_name \'{display_name}\' '
                   f'and admins \'{admins}\'')
        return Customer(name=name, display_name=display_name,
                        admins=admins)

    @staticmethod
    def update(customer: Customer, admins: list, override=False):
        if override:
            _LOG.debug(f'Overriding customer admins to \'{admins}\'')
            customer.admins = list(admins)
        else:
            if not customer.admins:
                customer.admins = []
            _LOG.debug(f'Adding new admins to customer \'{admins}\'')
            customer.admins = list(
                {*customer.admins, *admins})

    @staticmethod
    def save(customer: Customer):
        customer.save()
