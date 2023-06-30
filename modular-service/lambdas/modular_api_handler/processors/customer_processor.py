from typing import List

from routes.route import Route

from commons import validate_params, build_response, RESPONSE_OK_CODE, \
    RESPONSE_RESOURCE_NOT_FOUND_CODE
from commons.constants import GET_METHOD, POST_METHOD, PATCH_METHOD, \
    NAME_ATTR, DISPLAY_NAME_ATTR, ADMINS_ATTR, OVERRIDE_ATTR
from commons.log_helper import get_logger
from lambdas.modular_api_handler.processors.abstract_processor import \
    AbstractCommandProcessor
from services import SERVICE_PROVIDER
from services.customer_mutator_service import CustomerMutatorService

_LOG = get_logger(__name__)


class CustomerProcessor(AbstractCommandProcessor):
    def __init__(self, customer_service: CustomerMutatorService):
        self.customer_service = customer_service

    @classmethod
    def build(cls) -> 'CustomerProcessor':
        return cls(
            customer_service=SERVICE_PROVIDER.customer_service()
        )

    @classmethod
    def routes(cls) -> List[Route]:
        name = cls.controller_name()
        return [
            Route(None, '/customers', controller=name, action='get',
                  conditions={'method': [GET_METHOD]}),
            Route(None, '/customers', controller=name, action='post',
                  conditions={'method': [POST_METHOD]}),
            Route(None, '/customers', controller=name, action='patch',
                  conditions={'method': [PATCH_METHOD]}),
        ]

    def get(self, event):
        _LOG.debug(f'Describe customer event')
        name = event.get(NAME_ATTR)

        if name:
            _LOG.debug(f'Describing customer by name \'{name}\'')
            customers = [self.customer_service.get(name)]
        else:
            _LOG.debug(f'Describing all customers available')
            customers = self.customer_service.list()

        customers = [item for item in customers if item]
        if not customers:
            _LOG.debug(f'No customers found matching given query')
            return build_response(
                code=RESPONSE_RESOURCE_NOT_FOUND_CODE,
                content=f'No customers found matching given query'
            )

        _LOG.debug(f'Extracting customer dto')
        response = [self.customer_service.get_dto(customer=customer)
                    for customer in customers]
        _LOG.debug(f'Response: {response}')
        return build_response(
            code=RESPONSE_OK_CODE,
            content=response
        )

    def post(self, event):
        _LOG.debug(f'Add customer event: {event}')
        validate_params(event, (NAME_ATTR, DISPLAY_NAME_ATTR))

        name = event.get(NAME_ATTR)
        display_name = event.get(DISPLAY_NAME_ATTR)
        admins = event.get(ADMINS_ATTR, [])

        _LOG.debug(f'Creating customer \'{name}\'')
        customer = self.customer_service.create(
            name=name,
            display_name=display_name,
            admins=admins
        )

        _LOG.debug(f'Saving customer')
        self.customer_service.save(customer=customer)

        _LOG.debug(f'Extracting customer dto')
        response = self.customer_service.get_dto(customer=customer)

        _LOG.debug(f'Response: {response}')
        return build_response(
            code=RESPONSE_OK_CODE,
            content=response
        )

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
            return build_response(
                code=RESPONSE_RESOURCE_NOT_FOUND_CODE,
                content=f'Customer with name {name} is not found'
            )

        _LOG.debug(f'Updating customer \'{name}\'')
        self.customer_service.update(
            customer=customer, admins=emails, override=override
        )

        _LOG.debug(f'Saving customer')
        self.customer_service.save(customer)

        _LOG.debug(f'Extracting customer dto')
        response = self.customer_service.get_dto(customer=customer)
        _LOG.debug(f'Response: {response}')

        return build_response(
            code=RESPONSE_OK_CODE,
            content=response
        )
