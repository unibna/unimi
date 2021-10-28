from django.contrib import admin

from apps.account.models import (
    CustomUser,
    Customer, Employee, Shipper
)


admin.site.register(CustomUser)
admin.site.register(Customer)
admin.site.register(Employee)
admin.site.register(Shipper)
