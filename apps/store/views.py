import json
from rest_framework.generics import RetrieveAPIView, RetrieveUpdateAPIView, CreateAPIView
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Q
from apps import store

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
    Menu, Item,
    StoreCategory
)
from apps.store.mixins import (
    ItemMixin,
    StoreMixin,
    MenuMixin,
)
from apps.core import responses


class StoreCategoryAPI(
    RetrieveUpdateAPIView,
    EmployeeMixin,
    StoreMixin,
):

    serializer_class = serializers.StoreCategorySerializer

    def get_object(self, pk=None):
        try:
            return StoreCategory.objects.get(pk=pk)
        except:
            return None

    def get(self, request, *args, **kwargs):
        if "category_id" in kwargs:
            res = self.retrieve_category(request, *args, **kwargs)
        else:
            res = self.list(request, *args, **kwargs)

        return responses.client_success(res)

    def retrieve_category(self, request, *args, **kwargs):
        cat = self.get_object(kwargs["category_id"])
        if not cat:
            raise responses.NOT_FOUND

        stores = [
            serializers.StoreSerializer(store).data for store in cat.store_set.all()
        ]
        for i in range(len(stores)):
            stores[i].pop("secret_key")

        res = {}
        res["store_category"] = serializers.StoreCategorySerializer(cat).data
        res["store_category"]["stores"] = stores
        return res

    def list(self, request, *args, **kwargs):
        cat_list = StoreCategory.objects.all()
        return {
            "store_categories": [
                serializers.StoreCategorySerializer(cat).data for cat in cat_list
            ]
        }


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
            store["store_category"] = serializers.StoreCategorySerializer(
                self.get_store_category(store["store_category"])
            ).data
            store.pop("secret_key")
            stores.append(store)
        return {"stores": stores}

    def retrieve_store(self, request, pk=None):
        empl = self.get_employee(request.user)
        store = self.get_store(pk=pk)
        if not store:
            raise responses.NOT_FOUND
        menu_list = store.menu_set.all()

        res = {}
        res["store"] = serializers.StoreSerializer(store).data
        res["store"]["menus"] = []

        if res["store"]["store_category"]:
            res["store"]["store_category"] = serializers.StoreCategorySerializer(
                self.get_store_category(res["store"]["store_category"])
            ).data
        if store.owner != empl:
            res["store"].pop("secret_key")

        for menu in menu_list:
            item_list = menu.item_set.all()
            menu_data = serializers.MenuSerializer(menu).data
            menu_data["items"] = [
                serializers.ItemSerializer(item).data for item in item_list
            ]
            res["store"]["menus"].append(menu_data)

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

            res = {}
            res["store"] = serializers.StoreSerializer(store).data
            res["store"]["store_category"] = serializers.StoreCategorySerializer(
                self.get_store_category(res["store"]["store_category"])
            ).data

            return responses.client_success(res)
        else:
            raise responses.client_error({
                "errors": serializer.errors
            })

    def put(self, request, *args, **kwargs):
        # check if request user is store's owner
        owner = self.get_owner(request.user)
        store = self.get_store(kwargs['store_id'])

        if store.owner != owner:
            raise responses.PERMISSION_DENIED
        elif not store or not owner:
            raise responses.BAD_REQUEST

        serializer = serializers.StoreSerializer(instance=store, data=request.data)
        if serializer.is_valid():
            store = serializer.save()

            res = {}
            res["store"] = serializers.StoreSerializer(store).data
            res["store"]["store_category"] = serializers.StoreCategorySerializer(
                self.get_store_category(res["store"]["store_category"])
            ).data

            return responses.client_success(res)
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

    def post(self, request, *args, **kwargs):
        # valid request data
        if "secret_key" not in request.POST \
                or "employee_role" not in request.POST:
            print("1")
            raise responses.BAD_REQUEST

        empl = self.get_free_employee(request.user)
        if not empl:
            raise responses.client_error({
                "errors": "You are in a store"
            })

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

        serializer = serializers.JoinStoreSerializer(data={
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
        store = Store.objects.filter(owner=owner)
        if not store:
            raise responses.BAD_REQUEST
        store = store[0]

        if type(request.data) == dict:
            req_data = request.data
        else:
            req_data = request.data.dict()
        req_data["store"] = store.pk

        serializer = serializers.MenuCreateSerialzer(data=req_data)
        if serializer.is_valid():
            menu = serializer.save()

            res = {}
            res["menu"] = serializers.MenuSerializer(menu).data
            res["menu"]["items"] = []
            if "items" in request.data:
                res["menu"]["items"] = self.create_menu_items(request, menu)

            return responses.client_success(res)
        else:
            raise responses.client_error({
                "errors": serializer.errors
            })

    def create_menu_items(self, request, menu):
        # parse items value to dict
        try:
            if type(request.data) == dict:
                items = request.data["items"]
            else:
                items = json.loads(request.data["items"])
        except:
            raise responses.client_error({
                "errors": "Cannot parse items value - Invalid json"
            })

        success_items = []
        failed_items = []
        for item in items:
            try:
                item["menu"] = menu
                item = Item(**item)
                item.save()
            except:
                failed_items.append(item)
            else:
                success_items.append(item)
        
        print(f"Success {len(success_items)}")
        print(success_items)
        print(f"Failed {len(failed_items)}")
        print(failed_items)

        item_data = [
            serializers.ItemSerializer(item).data for item in success_items
        ]
        return item_data

    def put(self, request, *args, **kwargs):
        owner = self.get_owner(request.user)
        menu = self.get_menu(kwargs['menu_id'])

        if menu.store not in Store.objects.filter(owner=owner):
            raise responses.PERMISSION_DENIED

        serializer = serializers.MenuSerializer(menu, data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()

            items = menu.item_set.all()
            res = {}
            res["menu"] = serializers.MenuSerializer(menu).data
            res["menu"]["items"] = [
                serializers.ItemSerializer(item).data for item in items
            ]

            return responses.client_success(res)
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
        res = {
            "item": serializers.ItemSerializer(item).data
        }

        # get extra group
        extra_group_list = item.itemextragroup_set.all()
        extra_groups = [
            serializers.ItemExtraGroupSerializer(group).data for group in extra_group_list
        ]
        for i in range(len(extra_groups)):
            extra_groups[i]["item_extras"] = [
                serializers.ItemExtraSerializer(extra).data for extra in extra_group_list[i].iteamextra_set.all()
            ]

        res["item"]["item_extra_groups"] = extra_groups

        return res

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
        if item.menu.store.owner != owner:
            raise responses.PERMISSION_DENIED

        ser = serializers.ItemSerializer(item, request.data)
        if ser.is_valid():
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
        res = {
            "item_extra_group": serializers.ItemExtraGroupSerializer(extra_group).data
        }
        
        res["item_extra_group"]["item_extras"] = [
            serializers.ItemExtraSerializer(extra).data for extra in extra_group.iteamextra_set.all()
        ]
        return res

    def list_item_extra_group(self, request, *args, **kwargs):
        item = self.get_item(request.GET["item"])
        if not item:
            raise responses.NOT_FOUND
        res = {
            "item": serializers.ItemSerializer(item).data,
        }
        res["item"]["item_extra_groups"] = [
            serializers.ItemExtraGroupSerializer(group).data for group in item.itemextragroup_set.all()
        ]
        return res

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
        res = {
            "item_extra_group": serializers.ItemExtraGroupCreateSerializer(extra_group).data,
        }
        # get all extra
        res["item_extra_group"]["item_extras"] = [
            serializers.ItemExtraSerializer(extra).data for extra in extra_group.iteamextra_set.all()
        ]
        return res

    def retrieve_item_extra(self, request, *args, **kwargs):
        # get extra
        extra = self.get_extra(kwargs["item_extra_id"])
        return {
            # "item": serializers.ItemSerializer(extra.item_extra_group.item).data,
            "item_extra": serializers.ItemExtraSerializer(extra).data
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


class StoreSearchAPI(
        RetrieveAPIView,
        StoreMixin,
        ItemMixin,
        MenuMixin
):

    def get(self, request, *args, **kwargs):
        if "keyword" not in request.GET and len(request.GET) != 1:
            raise responses.BAD_REQUEST

        key_word = request.GET["keyword"]

        store_result = Store.objects.filter(
            Q(name__contains=key_word) | Q(store_category__name__contains=key_word),
            # is_valid=True,
        )
        item_result = Item.objects.filter(
            is_active=True,
            name__contains=key_word
        )

        res = {}
        res["stores"] = [
            serializers.StoreSerializer(store).data for store in store_result
        ]
        for i in range(len(res["stores"])):
            res["stores"][i].pop("secret_key")
            res["stores"][i]["store_category"] = StoreCategory.objects.get(pk=res["stores"][i]["store_category"]).name

        res['items'] = [
            serializers.ItemSerializer(item).data for item in item_result
        ]

        return responses.client_success(res)
