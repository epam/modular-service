from http import HTTPStatus

from routes.route import Route

from commons.constants import (
    Endpoint,
    HTTPMethod,
)
from commons.lambda_response import ResponseFactory, build_response
from commons.log_helper import get_logger
from lambdas.modular_api_handler.processors.abstract_processor import (
    AbstractCommandProcessor,
)
from services import SERVICE_PROVIDER
from services.customer_mutator_service import CustomerMutatorService
from validators.request import CustomerPost, CustomerGet, CustomerPatch
from validators.utils import validate_kwargs
from validators.response import CustomersResponse

_LOG = get_logger(__name__)


class CustomerProcessor(AbstractCommandProcessor):
    def __init__(self, customer_service: CustomerMutatorService):
        self.customer_service = customer_service

    @classmethod
    def build(cls) -> 'CustomerProcessor':
        return cls(
            customer_service=SERVICE_PROVIDER.customer_service
        )

    @classmethod
    def routes(cls) -> tuple[Route, ...]:
        resp = (HTTPStatus.OK, CustomersResponse, None)
        return (
            cls.route(
                Endpoint.CUSTOMERS,
                HTTPMethod.GET,
                'get',
                response=resp
            ),
            cls.route(
                Endpoint.CUSTOMERS,
                HTTPMethod.POST,
                'post',
                response=resp
            ),
            cls.route(
                Endpoint.CUSTOMERS,
                HTTPMethod.PATCH,
                'patch',
                response=resp
            )
        )

    @validate_kwargs
    def get(self, event: CustomerGet):
        _LOG.debug('Describe customer event')

        name = event.name
        if name:
            _LOG.debug(f'Describing customer by name \'{name}\'')
            customers = [self.customer_service.get(name)]
        else:
            _LOG.debug('Describing all customers available')
            customers = self.customer_service.list()

        customers = [item for item in customers if item]
        if not customers:
            _LOG.debug('No customers found matching given query')
            raise ResponseFactory(HTTPStatus.NOT_FOUND).message(
                'No customers found matching given query'
            ).exc()

        _LOG.debug('Extracting customer dto')
        response = [self.customer_service.get_dto(customer=customer)
                    for customer in customers]
        return build_response(content=response)

    @validate_kwargs
    def post(self, event: CustomerPost):

        _LOG.debug(f'Creating customer \'{event.name}\'')
        customer = self.customer_service.create(
            name=event.name,
            display_name=event.display_name,
            admins=event.admins
        )

        _LOG.debug('Saving customer')
        self.customer_service.save(customer=customer)

        _LOG.debug('Extracting customer dto')
        response = self.customer_service.get_dto(customer=customer)

        _LOG.debug(f'Response: {response}')
        return build_response(content=response)

    @validate_kwargs
    def patch(self, event: CustomerPatch):
        _LOG.debug(f'Update customer admins event: {event}')

        name = event.name
        emails = event.admins

        _LOG.debug(f'Describing customer with name \'{name}\'')
        customer = self.customer_service.get(name=name)
        if not customer:
            _LOG.debug(f'Customer with name {name} is not found')
            raise ResponseFactory(HTTPStatus.NOT_FOUND).message(
                f'Customer with name {name} is not found'
            ).exc()

        _LOG.debug(f'Updating customer \'{name}\'')
        self.customer_service.update(
            customer=customer, admins=list(emails), override=event.override
        )

        _LOG.debug('Saving customer')
        self.customer_service.save(customer)

        _LOG.debug('Extracting customer dto')
        response = self.customer_service.get_dto(customer=customer)
        _LOG.debug(f'Response: {response}')

        return build_response(content=response)
