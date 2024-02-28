from http import HTTPStatus

from routes.route import Route

from commons.constants import (
    APPLICATION_ID_ATTR,
    DESCRIPTION_ATTR,
    Endpoint,
    HTTPMethod,
    PARENT_ID_ATTR,
    TYPE_ATTR,
)
from commons.lambda_response import ResponseFactory, build_response
from commons.log_helper import get_logger
from lambdas.modular_api_handler.processors.abstract_processor import (
    AbstractCommandProcessor,
)
from services import SERVICE_PROVIDER
from services.application_mutator_service import ApplicationMutatorService
from services.customer_mutator_service import CustomerMutatorService
from services.parent_mutator_service import ParentMutatorService
from services.tenant_mutator_service import TenantMutatorService
from validators.request import ParentDelete, ParentGet, ParentPatch, ParentPost
from validators.utils import validate_kwargs
from validators.response import ParentsResponse

_LOG = get_logger(__name__)


class ParentProcessor(AbstractCommandProcessor):
    def __init__(self, customer_service: CustomerMutatorService,
                 parent_service: ParentMutatorService,
                 application_service: ApplicationMutatorService,
                 tenant_service: TenantMutatorService):
        self.customer_service = customer_service
        self.parent_service = parent_service
        self.application_service = application_service
        self.tenant_service = tenant_service

    @classmethod
    def build(cls) -> 'ParentProcessor':
        return cls(
            customer_service=SERVICE_PROVIDER.customer_service,
            parent_service=SERVICE_PROVIDER.parent_service,
            application_service=SERVICE_PROVIDER.application_service,
            tenant_service=SERVICE_PROVIDER.tenant_service
        )

    @classmethod
    def routes(cls) -> tuple[Route, ...]:
        resp = (HTTPStatus.OK, ParentsResponse, None)
        return (
            cls.route(
                Endpoint.PARENTS,
                HTTPMethod.GET,
                'get',
                response=resp
            ),
            cls.route(
                Endpoint.PARENTS,
                HTTPMethod.POST,
                'post',
                response=resp
            ),
            cls.route(
                Endpoint.PARENTS,
                HTTPMethod.PATCH,
                'patch',
                response=resp
            ),
            cls.route(
                Endpoint.PARENTS,
                HTTPMethod.DELETE,
                'delete',
                response=resp
            ),
        )

    @validate_kwargs
    def get(self, event: ParentGet):

        parent_id = event.parent_id
        application_id = event.application_id

        if parent_id:
            _LOG.debug(f'Describing parent by id \'{parent_id}\'')
            parents = [self.parent_service.get_parent_by_id(
                parent_id=parent_id)]
        elif application_id:
            _LOG.debug(f'Describing application \'{application_id}\' parents')
            parents = self.parent_service.list_application_parents(
                application_id=application_id,
                only_active=False
            )
        else:
            _LOG.debug('Describing all parents')
            parents = self.parent_service.list()
        parents = [item for item in parents if item]
        if not parents:
            _LOG.warning('No parents found matching given query.')
            raise ResponseFactory(HTTPStatus.NOT_FOUND).message(
                'No parents found matching given query.'
            ).exc()

        _LOG.debug('Describing parent dto.')
        response = [self.parent_service.get_dto(parent=parent)
                    for parent in parents]

        _LOG.debug(f'Response: {response}')
        return build_response(content=response)

    @validate_kwargs
    def post(self, event: ParentPost):

        application_id = event.application_id

        _LOG.debug(f'Describing application by id \'{application_id}\'')
        application = self.application_service.get_application_by_id(
            application_id=application_id
        )
        if not application:
            _LOG.warning(f'Application with id \'{application_id}\' does not '
                         f'exist.')
            raise ResponseFactory(HTTPStatus.NOT_FOUND).message(
                f'Application with id \'{application_id}\' does not exist.'
            ).exc()

        _LOG.debug('Creating parent')
        parent = self.parent_service.create(
            application_id=application_id,
            customer_id=event.customer_id,
            parent_type=event.type.value,
            description=event.description,
            is_deleted=False,
            meta=event.meta,
            scope=event.scope.value,
            tenant_name=event.tenant,
            cloud=event.cloud.value
        )

        _LOG.debug('Saving parent')
        self.parent_service.save(parent=parent)

        _LOG.debug('Describing parent dto.')
        response = self.parent_service.get_dto(parent=parent)
        _LOG.debug(f'Response: {response}')
        return build_response(content=response)

    @validate_kwargs
    def patch(self, event: ParentPatch):
        _LOG.debug(f'Update parent event: {event}')

        # TODO rewrite
        optional_attrs = (APPLICATION_ID_ATTR, TYPE_ATTR, DESCRIPTION_ATTR)
        if not any([attr in event for attr in optional_attrs]):
            _LOG.warning(f'At least one of the following attributes must be '
                         f'specifies: \'{optional_attrs}\'.')
            raise ResponseFactory(HTTPStatus.BAD_REQUEST).message(
                f'At least one of the following attributes must be specifies: \'{optional_attrs}\'.'
            ).exc()

        parent_id = event.get(PARENT_ID_ATTR)

        _LOG.debug(f'Describing parent by id \'{parent_id}\'')
        parent = self.parent_service.get_parent_by_id(
            parent_id=parent_id
        )
        if not parent:
            _LOG.warning(f'Parent with id \'{parent_id}\' does not '
                         f'exist.')
            raise ResponseFactory(HTTPStatus.NOT_FOUND).message(
                f'Parent with id \'{parent_id}\' does not exist.'
            ).exc()
        app_id = event.get(APPLICATION_ID_ATTR)
        parent_type = event.get(TYPE_ATTR)
        description = event.get(DESCRIPTION_ATTR)
        _LOG.debug('Updating parent')
        self.parent_service.update(
            parent=parent, application_id=app_id,
            parent_type=parent_type, description=description
        )

        _LOG.debug('Saving updated parent')
        self.parent_service.save(parent=parent)

        _LOG.debug('Describing parent dto.')
        response = self.parent_service.get_dto(parent=parent)
        _LOG.debug(f'Response: {response}')

        return build_response(content=response)

    @validate_kwargs
    def delete(self, event: ParentDelete):
        _LOG.debug(f'Delete parent event: {event}')

        parent_id = event.parent_id
        _LOG.debug(f'Describing parent by id \'{parent_id}\'')
        parent = self.parent_service.get_parent_by_id(
            parent_id=parent_id
        )
        if not parent:
            _LOG.warning(f'Parent with id \'{parent_id}\' does not '
                         f'exist.')
            raise ResponseFactory(HTTPStatus.NOT_FOUND).message(
                f'Parent with id \'{parent_id}\' does not exist.'
            ).exc()

        _LOG.debug('Deleting parent')
        self.parent_service.mark_deleted(parent=parent)

        _LOG.debug('Saving parent')
        self.parent_service.save(parent=parent)

        _LOG.debug('Describing parent dto.')
        response = self.parent_service.get_dto(parent=parent)

        _LOG.debug(f'Response: {response}')
        return build_response(content=response)
