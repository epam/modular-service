import os


class EnvironmentService:

    @staticmethod
    def aws_region():
        return os.environ.get('AWS_REGION')

    @staticmethod
    def is_docker():
        return os.environ.get('service_mode') == 'docker'

    @staticmethod
    def get_user_pool_name():
        return os.environ.get('cognito_user_pool_name')

    @staticmethod
    def get_user_pool_id():
        return os.environ.get('user_pool_id')
