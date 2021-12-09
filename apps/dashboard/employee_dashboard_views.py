from django.views.generic import TemplateView

from apps.account.models import (
    Employee,
)
from apps.store.models import (
    Store,
    Menu, Item, ItemExtraGroup, IteamExtra
)
from apps.order.models import (
    Order, OrderItem, OrderItemExtra
)


class EmployeeDashboard(TemplateView):

    template_name = "dashboard/employee_dashboard.html"
