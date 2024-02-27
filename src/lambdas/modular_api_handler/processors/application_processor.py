from http import HTTPStatus

from routes.route import Route

from commons import NextToken
from commons.constants import (
    APPLICATION_ID_ATTR,
    CUSTOMER_ID_ATTR,
    DESCRIPTION_ATTR,
    Endpoint,
    HTTPMethod,
    TYPE_ATTR,
)
from commons.lambda_response import ResponseFactory, build_response
from commons.log_helper import get_logger
from lambdas.modular_api_handler.processors.abstract_processor import (
    AbstractCommandProcessor,
)
from commons.abstract_lambda import ProcessedEvent
from modular_sdk.commons.constants import ApplicationType
from modular_sdk.services.impl.maestro_credentials_service import AWSRoleApplicationMeta
from services import SERVICE_PROVIDER
from services.application_mutator_service import ApplicationMutatorService
from services.customer_mutator_service import CustomerMutatorService
from services.parent_mutator_service import ParentMutatorService
from validators.request import (
    ApplicationDelete,
    ApplicationQuery,
    ApplicationPatch,
    ApplicationPostAWSRole
)
from validators.response import ApplicationsResponse, MessageModel
from validators.utils import validate_kwargs

_LOG = get_logger(__name__)


class ApplicationProcessor(AbstractCommandProcessor):
    def __init__(self, application_service: ApplicationMutatorService,
                 customer_service: CustomerMutatorService,
                 parent_service: ParentMutatorService):
        self.application_service = application_service
        self.customer_service = customer_service
        self.parent_service = parent_service

    @classmethod
    def routes(cls) -> tuple[Route, ...]:
        return (
            cls.route(
                Endpoint.APPLICATIONS_AWS_ROLE,
                HTTPMethod.POST,
                'post_aws_role',
                summary='Create application with type AWS_ROLE',
                response=(HTTPStatus.CREATED, None, None)
            ),
            cls.route(
                Endpoint.APPLICATIONS_AWS_CREDENTIALS,
                HTTPMethod.POST,
                'post_aws_credentials',
                summary='Create application with type AWS_CREDENTIALS',
                response=(HTTPStatus.CREATED, None, None)
            ),
            cls.route(
                Endpoint.APPLICATIONS,
                HTTPMethod.GET,
                'query',
                response=(HTTPStatus.OK, ApplicationsResponse, None)
            ),
            cls.route(
                Endpoint.APPLICATIONS,
                HTTPMethod.PATCH,
                'patch',
                response=(HTTPStatus.OK, ApplicationsResponse, None)
            ),
            cls.route(
                Endpoint.APPLICATIONS,
                HTTPMethod.DELETE,
                'delete',
                summary='Marks an application as removed',
                response=(HTTPStatus.OK, MessageModel, None),
            )
        )

    @classmethod
    def build(cls) -> 'ApplicationProcessor':
        return cls(
            application_service=SERVICE_PROVIDER.application_service,
            customer_service=SERVICE_PROVIDER.customer_service,
            parent_service=SERVICE_PROVIDER.parent_service
        )

    @validate_kwargs
    def post_aws_role(self, event: ApplicationPostAWSRole,
                      _processed_event: ProcessedEvent):
        meta = AWSRoleApplicationMeta(
            roleName=event.role_name,
            accountNumber=event.account_id
        )

        app = self.application_service.build(
            customer_id=event.customer_id,
            type=ApplicationType.AWS_ROLE.value,
            description=event.description,
            is_deleted=False,
            meta=meta.dict(),
            created_by=_processed_event['cognito_user_id']
        )
        _LOG.debug('Saving application')
        self.application_service.save(app)

        return build_response(content=self.application_service.get_dto(app))

    def post_aws_credentials(self):
        pass

    @validate_kwargs
    def query(self, event: ApplicationQuery):
        cursor = self.application_service.list(
            customer=event.customer_id,
            _type=event.type.value if event.type else None,
            deleted=event.is_deleted,
            limit=event.limit,
            last_evaluated_key=NextToken.from_input(event.next_token).value,
        )
        items = list(cursor)

        return ResponseFactory().items(
            it=map(self.application_service.get_dto, items),
            next_token=NextToken(cursor.last_evaluated_key)
        ).build()

    @validate_kwargs
    def patch(self, event: ApplicationPatch):
        # TODO rewrite
        _LOG.debug(f'Update application event: {event}')

        validate_params(event, (APPLICATION_ID_ATTR,))
        # TODO rewrite

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

    @validate_kwargs
    def delete(self, event: ApplicationDelete):

        application_id = event.application_id
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
        return build_response(
            content=f'Application with id \'{application_id}\' has been deleted.')
