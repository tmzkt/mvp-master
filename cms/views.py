from copy import deepcopy
from datetime import timedelta
from typing import Dict

from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404, HttpResponseRedirect
from django.views import generic
from django.urls import reverse_lazy
from django.db.models import Q
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken

from .forms import FormHealthData, FormDisease
from .models import Device, Result, DiseaseRisk, CommonRecomendations, HealthData, Recomendations, Disease
from payment.models import Payment
from api.filters import user_recomendations, cardio_recomendations
import api.marker as marker


@login_required
def dashboard(request):
    data = request.user.health_data
    measuring_system = data.measuring_system
    if request.method == 'POST':
        form = FormHealthData(request.POST, instance=request.user.health_data)
        if form.is_valid():
            form.save(request.LANGUAGE_CODE)
            # return redirect('/result')
    else:
        form = FormHealthData(instance=request.user.health_data)

    requirements_fields = ['gender', 'birth_date', 'height', 'weight', 'hip', 'waist', 'wrist',
                          'smoker', 'neck', 'daily_activity_level', 'measuring_system']

    form_unfilled = {}
    for field in requirements_fields:
        if data.__dict__[field] is None:
            form_unfilled[field] = field

    return render(request, 'cms/dashboard.html', {'form': form,
                                                  'measuring_system': measuring_system,
                                                  'form_unfilled': form_unfilled})


@login_required
def result(request):
    res_id = request.user.health_data.result.id
    risk_all = DiseaseRisk.objects.filter(result=res_id).values('risk_string', 'message', 'risk_percents',
                                                                'recomendation')
    for key in range(len(risk_all)):
        if risk_all[key]['risk_string'] == 'High':
            risk_all[key]['risk_string'] = '#FFC6D1'
        else:
            risk_all[key]['risk_string'] = '#C7FFD0'

    recomendation_all = CommonRecomendations.objects.filter(result=res_id).values('message_short',
                                                                                'message_long',
                                                                              'importance_level')
    for key in range(len(recomendation_all)):
        if recomendation_all[key]['importance_level'] == 'High':
            recomendation_all[key]['importance_level'] = '#FFC6D1'
        elif recomendation_all[key]['importance_level'] == 'Without color':
            recomendation_all[key]['importance_level'] = ''
        else:
            recomendation_all[key]['importance_level'] = '#C7FFD0'

    # now = timezone.now()
    # start_trial_date = HealthData.objects.get(user=request.user).create
    # trial = True if start_trial_date + timedelta(days=30) >= now else False
    # try:
    #     full_version_end_date = Payment.objects.get(user=request.user).end_date
    #     full = True if full_version_end_date >= now else False
    #     if full_version_end_date - timedelta(days=3) <= now and full:
    #         messages.info(request, 'Через {} дня заканчивается подписка на полную версию приложения. Если Вы хотите и дальше использовать весь функционал приложения пожалуйста продлите подписку.'.format(
    #             str((full_version_end_date.date() - timedelta(days=3) - now.date()))[0]
    #         ))
    # except Payment.DoesNotExist:
    #     full = False
    # if start_trial_date + timedelta(days=27) <= now and not full:
    #     messages.info(request, 'Через {} дня заканчивается пробный период. Если Вы хотите и дальше использовать весь функционал приложения пожалуйста купите полную версию.'.format(
    #         str((now.date() - (start_trial_date.date() + timedelta(days=27))))[0]
    #     ))
    return render(request, 'cms/result.html', {'risks': risk_all,
                                               'recomendations': recomendation_all})


class DeleteDevice(LoginRequiredMixin, generic.DeleteView):
    model = Device
    template_name = 'cms/delete_device.html'
    success_url = reverse_lazy('users:profile')

    # Защита от удаления другим юзером
    def get_object(self):
        device = super(DeleteDevice, self).get_object()
        if not device.user == self.request.user:
            raise Http404
        return device

    def delete(self, request, *args, **kwargs):
        """
        Call the delete() method on the fetched object and then redirect to the
        success URL.
        """
        self.object = self.get_object()
        success_url = self.get_success_url()

        token = get_object_or_404(OutstandingToken, token=self.object.token)
        if hasattr(token, 'blacklistedtoken'):
            # Token already blacklisted. Skip
            pass
        else:
            BlacklistedToken.objects.create(token=token)
        self.object.delete()
        return HttpResponseRedirect(success_url)


@login_required
def delete_all_devices(request):
    if request.method == 'POST':
        queryset = Device.objects.filter(user=request.user)
        for device in queryset:
            token = get_object_or_404(OutstandingToken, token=device.token)
            if hasattr(token, 'blacklistedtoken'):
                # Token already blacklisted. Skip
                pass
            else:
                BlacklistedToken.objects.create(token=token)
            device.delete()
        return redirect('users:profile')
    return render(request, 'cms/delete_all_devices.html')

@login_required
def recommendation(request):
    list, cat = user_recomendations(request)
    field_locale = 'name_ru' if request.LANGUAGE_CODE.startswith('ru') else 'name_en'
    rec = Recomendations.objects.filter(Q(pk__in=list)|Q(category__pk__in=cat)).values_list(field_locale, flat=True).distinct()

    return render(request, 'cms/recommendation.html', {'rec': rec})

@login_required
def disease(request):
    data = Disease.objects.filter(user=request.user.id).first()
    form = FormDisease(instance=data)
    cd = ''
    if request.method == 'POST':
        form = FormDisease(request.POST)
        if form.is_valid():
            form.save(commit=False)
            cd = form.cleaned_data
            cd['user'] = request.user
            Disease.objects.update_or_create(cd)
    rec = True if data and (data.disease_blood_pressure or data.disease_heart_rate or data.risk_disease_blood_pressure or \
                  data.risk_disease_heart_rate) or (cd and (cd['disease_blood_pressure'] or cd['disease_heart_rate'])) else False
    return render(request, 'cms/disease.html', {'form': form, 'rec': rec})

@login_required
def cardio_recommendation(request):
    cat_yes, list, cat_not = cardio_recomendations(request)
    if list or cat_yes or cat_not:
        field_locale = 'name_ru' if request.LANGUAGE_CODE.startswith('ru') else 'name_en'
        rec = Recomendations.objects.filter(Q(pk__in=list)|Q(category__pk__in=cat_yes)).values_list(field_locale, flat=True).distinct()
        rec_not = Recomendations.objects.filter(category__pk__in=cat_not).values_list(field_locale, flat=True).distinct()
    else:
        data_no = no_data(request.user)
        return render(request, 'cms/empty_data.html', {'data': data_no})
    return render(request, 'cms/cardio_recommendation.html', {'rec': rec, 'rec_not': rec_not})


# Selection of blank fields
def no_data(user):
    data = HealthData.objects.filter(user=user).values()[0]
    data_res = deepcopy(data)
    for key, value in data.items():
        if value or key in ['smoker', 'country', 'cholesterol', 'glucose', 'locale', 'heart_rate_alone',
                            'blood_pressure_sys', 'blood_pressure_dia', 'measuring_system']:
            data_res.pop(key, None)
    data_res = [HealthData._meta.get_field(key).verbose_name for key in data_res]
    return data_res


def get_verbose_name(parameter: Dict) -> Dict:
    parameter['verbose_name'] = Result._meta.get_field(parameter['name']).verbose_name
    return parameter


@login_required
def parameters(request):
    res_id = request.user.health_data.result.id
    result = Result.objects.filter(pk=res_id).values('bmi', 'obesity_level', 'ideal_weight', 'base_metabolism',
                                                  'calories_to_low_weight', 'waist_to_hip_proportion',
                                                  'passport_age', 'common_risk_level', 'prognostic_age',
                                               'fat_percent', 'body_type')[0]
    
    params = marker.add_descriptions(result)['params']  # Add parameters -> ordered dict -> List[Dict]
    results = list(map(get_verbose_name, params))  # Add verbose name
    return render(request, 'cms/parameters.html', {'results': results})

