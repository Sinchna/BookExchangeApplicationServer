# platform/serializers.py
from rest_framework import serializers
from .models import CustomUser, Book, ExchangeRequest
from rest_framework import serializers
from django.contrib.auth import authenticate

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        # Use `set_password` to hash the password before saving
        user = CustomUser(
            username=validated_data['username'],
            email=validated_data['email']
        )
        user.set_password(validated_data['password'])
        user.save()
        return user
    
class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True)

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        if username and password:
            user = authenticate(request=self.context.get('request'), username=username, password=password)
            if user:
                return attrs
            else:
                raise serializers.ValidationError('Invalid username or password')
        raise serializers.ValidationError('Must include "username" and "password".')

class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = [
            'id', 'title', 'author', 'genre', 'condition', 'availability', 
            'owner', 'created_at', 'updated_at'
        ]
        read_only_fields = ['owner', 'created_at', 'updated_at']

    def create(self, validated_data):
        # Set the owner to the user making the request
        validated_data['owner'] = self.context['request'].user
        return Book.objects.create(**validated_data)

class UpdateBookSerializer(serializers.ModelSerializer):

    class Meta:
        model = Book
        fields = [
            'id', 'title', 'author', 'genre', 'condition', 'availability', 
            'owner', 'created_at', 'updated_at'
        ]
        read_only_fields = ['owner', 'created_at', 'updated_at']

    def update(self, instance, validated_data):
        # Update the fields of the existing instance
        instance.title = validated_data.get('title', instance.title)
        instance.author = validated_data.get('author', instance.author)
        instance.genre = validated_data.get('genre', instance.genre)
        instance.condition = validated_data.get('condition', instance.condition)
        instance.availability = validated_data.get('availability', instance.availability)

        # Save the updated instance
        instance.save()
        return instance

class ExchangeRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExchangeRequest
        fields = ['id', 'book', 'requestor', 'status', 'terms', 'created_at', 'updated_at']

class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'date_joined']