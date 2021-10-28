import logging

from django.http import JsonResponse
from django.contrib.auth.hashers import make_password
from django.utils import timezone

from rest_framework import status, exceptions
from rest_framework.generics import CreateAPIView, RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly

from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from apps.account import serializers
from apps.account.models import (
    CustomUser,
    Employee,
)
from apps.core import responses


class UserCreateAPI(CreateAPIView):

    serializer_class = serializers.UserCreateSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            # hash password
            serializer.validated_data['password'] = make_password(
                serializer.validated_data['password']
            )
            # create an User instance
            serializer.save()
            return responses.client_success({
                "message": "Create Successfully"
            })
        else:
            raise responses.client_error({
                "errors": serializer.errors
            })


class UserLoginAPI(TokenObtainPairView):

    serializer_class = TokenObtainPairSerializer

    def post(self, request):
        serializer = self.serializer_class(request.user, data=request.data)

        if serializer.is_valid():
            # log the login time
            user = CustomUser.objects.get(
                email=request.data["email"]
            )
            user.last_login = timezone.now()
            user.save()

            return responses.client_success(
                serializer.validated_data
            )
        else:
            raise responses.client_error({
                "errors": serializer.errors
            })


class UserAPI(RetrieveUpdateAPIView):

    permission_classes = [IsAuthenticatedOrReadOnly]
    serializer_class = serializers.UserSerializer

    def get_object(self, pk=None):
        if pk:
            user = CustomUser.objects.filter(pk=pk).first()
        else:
            user = self.request.user
        return user or None

    def retrieve(self, request, *args, **kwargs):
        user = self.get_object(kwargs["pk"])

        if not user:
            return responses.client_success({
                "user": {}
            })

        serializer = self.serializer_class(user)
        return responses.client_success({
            "user": serializer.data
        })

    def update(self, request, *args, **kwargs):
        user = self.get_object(kwargs['pk'])

        if not user:
            return responses.client_success({
                "user": {}
            })

        # check permission
        # if request user is user or admin => OK
        if request.user == user:
            logging.info(f"{user} update itself")
        elif request.user.is_superuser:
            logging.info(f"Admin update {user}")
        else:
            logging.error(f"{request.user} have no permission")
            raise responses.PERMISSION_DENIED

        serializer = self.serializer_class(user, data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return responses.client_success({
                "user": serializer.data
            })
        else:
            raise responses.client_error({
                "erros": serializer.errors
            })
