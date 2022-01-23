from django.contrib.auth import get_user_model, login as auth_login
from django.contrib.auth.views import LoginView, PasswordResetView
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.urls import reverse
from django.views.generic import CreateView
from django.http import HttpResponseRedirect
from django.utils.translation import get_language, gettext_lazy as _
from django.contrib import messages

from cms.models import HealthData, Result
from .tasks import mail_send
from .user_crypt import decoder
from .forms import CustomUserCreationForm, CustomUserChangeForm, CustomAuthenticationForm, ProfileForm, \
    HealthDataForm, ImageForm
from cms.models import HealthData
from cms.converting import feet_tu_cm
import requests
import json
from api.tasks import reset_pass_mail_send


User = get_user_model()


class PasswordReset(PasswordResetView):
    def form_valid(self, form):
        email = form.cleaned_data['email']
        if not User.objects.filter(email__iexact=email).exists():
            messages.error(self.request, _(f"User with email {email} doesn\'t exists."))
            return render(self.request, 'registration/password_reset_form.html')

        self.extra_email_context = {
            'fullurlstatic': self.request.build_absolute_uri('/static/'),
            'host': self.request.get_host(),
            'protocol': self.request.scheme,
        }
        self.html_email_template_name = 'email/password_reset_email.html'
        self.email_template_name = 'email/password_reset_email.html'

        return super().form_valid(form)


def activate_user_account(request, signed_user=None):
    user, signature = decoder(request, signed_user)
    if user and signature:
        user.email_confirm = True
        user.save()
        return render(request, 'email_verify_done.html', {'user': user})
    elif user:
        host = request.get_host()
        scheme = request.scheme
        lang = get_language()
        mail_send.delay(lang, scheme, host, user.id)
        return render(request, 'email_verify_end_of_time.html')
    else:
        return render(request, 'user_does_not_exist.html')


def signup(request):
    if request.method == 'POST':
        user_form = CustomUserCreationForm(request.POST)
        if user_form.is_valid():
            # Создаем нового пользователя, но не сохраняем
            new_user = user_form.save(commit=False)
            # Задаем пользователю зашифрованный пароль
            new_user.set_password(user_form.cleaned_data['password1'])
            # Сохраняем пользователя в БД
            new_user.save()
            # create HealthProfile(dashboard) for new user
            dashboard = HealthData.objects.create(user=new_user)
            # # create results panel
            Result.objects.create(dashboard=dashboard)
            # send confirm letter
            mail_send.delay(get_language(), request.scheme, request.get_host(), new_user.id)
            return render(request, 'registration/signup_done.html', {'new_user': new_user})
    else:
        user_form = CustomUserCreationForm()
    return render(request, 'registration/signup.html', {'user_form': user_form})


@login_required
def profile(request):
    form = ProfileForm(instance=request.user)
    form_image = ImageForm(instance=request.user)
    user = User.objects.filter(email=request.user).first()
    if HealthData.objects.filter(user_id=user).exists():
        form_data = HealthDataForm(instance=request.user.health_data)
    else:
        dashboard = HealthData.objects.create(user=user)
        Result.objects.create(dashboard=dashboard)
        form_data = HealthDataForm(instance=dashboard)
        # mail_send.delay(get_language(), request.scheme, request.get_host(), user.id)

    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=request.user)
        form_data = HealthDataForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
        if form_data.is_valid():
            cd = form_data.cleaned_data
            height = cd['height']
            if int(cd['measuring_system']) == 2:
                height = feet_tu_cm(height)
            HealthData.objects.filter(user=request.user).update(birth_date=cd['birth_date'],
                                                                country=cd['country'], gender=cd['gender'],
                                                                height=height, smoker=cd['smoker'],
                                                                measuring_system=cd['measuring_system'])

    return render(request, 'profile.html', {'form': form, 'form_image': form_image, 'form_data': form_data})


class CustomLoginView(LoginView):
    form_class = CustomAuthenticationForm

    def form_valid(self, form):
        """Security check complete. Log the user in."""
        auth_login(self.request, form.get_user(), backend='users.authenticate.CustomModelBackend')
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form):
        """If the form is invalid, render the invalid form."""
        num_attempt = self.request.session.get('num_attempt', 0)
        if num_attempt < 2:
            self.request.session['num_attempt'] = num_attempt + 1
        else:
            self.request.session['num_attempt'] = 2

        context = self.get_context_data(form=form)
        context['num_attempt'] = num_attempt

        if num_attempt == 1:
            post_url = self.request.scheme + "://" + self.request.get_host() + reverse('v2:rest_password_reset')
            post_data = {"email": self.request.POST['username']}
            reset_pass_mail_send.delay(post_url, post_data)

        return self.render_to_response(context=context)
