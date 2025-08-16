import datetime
from threading import Thread

import jwt
from django.conf import settings
from django.template.loader import render_to_string
from rest_framework.generics import get_object_or_404, CreateAPIView, UpdateAPIView, RetrieveUpdateAPIView
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth.models import User
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import ExpiredTokenError

from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate, get_user_model
from django.core.mail import EmailMessage, send_mail
from drf_spectacular.utils import extend_schema
from rest_framework_simplejwt.views import TokenViewBase

# from MyPerfectLife.utils import send_email
# from stripe_payment.permissions import IsSubscribed
# from .models import PerfectUser
from .serializers import (
	PasswordChangeSerializer,
	JTUserSerializer,
	UserRegisterSerializer,
    AccountActivationSerializer
)
from .utils import create_otp

# from .utils import create_otp

UserModel = get_user_model()


from django.contrib.auth import authenticate, get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from django.core.exceptions import ValidationError as DjangoValidationError

# User = get_user_model()


class JTLoginSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        try:
            user = UserModel.objects.get(email=email)
        except UserModel.DoesNotExist:
            raise AuthenticationFailed("No user with this email found.")

        if not user.check_password(password):
            raise AuthenticationFailed("Incorrect password.")

        # If everything is fine, use the parent class to return the token.
        return super().validate(attrs)


class JTLoginView(TokenViewBase):
    serializer_class = JTLoginSerializer

# class PerfectTimezoneView(RetrieveUpdateAPIView):
#     serializer_class = PerfectTimezoneSerializer
#     permission_classes = (IsAuthenticated, )
#
#     def get_object(self):
#         return self.request.user


class UserCreateAPIView(CreateAPIView):
    serializer_class = UserRegisterSerializer
    permission_classes = (AllowAny,)
    queryset = UserModel.objects.all()


@extend_schema(
    request=PasswordChangeSerializer,
    responses={
        200: {
            "example": {
                "success": True,
                "message": "password changed successfully"
            }
        }
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    old_password = request.data.get('old_password')
    if not old_password and request.user.has_usable_password():
        return Response(data={
            "error": "'old_password' is required"
        })
    if not request.user.check_password(old_password):
        return Response(data={
            "Error": "The old password is incorrect."
        }, status=status.HTTP_400_BAD_REQUEST)

    password = request.data.get('password')
    if not password:
        return Response(data={
            "error": "'password' is required"
        })

    request.user.set_password(password)
    request.user.save()
    return Response(data={
        "success": True,
        "message": "Password changed successfully."
    },status=status.HTTP_200_OK)


@extend_schema(
    request={
        'application/json': {
            'example': {
                'email': 'example@gmail.com',
            },
        }
    },
    responses={
        200: {'example':{
            "success": True,
            "message": "an otp is sent to example@gmail.com "
        }}
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def request_password_reset(request):
    email = request.data.get('email')
    email_subject = "Password Reset Request"

    if not email:
        return Response(data={
            "error": "'email' is required"
        }, status=status.HTTP_400_BAD_REQUEST)

    user = get_object_or_404(UserModel, email=email)
    # user.otp = create_otp()
    email_body = f"""
    <html>
        <head></head>
        <body>
            <h3>you password reset otp: <span style="text-color:yellow">{user.otp}</span>
        </body>
    </html>
    """
    print(f"email: {email}. otp: {user.otp}")
    Thread(
        target=send_mail,
        kwargs={
            "subject": email_subject,
            "message": f"your password reset otp: {user.otp}",
            "html_message": email_body,
            "from_email": settings.EMAIL_HOST_USER,
            "recipient_list": [email],
            "fail_silently": False,
        }
    ).start()

    return Response(data={
        "success": True,
        "message": f"an otp is sent to {email}"
    })


@extend_schema(
    request={
        'application/json': {
            'example': {
                'email': 'abc@example.com',
                'otp': '4232',
            }
        }
    },
    responses={
        200: {'example': {
            "success": True,
            "message": "otp is correct"
        }}
    }
)
@api_view(['post'])
@permission_classes([AllowAny])
def verify_otp(request):
    email = request.data.get('email')
    otp = request.data.get('otp')
    if not email:
        return Response(data={
            "error": "'email' is required"
        }, status=status.HTTP_400_BAD_REQUEST)
    if not otp:
        return Response(data={
            "error": "'otp' is required"
        }, status=status.HTTP_400_BAD_REQUEST)
    user = get_object_or_404(UserModel, email=email)
    if user.otp != otp:
        user.otp = create_otp()
        user.save()
        return Response(data={
            "error": "The OTP is incorrect."
        }, status=status.HTTP_400_BAD_REQUEST)
    return Response(data={
        "success": True,
        "password_reset_token": jwt.encode(
            payload={
                "user_id": user.id,
                'type': 'password_reset',
                'exp': datetime.datetime.now(datetime.UTC) + datetime.timedelta(minutes=1)
            },
            key=settings.SECRET_KEY,
            algorithm="HS256"
        ),
        "message": "Otp is Correct"
    })


@extend_schema(
    request={
        'application/json': {
            'example': {
                'email': 'abc@example.com',
                'password_reset_token': 'aslff.aasfd.asdff',
                'new_password': 'string',
            }
        }
    },
    responses={
        200: {'example': {
            "success": True,
            "message": "Password changed successfully."
        }}
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password(request):
    password_reset_token = request.data.get('password_reset_token')
    new_password = request.data.get('new_password')

    if not password_reset_token:
        return Response(data={
            "error": "'password_reset_token' is required"
        }, status=status.HTTP_400_BAD_REQUEST)

    if not new_password:
        return Response(data={
            "error": "'new_password' is required"
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        payload = jwt.decode(password_reset_token, settings.SECRET_KEY,
                             algorithms=["HS256"])
        if 'user_id' not in payload or 'type' not in payload or \
                payload['type'] != 'password_reset':
            raise ValidationError({"error": "given token is not password reset token"})
        user = get_object_or_404(UserModel, id=payload['user_id'])

    except jwt.ExpiredSignatureError as e:
        raise ValidationError({"error": "token expired"})

    except jwt.InvalidTokenError as e:
        raise ValidationError({"error": "invalid token"})

    except jwt.PyJWTError as e:
        raise ValidationError({"error": "token validation failed"})

    if user.check_password(new_password):
        return Response(data={
                "error": "You can not use the old password."
            }, status=status.HTTP_400_BAD_REQUEST
        )
    user.set_password(new_password)
    user.otp = create_otp()
    user.save()
    return Response(data={
        "success": True,
        "message": "Password changed successfully."
    })


class ProfileUpdateView(RetrieveUpdateAPIView):
    serializer_class = JTUserSerializer
    permission_classes = (IsAuthenticated,)

    http_method_names = ('get', 'patch',)
    # parser_classes = (MultiPartParser, FormParser, JSONParser)

    def get_object(self):
        return self.request.user


class ActivateAccountView(CreateAPIView):
    serializer_class = AccountActivationSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        otp = serializer.validated_data['otp']

        user = get_object_or_404(UserModel, email=email)
        print(user)
        print(user.otp, user.otp.__class__)
        print(otp, otp.__class__)
        if user.otp != otp:
            raise ValidationError({"error": "The OTP is incorrect."})
        user.otp = create_otp()
        user.is_active = True
        user.save()

        refresh = RefreshToken.for_user(user)

        return Response(data={
            "success": True,
            "message": "account activated",
            "refresh": str(refresh),
            "access": str(refresh.access_token)
        })
