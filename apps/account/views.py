from datetime import date
import logging
import re

from django.contrib.auth.hashers import make_password
from django.db.models.query import RawQuerySet
from django.utils import timezone
from rest_framework import permissions

from rest_framework.generics import CreateAPIView, RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly

from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from apps.account import serializers
from apps.account.mixins import EmployeeMixin, CustomerMixin
from apps.account.models import (
    CustomUser,
    EMPLOYEE_ROLES,
    Customer,
    Employee,
    Shipper
)
from apps.core import responses
from apps.store.models import (
    Store,
    JoinStore,
    StoreCategory,
)
from apps.store.serializers import (
    StoreSerializer
)
from apps.store.mixins import StoreMixin


class UserCreateAPI(CreateAPIView):

    allow_method = ['post']
    serializer_class = serializers.UserCreateSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            # hash password
            serializer.validated_data['password'] = make_password(
                serializer.validated_data['password']
            )
            # create an User instance
            serializer.save()
            return responses.client_success({
                "message": "Create Successfully"
            })
        else:
            raise responses.client_error({
                "errors": serializer.errors
            })


class UserLoginAPI(TokenObtainPairView):

    serializer_class = TokenObtainPairSerializer

    def post(self, request):
        serializer = self.serializer_class(request.user, data=request.data)

        if serializer.is_valid():
            # log the login time
            user = CustomUser.objects.get(
                email=request.data["email"]
            )
            user.last_login = timezone.now()
            user.save()

            return responses.client_success(
                serializer.validated_data
            )
        else:
            raise responses.client_error({
                "errors": serializer.errors
            })


class UserAPI(RetrieveUpdateAPIView):

    permission_classes = [IsAuthenticated]
    serializer_class = serializers.UserSerializer

    def get_object(self, pk=None):
        if pk:
            user = CustomUser.objects.filter(pk=pk).first()
        else:
            user = self.request.user
        return user or None

    def retrieve(self, request, *args, **kwargs):
        if not kwargs:
            # return request user data
            user = request.user
        else:
            user = self.get_object(kwargs["account_id"])
        data_res = {}

        if user:
            data_res["user"] = self.serializer_class(user).data
            if user.account_role == "customer":
                cus = Customer.objects.get(user=user)
                account_role_data = serializers.CustomerSerializer(cus).data
                
                # get cusomter addresses
                addr_list = cus.customeraddress_set.all()
                account_role_data["customer_addresses"] = [
                    serializers.CustomerAddressSerializer(addr).data for addr in addr_list
                ]
            elif user.account_role == "employee":
                empl = Employee.objects.get(user=user)
                account_role_data = serializers.EmployeeSerializer(empl).data
            elif user.account_role == "shipper":
                shipper = Shipper.objects.get(user=user)
                account_role_data = serializers.ShipperSerializer(shipper).data
            data_res["user"]["account_role_info"] = account_role_data

        return responses.client_success(data_res)

    def update(self, request, *args, **kwargs):
        user = self.get_object(kwargs['account_id'])

        if not user:
            return responses.client_success({
                "user": {}
            })

        # check permission
        # if request user is user or admin => OK
        if request.user == user:
            logging.info(f"{user} update itself")
        elif request.user.is_superuser:
            logging.info(f"Admin update {user}")
        else:
            logging.error(f"{request.user} have no permission")
            raise responses.PERMISSION_DENIED

        serializer = self.serializer_class(user, data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return responses.client_success({
                "user": serializer.data
            })
        else:
            raise responses.client_error({
                "erros": serializer.errors
            })


class EmployeeAPI(
    RetrieveUpdateAPIView,
    EmployeeMixin,
    StoreMixin,
):

    permission_classes = [IsAuthenticated]
    serializer_class = serializers.EmployeeSerializer

    def get_object(self, empl_id):
        try:
            return Employee.objects.get(pk=empl_id)
        except:
            return None

    def retrieve(self, request, *args, **kwargs):
        # check if user is employee
        if request.user.account_role != "employee":
            return responses.PERMISSION_DENIED

        # init response
        res = {}

        # classify action
        # list employee in a store by store id
        if "store_id" in request.GET:
            return self.get_store_employee(request, *args, **kwargs)

        # get employee data by id
        if "employee_id" in kwargs:
            empl = self.get_object(kwargs["employee_id"])
        # get employee data by request user
        elif not request.user.is_anonymous:
            empl = self.get_employee(request.user)
        else:
            raise responses.PERMISSION_DENIED
        res["employee"] = serializers.EmployeeSerializer(empl).data

        # get store data
        try:
            store = Store.objects.get(owner=empl)
        except:
            store = None

        res["employee"]["store"] = StoreSerializer(store).data
        if store:
            res["employee"]["store"]["store_category"] = StoreCategory.objects.get(pk=res["employee"]["store"]["store_category"]).name
            if not (empl and empl.user == request.user and store.owner == empl):
                res["employee"]["store"].pop("secret_key")

        return responses.client_success(res)

    def get_store_employee(self, request, *args, **kwargs):
        store = self.get_store(request.GET["store_id"])
        if not store:
            raise responses.NOT_FOUND

        # init response
        res = {}

        # get store data
        res["store"] = StoreSerializer(store).data
        empl = self.get_employee(request.user)
        if store:
            res["store"]["store_category"] = StoreCategory.objects.get(pk=res["store"]["store_category"]).name
            if not store.owner == empl:
                res["store"].pop("secret_key")


        # get employee
        employee_list = [ins.employee for ins in JoinStore.objects.filter(store=store)]
        res["store"]["employees"] = [
            serializers.EmployeeSerializer(empl).data for empl in employee_list
        ]

        return responses.client_success(res)


class CustomerAddressAPI(
    RetrieveUpdateAPIView,
    CreateAPIView,
    CustomerMixin
):
    permissions_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, *args, **kwargs):
        if "address_id" in kwargs:
            res = self.retrieve_address(request, *args, **kwargs)
        else:
            res = self.list_address(request, *args, **kwargs)

        return responses.client_success(res)

    def list_address(self, request, *args, **kwargs):
        customer = self.get_customer(request.user)
        if not customer:
            raise responses.PERMISSION_DENIED

        address_list = customer.customeraddress_set.all()
        return {
            # "customer": serializers.CustomerSerializer(customer).data,
            "customer_adress": [
                serializers.CustomerAddressSerializer(addr).data for addr in address_list
            ]
        }

    def retrieve_address(self, request, *args, **kwargs):
        customer = self.get_customer(request.user)
        if not customer:
            raise responses.PERMISSION_DENIED

        address = self.get_customer_address(kwargs["address_id"])
        # check customer permission
        if address.customer != customer:
            raise responses.PERMISSION_DENIED

        if not address:
            raise responses.NOT_FOUND

        return serializers.CustomerAddressSerializer(address).data

    def post(self, request, *args, **kwargs):
        customer = self.get_customer(request.user)
        if not customer:
            raise responses.PERMISSION_DENIED

        req_data = request.data.dict()
        req_data["customer"] = customer.pk

        serializer = serializers.CustomerAddressCreateSerializer(data=req_data)
        if serializer.is_valid():
            serializer.save()
            return responses.client_success({
                "customer_address": serializer.data
            })
        else:
            raise responses.client_error({
                "errors": serializer.errors
            })

    def put(self, request, *args, **kwargs):
        if "address_id" not in kwargs:
            raise responses.BAD_REQUEST

        customer = self.get_customer(request.user)
        address = self.get_customer_address(kwargs["address_id"])

        if not customer:
            raise responses.PERMISSION_DENIED
        elif not address:
            raise responses.BAD_REQUEST

        serializer = serializers.CustomerAddressSerializer(
            instance=address,
            data=request.data
        )
        if serializer.is_valid():
            serializer.save()
            return responses.client_success({
                "customer_address": serializer.data
            })
        else:
            raise responses.client_error({
                "errors": serializer.errors
            })
