from rest_framework import generics, permissions, status, viewsets, filters
from rest_framework.response import Response
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from django_filters.rest_framework import DjangoFilterBackend
from .models import Book, ExchangeRequest
from .serializers import UpdateBookSerializer, UserSerializer, BookSerializer, ExchangeRequestSerializer, LoginSerializer, CustomUserSerializer

import random
from django.core.cache import cache
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from django.conf import settings
from .models import CustomUser  # Import CustomUser model


class HealthCheckView(generics.GenericAPIView):
    def get(self, request):
        return Response({"status": "running"}, status=status.HTTP_200_OK)

class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)  # This will raise an error if validation fails
        username = serializer.validated_data['username']
        user = authenticate(username=username, password=serializer.validated_data['password'])
        if user:
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            })
        return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

class RegisterView(generics.CreateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]  # Allows anyone to access this endpoint

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                "user": UserSerializer(user, context=self.get_serializer_context()).data,
                "message": "User registered successfully."
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class BookListCreateView(generics.ListCreateAPIView):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

class BookDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        book = self.get_object()
        serializer = self.get_serializer(book)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def delete(self, request, *args, **kwargs):
        book = self.get_object()
        # Optional ownership check
        if book.owner != request.user:
            return Response({"detail": "You do not have permission to delete this book."}, status=status.HTTP_403_FORBIDDEN)
        
        book.delete()
        return Response({"detail": "Book deleted successfully."}, status=status.HTTP_204_NO_CONTENT)

class UpdateBookDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Book.objects.all()
    serializer_class = UpdateBookSerializer
    permission_classes = [permissions.IsAuthenticated]

class ExchangeRequestView(generics.ListCreateAPIView):
    queryset = ExchangeRequest.objects.all()
    serializer_class = ExchangeRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(requestor=self.request.user)

class ExchangeRequestDetailView(generics.RetrieveUpdateAPIView):
    queryset = ExchangeRequest.objects.all()
    serializer_class = ExchangeRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

class UserProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user

        # Serialize user data, including username, email, and date_joined
        user_data = {
            'username': user.username,
            'email': user.email,
            'date_joined': user.date_joined,
            **CustomUserSerializer(user).data  # Merge any additional data from the serializer
        }

        # Get books owned by the user
        user_books = Book.objects.filter(owner=user)
        user_books_data = BookSerializer(user_books, many=True, context={'request': request}).data

        # Get exchange requests made by the user
        user_requests = ExchangeRequest.objects.filter(requestor=user)
        user_requests_data = ExchangeRequestSerializer(user_requests, many=True).data

        # Get requests from others for the user's books
        requests_for_user_books = ExchangeRequest.objects.filter(book__owner=user).exclude(requestor=user)
        requests_for_user_books_data = ExchangeRequestSerializer(requests_for_user_books, many=True).data

        # Combine all data into a single response
        profile_data = {
            'user': user_data,
            'books': user_books_data,
            'exchange_requests_made': user_requests_data,
            'requests_for_my_books': requests_for_user_books_data,
        }

        return Response(profile_data)
    
class SendPasswordResetCodeView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email')
        
        # Print the email to the console for debugging
        print(f"Password reset requested for email: {email}")

        # Check if the email exists in the CustomUser model
        try:
            user = CustomUser.objects.get(email=email)  # Use CustomUser model here
            print(f"User found for email: {email}")
        except CustomUser.DoesNotExist:
            print(f"User with email {email} not found.")
            return Response({"error": "User with this email does not exist."}, status=status.HTTP_404_NOT_FOUND)
        
        # Generate a 6-digit verification code
        reset_code = str(random.randint(100000, 999999))
        print(f"Generated reset code: {reset_code}")

        # Store the reset code in cache with a timeout (e.g., 5 minutes)
        cache.set(f'password_reset_code_{user.id}', reset_code, timeout=300)
        print(f"Password reset code cached for user {user.id}.")

        # Prepare the email content
        message = Mail(
            from_email=settings.SENDGRID_FROM_EMAIL,
            to_emails=email,
            subject="Your Password Reset Code",
            html_content=f"<p>Your password reset code is: <strong>{reset_code}</strong></p>"
        )

        try:
            # Send the email using Twilio SendGrid
            sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
            sg.send(message)
            print(f"Password reset code sent to {email}")
            return Response({"message": "Password reset code sent."}, status=status.HTTP_200_OK)
        except Exception as e:
            print(f"Error sending email to {email}: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class VerifyResetCodeView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email')
        code = request.data.get('code')
        new_password = request.data.get('new_password')  # Use 'new_password' to match frontend data

        # Print received data for debugging
        print(f"Received request to verify reset code for email: {email}")
        print(f"Received code: {code}")

        # Check if the email exists using CustomUser model
        try:
            user = CustomUser.objects.get(email=email)
            print(f"User found: {user.id}")
        except CustomUser.DoesNotExist:
            print(f"User with email {email} not found.")
            return Response({"error": "User with this email does not exist."}, status=status.HTTP_404_NOT_FOUND)

        # Retrieve the reset code from cache
        cached_code = cache.get(f'password_reset_code_{user.id}')
        print(f"Cached reset code for user {user.id}: {cached_code}")

        if cached_code is None:
            print(f"Reset code for user {user.id} has expired or is invalid.")
            return Response({"error": "Reset code has expired or is invalid."}, status=status.HTTP_400_BAD_REQUEST)

        if cached_code == code:
            print(f"Reset code verified successfully for user {user.id}. Updating password.")

            # Update the user's password
            user.set_password(new_password)  # Make sure new_password is correctly referenced
            user.save()

            # Clear the reset code from cache
            cache.delete(f'password_reset_code_{user.id}')
            print(f"Password updated for user {user.id}. Reset code cleared from cache.")

            return Response({"message": "Password has been reset successfully."}, status=status.HTTP_200_OK)
        else:
            print(f"Invalid reset code provided for user {user.id}.")
            return Response({"error": "Invalid reset code."}, status=status.HTTP_400_BAD_REQUEST)