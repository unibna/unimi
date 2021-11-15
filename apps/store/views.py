from rest_framework.exceptions import NotFound
from rest_framework.generics import RetrieveUpdateAPIView, CreateAPIView
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.filters import SearchFilter, OrderingFilter

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
    ItemExtraGroup,
    JoinStore,
    Store,
    Menu, Item
)
from apps.store.mixins import (
    ItemMixin,
    StoreMixin,
    MenuMixin,
)
from apps.core import responses


class StoreAPI(
        RetrieveUpdateAPIView,
        CreateAPIView,
        EmployeeMixin,
        StoreMixin,
):

    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, *args, **kwargs):
        # check if request user is empl
        
        if "store_id" not in kwargs:
            # list all store
            res = self.list_store()
        else:
            # get store by id
            res = self.retrieve_store(request, kwargs["store_id"])
        
        return responses.client_success(res)

    def list_store(self):
        store_list = Store.objects.all()
        stores = []
        for store in store_list:
            store = serializers.StoreSerializer(store).data
            store.pop("secret_key")
            stores.append(store)
        return {"stores": stores}

    def retrieve_store(self, request, pk=None):
        empl = self.get_employee(request.user)
        store = self.get_store(pk=pk)
        if not store:
            raise responses.NOT_FOUND

        res = {}
        res["store"] = serializers.StoreSerializer(store).data
        if store.owner != empl:
            res["store"].pop("secret_key")

        if "menu_id" in request.GET:
            pass
        elif "item_id" in request.GET:
            pass
        else:
            res["menus"] = [
                serializers.MenuSerializer(menu).data for menu in store.menu_set.all()
            ]
        
        return res

    def post(self, request, *args, **kwargs):
        empl = self.get_free_employee(request.user)

        serializer = serializers.StoreCreateSerializer(data=request.data)
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

    def put(self, request, *args, **kwargs):
        # check if request user is store's owner
        owner = self.get_owner(request.user)
        store = self.get_store(kwargs['store_id'])

        serializer = serializers.StoreSerializer(store, data=request.data)
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
        # valid request data
        if "secret_key" not in request.POST \
                or "employee_role" not in request.POST:
            print("1")
            raise responses.BAD_REQUEST

        empl = self.get_free_employee(request.user)
        if not empl:
            raise responses.PERMISSION_DENIED

        # get store by secret key
        secret_key = request.POST["secret_key"]
        store = Store.objects.filter(secret_key=secret_key)
        if not store:
            raise responses.NOT_FOUND
        store = store[0]

        # verify role
        employee_role = request.POST["employee_role"]
        if employee_role != "staff" and employee_role != "manager":
            raise responses.BAD_REQUEST

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

class MenuAPI(
        RetrieveUpdateAPIView,
        CreateAPIView,
        EmployeeMixin,
        StoreMixin,
        MenuMixin,
):

    permissions_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, *args, **kwargs):
        if "menu_id" not in kwargs:
            # list all menu
            res = self.list_menu()
        else:
            # get menu by id
            res = self.retrieve_menu(request, *args, **kwargs)

        return responses.client_success(res)

    def list_menu(self):
        return {
            "menus": [
                serializers.MenuSerializer(menu).data for menu in Menu.objects.all()
            ]
        }

    def retrieve_menu(self, request, *args, **kwargs):
        menu = self.get_menu(kwargs["menu_id"])
        if not menu:
            raise responses.NOT_FOUND

        res = {}
        res["menu"] = serializers.MenuSerializer(menu).data

        # get menu's items
        if "item_id" in request.GET:
            pass
        else:
            item_list = menu.item_set.all()
            res["items"] = [
                serializers.ItemSerializer(item).data for item in item_list
            ]

        return res

    def post(self, request, *args, **kwargs):
        owner = self.get_owner(request.user)
        store = Store.objects.get(owner=owner)

        req_data = request.data.dict()
        req_data["store"] = store.pk

        serializer = serializers.MenuCreateSerialzer(data=req_data)
        if serializer.is_valid():
            print(type(serializer.save()), serializer.save())
            return responses.client_success({
                "menu": serializer.data
            })

        raise responses.client_error({
            "errors": serializer.errors
        })

    def put(self, request, *args, **kwargs):
        owner = self.get_owner(request.user)
        menu = self.get_menu(kwargs['menu_id'])

        if menu.store != Store.objects.get(owner=owner):
            raise responses.PERMISSION_DENIED

        serializer = serializers.MenuSerializer(menu, data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return responses.client_success({
                "menu": serializer.data
            })
        else:
            raise responses.client_error({
                "errors": serializer.errors
            })


class ItemAPI(
        RetrieveUpdateAPIView,
        CreateAPIView,
        StoreMixin,
        EmployeeMixin,
        MenuMixin,
        ItemMixin,
):

    permissions_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, *args, **kwargs):
        if "item_id" not in kwargs:
            # list all item
            res = self.list_item()
        else:
            # get item by id
            res = self.retrieve_item(request, *args, **kwargs)

        return responses.client_success(res)

    def list_item(self):
        item_list = Item.objects.all()
        return {
            "items": [
                serializers.ItemSerializer(item).data for item in item_list
            ]
        }

    def retrieve_item(self, request, *args, **kwargs):
        item = self.get_item(kwargs["item_id"])
        if not item:
            raise responses.NOT_FOUND

        # get extra group
        # get extra

        return {
            "item": serializers.ItemSerializer(item).data
        }

    def post(self, request, *args, **kwargs):
        # valid request params
        menu = self.get_menu(request.POST["menu"])
        if not menu:
            raise responses.NOT_FOUND

        # verify owner permission
        owner = self.get_owner(request.user)
        if menu.store != Store.objects.get(owner=owner):
            raise responses.PERMISSION_DENIED

        req_data = request.data.dict()
        req_data['menu'] = menu.pk

        ser = serializers.ItemCreateSerializer(data=req_data)
        if ser.is_valid(raise_exception=True):
            ser.save()
            return responses.client_success({
                "item": ser.data
            })
        else:
            raise responses.client_error({
                "errors": ser.errors
            })

    def put(self, request, *args, **kwargs):
        owner = self.get_owner(request.user)
        item = self.get_item(kwargs['item_id'])

        # verify owner permission
        if item.menu.store != Store.objects.get(owner=owner):
            raise responses.PERMISSION_DENIED

        ser = serializers.ItemSerializer(item, request.data)
        if ser.is_valid(raise_exception=True):
            ser.save()
            return responses.client_success({
                "item": ser.data
            })
        else:
            raise responses.client_error({
                "errors": ser.errors
            })


class ItemExtraGroupAPI(
        RetrieveUpdateAPIView,
        CreateAPIView,
        EmployeeMixin,
        StoreMixin,
        MenuMixin,
        ItemMixin,
):

    permissions_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, *args, **kwargs):
        print(request.GET)
        if "item" in request.GET:
            res = self.list_item_extra_group(request, *args, **kwargs)
        elif "item_extra_group_id" in kwargs:
            res = self.retrive_item_extra_group(request, *args, **kwargs)
        else:
            raise responses.BAD_REQUEST

        return responses.client_success(res)

    def retrive_item_extra_group(self, request, *args, **kwargs):
        extra_group = self.get_extra_group(kwargs["item_extra_group_id"])
        if not extra_group:
            raise responses.NOT_FOUND

        # get group's item extras
        extra_list = extra_group.iteamextra_set.all()
        return {
            "item_extra_groups": serializers.ItemExtraGroupSerializer(extra_group).data,
            "item_extras": [
                serializers.ItemExtraSerializer(extra).data for extra in extra_list
            ]
        }

    def list_item_extra_group(self, request, *args, **kwargs):
        item = self.get_item(request.GET["item"])
        if not item:
            raise responses.NOT_FOUND

        # get item's extra group
        extra_group_list = item.itemextragroup_set.all()
        return {
            "item": serializers.ItemSerializer(item).data,
            "item_extra_groups": [
                serializers.ItemExtraGroupSerializer(group).data for group in extra_group_list
            ]
        }

    def post(self, request, *args, **kwargs):
        if "item" not in request.POST:
            raise responses.BAD_REQUEST

        item = self.get_item(request.POST["item"])
        owner = self.get_owner(request.user)

        print(item.menu.store.owner)
        print(owner)
        # verify owner permisson
        if item.menu.store.owner != owner:
            raise responses.PERMISSION_DENIED

        serializer = serializers.ItemExtraGroupCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return responses.client_success({
                "item_extra_group": serializer.data
            })
        else:
            raise responses.client_error({
                "erros": serializer.errors
            })

    def put(self, request, *args, **kwargs):
        if "item_extra_group_id" not in kwargs:
            raise responses.BAD_REQUEST

        owner = self.get_owner(request.user)
        extra_group = self.get_extra_group(kwargs["item_extra_group_id"])

        # verify owner permission
        if extra_group.item.menu.store.owner != owner:
            raise responses.PERMISSION_DENIED

        serializer = serializers.ItemExtraGroupSerializer(extra_group, request.data)
        if serializer.is_valid():
            serializer.save()
            return responses.client_success({
                "item_extra_group": serializer.data
            })
        else:
            raise responses.client_error({
                "erros": serializer.errors
            })

class ItemExtraAPI(
        RetrieveUpdateAPIView,
        CreateAPIView,
        EmployeeMixin,
        StoreMixin,
        MenuMixin,
        ItemMixin,
):

    permissions_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, *args, **kwargs):
        if "item-extra-group" in request.GET:
            res = self.list_item_extra(request, *args, **kwargs)
        elif "item_extra_id" in kwargs:
            res = self.retrieve_item_extra(request, *args, **kwargs)
        else:
            raise responses.BAD_REQUEST
        
        return responses.client_success(res)

    def list_item_extra(self, request, *args, **kwargs):
        # get extra group
        extra_group = self.get_extra_group(request.GET["item-extra-group"])
        if not extra_group:
            raise responses.NOT_FOUND

        # get all extra
        extra_list = extra_group.iteamextra_set.all()
        return {
            "item_extra_group": serializers.ItemExtraGroupCreateSerializer(extra_group).data,
            "item_extras": [
                serializers.ItemExtraSeirializer(extra).data for extra in extra_list
            ]
        }

    def retrieve_item_extra(self, request, *args, **kwargs):
        # get extra
        extra = self.get_extra(kwargs["item_extra_id"])
        return {
            "item_extra": serializers.ItemExtraSeirializer(extra).data
        }

    def post(self, request, *args, **kwargs):
        if "item_extra_group" not in request.POST:
            raise responses.BAD_REQUEST
        
        owner = self.get_owner(request.user)
        extra_group = self.get_extra_group(request.POST["item_extra_group"])

        # verify owner permission
        if extra_group.item.menu.store.owner != owner:
            raise responses.PERMISSION_DENIED

        serializer = serializers.ItemExtraCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return responses.client_success({
                "item_extra": serializer.data
            })
        else:
            raise responses.client_error({
                "errors": serializer.errors
            })

    def put(self, request, *args, **kwargs):
        if "item_extra_id" not in kwargs:
            raise responses.BAD_REQUEST

        owner = self.get_owner(request.user)
        extra = self.get_extra(kwargs["item_extra_id"])

        # verify owner permission
        if extra.item_extra_group.item.menu.store.owner != owner:
            raise responses.PERMISSION_DENIED

        serializer = serializers.ItemExtraSerializer(extra, request.data)
        if serializer.is_valid():
            serializer.save()
            return responses.client_success({
                "item_extra": serializer.data
            })
        else:
            raise responses.client_error({
                "errors": serializer.errors
            })
