import copy
from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from api.tasks import post_health_data
from .models import HealthData, CardioActivity, Disease


class FormHealthData(forms.ModelForm):
    weight = forms.FloatField(
        help_text=None,
        initial=0,
        label=_("Weight"),
        widget=forms.NumberInput(attrs={'placeholder': '0', 'step': "1"})
    )
    hip = forms.FloatField(
        help_text=None,
        initial=0,
        label=_("Hip circumference"),
        widget=forms.NumberInput(attrs={'placeholder': '0', 'step': "1"})
    )
    waist = forms.FloatField(
        help_text=None,
        initial=0,
        label=_("Waist circumference"),
        widget=forms.NumberInput(attrs={'placeholder': '0', 'step': "1"})
    )
    neck = forms.FloatField(
        help_text=None,
        initial=0,
        label=_("Neck circumference"),
        widget=forms.NumberInput(attrs={'placeholder': '0', 'step': "1"})
    )
    wrist = forms.FloatField(
        help_text=None,
        initial=0,
        label=_("Wrist circumference"),
        widget=forms.NumberInput(attrs={'placeholder': '0', 'step': "1"})
    )

    blood_pressure_sys = forms.FloatField(
        required=False,
        # initial=120,
        help_text=None,
        label=_("Blood pressure"),
        widget=forms.NumberInput(attrs={'placeholder': '0', 'step': "1"})
    )
    blood_pressure_dia = forms.FloatField(
        required=False,
        # initial=80,
        help_text=None,
        widget=forms.NumberInput(attrs={'placeholder': '0', 'step': "1"})
    )

    cholesterol = forms.FloatField(
        label=_("Cholesterol"),
        required=False,
        help_text=None,
        widget=forms.NumberInput(attrs={'placeholder': '0', 'step': "0.1"})
    )
    glucose = forms.FloatField(
        label=_("Glucose level"),
        required=False,
        help_text=None,
        widget=forms.NumberInput(attrs={'placeholder': '0', 'step': "0.1"}),
    )
    heart_rate_alone = forms.IntegerField(
        # initial=60,
        label=_("Heart rate"),
        required=False,
        help_text=None,
        widget=forms.NumberInput(attrs={'placeholder': '0', 'step': "1"})
    )
    bpm = _('bpm')

    class Meta:
        model = HealthData
        fields = ('weight', 'hip', 'waist', 'wrist', 'neck', 'heart_rate_alone', 'daily_activity_level',
                  'blood_pressure_sys', 'blood_pressure_dia', 'cholesterol', 'glucose')

    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance', {})
        if instance.measuring_system == 2:
            initial = kwargs.get('initial', {})
            if instance.hip:
                initial['hip'] = round(instance.hip / 2.54, 1)
                if initial['hip'] < 7.8:
                    initial['hip'] = 7.8
                if initial['hip'] > 59.1:
                    initial['hip'] = 59.1
            if instance.waist:
                initial['waist'] = round(instance.waist / 2.54, 1)
                if initial['waist'] < 7.8:
                    initial['waist'] = 7.8
                if initial['waist'] > 102.4:
                    initial['waist'] = 102.4
            if instance.wrist:
                initial['wrist'] = round(instance.wrist / 2.54, 1)
                if initial['wrist'] < 3.9:
                    initial['wrist'] = 3.9
                if initial['wrist'] > 15.8:
                    initial['wrist'] = 15.8
            if instance.neck:
                initial['neck'] = round(instance.neck / 2.54, 1)
                if initial['neck'] < 7.8:
                    initial['neck'] = 7.8
                if initial['neck'] > 47.3:
                    initial['neck'] = 47.3
            if instance.weight:
                initial['weight'] = round(instance.weight * 2.2, 1)
                if initial['weight'] < 44:
                    initial['weight'] = 44
                if initial['weight'] > 1322.8:
                    initial['weight'] = 1322.8
            if instance.blood_pressure_sys:
                initial['blood_pressure_sys'] = round(instance.blood_pressure_sys / 7.501, 1)
                if initial['blood_pressure_sys'] < 10.7:
                    initial['blood_pressure_sys'] = 10.7
                if initial['blood_pressure_sys'] > 42.7:
                    initial['blood_pressure_sys'] = 42.7
            if instance.blood_pressure_dia:
                initial['blood_pressure_dia'] = round(instance.blood_pressure_dia / 7.501, 1)
                if initial['blood_pressure_dia'] < 5.3:
                    initial['blood_pressure_dia'] = 5.3
                if initial['blood_pressure_dia'] > 30.7:
                    initial['blood_pressure_dia'] = 30.7
            if instance.cholesterol:
                initial['cholesterol'] = round(instance.cholesterol * 18.016, 1)
                if 0 > initial['cholesterol'] > 5.4:
                    initial['cholesterol'] = 5.4
                if initial['cholesterol'] > 162:
                    initial['cholesterol'] = 162
            if instance.glucose:
                initial['glucose'] = round(instance.glucose * 18.016, 1)
                if 0 > initial['glucose'] > 45 :
                    initial['glucose'] = 45
                if initial['glucose'] > 252:
                    initial['glucose'] = 252
            kwargs['initial'] = initial

        super(FormHealthData, self).__init__(*args, **kwargs)

    def clean(self):
        measuring_system = self.instance.measuring_system
        cd = self.cleaned_data
        if measuring_system == 2:
            if cd['weight'] < 44 or cd['weight'] > 1322.8:
                FormHealthData.add_error(self, field='weight', error=ValidationError(_('The value must be between 44 up to 1322.8 lb')))
            if cd['hip'] < 7.8 or cd['hip'] > 59.1:
                FormHealthData.add_error(self, field='hip', error=ValidationError(_('The value must be between 7.8 up to 59.1 in')))
            if cd['waist'] < 7.8 or cd['waist'] > 102.4:
                FormHealthData.add_error(self, field='waist', error=ValidationError(_('The value must be between 7.8 up to 102.4 in')))
            if cd['wrist'] < 3.9 or cd['wrist'] > 15.8:
                FormHealthData.add_error(self, field='wrist', error=ValidationError(_('The value must be between 3.9 up to 15.8 in')))
            if cd['neck'] < 7.8 or cd['neck'] > 47.3:
                FormHealthData.add_error(self, field='neck', error=ValidationError(_('The value must be between 7.8 up to 47.3 in')))
            if cd['blood_pressure_sys'] != None and cd['blood_pressure_sys'] != 0 and (cd['blood_pressure_sys'] < 10.7 or cd['blood_pressure_sys'] > 42.7):
                FormHealthData.add_error(self, field='blood_pressure_sys', error=ValidationError(_('The value must be between 10.7 up to 42.7 kPa')))
            if cd['blood_pressure_dia'] != None and cd['blood_pressure_dia'] != 0 and (cd['blood_pressure_dia'] < 5.3 or cd['blood_pressure_dia'] > 30.7):
                FormHealthData.add_error(self, field='blood_pressure_dia', error=ValidationError(_('The value must be between 5.3 up to 30.7 kPa')))
            if cd['cholesterol'] != None and cd['cholesterol'] != 0 and (cd['cholesterol'] < 5.4 or cd['cholesterol'] > 162):
                FormHealthData.add_error(self, field='cholesterol', error=ValidationError(_('The value must be between 5.4 up to 162 mg/dL')))
            if cd['glucose'] != None and cd['glucose'] != 0 and (cd['glucose'] < 45 or cd['glucose'] > 252):
                FormHealthData.add_error(self, field='glucose', error=ValidationError(_('The value must be between 45 up to 252 mg/dL')))
        else:
            if cd['weight'] < 20 or cd['weight'] > 600:
                FormHealthData.add_error(self, field='weight', error=ValidationError(_('The value must be between 20 up to 600 kg')))
            if cd['hip'] < 20 or cd['hip'] > 150:
                FormHealthData.add_error(self, field='hip', error=ValidationError(_('The value must be between 20 up to 150 cm')))
            if cd['waist'] < 20 or cd['waist'] > 260:
                FormHealthData.add_error(self, field='waist', error=ValidationError(_('The value must be between 20 up to 260 cm')))
            if cd['wrist'] < 10 or cd['wrist'] > 40:
                FormHealthData.add_error(self, field='wrist', error=ValidationError(_('The value must be between 10 up to 40 cm')))
            if cd['neck'] < 20 or cd['neck'] > 120:
                FormHealthData.add_error(self, field='neck', error=ValidationError(_('The value must be between 20 up to 120 cm')))
            if cd['blood_pressure_sys'] != None and cd['blood_pressure_sys'] !=0 and (cd['blood_pressure_sys'] < 80 or cd['blood_pressure_sys'] > 320):
                FormHealthData.add_error(self, field='blood_pressure_sys', error=ValidationError(_('The value must be between 80 up to 320 mmHg')))
            if cd['blood_pressure_dia'] != None and cd['blood_pressure_dia'] !=0 and (cd['blood_pressure_dia'] < 40 or cd['blood_pressure_dia'] > 230):
                FormHealthData.add_error(self, field='blood_pressure_dia', error=ValidationError(_('The value must be between 40 up to 230 mmHg')))
            if cd['cholesterol'] != None and cd['cholesterol'] != 0 and (cd['cholesterol'] < 0.3 or cd['cholesterol'] > 9):
                FormHealthData.add_error(self, field='cholesterol', error=ValidationError(_('The value must be between 0.3 up to 9 mmol/L')))
            if cd['glucose'] != None and cd['glucose'] != 0 and (cd['glucose'] < 2.5 or cd['glucose'] > 14):
                FormHealthData.add_error(self, field='glucose', error=ValidationError(_('The value must be between 2.5 up to 14 mmol/L')))
        if cd['heart_rate_alone'] != None and cd['heart_rate_alone'] != 0 and (cd['heart_rate_alone'] < 40 or cd['heart_rate_alone'] > 280):
            FormHealthData.add_error(self, field='heart_rate_alone', error=ValidationError(_('The value must be between 40 up to 280')))

    def save(self, LANGUAGE_CODE="en-us", commit=True):
        instance = super(FormHealthData, self).save(commit=False)
        measuring_system = HealthData.objects.get(pk=instance.id).measuring_system
        if measuring_system == 2:
            if instance.hip:
                instance.hip = round(instance.hip * 2.54)
                if instance.hip < 20:
                    instance.hip = 20
                if instance.hip > 150:
                    instance.hip = 150
            if instance.waist:
                instance.waist = round(instance.waist * 2.54)
                if instance.waist < 20:
                    instance.waist = 20
                if instance.waist > 260:
                    instance.waist = 260
            if instance.wrist:
                instance.wrist = round(instance.wrist * 2.54)
                if instance.wrist < 10:
                    instance.wrist = 10
                if instance.wrist > 40:
                    instance.wrist = 40
            if instance.neck:
                instance.neck = round(instance.neck * 2.54)
                if instance.neck < 20:
                    instance.neck = 20
                if instance.neck > 120:
                    instance.neck = 120
            if instance.weight:
                instance.weight = round(instance.weight / 2.2)
                if instance.weight < 20:
                    instance.weight = 20
                if instance.weight > 600:
                    instance.weight = 600
            if instance.blood_pressure_sys:
                instance.blood_pressure_sys = round(instance.blood_pressure_sys * 7.501)
                if instance.blood_pressure_sys < 80:
                    instance.blood_pressure_sys = 80
                if instance.blood_pressure_sys > 320:
                    instance.blood_pressure_sys = 320
            if instance.blood_pressure_dia:
                instance.blood_pressure_dia = round(instance.blood_pressure_dia * 7.501)
                if instance.blood_pressure_dia < 40:
                    instance.blood_pressure_dia = 40
                if instance.blood_pressure_dia > 230:
                    instance.blood_pressure_dia = 230
            if instance.cholesterol:
                instance.cholesterol = round(instance.cholesterol / 18.016, 1)
                if 0 > instance.cholesterol > 0.3:
                    instance.cholesterol = 0.3
                if instance.cholesterol > 9:
                    instance.cholesterol = 9
            if instance.glucose:
                instance.glucose = round(instance.glucose / 18.016, 1)
                if 0 > instance.glucose > 2.5:
                    instance.glucose = 2.5
                if instance.glucose > 14:
                    instance.glucose = 14

        if commit:
            instance.save()
            HealthData.objects.filter(pk=instance.id).update(
                weight=instance.weight, hip=instance.hip, waist=instance.waist, wrist=instance.wrist,
                neck=instance.neck, heart_rate_alone=instance.heart_rate_alone,
                blood_pressure_sys=instance.blood_pressure_sys, blood_pressure_dia=instance.blood_pressure_dia,
                cholesterol=instance.cholesterol, glucose=instance.glucose
            )
            # create cardio object on HealthData model base
            cardiac_activity = CardioActivity.objects.create(health_model=instance,
                                                             heart_rate_alone=instance.heart_rate_alone,
                                                             blood_pressure_dia=instance.blood_pressure_dia,
                                                             blood_pressure_sys=instance.blood_pressure_sys)
            cardiac_activity.save()

        # prepare health-data for send to main database
        # sended_data = copy.deepcopy(self.cleaned_data)
        data = HealthData.objects.filter(pk=instance.id).values()[0]
        data_res = copy.deepcopy(data)
        for key, value in data.items():
            if value or HealthData._meta.get_field(key).blank or key == 'smoker' or key == 'country':
                data_res.pop(key, None)
        data_res = [HealthData._meta.get_field(key).verbose_name for key in data_res]
        if not data_res:
            data['user_id'] = instance.id
            data['user_email'] = instance.user.email
            if data['birth_date']:
                data['birth_date'] = data['birth_date'].strftime("%d.%m.%Y")
            if LANGUAGE_CODE.startswith("ru"):
                data['locale'] = "ru-ru"
            else:
                data['locale'] = "en-us"
            # # call async process for send health-data to main database
            post_health_data.delay(data)
            return instance


class FormDisease(forms.ModelForm):
    class Meta:
        model = Disease
        fields = ('disease_blood_pressure', 'disease_heart_rate', 'disease_obesity')

