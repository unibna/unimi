from django.urls import path, re_path
from rest_framework.routers import SimpleRouter

from . import views

router = SimpleRouter()


urlpatterns = [
    # store
    path('store/', views.StoreAPI.as_view()),
    path('store/<int:store_id>', views.StoreAPI.as_view()),

    # join store
    path('store/join', views.JoinStoreAPI.as_view()),

    # menu
    path('menu/', views.MenuAPI.as_view()),
    path('menu/<int:menu_id>', views.MenuAPI.as_view()),

    # item
    path('item/', views.ItemAPI.as_view()),
    path('item/<int:item_id>', views.ItemAPI.as_view()),

    # extra group
    path('item-extra-group', views.ItemExtraGroupAPI.as_view()),
    path('item-extra-group/<int:item_extra_group_id>', views.ItemExtraGroupAPI.as_view()),

    # extra
    path('item-extra', views.ItemExtraAPI.as_view()),
    path('item-extra/<int:item_extra_id>', views.ItemExtraAPI.as_view()),

]
urlpatterns += router.urls
