from django.contrib import admin
from django.db import models

from .models import (
    StoreCategory, Store,
    JoinStore,
)


admin.site.register(Store)
admin.site.register(JoinStore)


@admin.register(StoreCategory)
class StoreCategoryAdmin(admin.ModelAdmin):

    model = StoreCategory
    readonly_fields = ['slug']
