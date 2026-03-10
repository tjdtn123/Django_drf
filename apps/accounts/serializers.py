from django.contrib.auth.models import User
from rest_framework import serializers

from .models import Advertiser


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name')
        read_only_fields = ('id',)


class AdvertiserSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Advertiser
        fields = ('id', 'user', 'company_name', 'business_number', 'balance', 'created_at')
        read_only_fields = ('id', 'balance', 'created_at')


class RegisterSerializer(serializers.Serializer):
    """광고주 회원가입"""
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    company_name = serializers.CharField(max_length=100)
    business_number = serializers.CharField(max_length=20)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("이미 사용 중인 아이디입니다.")
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
        )
        Advertiser.objects.create(
            user=user,
            company_name=validated_data['company_name'],
            business_number=validated_data['business_number'],
        )
        return user
