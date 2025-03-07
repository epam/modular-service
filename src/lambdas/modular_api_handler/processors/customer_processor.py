from http import HTTPStatus

from modular_sdk.models.customer import Customer
from routes.route import Route

from commons import NextToken
from commons.constants import Endpoint, HTTPMethod, Permission
from commons.lambda_response import ResponseFactory, build_response
from commons.log_helper import get_logger
from lambdas.modular_api_handler.processors.abstract_processor import (
    AbstractCommandProcessor,
)
from services import SERVICE_PROVIDER
from services.customer_mutator_service import CustomerMutatorService
from validators.request import CustomerPatch, CustomerPost, CustomerQuery, BaseModel
from validators.response import CustomerResponse, CustomersResponse
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
    def routes(cls) -> tuple[Route, ...]:
        return (
            cls.route(
                Endpoint.CUSTOMERS,
                HTTPMethod.GET,
                'query',
                response=(HTTPStatus.OK, CustomersResponse, None),
                description='Currently each user can have only one customer. '
                            'So, generally this endpoint will return a list '
                            'with only one customer (unless you are a system '
                            'user)',
                permission=Permission.CUSTOMER_DESCRIBE
            ),
            cls.route(
                Endpoint.CUSTOMERS_NAME,
                HTTPMethod.GET,
                'get',
                response=(HTTPStatus.OK, CustomerResponse, None),
                permission=Permission.CUSTOMER_DESCRIBE
            ),
            cls.route(
                Endpoint.CUSTOMERS,
                HTTPMethod.POST,
                'post',
                response=(HTTPStatus.OK, CustomerResponse, None),
                permission=Permission.CUSTOMER_CREATE
            ),
            cls.route(
                Endpoint.CUSTOMERS_NAME,
                HTTPMethod.PATCH,
                'patch',
                response=(HTTPStatus.OK, CustomerResponse, None),
                permission=Permission.CUSTOMER_UPDATE
            ),
            cls.route(
                Endpoint.CUSTOMERS_NAME_ACTIVATE,
                HTTPMethod.POST,
                'activate',
                summary='Activates the customer',
                response=(HTTPStatus.OK, CustomerResponse, None),
                permission=Permission.CUSTOMER_ACTIVATE
            ),
            cls.route(
                Endpoint.CUSTOMERS_NAME_DEACTIVATE,
                HTTPMethod.POST,
                'deactivate',
                summary='Deactivates the customer',
                response=(HTTPStatus.OK, CustomerResponse, None),
                permission=Permission.CUSTOMER_DEACTIVATE
            )
        )

    @validate_kwargs
    def query(self, event: CustomerQuery):
        _LOG.debug('Describe customer event')

        cursor = self.customer_service.i_get_customer(
            is_active=event.is_active,
            limit=event.limit,
            name=event.customer_id,
            last_evaluated_key=NextToken.from_input(event.next_token).value,
        )
        items = list(cursor)

        return ResponseFactory().items(
            it=map(self.customer_service.get_dto, items),
            next_token=NextToken(cursor.last_evaluated_key)
        ).build()

    def _get_customer(self, name: str,
                      customer_id: str | None) -> Customer | None:
        """
        Note that name and customer_id are the same logical thing. But name
        is given by user whereas customer_id is retrieved from user's jwt.
        This method should work the same way _get_tenant, and other similar
        methods work in other controllers. But since one user currently can
        have only one customer this method seems strange. I keep it to make
        things more or less similar and consistent. Maybe some day one user
        will be able to have multiple customers. Then the usage of this method
        will be justified
        :param name:
        :param customer_id:
        :return:
        """
        if customer_id and name != customer_id:
            return
        return self.customer_service.get(name)

    @validate_kwargs
    def get(self, event: BaseModel, name: str):
        item = self._get_customer(name, event.customer_id)
        if not item:
            raise ResponseFactory(HTTPStatus.NOT_FOUND).default().exc()
        return build_response(self.customer_service.get_dto(item))

    @validate_kwargs
    def post(self, event: CustomerPost):
        name = event.name
        _LOG.debug(f'Creating customer \'{name}\'')
        existing = self.customer_service.get(name)
        if existing:
            raise ResponseFactory(HTTPStatus.CONFLICT).message(
                f'Customer {name} already exists'
            ).exc()
        customer = self.customer_service.build(
            name=name,
            display_name=event.display_name,
            admins=list(event.admins)
        )

        _LOG.debug('Saving customer')
        self.customer_service.save(customer=customer)
        return build_response(content=self.customer_service.get_dto(customer))

    @validate_kwargs
    def patch(self, event: CustomerPatch, name: str):

        _LOG.debug(f'Describing customer with name \'{name}\'')
        customer = self._get_customer(name, event.customer_id)
        if not customer:
            _LOG.debug(f'Customer with name {name} is not found')
            raise ResponseFactory(HTTPStatus.NOT_FOUND).message(
                f'Customer with name {name} is not found'
            ).exc()
        self.customer_service.update(
            customer=customer,
            actions=[Customer.admins.set(list(event.admins))]
        )

        return build_response(self.customer_service.get_dto(customer))

    @validate_kwargs
    def activate(self, event: BaseModel, name: str):
        customer = self._get_customer(name, event.customer_id)
        if not customer:
            _LOG.debug(f'Customer with name {name} is not found')
            raise ResponseFactory(HTTPStatus.NOT_FOUND).message(
                f'Customer with name {name} is not found'
            ).exc()
        self.customer_service.activate(customer)
        return build_response(self.customer_service.get_dto(customer))

    @validate_kwargs
    def deactivate(self, event: BaseModel, name: str):
        customer = self._get_customer(name, event.customer_id)
        if not customer:
            _LOG.debug(f'Customer with name {name} is not found')
            raise ResponseFactory(HTTPStatus.NOT_FOUND).message(
                f'Customer with name {name} is not found'
            ).exc()
        self.customer_service.deactivate(customer)
        return build_response(self.customer_service.get_dto(customer))
