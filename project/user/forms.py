from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.forms import ValidationError
from django import forms
from django.db.models import Q
from django.utils import timezone
from django.forms import ModelForm

from datetime import timedelta

from .models import Book

class UserCacheMixin:
    user_cache = None

class SignUpForm(UserCreationForm):
    class Meta:
        model = User
        fields = settings.SIGN_UP_FIELDS

    def clean_email(self):
        email = self.cleaned_data['email']

        user = User.objects.filter(email__iexact=email).exists()
        if user:
            raise ValidationError('This email is already taken.')

        return email

class LogInForm(UserCacheMixin, forms.Form):
    email_or_username = forms.CharField(label='Email or username')
    password = forms.CharField(label='Password', strip=False, widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['remember_me'] = forms.BooleanField(label='Remember me', required=False)

    @property
    def field_order(self):
        return ['email_or_username', 'password', 'remember_me']

    def clean_email_or_username(self):
        email_or_username = self.cleaned_data['email_or_username']

        user = User.objects.filter(Q(username=email_or_username) | Q(email__iexact=email_or_username)).first()
        if not user:
            raise ValidationError('Invalid email address or username.')

        if not user.is_active:
            raise ValidationError('Your account has not been activated yet.')
        
        self.user_cache = user

        return email_or_username

    def clean_password(self):
        password = self.cleaned_data['password']

        if not self.user_cache:
            return password

        if not self.user_cache.check_password(password):
            raise ValidationError('Invalid password.')

        return password

class ResendActivationCodeForm(UserCacheMixin, forms.Form):
    email_or_username = forms.CharField(label='Email or Username')

    def clean_email_or_username(self):
        email_or_username = self.cleaned_data['email_or_username']

        user = User.objects.filter(Q(username=email_or_username) | Q(email__iexact=email_or_username)).first()
        if not user:
            raise ValidationError('Invalid username or password.')

        if user.is_active:
            raise ValidationError('This account has already been activated.')

        activation = user.activation_set.first()
        if not activation:
            raise ValidationError('This account does not exist. Please sign up again.')

        yesterday = timezone.now() - timedelta(hours=24)
        if activation.created_at > yesterday:
            raise ValidationError('The activation code has already been sent. Please wait for 24 hours before trying again.')

        self.user_cache = user

        return email_or_username

class ForgotUsernameForm(UserCacheMixin, forms.Form):
    email = forms.EmailField(label='Email')

    def clean_email(self):
        email = self.cleaned_data['email']

        user = User.objects.filter(email__iexact=email).first()
        if not user:
            raise ValidationError('Invalid email address.')

        if not user.is_active:
            raise ValidationError('Your account has not been activated yet.')

        self.user_cache = user

        return email

class ResetPasswordForm(UserCacheMixin, forms.Form):
    email = forms.EmailField(label='Email')

    def clean_email(self):
        email = self.cleaned_data['email']

        user = User.objects.filter(email__iexact=email).first()
        if not user:
            raise ValidationError('Invalid email address.')

        if not user.is_active:
            raise ValidationError('Your account has not been activated yet.')

        self.user_cache = user

        return email

class ChangeProfileForm(forms.Form):
    first_name = forms.CharField(label='First name', max_length=30, required=False)
    last_name = forms.CharField(label='Last name', max_length=30, required=False)
    email = forms.EmailField(label='Email')

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_email(self):
        email = self.cleaned_data['email']

        user = User.objects.filter(Q(email__iexact=email) & ~Q(id=self.user.id)).exists()
        if user:
            raise ValidationError('This email has another account registered with it.')

        return email
