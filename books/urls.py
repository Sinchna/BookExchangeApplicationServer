# platform/urls.py
from django.urls import path
from .views import RegisterView, UserProfileView, LoginView, BookListCreateView, BookDetailView, ExchangeRequestView, ExchangeRequestDetailView, HealthCheckView, SendPasswordResetCodeView, VerifyResetCodeView, UpdateBookDetailView

urlpatterns = [
    path('', HealthCheckView.as_view(), name='health_check'),  # Root URL
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('books/', BookListCreateView.as_view(), name='book_list_create'),
    path('books/<int:pk>/', UpdateBookDetailView.as_view(), name='book_list_update'),
    path('books/<int:pk>/', BookDetailView.as_view(), name='book_detail'),
    path('exchange-requests/', ExchangeRequestView.as_view(), name='exchange_requests'),
    path('exchange-requests/<int:pk>/', ExchangeRequestDetailView.as_view(), name='exchange_request_detail'),
    path('send-password-reset-code/', SendPasswordResetCodeView.as_view(), name='send_password_reset_code'),
    path('verify-reset-code/', VerifyResetCodeView.as_view(), name='verify_reset_code'),
]
