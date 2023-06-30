import os
from pathlib import Path

import requests
import yaml

from service.logger import get_logger, get_user_logger

SYSTEM_LOG = get_logger('modular_service_admin_cli.service.config')
USER_LOG = get_user_logger('user')

HOME_FOLDER_NAME = '.modular_service_admin_cli'
HOME_FOLDER_FULL_PATH = os.path.join(Path.home(), HOME_FOLDER_NAME)


def create_configuration(api_link):
    try:
        requests.get(api_link)
        # to allow connect to localhost
        # if response.status_code == 404:
        #     return f'Invalid API link: {api_link}. Status code: 404.'
    except (requests.exceptions.MissingSchema,
            requests.exceptions.ConnectionError):
        return f'Invalid API link: {api_link}'
    except requests.exceptions.InvalidURL:
        return f'Invalid URL \'{api_link}\': No host specified.'
    except requests.exceptions.InvalidSchema:
        return f'Invalid URL \'{api_link}\': No network protocol specified ' \
               f'(http/https).'

    try:
        Path(HOME_FOLDER_FULL_PATH).mkdir(exist_ok=True)
    except OSError:
        SYSTEM_LOG.exception(f'Creation of the directory {HOME_FOLDER_FULL_PATH} failed')
        USER_LOG.info(f'Unable to create configuration folder {HOME_FOLDER_FULL_PATH}')
    config_file_path = f'{HOME_FOLDER_FULL_PATH}/credentials'
    config_data = dict(api_link=api_link)
    with open(config_file_path, 'w+') as config_file:
        config_file.write(yaml.dump(config_data))
    # todo review:fix
    return 'Great! has been configured.'


def save_token(access_token: str):
    config_file_path = f'{HOME_FOLDER_FULL_PATH}/credentials'
    if not Path(config_file_path).exists():
        SYSTEM_LOG.exception(f'The tool is not configured. Please contact'
                             f'the support team.')
        return 'The tool is not configured. Please contact the support team.'
    with open(config_file_path, 'r') as config_file:
        config = yaml.safe_load(config_file.read())
    config[CONF_ACCESS_TOKEN] = access_token

    with open(config_file_path, 'w+') as config_file:
        config_file.write(yaml.dump(config))
    # todo review:fix
    return 'Great! The access token has been saved.'


def clean_up_configuration():
    config_file_path = f'{HOME_FOLDER_FULL_PATH}/credentials'
    try:
        os.remove(path=config_file_path)
        os.removedirs(HOME_FOLDER_FULL_PATH)
    except OSError:
        SYSTEM_LOG.exception(
            f'Error occurred while cleaning '
            f'configuration by path: {HOME_FOLDER_FULL_PATH}')
    # todo review:fix
    return 'The configuration has been deleted.'


CONF_ACCESS_TOKEN = 'access_token'
CONF_API_LINK = 'api_link'

REQUIRED_PROPS = [CONF_API_LINK]


class ConfigurationProvider:

    def __init__(self):
        self.config_path = f'{HOME_FOLDER_FULL_PATH}/credentials'
        if not os.path.exists(self.config_path):
            raise AssertionError(
                'The tool is not configured. Please execute the '
                'following command: \'configure\'.')
        self.config_dict = None
        with open(self.config_path, 'r') as config_file:
            self.config_dict = yaml.safe_load(config_file.read())
        missing_property = []
        for prop in REQUIRED_PROPS:
            if not self.config_dict.get(prop):
                missing_property.append(prop)
        if missing_property:
            raise AssertionError(
                f'The configuration is broken. '
                f'The following properties are '
                f'required but missing: {missing_property}')

        SYSTEM_LOG.info(f'configuration has been loaded')

    @property
    def api_link(self):
        return self.config_dict.get(CONF_API_LINK)

    @property
    def access_token(self):
        return self.config_dict.get(CONF_ACCESS_TOKEN)
