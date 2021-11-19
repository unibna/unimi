from django.urls import path

from . import views

urlpatterns = [
    # order
    path('order', views.OrderAPI.as_view()),
    path('order/<int:order_id>', views.OrderAPI.as_view()),

    # order item
    path('order-item', views.OrderItemAPI.as_view()),
    path('order-item/<int:order_item_id>', views.OrderItemAPI.as_view()),

    # order item extra
    path('order-item-extra', views.OrderItemExtraAPI.as_view()),
    path('order-item-extra/<int:order_item_extra_id>', views.OrderItemExtraAPI.as_view()),
]
urlpatterns
