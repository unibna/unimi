from django.urls import path
from rest_framework.routers import SimpleRouter

from . import views

router = SimpleRouter()


urlpatterns = [
    # store
    path('create', views.StoreCreateAPI.as_view(), name='api-store-create'),
    path('list', views.StoreListAPI.as_view(), name='api-store-list'),
    path('<int:store_id>/get', views.StoreRetrieveUpdateAPI.as_view(), name='api-store-get'),
    path('<int:store_id>/update', views.StoreRetrieveUpdateAPI.as_view(), name='api-store-update'),

    # employee join a store
    path('<int:store_id>/join', views.JoinStoreAPI.as_view(), name='api-store-join'),
    # list all employee in a store (only employee users can use)
    path('<int:store_id>/employee/list', views.StoreEmployeeListAPI.as_view(), name='api-store-employee-list'),

    # menu
    path('<int:store_id>/menu/create', views.MenuCreateAPI.as_view(), name='api-store-menu-create'),
    path('<int:store_id>/menu/list', views.StoreMenuListAPI.as_view(), name='api-store-menu-list'),
    path('<int:store_id>/menu/<int:menu_id>/get', views.MenuAPI.as_view(), name='api-store-menu-get'),
    path('<int:store_id>/menu/<int:menu_id>/update', views.MenuAPI.as_view(), name='api-store-menu-update'),

    # item
    path('<int:store_id>/menu/<int:menu_id>/item/create', views.ItemCreateAPI.as_view(), name='api-store-item-create'),
    path('<int:store_id>/menu/<int:menu_id>/item/list', views.MenuListAPI.as_view(), name='api-store-item-list'),
    path('<int:store_id>/menu/<int:menu_id>/item/<int:item_id>/get', views.ItemAPI.as_view(), name='api-store-item-get'),
    path('<int:store_id>/menu/<int:menu_id>/item/<int:item_id>/update', views.ItemAPI.as_view(), name='api-store-item-update'),
]
urlpatterns += router.urls
