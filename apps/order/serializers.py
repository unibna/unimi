from rest_framework import serializers

from apps.core import responses
from apps.order import models


class OrderCreateSerializer(serializers.ModelSerializer):

    class Meta:

        model = models.Order
        fields = '__all__'
        read_only_fields = ['status', 'created']


class OrderSerializer(serializers.ModelSerializer):

    class Meta:

        model = models.Order
        fields = '__all__'
        read_only_fields = [
            'customer',
            'store',
            'total',
            'created',
        ]


class OrderItemCreateSerializer(serializers.ModelSerializer):

    class Meta:

        model = models.OrderItem
        fields = '__all__'


class OrderItemSerializer(serializers.ModelSerializer):

    class Meta:

        model = models.OrderItem
        fields = '__all__'
        read_only_fields = [
            'order',
            'item',
            'amount',
        ]


class OrderItemExtraCreateSerializer(serializers.ModelSerializer):

    class Meta:

        model = models.OrderItemExtra
        fields = '__all__'


class OrderItemExtraSerializer(serializers.ModelSerializer):

    class Meta:

        model = models.OrderItemExtra
        fields = '__all__'
        read_only_fields = [
            'order_item',
            'item_extra',
            'amount'
        ]