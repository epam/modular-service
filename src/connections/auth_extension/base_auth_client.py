import os

from commons.log_helper import get_logger

_LOG = get_logger(__name__)

SERVICE_MODE = os.getenv('service_mode')
is_docker = SERVICE_MODE == 'docker'

AUTH_HANDLER = None


class AuthClient:
    is_docker = SERVICE_MODE == 'docker'

    def __init__(self, client):
        self.client = client

    def admin_initiate_auth(self, username, password):
        return self.client.admin_initiate_auth(username=username,
                                               password=password)

    def is_user_exists(self, username):
        return self.client.is_user_exists(username=username)

    def sign_up(self, username, password, customer, role):
        return self.client.sign_up(username=username, password=password,
                                   customer=customer, role=role)

    def set_password(self, username, password, permanent=True):
        return self.client.set_password(username=username, password=password,
                                        permanent=permanent)

    def get_user(self, username):
        return self.client.get_user(username=username)

    def update_role(self, username, role):
        return self.client.update_role(username=username, role=role)

    def get_user_customer(self, username):
        return self.client.get_user_customer(username=username)

    def get_user_role(self, username):
        return self.client.get_user_role(username=username)

    def update_customer(self, username, customer):
        return self.client.update_customer(username=username,
                                           customer=customer)

    def delete_role(self, username):
        return self.client.delete_role(username=username)

    def delete_customer(self, username):
        return self.client.delete_customer(username=username)

    def is_system_user_exists(self):
        return self.client.is_system_user_exists()

    def get_system_user(self):
        return self.client.get_system_user()

    def get_customers_latest_logins(self, customers=None):
        return self.client.get_customers_latest_logins(customers)
