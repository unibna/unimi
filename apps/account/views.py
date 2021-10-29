import logging

from django.http import JsonResponse
from django.contrib.auth.hashers import make_password
from django.utils import timezone

from rest_framework import status, exceptions
from rest_framework import permissions
from rest_framework.generics import CreateAPIView, RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly

from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from apps.account import serializers
from apps.account.mixins import EmployeeMixin
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
)
from apps.store.serializers import (
    StoreSerializer
)

class UserCreateAPI(CreateAPIView):

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

    permission_classes = [IsAuthenticatedOrReadOnly]
    serializer_class = serializers.UserSerializer

    def get_object(self, pk=None):
        if pk:
            user = CustomUser.objects.filter(pk=pk).first()
        else:
            user = self.request.user
        return user or None

    def retrieve(self, request, *args, **kwargs):
        user = self.get_object(kwargs["account_id"])
        data_res = {}

        if user:
            data_res["user"] = self.serializer_class(user).data
            if user.account_role == "customer":
                cus = Customer.objects.get(user=user)
                data_res["customer"] = serializers.CustomerSerializer(cus).data
            elif user.account_role == "employee":
                empl = Employee.objects.get(user=user)
                data_res["employee"] = serializers.EmployeeSerializer(empl).data
            elif user.account_role == "shipper":
                shipper = Shipper.objects.get(user=user)
                data_res["shipper"] = serializers.ShipperSerializer(shipper).data

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
):

    model = Employee
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.EmployeeSerializer

    def get_object(self, pk=None):
        try:
            return self.model.objects.get(pk=pk)
        except:
            return None

    def retrieve(self, request, *args, **kwargs):
        empl = self.get_object(kwargs["employee_id"])
        data_res = {}
        data_res["employee"] = serializers.EmployeeSerializer(empl).data

        # get employee store
        store_id = None
        if empl.employee_role == "owner":
            store_id = Store.objects.get(owner=empl).pk
        elif empl.employee_role in EMPLOYEE_ROLES:
            store_id = JoinStore.objects.get(employee=empl).store.pk

        data_res["store"] = {
            "id": store_id
        }

        return responses.client_success(data_res)
