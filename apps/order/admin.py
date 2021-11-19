from django.contrib import admin
from apps.order.models import *


admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(OrderItemExtra)
