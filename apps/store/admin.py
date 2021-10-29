from django.contrib import admin
from django.db import models

from .models import (
    StoreCategory, Store,
    JoinStore,
    Menu, Item
)


admin.site.register(Store)
admin.site.register(JoinStore)
admin.site.register(Menu)
admin.site.register(Item)


@admin.register(StoreCategory)
class StoreCategoryAdmin(admin.ModelAdmin):

    model = StoreCategory
    readonly_fields = ['slug']
