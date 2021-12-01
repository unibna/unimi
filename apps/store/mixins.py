from apps.account.models import (
    Employee,
    EMPLOYEE_ROLES,
)
from apps.store.models import (
    JoinStore,
    Store,
    Menu, Item,
    ItemExtraGroup, IteamExtra,
    StoreCategory
)
from apps.core import responses

class StoreMixin:

    def get_store(self, pk=None):
        try:
            return Store.objects.get(pk=pk)
        except:
            return None

    def list_store(self):
        # should order by (date or something) later
        return Store.objects.all()

    def get_employee_store(self, empl):
        try:
            return JoinStore.objects.get(employee=empl).store
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

    def is_store_owner(self, store, owner):
        try:
            return store.owner == owner
        except:
            return False

    def get_store_category(self, pk=None):
        try:
            return StoreCategory.objects.get(pk=pk)
        except:
            return None


class MenuMixin:

    def get_menu(self, pk=None):
        try:
            return Menu.objects.get(pk=pk)
        except:
            return None


class ItemMixin:

    def get_item(self, pk=None):
        try:
            return Item.objects.get(pk=pk)
        except:
            return None

    def get_extra_group(self, pk=None):
        try:
            return ItemExtraGroup.objects.get(pk=pk)
        except:
            return None

    def get_extra(self, pk=None):
        try:
            return IteamExtra.objects.get(pk=pk)
        except:
            return None