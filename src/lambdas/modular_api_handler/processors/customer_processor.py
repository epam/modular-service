from http import HTTPStatus

from routes.route import Route

from commons import validate_params
from commons.constants import (
    ADMINS_ATTR,
    Endpoint,
    HTTPMethod,
    NAME_ATTR,
    OVERRIDE_ATTR,
)
from commons.lambda_response import ResponseFactory, build_response
from commons.log_helper import get_logger
from lambdas.modular_api_handler.processors.abstract_processor import (
    AbstractCommandProcessor,
)
from services import SERVICE_PROVIDER
from services.customer_mutator_service import CustomerMutatorService
from validators.request import CustomerPost
from validators.utils import validate_kwargs

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
    def routes(cls) -> list[Route]:
        name = cls.controller_name()
        endpoint = Endpoint.CUSTOMERS.value
        return [
            Route(None, endpoint, controller=name, action='get',
                  conditions={'method': [HTTPMethod.GET]}),
            Route(None, endpoint, controller=name, action='post',
                  conditions={'method': [HTTPMethod.POST]}),
            Route(None, endpoint, controller=name, action='patch',
                  conditions={'method': [HTTPMethod.PATCH]}),
        ]

    def get(self, event):
        _LOG.debug('Describe customer event')
        name = event.get(NAME_ATTR)

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
        _LOG.debug(f'Response: {response}')
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

    def patch(self, event):
        _LOG.debug(f'Update customer admins event: {event}')
        validate_params(event, (NAME_ATTR, ADMINS_ATTR))

        name = event.get(NAME_ATTR)
        emails = event.get(ADMINS_ATTR)
        override = event.get(OVERRIDE_ATTR)
        if not isinstance(override, bool):
            override = True if override.lower() in ('true', 'y', 'yes') \
                else False

        _LOG.debug(f'Describing customer with name \'{name}\'')
        customer = self.customer_service.get(name=name)
        if not customer:
            _LOG.debug(f'Customer with name {name} is not found')
            raise ResponseFactory(HTTPStatus.NOT_FOUND).message(
                f'Customer with name {name} is not found'
            ).exc()

        _LOG.debug(f'Updating customer \'{name}\'')
        self.customer_service.update(
            customer=customer, admins=emails, override=override
        )

        _LOG.debug('Saving customer')
        self.customer_service.save(customer)

        _LOG.debug('Extracting customer dto')
        response = self.customer_service.get_dto(customer=customer)
        _LOG.debug(f'Response: {response}')

        return build_response(content=response)
