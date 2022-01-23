import json
from django.db import models
from datetime import date, timedelta
from django.core.exceptions import ValidationError
from django.forms import model_to_dict
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.translation import get_language

from .countries import COUNTRIES
from . import disease

User = get_user_model()


def validate_date(value):
    last_date = (date.today() - timedelta(days=47450))
    future_date = (date.today() - timedelta(days=3650))
    if not (last_date < value < future_date):
        raise ValidationError(_('Make sure the date is between {} and {}').format(last_date, future_date))


class JSONField(models.TextField):
    """
    JSONField is a generic textfield that neatly serializes/unserializes
    JSON objects seamlessly.
    example:
        class Page(models.Model):
            data = JSONField(blank=True, null=True)
        page = Page.objects.get(pk=5)
        page.data = {'title': 'test', 'type': 3}
        page.save()
    """
    def to_python(self, value):
        locale = get_language()
        if value == "":
            return None
        try:
            if isinstance(value, str):
                data = json.loads(value)
                data = data['ru'] if locale == 'ru' else data['en']
                return data
        except ValueError:
            pass
        return value

    def from_db_value(self, value, *args):
        return self.to_python(value)

    def get_db_prep_save(self, value, *args, **kwargs):
        if value == "":
            return None
        if isinstance(value, dict):
            value = json.dumps(value, cls=DjangoJSONEncoder)
        return value


class HealthDataAbstractModel(models.Model):
    MEASURING_SYSTEM = (
        (1, _('Metric')),
        (2, _('Inch'))
    )

    cholesterol = models.FloatField(
        null=True, blank=True,
        default=None, verbose_name=_('Cholesterol'),
        help_text=None
    )
    blood_pressure_sys = models.PositiveSmallIntegerField(
        null=True, blank=True,
        default=120, verbose_name=_('higher'),
        help_text=None
    )
    blood_pressure_dia = models.PositiveSmallIntegerField(
        null=True, blank=True,
        default=80, verbose_name=_('lower'),
        help_text=None
    )
    blood_saturation = models.PositiveSmallIntegerField(
        null=True, blank=True,
        default=0, verbose_name=_('higher'),
        help_text=None,
        validators=[MinValueValidator(30), MaxValueValidator(100)]
    )
    glucose = models.FloatField(
        null=True, blank=True,
        default=None, verbose_name=_('Glucose'),
        help_text=None
    )
    heart_rate_alone = models.PositiveSmallIntegerField(
        null=True, blank=True,
        default=60, verbose_name=_('heart rate'),
        help_text=None
    )
    weight = models.FloatField(
        null=True, blank=True,
        verbose_name=_('weight'),
        help_text=None, default=None
    )
    waist = models.FloatField(
        null=True, blank=True,
        verbose_name=_('waist'),
        help_text=None, default=None
    )
    wrist = models.FloatField(
        null=True, blank=True,
        verbose_name=_('wrist'),
        help_text=None, default=None
    )
    neck = models.FloatField(
        null=True, blank=True,
        default=None, verbose_name=_('neck'),
        help_text=None
    )
    hip = models.FloatField(
        null=True, blank=True,
        verbose_name=_('hip'), help_text=None,
        default=None
    )
    measuring_system = models.PositiveSmallIntegerField(
        choices=MEASURING_SYSTEM, default=1,
        verbose_name=_('Measuring system'),
        help_text=None
    )

    create = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


class HealthData(HealthDataAbstractModel):
    GENDERS = (
        (1, _('Male')),
        (2, _('Female')),
    )
    ACTIVITY_LEVEL = (
       (1.2, _('Minimum')),
       (1.375, _('Lower')),
       (1.55, _('Medium')),
       (1.725, _('High')),
       (1.9, _('Very high')),
    )

    gender = models.PositiveSmallIntegerField(
        null=True, blank=True, choices=GENDERS, verbose_name=_('gender'), help_text=None,
        default=1, error_messages={'required': _('Select gender')}
    )
    birth_date = models.DateField(
        null=True, blank=True, validators=[validate_date], default='1990-01-01',
        verbose_name=_('Date of Birth'), help_text=None, error_messages={'required': _('Enter your date of birth')}
    )
    country = models.PositiveSmallIntegerField(
        null=True, blank=True, validators=[MinValueValidator(1, message=_('Choose a country Residence'))],
        choices=COUNTRIES, verbose_name=_('country'), help_text=None,
        error_messages={'required': _('Choose a country Residence')}, default=0
    )
    height = models.FloatField(null=True, blank=True, verbose_name=_('height'), help_text=None, default=None)
    smoker = models.BooleanField(null=True, blank=True, verbose_name=_('Smoker'), default=False)
    locale = models.CharField(blank=True, default='', max_length=8, help_text=None)

    user = models.OneToOneField(User, null=True, on_delete=models.SET_NULL, related_name='health_data')
    daily_activity_level = models.FloatField(
        null=True, blank=True, choices=ACTIVITY_LEVEL, default=1.55,
        verbose_name=_('Daily activity level'), help_text=None
    )
    update = models.DateTimeField(auto_now=True)

    # Fields that will be checked for changes and if changed then history is added
    relevant_fields = [
            'cholesterol', 'blood_pressure_sys', 'blood_pressure_dia',
            'blood_saturation', 'glucose', 'heart_rate_alone',
            'weight', 'waist', 'wrist', 'neck', 'hip'
            'measuring_system'
        ]

    def is_data_changed(self, previous_instance, new_instance):
        """
        :param previous_instance: Model Instance that has previous data
        :param new_instance: Model Instance that has new data
        :return: Boolean if data has been changed or not
        """
        previous_data = model_to_dict(
            previous_instance, fields=self.relevant_fields
        )
        new_data = model_to_dict(
            new_instance, fields=self.relevant_fields
        )
        return previous_data != new_data

    def make_history(self, previous_instance):
        """
        :param previous_instance: Instance that has previous data that will be added as history
        :return:
        """
        data = model_to_dict(
            previous_instance,
            fields=self.relevant_fields
        )
        HealthDataHistory.objects.create(
            health_data=self,
            **data
        )

    def save(self, **kwargs):
        # Only if data update
        if self.pk:
            previous_data_instance = HealthData.objects.get(id=self.pk)
            if self.is_data_changed(previous_data_instance, self):
                self.refresh_from_db()
                self.make_history(self)

            # Make history with previous data
            super().save(**kwargs)
        else:
            super().save(**kwargs)


class HealthDataHistory(HealthDataAbstractModel):
    health_data = models.ForeignKey(
        HealthData,
        on_delete=models.CASCADE,
        related_name='history'
    )


class CardioActivity(models.Model):
    health_model = models.ForeignKey(HealthData, on_delete=models.CASCADE, related_name='health_data')

    measuring_date = models.DateTimeField(auto_now_add=True)

    heart_rate_alone = models.PositiveSmallIntegerField(null=True, blank=True,
                                                        verbose_name=_('heart rate'),
                                                        help_text=None)
    blood_pressure_sys = models.PositiveSmallIntegerField(null=True, blank=True,
                                                          verbose_name=_('blood pressure systolic'),
                                                          help_text=None)
    blood_pressure_dia = models.PositiveSmallIntegerField(null=True, blank=True,
                                                          verbose_name=_('blood pressure diastolic'),
                                                          help_text=None)

    class Meta:
        ordering = ('-measuring_date',)


class Device(models.Model):
    device_uuid = models.UUIDField(primary_key=True, editable=True, unique=True)
    os_name = models.CharField(blank=True, default='', max_length=30)
    os_version = models.CharField(blank=True, default='', max_length=30)
    device_model = models.CharField(max_length=50, verbose_name=_('device model'))
    app_version = models.CharField(blank=True, max_length=30)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='device')
    token = models.TextField(blank=True, default='')


class Result(models.Model):
    dashboard = models.OneToOneField(HealthData, on_delete=models.CASCADE, related_name='result')
    bmi = models.FloatField(blank=True, null=True, verbose_name=_('Body mass index'), help_text=None)
    obesity_level = JSONField(blank=True, null=True, default='', verbose_name=_('Weight excess'), help_text=None)
    ideal_weight = models.FloatField(blank=True, null=True, verbose_name=_('Ideal weight'), help_text=None)
    base_metabolism = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name=_('Basal metabolism'),
                                                       help_text=None)
    calories_to_low_weight = models.PositiveSmallIntegerField(null=True, blank=True, help_text=None,
                                                              verbose_name=_('Calories to low weight'))
    waist_to_hip_proportion = models.FloatField(null=True, blank=True, verbose_name=_('Waist-hip ratio'),
                                                help_text=None)
    passport_age = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name=_('Passport age'),
                                                    help_text=None)
    common_risk_level = JSONField(blank=True, default='', null=True, verbose_name=_('Common risk level'),
                                  help_text=None)
    prognostic_age = models.PositiveSmallIntegerField(blank=True, null=True, verbose_name=_('Prognostic age'),
                                                      help_text=_('Calculated age'))
    unfilled = models.TextField(blank=True, null=True)
    fat_percent = models.PositiveSmallIntegerField(
        blank=True, null=True, verbose_name=_('Body fat percentage'), help_text=None
    )
    body_type = JSONField(blank=True, null=True, verbose_name=_('Body type'), help_text=None)
    CVD = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name=_('Risk of cardiovascular disease'),
                                           help_text=None)
    fat_category = models.PositiveSmallIntegerField(blank=True, null=True, verbose_name=_(''),
                                                    help_text=None)
    diabetes = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name=_('Risk of diabetes'),
                                                help_text=None)

    def __str__(self):
        return "Result({}) for user: {}".format(self.id, self.dashboard.user)


class DiseaseRisk(models.Model):
    result = models.ForeignKey(Result, on_delete=models.CASCADE, related_name='disease_risk')
    icd_id = models.PositiveSmallIntegerField(null=True, blank=True)
    risk_string = models.CharField(blank=True, default='', null=True, max_length=30, verbose_name=_('Risk string'),
                                   help_text=None)
    message = JSONField(blank=True, default='', null=True, verbose_name=_('Message'), help_text=None)
    risk_percents = models.CharField(max_length=25, null=True, blank=True, verbose_name=_('Risk percents'),
                                     help_text=None)
    recomendation = JSONField(blank=True, default='', null=True, verbose_name=_('Recomendation'), help_text=None)


class CommonRecomendations(models.Model):
    result = models.ForeignKey(Result, on_delete=models.CASCADE, related_name='common_recomendations')
    message_short = JSONField(blank=True, default='', null=True, verbose_name=_('Message short'))
    message_long = JSONField(blank=True, default='', null=True, verbose_name=_('Message long'))
    importance_level = models.CharField(blank=True, default='', null=True, max_length=30,
                                        verbose_name=_('Importance level'))


class CategoryRecomendations(models.Model):
    name = models.CharField(max_length=255, unique=True, verbose_name='категория рекоммендаций')

    def __str__(self):
        return self.name


class Recomendations(models.Model):
    category = models.ForeignKey(CategoryRecomendations, on_delete=models.CASCADE, verbose_name='категория',
                                 related_name='recomendations')
    name_ru = models.CharField(max_length=500, unique=True, verbose_name='рекоммендация на русском')
    name_en = models.CharField(max_length=500, verbose_name='рекоммендация на английском')

    def __str__(self):
        return self.name_ru


class Disease(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='disease')
    disease_blood_pressure = models.PositiveSmallIntegerField(choices=disease.RELATED_TO_BLOOD_PRESSURE,
                                                              default=0,
                                                              verbose_name=_('Blood pressure related'))
    disease_heart_rate = models.PositiveSmallIntegerField(choices=disease.RELATED_TO_HEART_RATE,
                                                          default=0,
                                                          verbose_name=_('Associated with abnormal heart rhythm'))
    disease_obesity = models.PositiveSmallIntegerField(choices=disease.RELATED_TO_EATING_DISORDERS,
                                                       default=0,
                                                       verbose_name=_('Nutritional and metabolic disorders'))
    risk_disease_blood_pressure = models.PositiveSmallIntegerField(
        blank=True, null=True, editable=False, verbose_name=_(
            'The likelihood of having a disease associated with blood pressure'
        )
    )
    risk_disease_heart_rate = models.PositiveSmallIntegerField(
        blank=True, null=True, editable=False, verbose_name=_(
            'The likelihood of having a disease associated with an irregular heart rhythm'
        )
    )
    create = models.DateTimeField(auto_now_add=True)
    update = models.DateTimeField(auto_now=True)
    update_count = models.DateTimeField(editable=False, blank=True, null=True)
