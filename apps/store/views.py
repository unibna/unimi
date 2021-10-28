import logging
import json
from rest_framework import permissions

from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveUpdateAPIView, CreateAPIView
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly

from apps.account.models import (
    Employee,
    EMPLOYEE_ROLES,
)
from apps.account.serializers import (
    UserSerializer,
    EmployeeSerializer,
)
from apps.store import serializers
from apps.store.models import (
    JoinStore,
    Store,
)
from apps.core import responses


class EmployeeMixin:

    def get_employee(self, user):
        try:
            return Employee.objects.get(user=user)
        except:
            return None


class StoreMixin:

    def get_store(self, pk=None):
        try:
            return Store.objects.get(pk=pk)
        except:
            return None

    def is_store_employee(self, store, empl):
        try:
            JoinStore.objects.get(
                store=store,
                empl=empl,
            )
            return True
        except:
            return False



class StoreCreateAPI(
        CreateAPIView,
        EmployeeMixin,
):

    permission_classes = [IsAuthenticated]
    serializer_class = serializers.StoreCreateSerializer

    def post(self, request, *args, **kwargs):
        empl = self.get_employee(request.user)
        if not empl:
            logging.error("User is not Employee")
            print("User is not Employee")
            raise responses.PERMISSION_DENIED
        elif empl.store_set.all():
            logging.error("Employee is in a store")
            print("Employee is in a store")
            raise responses.PERMISSION_DENIED

        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            store = serializer.save()
            store.owner = empl
            store.save()

            # update new store for employee
            empl.employee_role = "owner"
            empl.save()

            return responses.client_success({
                "store": serializer.data,
            })
        else:
            raise responses.client_error({
                "errors": serializer.errors
            })


class StoreListAPI(
        ListAPIView
):
    serializer_class = serializers.StoreSerializer

    def get(self, request, *args, **kwargs):
        store_list = Store.objects.all()
        return responses.client_success({
            "stores": [
                self.serializer_class(store).data for store in store_list
            ]
        })


class StoreRetrieveUpdateAPI(
        RetrieveUpdateAPIView,
        EmployeeMixin,
        StoreMixin,
):

    permission_classes = [IsAuthenticatedOrReadOnly]
    serializer_class = serializers.StoreSerializer

    def retrieve(self, request, *args, **kwargs):
        empl = self.get_employee(request.user)
        store = self.get_store(kwargs['pk'])

        if not store:
            print("Store is not found")
            raise responses.NOT_FOUND

        serializer = self.serializer_class(store)
        store_data = serializer.data

        # limit readable fields with anonymous user
        if not empl or store.owner != empl:
            store_data.pop("secret_key")

        return responses.client_success({
            "store": store_data
        })

    def update(self, request, *args, **kwargs):
        # check if request user is store's owner
        empl = self.get_employee(request.user)
        store = self.get_store(kwargs['pk'])
        if not empl:
            print("User is not Emloyee")
            raise responses.PERMISSION_DENIED
        elif store.owner != empl:
            print("Employee is not Owner")
            raise responses.PERMISSION_DENIED
        elif not store:
            print("Store is not found")
            raise responses.NOT_FOUND

        serializer = self.serializer_class(store, data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return responses.client_success({
                "store": serializer.data
            })
        else:
            raise responses.client_error({
                "errors": serializer.errors
            })


class JoinStoreAPI(
        CreateAPIView,
        EmployeeMixin,
        StoreMixin,
):

    permission_classes = [IsAuthenticated,]
    serializer_class = serializers.JoinStoreSerializer

    def post(self, request, *args, **kwargs):
        try:
            sec_key = request.data['secret_key']
            employee_role = request.data['employee_role']
        except:            
            print("Invalid parameters")
            raise responses.client_error({
                "errors": "Invalid parameters"
            })

        empl = self.get_employee(request.user)
        store = self.get_store(kwargs['pk'])
        if not empl:
            print("User is not Employee")
            raise responses.PERMISSION_DENIED
        elif empl.joinstore_set.all():
            print("Employee is in a store")
            raise responses.PERMISSION_DENIED
        elif not store:
            print("Store is not exist")
            raise responses.NOT_FOUND
        elif store.secret_key != sec_key:
            print("Invalid Secret Key")
            raise responses.client_error({
                "errors": "Invalid Secret Key"
            })
        elif employee_role == "owner" \
                or employee_role not in EMPLOYEE_ROLES:
            print("Invalid Employee Role")
            raise responses.client_error({
                "errors": "Invalid Employee Role"
            })

        serializer = self.serializer_class(data={
            "employee": empl.pk,
            "store": store.pk,
        })
        if serializer.is_valid(raise_exception=True):
            serializer.save()

            empl.employee_role = employee_role
            empl.save()

            return responses.client_success({
                "join": serializer.data,
            })
        else:
            raise responses.client_error({
                "errors": serializer.errors
            })


class StoreEmployeeListAPI(
    ListAPIView,
    EmployeeMixin,
    StoreMixin,
):
    permission_class = [IsAuthenticated,]

    def get(self, request, *args, **kwargs):
        empl = self.get_employee(request.user)
        if not empl:
            print("User is not Employee")
            raise responses.PERMISSION_DENIED
        elif not empl.employee_role:
            print("Employee is not in any store")
            raise responses.PERMISSION_DENIED

        # get empl's store
        if empl.employee_role == "owner":
            store = Store.objects.get(owner=empl)
        else:
            store = JoinStore.objects.get(employee=empl).store
        # get store's employee list
        joinstore_list = store.joinstore_set.all()
        employee_list = [store.owner] + [js.employee for js in joinstore_list]

        return responses.client_success({
            "employees": [
                {
                    "employee": EmployeeSerializer(empl).data,
                    "user": UserSerializer(empl.user).data,
                } for empl in employee_list
            ]
        })

# class MenuCreateAPI(CreateAPIView, EmployeeMixin):

#     permission_classes = [IsAuthenticated]
#     serializer_class = serializers.MenuCreateSerialzer

#     def post(self, request):
#         empl = self.get_employee(request.user)
#         if empl.employee_role != "owner":
#             raise responses.PERMISSION_DENIED

#         serializer = self.serializer_class(data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return responses.client_success({
#                 "menu": serializer.data
#             })

#         raise responses.client_error({
#             "errors": serializer.errors
#         })


# class MenuAPI(RetrieveUpdateAPIView, EmployeeMixin):

#     permission_classes = [IsAuthenticatedOrReadOnly]
#     serializer_class = serializers.MenuSerializer

#     def get_object(self):
#         try:
#             return Menu.objects.get(pk=self.request.data["id"])
#         except:
#             raise responses.NOT_FOUND

#     def retrieve(self, request, *args, **kwargs):
#         menu = self.get_object()
#         serializer = self.serializer_class(menu)

#         return responses.client_success({
#             "menu": serializer.data
#         })

#     def update(self, request, *args, **kwargs):
#         empl = self.get_employee(request.user)
#         if empl.employee_role != "owner":
#             raise responses.PERMISSION_DENIED

#         menu = self.get_object()
#         serializer = self.serializer_class(menu, data=request.data)

#         if serializer.is_valid(raise_exception=True):
#             serializer.save()
#             return responses.client_success({
#                 "menu": serializer.data
#             })
#         else:
#             raise responses.client_error({
#                 "errors": serializer.errors
#             })
