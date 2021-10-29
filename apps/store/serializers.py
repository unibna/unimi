from rest_framework import serializers

from apps.account import models
from apps.store.models import (
    Store,
    JoinStore,
    Menu, Item,
)
from apps.core import responses


class StoreCreateSerializer(serializers.ModelSerializer):

    class Meta:

        model = Store
        fields = ['name', 'email', 'phone']


class StoreSerializer(serializers.ModelSerializer):

    class Meta:

        model = Store
        fields = '__all__'
        read_only_fields = (
            "rating", "slug",
            "secret_key", "is_valid",
        )

    def update(self, instance, validated_data):
        store = super().update(instance, validated_data)

        # check data valid here
        store.is_valid = True

        return store


class JoinStoreSerializer(serializers.ModelSerializer):

    class Meta:

        model = JoinStore
        fields = '__all__'
        read_only_fields = ['join_date', 'is_valid']


class MenuCreateSerialzer(serializers.ModelSerializer):

    class Meta:

        model = Menu
        fields = ['name', 'store', 'is_active']


class MenuSerializer(serializers.ModelSerializer):

    class Meta:

        model = Menu
        fields = '__all__'
        read_only_fields = [
            'store',
            'created',
        ]


class ItemCreateSerializer(serializers.ModelSerializer):

    class Meta:

        model = Item
        fields = [
            'id',
            'menu',
            'name',
            'is_active',
            'price'
        ]
        optional_fields = ['is_active']
        read_only_fields = ['id']


class ItemSerializer(serializers.ModelSerializer):

    class Meta:

        model = Item
        fields = '__all__'
        read_only_fields = [
            'menu',
            'created',
            'rating'
        ]
