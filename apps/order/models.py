from django.db import models

from apps.account.models import (
    Customer,
    CustomerAddress,
    Shipper
)
from apps.store.models import (
    Store,
    Item, IteamExtra,
)


order_status_choices = [
    # create successfully
    ['created', 'created'],
    # by shipper
    ['confirm', 'confirm'],
    # by store
    ['doing', 'doing'],
    # by shipper
    ['delivery', 'delivery'],
    # by shipper
    ['done', 'done'],
]


class Order(models.Model):

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    store = models.ForeignKey(Store, on_delete=models.CASCADE)
    customer_address = models.ForeignKey(CustomerAddress, on_delete=models.CASCADE, blank=True)
    total = models.FloatField(default=0)
    status = models.CharField(max_length=32, choices=order_status_choices, default="created")
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.status}-{self.customer.user.email}-{self.store.name}"


class OrderItem(models.Model):

    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=0)
    amount = models.FloatField(default=0)

    def __str__(self):
        return f"{self.item.name}-{self.quantity}"


class OrderItemExtra(models.Model):

    order_item = models.ForeignKey(OrderItem, on_delete=models.CASCADE)
    item_extra = models.ForeignKey(IteamExtra, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=0)
    amount = models.FloatField(default=0)

    def __str__(self):
        return f"{self.item_extra.name}-{self.quantity}"


class GetOrder(models.Model):

    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    shipper = models.ForeignKey(Shipper, on_delete=models.CASCADE)
    # cost = items cost + delivery fee
    cost = models.FloatField(default=0)
    distance = models.FloatField(default=0)
    # minute
    estimate_time = models.TimeField()
    is_successful = models.BooleanField(default=False)


class Payment(models.Model):

    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    is_complete = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)


class Feedback(models.Model):

    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    content = models.CharField(max_length=512, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
