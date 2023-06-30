from typing import List

from routes.route import Route

from commons import RESPONSE_BAD_REQUEST_CODE, validate_params, build_response, \
    RESPONSE_RESOURCE_NOT_FOUND_CODE, \
    RESPONSE_OK_CODE
from commons.constants import GET_METHOD, POST_METHOD, PATCH_METHOD, \
    DELETE_METHOD, APPLICATION_ID_ATTR, TYPE_ATTR, DESCRIPTION_ATTR, \
    PARENT_ID_ATTR, CUSTOMER_ID_ATTR
from commons.log_helper import get_logger
from lambdas.modular_api_handler.processors.abstract_processor import \
    AbstractCommandProcessor
from services import SERVICE_PROVIDER
from services.application_mutator_service import ApplicationMutatorService
from services.customer_mutator_service import CustomerMutatorService
from services.parent_mutator_service import ParentMutatorService
from services.tenant_mutator_service import TenantMutatorService

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
            customer_service=SERVICE_PROVIDER.customer_service(),
            parent_service=SERVICE_PROVIDER.parent_service(),
            application_service=SERVICE_PROVIDER.application_service(),
            tenant_service=SERVICE_PROVIDER.tenant_service()
        )

    @classmethod
    def routes(cls) -> List[Route]:
        name = cls.controller_name()
        return [
            Route(None, '/parents', controller=name, action='get',
                  conditions={'method': [GET_METHOD]}),
            Route(None, '/parents', controller=name, action='post',
                  conditions={'method': [POST_METHOD]}),
            Route(None, '/parents', controller=name, action='patch',
                  conditions={'method': [PATCH_METHOD]}),
            Route(None, '/parents', controller=name, action='delete',
                  conditions={'method': [DELETE_METHOD]}),
        ]

    def get(self, event):
        _LOG.debug(f'Describe parent event: {event}')

        parent_id = event.get(PARENT_ID_ATTR)
        application_id = event.get(APPLICATION_ID_ATTR)

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
            _LOG.debug(f'Describing all parents')
            parents = self.parent_service.list()
        parents = [item for item in parents if item]
        if not parents:
            _LOG.error(f'No parents found matching given query.')
            return build_response(
                code=RESPONSE_RESOURCE_NOT_FOUND_CODE,
                content=f'No parents found matching given query.'
            )

        _LOG.debug(f'Describing parent dto.')
        response = [self.parent_service.get_dto(parent=parent)
                    for parent in parents]

        _LOG.debug(f'Response: {response}')
        return build_response(
            code=RESPONSE_OK_CODE,
            content=response
        )

    def post(self, event):
        _LOG.debug(f'Add parent event: {event}')
        validate_params(event, (APPLICATION_ID_ATTR, TYPE_ATTR,
                                CUSTOMER_ID_ATTR))

        application_id = event.get(APPLICATION_ID_ATTR)

        _LOG.debug(f'Describing application by id \'{application_id}\'')
        application = self.application_service.get_application_by_id(
            application_id=application_id
        )
        if not application:
            _LOG.error(f'Application with id \'{application_id}\' does not '
                       f'exist.')
            return build_response(
                code=RESPONSE_RESOURCE_NOT_FOUND_CODE,
                content=f'Application with id \'{application_id}\' does not '
                        f'exist.'
            )

        parent_type = event.get(TYPE_ATTR)
        description = event.get(DESCRIPTION_ATTR)
        customer_id = event.get(CUSTOMER_ID_ATTR)

        _LOG.debug(f'Creating parent')
        parent = self.parent_service.create(
            application_id=application_id,
            customer_id=customer_id,
            parent_type=parent_type,
            description=description,
            is_deleted=False
        )

        _LOG.debug(f'Saving parent')
        self.parent_service.save(parent=parent)

        _LOG.debug(f'Describing parent dto.')
        response = self.parent_service.get_dto(parent=parent)
        _LOG.debug(f'Response: {response}')
        return build_response(
            code=RESPONSE_OK_CODE,
            content=response
        )

    def patch(self, event):
        _LOG.debug(f'Update parent event: {event}')
        validate_params(event, (PARENT_ID_ATTR,))

        optional_attrs = (APPLICATION_ID_ATTR, TYPE_ATTR, DESCRIPTION_ATTR)
        if not any([attr in event for attr in optional_attrs]):
            _LOG.error(f'At least one of the following attributes must be '
                       f'specifies: \'{optional_attrs}\'.')
            return build_response(
                code=RESPONSE_BAD_REQUEST_CODE,
                content=f'At least one of the following attributes must be '
                        f'specifies: \'{optional_attrs}\'.'
            )

        parent_id = event.get(PARENT_ID_ATTR)

        _LOG.debug(f'Describing parent by id \'{parent_id}\'')
        parent = self.parent_service.get_parent_by_id(
            parent_id=parent_id
        )
        if not parent:
            _LOG.error(f'Parent with id \'{parent_id}\' does not '
                       f'exist.')
            return build_response(
                code=RESPONSE_RESOURCE_NOT_FOUND_CODE,
                content=f'Parent with id \'{parent_id}\' does not '
                        f'exist.'
            )
        app_id = event.get(APPLICATION_ID_ATTR)
        parent_type = event.get(TYPE_ATTR)
        description = event.get(DESCRIPTION_ATTR)
        _LOG.debug(f'Updating parent')
        self.parent_service.update(
            parent=parent, application_id=app_id,
            parent_type=parent_type, description=description
        )

        _LOG.debug(f'Saving updated parent')
        self.parent_service.save(parent=parent)

        _LOG.debug(f'Describing parent dto.')
        response = self.parent_service.get_dto(parent=parent)
        _LOG.debug(f'Response: {response}')

        return build_response(
            code=RESPONSE_OK_CODE,
            content=response
        )

    def delete(self, event):
        _LOG.debug(f'Delete parent event: {event}')
        validate_params(event, (PARENT_ID_ATTR,))

        parent_id = event.get(PARENT_ID_ATTR)
        _LOG.debug(f'Describing parent by id \'{parent_id}\'')
        parent = self.parent_service.get_parent_by_id(
            parent_id=parent_id
        )
        if not parent:
            _LOG.error(f'Parent with id \'{parent_id}\' does not '
                       f'exist.')
            return build_response(
                code=RESPONSE_RESOURCE_NOT_FOUND_CODE,
                content=f'Parent with id \'{parent_id}\' does not '
                        f'exist.'
            )

        _LOG.debug(f'Deleting parent')
        self.parent_service.mark_deleted(parent=parent)

        _LOG.debug(f'Saving parent')
        self.parent_service.save(parent=parent)

        _LOG.debug(f'Describing parent dto.')
        response = self.parent_service.get_dto(parent=parent)

        _LOG.debug(f'Response: {response}')
        return build_response(
            code=RESPONSE_OK_CODE,
            content=response
        )
