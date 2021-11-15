from apps.account.models import (
    Employee
)
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
