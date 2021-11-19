import logging
import re
from django.shortcuts import resolve_url
from rest_framework import serializers
from rest_framework.utils import field_mapping

from apps.account.models import (
    CustomUser,
    Customer, CustomerAddress,
    Employee, Shipper
)
from apps.core import responses, utils


class UserCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = CustomUser
        fields = ('email', 'password', 'account_role')


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = CustomUser
        fields = (
            'id', 'email', 'username',
            'is_valid', 'account_role',
            'first_name', 'last_name', 'phone'
        )
        read_only_fields = (
            'email', 'username',
            'account_role', 'is_valid',
        )

    def validate(self, attrs):
        phone = attrs.get('phone', None)
        first_name = attrs.get('first_name', None)
        last_name = attrs.get('last_name', None)

        error_list = []
        if not utils.is_phone(phone):
            error_list.append("phone")
        if not utils.is_valid_name(first_name):
            error_list.append("first_name")
        if not utils.is_valid_name(last_name):
            error_list.append("last_name")

        if error_list:
            raise responses.client_error({
                "Invalid Parameters": error_list
            })
        else:
            return attrs

    def update(self, instance, validated_data):
        user = super().update(instance, validated_data)

        # check if user can be activate
        if user.phone \
                and user.first_name \
                and user.last_name \
                and user.email:
            user.is_valid = True

        return user


class CustomerSerializer(serializers.ModelSerializer):

    class Meta:

        model = Customer
        fields = '__all__'
        read_only_fields = ['user']


class CustomerAddressCreateSerializer(serializers.ModelSerializer):

    class Meta:

        model = CustomerAddress
        fields = '__all__'


class CustomerAddressSerializer(serializers.ModelSerializer):

    class Meta:

        model = CustomerAddress
        fields = '__all__'
        read_only_fields = ['customer']


class EmployeeSerializer(serializers.ModelSerializer):

    class Meta:

        model = Employee
        fields = '__all__'
        read_only_fields = ['user']


class ShipperSerializer(serializers.ModelSerializer):

    class Meta:

        model = Shipper
        fields = '__all__'
        read_only_fields = ['user']
