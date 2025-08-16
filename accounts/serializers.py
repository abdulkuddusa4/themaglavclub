from threading import Thread

from django.conf import settings
from django.core.mail import send_mail
from rest_framework import serializers

from rest_framework import serializers
from accounts.models import JTUser
from django.contrib.auth import get_user_model


UserModel = get_user_model()


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    new_password = serializers.CharField(write_only=True, style={'input_type': 'password'})


class JTUserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = UserModel
        fields = [
            'first_name', 'last_name', 'full_name',
            'profile_image', 'age', 'gender',
        ]
        # read_only_fields = ['email', 'username', 'otp', 'is_superuser', 'is_staff', 'date_joined']

    def get_full_name(self, obj):
        return obj.first_name + ' ' + obj.last_name


class UserRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserModel
        fields = ['email', 'password']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        password = validated_data.pop('password')
        email = validated_data.pop('email')
        user = UserModel(email=email)
        user.set_password(password)

        # BLOCK: USER ACTIVATION THROUGH EMAIL. COMMENT IT FOR EASE OF DEVELOPMENT

        user.is_active = False
        user.save()
        Thread(
            target=send_mail,
            kwargs={
                'subject': 'Account Verification Token',
                'message': f'Plz use this Token to verify your account: {user.otp}',
                'from_email': settings.DEFAULT_FROM_EMAIL,
                'recipient_list': [email],
            }
        ).start()

        # END BLOCK

        return user


class AccountActivationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField()
