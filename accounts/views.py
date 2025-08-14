import logging

from django.contrib.auth import get_user_model
from django.db import models
from rest_framework.views import APIView 
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from drf_spectacular.utils import extend_schema 

from utils.responses import CustomResponse

from .serializers import (
    CustomTokenObtainPairSerializer,
    UserCreationSerializer,
    UserChangeSerializer,
    LogoutSerializer,
    UserSerializer
)


logger = logging.getLogger('accounts')
User = get_user_model()

# Create your views here.

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

class RegistrationAPIView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle] 

    @extend_schema(
        operation_id='register_user',
        summary='Register New User',
        description='Create a new user account',
        request=UserCreationSerializer,
        responses={
            201: UserSerializer,
            400: {'description': 'Validation errors'}
        },
        tags=['Authentication']
    )
    def post(self, request):
        logger.info(
            f"Registration attempt from IP: {get_client_ip(request)}"
        )
        serializer = UserCreationSerializer(request.data)

        if serializer.is_valid():
            user = serializer.save()
            user_serializer = UserSerializer(user)

            logger.info(
                f"User registered successfully {user.username} {user.email}" #type:ignore
            )

            return CustomResponse.created(
                data= user_serializer.data,
                message="User created successfully"
            )
        else:
            logger.warning(
                f"Registration attempt failed",
            )
            return CustomResponse.bad_request(
                errors = serializer.errors,
                message = "Registration Failed"
            )

class LoginView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle]

    @extend_schema(
        operation_id='login_user',
        summary='User Login',
        description='Authenticate user and return access and refresh tokens',
        request=CustomTokenObtainPairSerializer,
        responses={
            200: CustomTokenObtainPairSerializer,
            401: {'description': 'Invalid credentials'}
        },
        tags=['Authentication']
    )
    def post(self, request):
        client_ip = get_client_ip(request)
        logger.info(
            f'login attempt for {client_ip}'
        )
        login_serializer = CustomTokenObtainPairSerializer(request.data)
        if login_serializer.is_valid():
            try:
                tokens = login_serializer.validated_data
                user = tokens.get('user') #type:ignore 
                logger.info(
                    f"Successful login for {user}"
                )
                return CustomResponse.success(
                    data=tokens,
                    message = 'Login successful'
                )
            except Exception as e:
                logger.error(
                    f"Unexpected error during login", exc_info=True
                )
                return CustomResponse.internal_server_error(

                )
        else:
            logger.warning(
                f"Failed login attempt for {client_ip}"
            )
            return CustomResponse.unauthorized(
                message="Invalid Credentials"
            )



class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id='logout_user',
        summary='User Logout',
        description='Logout user and blacklist refresh token',
        request=LogoutSerializer,
        responses={
            204: {'description': 'Logout successful'},
            400: {'description': 'Invalid request'},
            500: {'description': 'Internal server error'}
        },
        tags=['Authentication']
    )
    def post(self, request):
        serializer = LogoutSerializer(request.data)
        if serializer.is_valid():
            try:
                serializer.save()
                logger.info(
                    f"{request.user} logged out successfully"
                )
                return CustomResponse.no_content()
            except Exception as e:
                logger.error(
                    "Error occured during logout"
                )
                return CustomResponse.internal_server_error()
        else:
            logger.warning(
                f"Logout failed for user {request.user}"
            )
            return CustomResponse.bad_request(
                errors=serializer.errors
            )

class UserChangeAPIView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]


    @extend_schema(
        operation_id='update_user_profile',
        summary='Update User Profile',
        description='Update user profile information',
        request=UserChangeSerializer,
        responses={
            200: UserSerializer,
            400: {'description': 'Validation errors'},
            500: {'description': 'Internal server error'}
        },
        tags=['Users']
    )
    def put(self, request):
        serializer = UserChangeSerializer(
            instance = request.user,
            data = request.data,
            partial=True 
        )

        if serializer.is_valid():
            try:
                user = serializer.save()
                response_serializer = UserSerializer(user)
                logger.info(
                    f"{user}'s profile updated successfully"
                )
                return CustomResponse.success(
                    data = response_serializer.data,
                    message='profile updated successfully'
                )
            except Exception as e:
                logger.error(
                    f"Error updating profile for {request.user}", exc_info=True
                    )
                return CustomResponse.internal_server_error()
        else:
            logger.warning(
                f'Profile update validation error'
            )
            return CustomResponse.bad_request(
                message='profile update failed',
                errors=serializer.errors
            )