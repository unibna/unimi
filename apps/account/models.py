from django.db import models
from django.contrib.auth.models import AbstractUser


ACCOUNT_ROLES = [
    "customer",
    "employee",
    "shipper"
]
EMPLOYEE_ROLES = [
    "staff",
    "manager",
    "owner"
]

ACCOUNT_ROLES_CHOICE = [
    ["customer", "customer"],
    ["employee", "employee"],
    ["shipper", "shipper"],
]
EMPLOYEE_ROLES_CHOICE = [
    ["staff", "staff"],
    ["manager", "manager"],
    ["owner", "owner"]
]


class CustomUser(AbstractUser):

    email = models.EmailField(max_length=64, unique=True)
    is_valid = models.BooleanField(default=False)
    phone = models.CharField(max_length=11, default="")
    account_role = models.CharField(max_length=12, choices=ACCOUNT_ROLES_CHOICE)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.username

    def save(self, *args, **kwargs):
        self.username = self.email.split("@")[0]
        super().save(*args, **kwargs)

        if self.customer_set.all() \
                or self.employee_set.all() \
                or self.shipper_set.all():
            return

        if self.account_role == "customer":
            customer = Customer(user=self)
            customer.save()
        elif self.account_role == "employee":
            employee = Employee(user=self)
            employee.save()
        elif self.account_role == "shipper":
            shipper = Shipper(user=self)
            shipper.save()
        else:
            print("Invalid User")


class Customer(models.Model):

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    balance = models.IntegerField(default=0)
    total = models.IntegerField(default=0)

    def __str__(self):
        return self.user.username


class CustomerAddress(models.Model):

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    address = models.CharField(max_length=256, null=True)


class Employee(models.Model):

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    employee_role = models.CharField(max_length=8, choices=EMPLOYEE_ROLES_CHOICE, null=True)

    def __str__(self):
        return f"{self.employee_role}-{self.user.username}"


class Shipper(models.Model):

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    income = models.IntegerField(default=0)

    def __str__(self):
        return self.user.username
