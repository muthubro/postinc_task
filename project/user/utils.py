from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.urls import reverse

def send_email(recepient, template, context):
    content = render_to_string(f'emails/user/{template}.txt', context)

    mail = EmailMessage(context['subject'], content, to=[recepient])
    mail.send()

def send_activation_email(request, email, code):
    context = {
        'subject': 'Account activation',
        'uri': request.build_absolute_uri(reverse('user:activate', kwargs={'code': code}))
    }

    send_email(email, 'activate_account', context)

def send_forgot_username_email(request, email, username):
    context = {
        'subject': 'Retrieve username',
        'username': username
    }

    send_email(email, 'recover_username', context)

def send_password_reset_email(request, email, token, uid):
    context = {
        'subject': 'Reset password',
        'uri': request.build_absolute_uri(
            reverse('user:reset_password_confirm', 
            kwargs={
                'uidb64': uid,
                'token': token
            }))
    }

    send_email(email, 'reset_password_email', context)

def send_change_email_activation(request, email, code):
    context = {
        'subject': 'Account activation',
        'uri': request.build_absolute_uri(reverse('user:change_email_activate', kwargs={'code': code}))
    }

    send_email(email, 'change_email', context)
