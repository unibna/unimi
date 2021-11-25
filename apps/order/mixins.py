from apps.order.models import *


class OrderMixin:

    def get_order(self, pk=None):
        try:
            return Order.objects.get(pk=pk)
        except:
            return None

    def get_order_item(self, pk=None):
        try:
            return OrderItem.objects.get(pk=pk)
        except:
            return None

    def get_order_item_extra(self, pk=None):
        try:
            return OrderItemExtra.objects.get(pk=pk)
        except:
            return None

    def get_taken_order(self, pk=None):
        try:
            return GetOrder.objects.get(pk=pk)
        except:
            return None