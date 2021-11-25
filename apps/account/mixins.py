from apps.account.models import (
    Customer, CustomerAddress,
    Employee, Shipper
)
from apps.account.serializers import CustomerAddressSerializer
from apps.core import responses
from apps.store.models import JoinStore


class EmployeeMixin:

    def get_employee(self, user):
        try:
            return Employee.objects.get(user=user)
        except:
            return None

    def is_owner(self, empl):
        if not empl:
            return False
        elif empl.employee_role != "owner":
            return False
        return True

    def get_owner(self, user):
        empl = self.get_employee(user)
        if not empl:
            raise responses.PERMISSION_DENIED
        elif empl.employee_role != "owner":
            raise responses.PERMISSION_DENIED
        return empl

    def get_free_employee(self, user):
        empl = self.get_employee(user)
        if not JoinStore.objects.filter(employee=empl):
            return empl
        return None

    def get_hired_employee(self, user):
        empl = self.get_employee(user)
        if not empl:
            raise responses.PERMISSION_DENIED
        elif not empl.store_set.all():
            raise responses.PERMISSION_DENIED
        return empl


class CustomerMixin:

    def get_customer(self, user=None):
        try:
            return Customer.objects.get(user=user)
        except:
            return None

    def get_customer_address(self, pk=None):
        try:
            return CustomerAddress.objects.get(pk=pk)
        except:
            return None


class ShipperMixin:

    def get_shipper(self, user=None):
        try:
            return Shipper.objects.get(user=user)
        except:
            return None