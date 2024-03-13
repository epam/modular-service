from modular_sdk.models.customer import Customer
from modular_sdk.services.customer_service import CustomerService
from pynamodb.expressions.update import Action


class CustomerMutatorService(CustomerService):

    def build(self, name: str, display_name: str, 
              admins: list[str] | None = None,
              is_active: bool = True) -> Customer:
        if not admins:
            admins = []
        return Customer(
            name=name,
            display_name=display_name,
            admins=admins,
            is_active=is_active
        )

    @staticmethod
    def save(customer: Customer):
        customer.save()

    @staticmethod
    def update(customer: Customer, actions: list[Action]) -> None:
        if actions:
            customer.update(actions=actions)

    def activate(self, customer: Customer) -> None:
        if customer.is_active:
            return
        self.update(
            customer=customer,
            actions=[
                Customer.is_active.set(True),
            ]
        )

    def deactivate(self, customer: Customer) -> None:
        if not customer.is_active:
            return
        self.update(
            customer=customer,
            actions=[
                Customer.is_active.set(False),
            ]
        )
