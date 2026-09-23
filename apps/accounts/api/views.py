from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.services.auth import AuthService

from .serializers import (
    RequestLoginOTPSerializer,
    VerifyLoginOTPSerializer,
    MeSerializer,
)


class RequestLoginOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RequestLoginOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data["phone"]

        user, challenge, _code = AuthService.request_login_otp(
            phone=phone,
        )

        return Response(
            {
                "challenge_id": str(challenge.id),
                "message": "OTP sent successfully.",
            },
            status=status.HTTP_200_OK,
        )


class VerifyLoginOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerifyLoginOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            tokens = AuthService.verify_login_otp(
                challenge_id=serializer.validated_data["challenge_id"],
                code=serializer.validated_data["code"],
            )
        except ValueError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "access": tokens["access"],
                "refresh": tokens["refresh"],
            },
            status=status.HTTP_200_OK,
        )


class MeView(APIView):
    def get(self, request):
        serializer = MeSerializer(request.user)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )