from abc import abstractmethod
from typing import Optional

from commons.constants import (
    PARAM_HTTP_METHOD, PARAM_REQUEST_CONTEXT, PARAM_RESOURCE_PATH,
    PARAM_COGNITO_USERNAME, PARAM_AUTHORIZER, PARAM_CLAIMS
)
from commons.log_helper import get_logger
from commons import (
    build_response, RESPONSE_BAD_REQUEST_CODE, RESPONSE_FORBIDDEN_CODE,
    ApplicationException, RESPONSE_INTERNAL_SERVER_ERROR
)
from services import SERVICE_PROVIDER


from commons import LambdaContext, deep_get, reformat_request_path, secure_event
from services.rbac.endpoint_to_permission_mapping import (
    ENDPOINT_PERMISSION_MAPPING
)

_LOG = get_logger('abstract-api-handler-lambda')


class AbstractApiHandlerLambda:

    @abstractmethod
    def validate_request(self, event: dict) -> dict:
        """
        Validates event attributes
        :param event: lambda incoming event
        :return: dict with attribute_name in key and error_message in value
        """
        pass

    @abstractmethod
    def handle_request(self, event: dict, context: LambdaContext) -> dict:
        """
        Inherited lambda function code
        :param event: lambda event
        :param context: lambda context
        :return:
        """
        pass

    def lambda_handler(self, event: dict, context: LambdaContext) -> dict:
        try:
            _LOG.debug(f'Request: {secure_event(event)}')

            _LOG.debug('Checking user permissions')

            user_id = deep_get(
                event, (PARAM_REQUEST_CONTEXT, PARAM_AUTHORIZER,
                        PARAM_CLAIMS, PARAM_COGNITO_USERNAME)
            )
            request_path = deep_get(
                event, (PARAM_REQUEST_CONTEXT, PARAM_RESOURCE_PATH)
            )
            http_method = deep_get(
                event, (PARAM_REQUEST_CONTEXT, PARAM_HTTP_METHOD)
            )

            _service = SERVICE_PROVIDER.access_control_service()

            target_permission = self._get_target_permission(event)
            if not target_permission:  # required to access signup/signin
                _LOG.debug(
                    f'No permissions provided for the given endpoint: '
                    f'{request_path} and method: {http_method}'
                )
            elif not _service.is_allowed_to_access(event, target_permission):
                _LOG.debug(
                    f'User \'{user_id}\' is not allowed to access the '
                    f'resource: {request_path}'
                )
                return build_response(
                    code=RESPONSE_FORBIDDEN_CODE,
                    content=f'You are not allowed to access the resource '
                            f'{target_permission}'
                )

            errors = self.validate_request(event)
            if errors:
                return build_response(
                    code=RESPONSE_BAD_REQUEST_CODE,
                    content=errors
                )

            execution_result = self.handle_request(event, context)
            _LOG.debug(f'Response: {secure_event(execution_result)}')
            return execution_result
        except ApplicationException as e:
            _LOG.error(
                f'Error occurred; Event: {secure_event(event)}; Error: {e}'
            )
            return build_response(
                code=e.code,
                content=e.content
            )
        except Exception as e:
            _LOG.error(
                f'Unexpected error occurred; Event: {secure_event(event)}; '
                f'Error: {e}'
            )
            return build_response(
                code=RESPONSE_INTERNAL_SERVER_ERROR,
                content='Internal server error'
            )

    @staticmethod
    def _get_target_permission(event: dict) -> Optional[str]:
        request_path = deep_get(
            event, (PARAM_REQUEST_CONTEXT, PARAM_RESOURCE_PATH)
        )
        http_method = deep_get(
            event, (PARAM_REQUEST_CONTEXT, PARAM_HTTP_METHOD)
        )

        request_path = reformat_request_path(request_path)

        target_permission = deep_get(
            ENDPOINT_PERMISSION_MAPPING, (request_path, http_method)
        )

        return target_permission
