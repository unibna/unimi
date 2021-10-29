from apps.account.models import (
    Employee
)



class EmployeeMixin:

    def get_employee(self, user):
        try:
            return Employee.objects.get(user=user)
        except:
            return None

    def is_owner(self, empl):
        if not empl:
            print("User is not Employee")
            return False
        elif empl.employee_role != "owner":
            print("Employee is not Owner")
            return False
        return True

    def get_owner(self, user):
        empl = self.get_employee(user)
        if not empl:
            print("User is not Employee")
            raise responses.PERMISSION_DENIED
        elif empl.employee_role != "owner":
            print("Employee is not Owner")
            raise responses.PERMISSION_DENIED
        return empl

    def get_free_employee(self, user):
        empl = self.get_employee(user)
        if not empl:
            logging.error("User is not Employee")
            print("User is not Employee")
            raise responses.PERMISSION_DENIED
        elif empl.store_set.all():
            logging.error("Employee is in a store")
            print("Employee is in a store")
            raise responses.PERMISSION_DENIED
        return empl

    def get_hired_employee(self, user):
        empl = self.get_employee(user)
        if not empl:
            logging.error("User is not Employee")
            print("User is not Employee")
            raise responses.PERMISSION_DENIED
        elif not empl.store_set.all():
            logging.error("Employee is not in a store")
            print("Employee is in a store")
            raise responses.PERMISSION_DENIED
        return empl