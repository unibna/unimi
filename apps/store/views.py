import logging

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
from apps.account.mixins import (
    EmployeeMixin
)
from apps.store import serializers
from apps.store.models import (
    JoinStore,
    Store,
    Menu, Item
)
from apps.core import responses


class StoreMixin:

    def get_store(self, pk=None):
        try:
            return Store.objects.get(pk=pk)
        except:
            print("Store is not exist")
            raise responses.NOT_FOUND

    def is_store_employee(self, store, empl):
        try:
            JoinStore.objects.get(
                store=store,
                empl=empl,
            )
            return True
        except:
            return False

    def is_store_owner(self, store, owner):
        try:
            if store.owner == owner:
                return True
        except:
            return False


class MenuMixin:

    def get_menu(self, pk=None):
        try:
            return Menu.objects.get(pk=pk)
        except:
            print("Menu is not exist")
            raise responses.client_error({
                "errors": "Menu is not exist"
            })


class StoreCreateAPI(
        CreateAPIView,
        EmployeeMixin,
):

    permission_classes = [IsAuthenticated]
    serializer_class = serializers.StoreCreateSerializer

    def post(self, request, *args, **kwargs):
        empl = self.get_free_employee(request.user)

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


class StoreRetrieveUpdateAPI(
        RetrieveUpdateAPIView,
        EmployeeMixin,
        StoreMixin,
):

    permission_classes = [IsAuthenticatedOrReadOnly]
    serializer_class = serializers.StoreSerializer

    def retrieve(self, request, *args, **kwargs):
        empl = self.get_employee(request.user)
        store = self.get_store(kwargs['store_id'])

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
        owner = self.get_owner(request.user)
        store = self.get_store(kwargs['store_id'])

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

        empl = self.get_free_employee(request.user)
        store = self.get_store(kwargs['store_id'])
        if store.secret_key != sec_key:
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


class MenuCreateAPI(
        CreateAPIView,
        EmployeeMixin,
        StoreMixin
):
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.MenuCreateSerialzer

    def post(self, request, *args, **kwargs):
        owner = self.get_owner(request.user)
        store = self.get_store(kwargs['store_id'])

        if not self.is_store_owner(store, owner):
            print(f"{owner} is not {store}'s Owner")

        req_data = request.data.dict()
        req_data["store"] = store

        serializer = self.serializer_class(data=req_data)
        if serializer.is_valid():
            serializer.save()
            return responses.client_success({
                "menu": serializer.data
            })

        raise responses.client_error({
            "errors": serializer.errors
        })


class MenuAPI(
        RetrieveUpdateAPIView,
        EmployeeMixin,
        StoreMixin
):

    permission_classes = [IsAuthenticatedOrReadOnly]
    serializer_class = serializers.MenuSerializer

    def get_object(self, pk=None):
        try:
            return Menu.objects.get(pk=pk)
        except:
            return None

    def retrieve(self, request, *args, **kwargs):
        store = self.get_store(kwargs['store_id'])
        menu = self.get_object(kwargs['menu_id'])

        if menu.store != store:
            raise responses.client_error({
                "errors": f"{menu} is not in {store}"
            })

        serializer = self.serializer_class(menu)
        return responses.client_success({
            "menu": serializer.data
        })

    def update(self, request, *args, **kwargs):
        owner = self.get_owner(request.user)
        store = self.get_store(kwargs['store_id'])
        menu = self.get_object(kwargs['menu_id'])

        if menu.store != store:
            raise responses.client_error({
                "errors": f"{menu} is not in {store}"
            })

        serializer = self.serializer_class(menu, data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return responses.client_success({
                "menu": serializer.data
            })
        else:
            raise responses.client_error({
                "errors": serializer.errors
            })


class ItemCreateAPI(
        CreateAPIView,
        EmployeeMixin,
        StoreMixin,
        MenuMixin,
):

    permission_classes = [IsAuthenticated]
    serializer_class = serializers.ItemCreateSerializer

    def post(self, request, *args, **kwargs):
        owner = self.get_owner(request.user)
        store = self.get_store(kwargs['store_id'])
        menu = self.get_menu(kwargs['menu_id'])

        if menu.store != store:
            raise responses.client_error({
                "errors": f"{menu} is not in {store}"
            })

        req_data = request.data.dict()
        req_data['menu'] = menu.pk

        ser = self.serializer_class(data=req_data)
        if ser.is_valid(raise_exception=True):
            ser.save()
            return responses.client_success({
                "item": ser.data
            })
        else:
            return responses.client_error({
                "errors": ser.errors
            })


class ItemAPI(
        RetrieveUpdateAPIView,
        EmployeeMixin,
        StoreMixin,
        MenuMixin,
):

    permission_classes = [IsAuthenticated]
    serializer_class = serializers.ItemSerializer

    def get_object(self, pk=None):
        try:
            return Item.objects.get(pk=pk)
        except:
            return None

    def retrieve(self, request, *args, **kwargs):
        store = self.get_store(kwargs['store_id'])
        menu = self.get_menu(kwargs['menu_id'])
        item = self.get_object(kwargs['item_id'])

        if not item:
            raise responses.client_error({
                "errors": "Item is not exist"
            })
        elif item.menu != menu:
            raise responses.client_error({
                "errors": f"{item} is not in {menu}"
            })
        elif menu.store != store:
            raise responses.client_error({
                "errors": f"{menu} is not in {store}"
            })
        
        ser = self.serializer_class(item)
        return responses.client_success({
                "item": ser.data
            })

    def update(self, request, *args, **kwargs):
        owner = self.get_owner(request.user)
        store = self.get_store(kwargs['store_id'])
        menu = self.get_menu(kwargs['menu_id'])
        item = self.get_object(kwargs['item_id'])

        ser = self.serializer_class(item, request.data)
        if ser.is_valid(raise_exception=True):
            ser.save()
            return responses.client_success({
                "item": ser.data
            })
        else:
            return responses.client_error({
                "errors": ser.errors
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


class StoreMenuListAPI(
        ListAPIView,
        StoreMixin,
):

    def get(self, request, *args, **kwargs):
        store = self.get_store(kwargs['store_id'])

        menu_list = store.menu_set.all()
        return responses.client_success({
            "store": serializers.StoreSerializer(store).data,
            "menus": [
                serializers.MenuSerializer(menu).data for menu in menu_list
            ],
        })


class StoreEmployeeListAPI(
        ListAPIView,
        EmployeeMixin,
        StoreMixin,
):
    permission_class = [IsAuthenticated,]

    def get(self, request, *args, **kwargs):
        empl = self.get_hired_employee(request.user)

        # get empl's store
        if empl.employee_role == "owner":
            store = Store.objects.get(owner=empl)
        else:
            store = JoinStore.objects.get(employee=empl).store

        # get store's employee list
        joinstore_list = store.joinstore_set.all()
        employee_list = [store.owner] + [js.employee for js in joinstore_list]

        return responses.client_success({
            "store": serializers.StoreSerializer(store).data,
            "employees": [
                {
                    "employee": EmployeeSerializer(empl).data,
                    "user": UserSerializer(empl.user).data,
                } for empl in employee_list
            ]
        })


class MenuListAPI(
        ListAPIView,
        StoreMixin,
        MenuMixin
):

    def get_object(self, pk=None):
        try:
            return Menu.objects.get(pk=pk)
        except:
            return None

    def get(self, request, *args, **kwargs):
        store = self.get_store(kwargs['store_id'])
        menu = self.get_menu(kwargs['menu_id'])

        if menu.store != store:
            raise responses.client_error({
                "errors": f"{menu} is not in {store}"
            })

        item_list = menu.item_set.all()
        return responses.client_success({
            "store": serializers.StoreSerializer(store).data,
            "menu": serializers.MenuSerializer(menu).data,
            "items": [
                serializers.ItemSerializer(item).data for item in item_list
            ],
        })
