from django.urls import path

from .views import (
    SignUpView, LogInView, LogOutView, ActivateView, ResendActivationView, 
    ForgotUsernameView, ResetPasswordView, ResetPasswordDoneView, ResetPasswordConfirmView,
    ChangeProfileView, ChangeEmailActivateView, AddBookView, EditBookView,
    DeleteBookView, AddLibraryView, BrowseUserView, UserDetailsView
)

app_name = 'user'

urlpatterns = [
    path('sign-up/', SignUpView.as_view(), name='signup'),
    path('log-in/', LogInView.as_view(), name='login'),
    path('log-out/', LogOutView.as_view(), name='logout'),
    path('activate/<code>', ActivateView.as_view(), name='activate'),
    path('resend-activation/', ResendActivationView.as_view(), name='resend_activation'),
    path('forgot-username/', ForgotUsernameView.as_view(), name='forgot_username'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset_password'),
    path('reset-password/done/', ResetPasswordDoneView.as_view(), name='reset_password_done'),
    path('reset-password/confirm/<uidb64>/<token>/', ResetPasswordConfirmView.as_view(), name='reset_password_confirm'),
    path('profile/', ChangeProfileView.as_view(), name='profile'),
    path('change-email/activate/<code>/', ChangeEmailActivateView.as_view(), name='change_email_activate'),
    path('add/book/<pk>/', AddBookView.as_view(), name='add_book'),
    path('edit/book/<pk>/', EditBookView.as_view(), name='edit_book'),
    path('delete/book/<pk>/', DeleteBookView.as_view(), name='delete_book'),
    path('add/library/', AddLibraryView.as_view(), name='add_library'),
    path('browse/users/', BrowseUserView.as_view(), name='browse_users'),
    path('details/<pk>/', UserDetailsView.as_view(), name='user_details'),
]
