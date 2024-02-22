from http import HTTPStatus

from routes.route import Route

from commons import validate_params
from commons.constants import (
    APPLICATION_ID_ATTR,
    CUSTOMER_ID_ATTR,
    DESCRIPTION_ATTR,
    Endpoint,
    HTTPMethod,
    META_ATTR,
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

_LOG = get_logger(__name__)


class ApplicationProcessor(AbstractCommandProcessor):
    def __init__(self, application_service: ApplicationMutatorService,
                 customer_service: CustomerMutatorService,
                 parent_service: ParentMutatorService):
        self.application_service = application_service
        self.customer_service = customer_service
        self.parent_service = parent_service

    @classmethod
    def routes(cls) -> list[Route]:
        name = cls.controller_name()
        endpoint = Endpoint.APPLICATIONS.value
        return [
            Route(None, endpoint, controller=name, action='get',
                  conditions={'method': [HTTPMethod.GET]}),
            Route(None, endpoint, controller=name, action='post',
                  conditions={'method': [HTTPMethod.POST]}),
            Route(None, endpoint, controller=name, action='patch',
                  conditions={'method': [HTTPMethod.PATCH]}),
            Route(None, endpoint, controller=name, action='delete',
                  conditions={'method': [HTTPMethod.DELETE]},
                  description='Marks an applications as removed application'),
        ]

    @classmethod
    def build(cls) -> 'ApplicationProcessor':
        return cls(
            application_service=SERVICE_PROVIDER.application_service,
            customer_service=SERVICE_PROVIDER.customer_service,
            parent_service=SERVICE_PROVIDER.parent_service
        )

    def get(self, event):
        _LOG.debug(f'Describe application event: {event}')

        application_id = event.get(APPLICATION_ID_ATTR)

        if application_id:
            _LOG.debug(f'Describing application with id \'{application_id}\'')
            applications = [self.application_service.get_application_by_id(
                application_id=application_id)]
        else:
            _LOG.debug('Describing all applications available')
            applications = self.application_service.list()

        applications = [item for item in applications if item]
        if not applications:
            _LOG.warning('No application found matching given query')
            raise ResponseFactory(HTTPStatus.NOT_FOUND).message(
                'No application found matching given query'
            ).exc()

        _LOG.debug('Extracting application dto')
        response = [self.application_service.get_dto(app) for app
                    in applications]
        _LOG.debug(f'Response: {response}')

        return build_response(content=response)

    def post(self, event):
        _LOG.debug(f'Activate application event: {event}')

        validate_params(event, (TYPE_ATTR, CUSTOMER_ID_ATTR))

        app_type = event.get(TYPE_ATTR)
        customer_id = event.get(CUSTOMER_ID_ATTR)
        description = event.get(DESCRIPTION_ATTR)
        meta = event.get(META_ATTR)

        _LOG.debug('Creating application')
        application = self.application_service.create(
            customer_id=customer_id,
            type=app_type,
            description=description,
            is_deleted=False,
            meta=meta
        )
        _LOG.debug('Saving application')
        self.application_service.save(application)

        _LOG.debug('Extracting application dto')
        application_dto = self.application_service.get_dto(application)

        _LOG.debug(f'Response: {application_dto}')
        return build_response(content=application_dto)

    def patch(self, event):
        _LOG.debug(f'Update application event: {event}')

        validate_params(event, (APPLICATION_ID_ATTR,))

        optional_attrs = (TYPE_ATTR, CUSTOMER_ID_ATTR, DESCRIPTION_ATTR)
        if not any([attr in event for attr in optional_attrs]):
            _LOG.error(f'At least one of the following attributes must be '
                       f'specified: \'{optional_attrs}\'')
            raise ResponseFactory(HTTPStatus.BAD_REQUEST).message(
                f'At least one of the following attributes must be specified: \'{optional_attrs}\''
            ).exc()

        application_id = event.get(APPLICATION_ID_ATTR)
        application = self.application_service.get_application_by_id(
            application_id=application_id)
        if not application:
            _LOG.error(f'Application with id \'{application_id}\' does not '
                       f'exist.')
            raise ResponseFactory(HTTPStatus.NOT_FOUND).message(
                f'Application with id \'{application_id}\' does not exist.'
            ).exc()

        app_type = event.get(TYPE_ATTR)
        customer_id = event.get(CUSTOMER_ID_ATTR)
        description = event.get(DESCRIPTION_ATTR)

        _LOG.debug('Updating application')
        self.application_service.update(
            application=application,
            application_type=app_type,
            customer_id=customer_id,
            description=description
        )

        _LOG.debug('Saving application')
        self.application_service.save(application=application)

        _LOG.debug('Extracting application dto')
        response = self.application_service.get_dto(application=application)
        _LOG.debug(f'Response: {response}')
        return build_response(content=response)

    def delete(self, event):
        _LOG.debug(f'Delete application event: {event}')

        validate_params(event, (APPLICATION_ID_ATTR,))

        application_id = event.get(APPLICATION_ID_ATTR)
        application = self.application_service.get_application_by_id(
            application_id=application_id)
        if not application:
            _LOG.error(f'Application with id \'{application_id}\' does not '
                       f'exist.')
            raise ResponseFactory(HTTPStatus.NOT_FOUND).message(
                f'Application with id \'{application_id}\' does not exist.'
            ).exc()

        _LOG.debug(f'Deleting application \'{application_id}\'')
        self.application_service.mark_deleted(
            application=application
        )

        _LOG.debug('Saving application')
        self.application_service.save(application)

        _LOG.info(f'Application with id \'{application_id}\' has been '
                  f'deleted.')
        return build_response(content=f'Application with id \'{application_id}\' has been deleted.')
