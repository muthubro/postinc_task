from django.contrib.auth import login, authenticate, REDIRECT_FIELD_NAME
from django.shortcuts import redirect, get_object_or_404, render
from django.views.generic import (
    View, FormView, CreateView, UpdateView, DeleteView, ListView, DetailView
)
from django.conf import settings
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.views.decorators.debug import sensitive_post_parameters
from django.utils.http import is_safe_url, urlsafe_base64_encode
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import (
    LogoutView as BaseLogoutView, PasswordResetDoneView as BasePasswordResetDoneView,
    PasswordResetConfirmView as BasePasswordResetConfirmView
)
from django.utils.crypto import get_random_string
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.forms.widgets import DateInput
from django.contrib.auth.models import User

from .forms import (
    SignUpForm, LogInForm, ResendActivationCodeForm, ForgotUsernameForm, ResetPasswordForm,
    ChangeProfileForm
)
from .models import Activation, Book, Library
from .utils import (
    send_activation_email, send_forgot_username_email, send_password_reset_email,
    send_change_email_activation
)

# Create your views here.
class GuestView(View):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(settings.LOGIN_REDIRECT_URL)

        return super().dispatch(request, *args, **kwargs)

class SignUpView(GuestView, FormView):
    template_name = 'user/sign_up.html'
    form_class = SignUpForm

    def form_valid(self, form):
        request = self.request
        user = form.save(commit=False)

        user.is_active = False
        user.save()

        username = form.cleaned_data['username']

        if settings.REQUIRE_USER_ACTIVATION:
            code = get_random_string(20)

            act = Activation()
            act.user = user
            act.code = code
            
            try:
                act.save()
                send_activation_email(request, user.email, code)
                messages.success(request, 'You have successfully signed up. Follow the link sent to your email address to activate your account.')

            except:
                user.delete()
                messages.error(request, 'Something went wrong. Please try again later.')          

        else:
            password = form.cleaned_data['password1']

            user = authenticate(username=username, password=password)
            login(request, user)

            messages.success(request, 'You have successfully signed up.')

        return redirect(settings.LOGIN_REDIRECT_URL)

class LogInView(GuestView, FormView):
    template_name = 'user/log_in.html'
    form_class = LogInForm

    @method_decorator(sensitive_post_parameters('password'))
    @method_decorator(never_cache)
    def dispatch(self, request, *args, **kwargs):
        request.session.set_test_cookie()

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        request = self.request

        if request.session.test_cookie_worked():
            request.session.delete_test_cookie()

        if not form.cleaned_data['remember_me']:
            request.session.set_expiry(0)

        login(request, form.user_cache)

        redirect_url = request.POST.get(REDIRECT_FIELD_NAME, request.GET.get(REDIRECT_FIELD_NAME))
        url_is_safe = is_safe_url(redirect_url, allowed_hosts=request.get_host(), require_https=request.is_secure())

        if url_is_safe:
            return redirect(redirect_url)

        return redirect(settings.LOGIN_REDIRECT_URL)

class LogOutView(BaseLogoutView, LoginRequiredMixin):
    template_name = 'user/log_out.html'

class ActivateView(View):
    @staticmethod
    def get(request, code):
        act = get_object_or_404(Activation, code=code)

        user = act.user
        user.is_active = True
        user.save()

        act.delete()

        messages.success(request, 'You have successfully activated your account.')

        return redirect('user:login')

class ResendActivationView(GuestView, FormView):
    template_name = 'user/resend_activation_code.html'
    form_class = ResendActivationCodeForm

    def form_valid(self, form):
        request = self.request
        user = form.user_cache

        act = user.activation_set.first()
        act.delete()

        code = get_random_string(20)

        act = Activation()
        act.user = user
        act.code = code
        act.save()

        send_activation_email(request, user.email, code)

        messages.success(request, 'A new activation code has been sent to your email address.')

        return redirect('user:resend_activation')

class ForgotUsernameView(GuestView, FormView):
    template_name = 'user/forgot_username.html'
    form_class = ForgotUsernameForm

    def form_valid(self, form):
        request = self.request
        user = form.user_cache

        send_forgot_username_email(request, user.email, user.username)

        messages.success(request, 'The username has been sent to your email address.')

        return redirect('user:forgot_username')

class ResetPasswordView(GuestView, FormView):
    template_name = 'user/reset_password.html'
    form_class = ResetPasswordForm

    def form_valid(self, form):
        request = self.request
        user = form.user_cache

        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk)).decode()

        send_password_reset_email(request, user.email, token, uid)

        return redirect('user:reset_password_done')

class ResetPasswordDoneView(BasePasswordResetDoneView):
    template_name = 'user/reset_password_done.html'

class ResetPasswordConfirmView(BasePasswordResetConfirmView):
    template_name = 'user/reset_password_confirm.html'

    def form_valid(self, form):
        form.save()

        messages.success(self.request, 'You have successfully reset your password.')

        return redirect('user:login')

class ChangeProfileView(LoginRequiredMixin, FormView):
    template_name = 'user/profile.html'
    form_class = ChangeProfileForm

    def get_context_data(self):
        context = super().get_context_data()
        context['user'] = self.request.user

        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user

        return kwargs

    def get_initial(self):
        user = self.request.user

        initial = super().get_initial()
        initial['first_name'] = user.first_name
        initial['last_name'] = user.last_name
        initial['email'] = user.email

        return initial

    def form_valid(self, form):
        request = self.request
        user = request.user

        user.first_name = form.cleaned_data['first_name']
        user.last_name = form.cleaned_data['last_name']
        user.save()

        email = form.cleaned_data['email']
        if email != user.email:
            if settings.REQUIRE_USER_ACTIVATION:
                code = get_random_string(20)

                act = Activation()
                act.user = user
                act.code = code
                act.email = email
                
                try:
                    act.save()
                    send_change_email_activation(request, email, code)
                    messages.success(request, 'Follow the link sent to your email address to change your email address.')

                except:
                    user.delete()
                    messages.error(request, 'Something went wrong. Please try again later.')

            else:
                user.email = email
                user.save()

                messages.success(request, 'Email address changed.')

        return redirect('user:profile')

class ChangeEmailActivateView(View):
    @staticmethod
    def get(request, code):
        act = get_object_or_404(Activation, code=code)

        user = act.user
        user.email = act.email
        user.save()

        act.delete()

        messages.success(request, 'You have successfully changed your email address.')

        return redirect('user:profile')

class AddBookView(LoginRequiredMixin, CreateView):
    template_name = 'user/add_book.html'
    model = Book
    fields = ['library', 'name', 'author', 'genre', 'publish_date']

    def dispatch(self, request, *args, **kwargs):
        self.library_id = kwargs['pk']

        return super().dispatch(request, *args, **kwargs)

    def get_form(self):
        form = super().get_form()
        form.fields['library'].queryset = Library.objects.filter(user=self.request.user)

        return form

    def get_initial(self):
        initial = super().get_initial()
        initial['library'] = Library.objects.get(pk=self.library_id)

        return initial

    def form_valid(self, form):
        request = self.request
        self.object = form.save(commit=False)
        
        self.object.user = request.user
        self.object.save()

        messages.success(request, 'Book has been successfully added.')

        return redirect('user:profile')

class EditBookView(LoginRequiredMixin, UpdateView):
    template_name = 'user/edit_book.html'
    model = Book
    fields = ['library', 'name', 'author', 'genre', 'publish_date']

    def form_valid(self, form):
        request = self.request
        self.object = form.save()

        messages.success(request, 'Book has been successfully edited.')

        return redirect('user:profile')

class DeleteBookView(LoginRequiredMixin, DeleteView):
    template_name = 'user/delete_book.html'
    model = Book
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()

        messages.success(request, 'Book has been deleted.')

        return redirect('user:profile')

class AddLibraryView(LoginRequiredMixin, CreateView):
    template_name = 'user/add_library.html'
    model = Library
    fields = ['name']

    def form_valid(self, form):
        request = self.request
        self.object = form.save(commit=False)

        self.object.user = request.user
        self.object.save()

        messages.success(request, 'Library has been successfully added.')

        return redirect('user:profile')

class BrowseUserView(ListView):
    template_name = 'user/browse_user.html'
    model = User
    paginate_by = 10

class UserDetailsView(DetailView):
    template_name = 'user/user_details.html'
    model = User
