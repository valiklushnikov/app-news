from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import login, logout
from .models import User
from . import serializers


class RegisterView(generics.CreateAPIView):
    """Register a new user."""

    queryset = User.objects.all()
    serializer_class = serializers.UserRegistrationSerializer
    permission_classes = (permissions.AllowAny,)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)

        return Response({
            "user": serializers.UserProfileSerializer(user).data,
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "message": "User registered successfully."
        }, status=status.HTTP_201_CREATED)


class LoginView(generics.GenericAPIView):
    """Login a user."""

    serializer_class = serializers.UserLoginSerializer
    permission_classes = (permissions.AllowAny,)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        login(request, user)
        refresh = RefreshToken.for_user(user)

        return Response({
            "user": serializers.UserProfileSerializer(user).data,
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "message": "User login successfully."
        }, status=status.HTTP_200_OK)


class ProfileView(generics.RetrieveUpdateAPIView):
    """Profile view and update."""

    serializer_class = serializers.UserProfileSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return serializers.UserProfileUpdateSerializer
        return serializers.UserProfileSerializer


class ChangePasswordView(generics.UpdateAPIView):
    """Password change view."""

    serializer_class = serializers.ChangePasswordSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            "message": "Password changed successfully."
        }, status=status.HTTP_200_OK)



@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def logout_view(request):
    """Logout a user."""

    try:
        refresh_token = request.data.get("refresh_token")
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
        return Response({
            "message": "User logout successfully."
        }, status=status.HTTP_200_OK)
    except Exception:
        return Response({
            "message": "Invalid token."
        }, status=status.HTTP_400_BAD_REQUEST)