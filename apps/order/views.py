from django.shortcuts import resolve_url
from rest_framework import permissions
from rest_framework.exceptions import NotFound
from rest_framework.generics import RetrieveAPIView, RetrieveUpdateAPIView, CreateAPIView
from rest_framework.permissions import NOT, OR, IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.serializers import raise_errors_on_nested_writes
from apps.account.models import Employee
from apps.account.serializers import CustomerSerializer, ShipperSerializer

from apps.order import serializers
from apps.order.mixins import *
from apps.order.models import *

from apps.core import responses
from apps.account.mixins import (
    CustomerMixin,
    EmployeeMixin,
    ShipperMixin,
)
from apps.store.mixins import ItemMixin, StoreMixin


class OrderAPI(
    RetrieveUpdateAPIView,
    CreateAPIView,
    OrderMixin,
    CustomerMixin,
    EmployeeMixin,
    StoreMixin,
):

    permissions_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        if "order_id" in kwargs:
            res = self.retrieve_order(request, *args, **kwargs)
        else:
            res = self.list_order(request, *args, **kwargs)

        return responses.client_success(res)

    def retrieve_order(self, request, *args, **kwargs):
        order = self.get_order(kwargs["order_id"])
        if not order:
            raise responses.NOT_FOUND
        res = {"order": serializers.OrderSerializer(order).data}
        
        order_item_list = order.orderitem_set.all()
        order_items = [
            serializers.OrderItemSerializer(item).data for item in order_item_list
        ]
        for i in range(len(order_items)):
            order_items[i]["order_item_extras"] = [
                serializers.OrderItemExtraSerializer(extra).data for extra in order_item_list[i].orderitemextra_set.all()
            ]
        res["order"]["order_items"] = order_items

        return res

    def list_order(self, request, *args, **kwargs):
        # list order by status
        if "status" in request.GET:
            order_list = Order.objects.filter(status=request.GET["status"])
        else:
            order_list = Order.objects.all()

        return {
            "orders": [
                serializers.OrderSerializer(order).data for order in order_list
            ]
        }

    def post(self, request, *args, **kwargs):
        customer = self.get_customer(request.user)
        if not customer:
            raise responses.PERMISSION_DENIED

        req_data = request.data.dict()
        req_data["customer"] = customer.pk

        # verify customer address
        addr = self.get_customer_address(req_data["customer_address"])
        if addr.customer != customer:
            raise responses.client_error({
                "errors": "Not assigned address"
            })

        serializer = serializers.OrderCreateSerializer(data=req_data)
        if serializer.is_valid():
            serializer.save()
            return responses.client_success({
                "order": serializer.data
            })
        else:
            raise responses.client_error({
                "errors": serializer.errors
            })

    def put(self, request, *args, **kwargs):
        if "order_id" not in kwargs:
            raise responses.BAD_REQUEST

        # get update order
        order = self.get_order(kwargs["order_id"])
        if not order:
            raise responses.BAD_REQUEST

        # verify user permission
        if len(request.data) > 1:
            raise responses.BAD_REQUEST
        # address can be change if user is customer
        elif "customer_address" in request.data:
            customer = self.get_customer(request.user)
            addr = self.get_customer_address(request.data["customer_address"])

            if not customer:
                raise responses.client_error({
                    "errors": "Invalid customer"
                })
            # check if submit address is customer address
            elif not addr or addr.customer != customer:
                raise responses.client_error({
                    "errors": "Invalid address"
                })
        # employee and shipper can only change order status
        elif "status" in request.data:
            if request.user.account_role == "employee":
                empl = self.get_employee(request.user)
                empl_store = self.get_employee_store(empl)

                if order.store != empl_store:
                    raise responses.PERMISSION_DENIED
            elif request.user.account_role == "shipper":
                pass 
                # handle later
            else:
                raise responses.PERMISSION_DENIED
        else:
            raise responses.BAD_REQUEST

        serializer = serializers.OrderSerializer(order, request.data)
        if serializer.is_valid():
            serializer.save()
            return responses.client_success({
                "order": serializer.data
            })
        else:
            raise responses.client_error({
                "errors": serializer.errors
            })


class OrderItemAPI(
    RetrieveUpdateAPIView,
    CreateAPIView,
    OrderMixin,
    CustomerMixin,
    ItemMixin,
):

    permissions_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, *args, **kwargs):
        if "order_item_id" in kwargs:
            res = self.retrieve(request, *args, **kwargs)
        else:
            res = self.list(request, *args, **kwargs)

        return responses.client_success(res)

    def retrieve(self, request, *args, **kwargs):
        item = self.get_order_item(kwargs["order_item_id"])
        if not item:
            raise responses.NOT_FOUND
        res = {"order_item": serializers.OrderItemSerializer(item).data}
        res["order_item"]["order_item_extras"] = [
            serializers.OrderItemExtraSerializer(extra).data for extra in item.orderitemextra_set.all()
        ]

        return res

    def list(self, request, *args, **kwargs):
        if "order" not in request.GET:
            raise responses.BAD_REQUEST

        order = self.get_order(request.GET["order"])
        item_list = order.orderitem_set.all()
        return {
            "order": serializers.OrderSerializer(order).data,
            "order_items": [
                serializers.OrderItemSerializer(item).data for item in item_list
            ]
        }

    def post(self, request, *args, **kwargs):
        customer = self.get_customer(request.user)
        if not customer:
            raise responses.PERMISSION_DENIED

        # valid input
        if "order" not in request.data \
                or "item" not in request.data \
                or "quantity" not in request.data:
            raise responses.BAD_REQUEST

        order = self.get_order(request.data["order"])
        if order.customer != customer:
            raise responses.PERMISSION_DENIED

        item = self.get_item(request.data["item"])
        if not item:
            raise responses.NOT_FOUND

        if order.store != item.menu.store:
            raise responses.client_error({
                "errors": f"{item} is not in {order.store}"
            })
        elif float(request.data["quantity"]) < 1:
            raise responses.BAD_REQUEST

        # compute amount of order item
        req_data = request.data.dict()
        req_data["amount"] = item.price * float(request.data["quantity"])

        serializer = serializers.OrderItemCreateSerializer(data=req_data)
        if serializer.is_valid():
            order_item = serializer.save()

            # update order total
            order.total += order_item.amount
            order.save()

            return responses.client_success({
                "order_item": serializer.data
            })
        else:
            raise responses.client_error({
                "errors": serializer.errors
            })

    def put(self, request, *args, **kwargs):
        customer = self.get_customer(request.user)
        if not customer:
            raise responses.PERMISSION_DENIED

        if "order_item_id" not in kwargs:
            raise responses.BAD_REQUEST

        order_item = self.get_order_item(kwargs["order_item_id"])
        if not order_item:
            raise responses.NOT_FOUND
        elif order_item.order.customer != customer:
            raise responses.PERMISSION_DENIED

        req_data = request.data.dict()
        if "quantity" in request.data:
            req_data["amount"] = order_item.item.price * float(request.data["quantity"])

        serializer = serializers.OrderItemSerializer(order_item, req_data)
        if serializer.is_valid():
            order_item = serializer.save()

            # update order total
            order_item.order.total += order_item.amount
            order_item.order.save()

            return responses.client_success({
                "order_item": serializer.data
            })
        else:
            raise responses.client_error({
                "errors": serializer.errors
            })


class OrderItemExtraAPI(
    RetrieveUpdateAPIView,
    CreateAPIView,
    OrderMixin,
    CustomerMixin,
    ItemMixin,
):

    permissions_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, *args, **kwargs):
        if "order_item_extra_id" in kwargs:
            res = self.retrieve(request, *args, **kwargs)
        else:
            res = self.list(request, *args, **kwargs)

        return responses.client_success(res)

    def retrieve(self, request, *args, **kwargs):
        extra = self.get_order_item_extra(kwargs["order_item_extra_id"])
        if not extra:
            raise responses.NOT_FOUND
        
        return {
            "order_item_extra": serializers.OrderItemExtraSerializer(extra).data
        }

    def list(self, request, *args, **kwargs):
        res = {}

        if "order" in request.GET:
            order = self.get_order(request.GET["order"])
            if not order:
                raise responses.NOT_FOUND
            res["order"] = serializers.OrderSerializer(order).data
            order_item_list = order.orderitem_set.all()
            res["order"]["order_items"] = [
                serializers.OrderItemSerializer(item).data for item in order_item_list
            ]
            for i in range(len(order_item_list)):
                res["order"]["order_items"][i]["order_item_extras"] = [
                    serializers.OrderItemExtraSerializer(extra).data for extra in order_item_list[i].orderitemextra_set.all()
                ]
        elif "order-item" in request.GET:
            item = self.get_order_item(request.GET["order-item"])
            extra_list = item.orderitemextra_set.all()

            res["order_items"] = serializers.OrderItemSerializer(item).data
            res["order_items"]["order_item_extras"] = [
                serializers.OrderItemExtraSerializer(extra) for extra in extra_list
            ]

        return res

    def post(self, request, *args, **kwargs):
        customer = self.get_customer(request.user)
        if not customer:
            raise responses.PERMISSION_DENIED

        # valid params
        if "order_item" not in request.data \
                or "item_extra" not in request.data \
                or "quantity" not in request.data:
            raise responses.BAD_REQUEST

        # get request instances
        order_item = self.get_order_item(request.data["order_item"])
        item_extra = self.get_extra(request.data["item_extra"])
        order = order_item.order

        if not order_item \
                or not item_extra:
            print('3')
            raise responses.NOT_FOUND

        # check value and permission
        if order_item.item != item_extra.item_extra_group.item:
            raise responses.client_error({
                "errors": f"Invalid Item extra"
            })

        if order.customer != customer:
            raise responses.PERMISSION_DENIED

        if int(request.data["quantity"]) < 0:
            raise responses.BAD_REQUEST

        # compute total
        req_data = request.data.dict()
        req_data["amount"] = item_extra.price * float(request.data["quantity"])

        serializer = serializers.OrderItemExtraCreateSerializer(data=req_data)
        if serializer.is_valid():
            ins = serializer.save()

            # update order total
            order.total += ins.amount
            order.save()

            return responses.client_success({
                "order_item_extra": serializer.data
            })
        else:
            raise responses.client_error({
                "errors": serializer.errors
            })

    def put(self, request, *args, **kwargs):
        customer = self.get_customer(request.user)
        if not customer:
            raise responses.PERMISSION_DENIED

        # verify params
        if "order_item_extra_id" not in kwargs:
            raise responses.BAD_REQUEST

        order_extra = self.get_order_item_extra(kwargs["order_item_extra_id"])
        if not order_extra:
            raise responses.NOT_FOUND

        # verify customer permission
        order = order_extra.order_item.order
        if order.customer != customer:
            raise responses.PERMISSION_DENIED

        # verify update data
        req_data = request.data.dict()
        if "quantity" in request.data and int(request.data["quantity"]) > 0:
            req_data["amount"] = order_extra.item_extra.price * float(req_data["quantity"])

        serializer = serializers.OrderItemExtraSerializer(order_extra, req_data)
        if serializer.is_valid():
            ins = serializer.save()

            # update order total
            order.total += ins.amount
            order.save()

            return responses.client_success({
                "order_item_extra": serializer.data
            })
        else:
            raise responses.client_error({
                "errors": serializer.errors
            })


class GetOrderAPI(
    RetrieveUpdateAPIView,
    CreateAPIView,
    ShipperMixin,
    OrderMixin,
    EmployeeMixin,
    StoreMixin,
    CustomerMixin
):

    permissions_classes = [IsAuthenticated]

    def is_related_user(self, request, taken_order):
        if request.user.account_role == "customer":
            if taken_order.order.customer.user != request.user:
                return False
        elif request.user.account_role == "shipper":
            if taken_order.shipper.user != request.user:
                return False
        elif request.user.account_role == "employee":
            empl = self.get_employee(request.user)
            store = self.get_employee_store(empl)
            if not store or store != taken_order.order.store:
                return False
        else:
            return False
        return True

    def get(self, request, *args, **kwargs):
        if "get_order_id" in kwargs:
            res = self.retrieve(request, *args, **kwargs)
        else:
            res = self.list(request, *args, **kwargs)

        return responses.client_success(res)

    def retrieve(self, request, *args, **kwargs):
        taken_order = self.get_taken_order(kwargs["get_order_id"])
        if not taken_order:
            raise responses.NOT_FOUND

        if not self.is_related_user(request.user, taken_order):
            raise responses.PERMISSION_DENIED

        return {
            "get_order": serializers.GetOrderSerializer(taken_order).data,
            "order": serializers.OrderSerializer(taken_order.order).data,
            "shipper": ShipperSerializer(taken_order.shipper).data,
            "customer": CustomerSerializer(taken_order.order.customer).data,
        }

    def list(self, request, *args, **kwargs):
        params_len = len(request.GET)
        print(params_len)

        if params_len == 0:
            res = self.list_all(request, *args, **kwargs)
        if "shipper" in request.GET and params_len == 1:
            res = self.list_by_shipeer(request, *args, **kwargs)
        elif "customer" in request.GET and params_len == 1:
            res = self.list_by_customer(request, *args, **kwargs)
        elif "order" in request.GET and params_len == 1:
            pass
        else:
            raise responses.BAD_REQUEST

        return responses.client_success(res)

    def list_all(self, request, *args, **kwargs):
        # classify user by account role
        if request.user.account_role == "customer":
            customer = self.get_customer(request.user)
            if not customer:
                raise responses.PERMISSION_DENIED
            order_list = customer.order_set.all()
            get_order_list = [order.getorder_set.all() for order in order_list]
        elif request.user.account_role == "shipper":
            shipper = self.get_shipper(request.user)
            if not shipper:
                raise responses.PERMISSION_DENIED
            get_order_list = shipper.getorder_set.all()
            order_list = [ins.order for ins in get_order_list]
        elif request.user.account_role == "employee":
            empl = self.get_employee(request.user)
            store = self.get_employee_store(empl)
            if not store:
                raise responses.PERMISSION_DENIED
            order_list = store.order_set.all()
            get_order_list = [order.getorder_set.all() for order in order_list]
        else:
            raise responses.PERMISSION_DENIED

        order_list = list(np.array(order_list).flat)
        get_order_list = list(np.array(get_order_list).flat)

        return {
            "orders": [
                serializers.OrderSerializer(order).data for order in order_list
            ],
            "get_orders": [
                serializers.GetOrderSerializer(get_order).data for get_order in get_order_list
            ]
        }


    def list_by_shipper(self, request, *args, **kwargs):
        pass

    def list_by_customer(self, request, *args, **kwargs):
        pass

    def post(self, request, *args, **kwargs):
        shipper = self.get_shipper(request.user)
        if not shipper:
            raise responses.PERMISSION_DENIED

        if len(request.data) != 2 \
                or "order" not in request.data \
                or "distance" not in request.data:
            raise responses.BAD_REQUEST

        order = self.get_order(request.data["order"])
        if not order:
            raise responses.NOT_FOUND

        distance = float(request.data["distance"])
        if distance < 0:
            raise responses.BAD_REQUEST

        req_data = request.data.dict()
        # should base on distance (handle later)
        req_data["estimate_time"] = "00:30"
        req_data["cost"] = 5000 * distance
        req_data["shipper"] = shipper.pk

        serializer = serializers.GetOrderCreateSerializer(data=req_data)
        if serializer.is_valid():
            serializer.save()

            # update order status
            order.status = "confirm"
            order.save()

            return responses.client_success({
                "get_order": serializer.data,
                "shipper": ShipperSerializer(shipper).data,
                "order": serializers.OrderSerializer(order).data,
            })
        else:
            return responses.client_error({
                "errors": serializer.errors
            })

    def put(self, request, *args, **kwargs):
        shipper = self.get_shipper(request.user)
        if not shipper:
            raise responses.PERMISSION_DENIED

        # verify params
        if len(request.data) != 1 \
                or "is_successful" not in request.data \
                or "get_order_id" not in kwargs:
            raise responses.BAD_REQUEST

        taken_order = self.get_taken_order(kwargs["get_order_id"])

        serializer = serializers.GetOrderSerializer(taken_order, request.data)
        if serializer.is_valid():
            ins = serializer.save()

            # update order and shipper data
            # if delivery successfully
            # prevent shipper confirm multi times
            # to get more cost
            if ins.is_successful \
                    and ins.order.status != "done":
                ins.order.status = "done"
                ins.order.save()

                shipper.income += ins.cost
                shipper.save()

            return responses.client_success({
                "get_order": serializer.data,
                "shipper": ShipperSerializer(shipper).data,
                "order": serializers.OrderSerializer(ins.order).data,
            })
        else:
            return responses.client_error({
                "errors": serializer.errors
            })


class PaymentAPI(
    RetrieveAPIView,
    CreateAPIView,
    CustomerMixin,
    ShipperMixin,
    StoreMixin,
    OrderMixin
):

    permissions_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        customer = self.get_customer(request.user)
        if not customer:
            raise responses.PERMISSION_DENIED
