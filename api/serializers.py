from datetime import datetime
import logging
import copy
import base64
import six
import uuid
from django.core.files.base import ContentFile, File
from django.contrib.auth import get_user_model
from django.contrib.auth import password_validation as validators
from django.conf import settings
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ObjectDoesNotExist
from django.utils.http import urlsafe_base64_decode as uid_decoder
from django.utils.translation import gettext_lazy as _
from django.utils.encoding import force_text
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator

from rest_framework import serializers, exceptions
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.settings import api_settings as rest_settings
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
from rest_framework_simplejwt.utils import datetime_from_epoch
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

from cms.models import Device, Result, DiseaseRisk, CommonRecomendations, Recomendations, HealthData, \
    CardioActivity, Disease, HealthDataHistory
from .tasks import post_health_data
from .marker import marker, marker_1, add_descriptions
from .count import unfilled_data_error
from cms.validators import MinValidatorUniversal
from cms.views import no_data

User = get_user_model()

logger = logging.getLogger('django')


# https://www.django-rest-framework.org/api-guide/serializers/#dynamically-modifying-fields
class DynamicFieldsModelSerializer(serializers.ModelSerializer):
    """
    A ModelSerializer that takes an additional `fields` argument that
    controls which fields should be displayed.
    """

    def __init__(self, *args, **kwargs):
        # Don't pass the 'fields' arg up to the superclass
        fields = kwargs.pop('fields', None)

        # Instantiate the superclass normally
        super(DynamicFieldsModelSerializer, self).__init__(*args, **kwargs)

        if fields is not None:
            # Drop any fields that are not specified in the `fields` argument.
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)


class UserCreateSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True,
                                   allow_blank=False,
                                   style={'placeholder': 'Email',
                                          'autofocus': True},
                                   )
    password = serializers.CharField(write_only=True, required=True, style={
                                     "input_type": "password"})

    class Meta:
        model = User
        fields = [
            "email",
            "password",
        ]
        extra_kwargs = {"password": {"write_only": True}}

    def __init__(self, *args, **kwargs):
        super(UserCreateSerializer, self).__init__(*args, **kwargs)
        self.fields["email"].error_messages["blank"] = "email cannot be blank"
        self.fields["password"].error_messages["blank"] = "password is required"

    def to_internal_value(self, data):
        try:
            user_data = data['user']
        except:
            raise exceptions.ParseError(detail=_("user data should be a separate block in json"))
        return super().to_internal_value(user_data)

    # add password validation
    def validate_password(self, value):
        # if value.isalnum():
        #     raise serializers.ValidationError('password must have atleast one special character.')
        return value

    def validate(self, data):
        # validators.validate_password(password=data, user=User)
        # return data

        # here data has all the fields which have validated values
        # so we can create a User instance out of it
        user = User(**data)

        # get the password from the data
        password = data.get('password')

        errors = dict()
        try:
            # validate the password and catch the exception
            validators.validate_password(password=password, user=user)

        # the exception raised here is different than serializers.ValidationError
        except exceptions.ValidationError as e:
            errors['password'] = list(e.messages)

        if errors:
            raise serializers.ValidationError(errors)

        return super(UserCreateSerializer, self).validate(data)

    def create(self, validated_data):
        email = validated_data["email"]
        password = validated_data["password"]

        if User.objects.filter(email=email).exists():
            exist_user = User.objects.get(email=email)
            if exist_user.email_confirm:
                raise serializers.ValidationError(
                    {"detail": "Email addresses must be unique."})
            else:
                exist_user.delete()

        return User.objects.create_user(**validated_data)


class ProfileSerializer(serializers.ModelSerializer):
    # image = serializers.ImageField(use_url=True)
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "image"]

class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, six.string_types):
            if 'data:' in data and ';base64,' in data:
                header, data = data.split(';base64,')
                ext = header.split('/')[-1]
                file_name = str(uuid.uuid4())[:10] + ".{}".format(ext)
            try:
                decoded_file = base64.b64decode(data)
            except TypeError:
                self.fail('invalid_image')
            data = ContentFile(decoded_file, name=file_name)

        return super(Base64ImageField, self).to_internal_value(data)

    # def to_representation(self, value):
    #     # Return url including domain name.
    #     return value.name


class ImageSerializer(serializers.ModelSerializer):
    image = Base64ImageField(required=False)

    class Meta:
        model = User
        fields = ('image',)

    def update(self, instance, validated_data):
        return super(ImageSerializer, self).update(instance, validated_data)


class EmailCheckSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True, allow_blank=False, style={
        'placeholder': 'Email', 'autofocus': True})

    class Meta:
        model = User
        fields = [
            "email",
        ]

    def validate(self, attrs):
        if User.objects.filter(email=attrs['email']):
            raise serializers.ValidationError(
                {"detail": "Email must be unique."})
        return attrs


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):

    def __init__(self, *args, **kwargs):
        super(MyTokenObtainPairSerializer, self).__init__(*args, **kwargs)
        self.fields["email"].error_messages["blank"] = "email cannot be blank"
        self.fields["password"].error_messages["blank"] = "password is required"

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        return token

    def to_internal_value(self, data):
        try:
            user_data = data['user']
        except:
            raise exceptions.ParseError(detail=_("user data should be a separate block in json"))
        return super().to_internal_value(user_data)


class MyTokenRefreshSerializer(TokenRefreshSerializer):

    def to_internal_value(self, data):
        try:
            token_data = data['token']
        except:
            raise exceptions.ParseError(detail=_("token data not found or not separate block in json"))
        return super().to_internal_value(token_data)

    def validate(self, attrs):
        try:
            user = OutstandingToken.objects.get(token=attrs['refresh']).user
        except ObjectDoesNotExist:
            raise InvalidToken()
        refresh = RefreshToken(attrs['refresh'])

        data = {'access': str(refresh.access_token)}

        if rest_settings.ROTATE_REFRESH_TOKENS:
            if rest_settings.BLACKLIST_AFTER_ROTATION:
                try:
                    # Attempt to blacklist the given refresh token
                    refresh.blacklist()
                except AttributeError:
                    # If blacklist app not installed, `blacklist` method will
                    # not be present
                    pass

            refresh.set_jti()
            refresh.set_exp()
            refresh.user = user.email

            OutstandingToken.objects.create(
                user=user,
                jti=refresh['jti'],
                token=str(refresh),
                created_at=datetime.now(),
                expires_at=datetime_from_epoch(refresh['exp']),
            )

            data['refresh'] = str(refresh)

        return data, user


class HealthCardioSerializer(serializers.ModelSerializer):
    class Meta:
        model = HealthData
        fields = ['heart_rate_alone', 'blood_pressure_sys', 'blood_pressure_dia']

    def update(self, instance, validated_data):
        resp = super(HealthCardioSerializer, self).update(instance, validated_data)
        return resp


class HealthDataSerializerVersion2(serializers.ModelSerializer):
    birth_date = serializers.DateField(allow_null=True, required=False)
    gender = serializers.IntegerField(allow_null=True, required=False)
    height = serializers.FloatField(allow_null=True, required=False,
                                    validators=[MinValidatorUniversal(50), MaxValueValidator(260)])
    weight = serializers.FloatField(allow_null=True, required=False,
                                    validators=[MinValidatorUniversal(20), MaxValueValidator(600)])
    hip = serializers.FloatField(allow_null=True, required=False,
                                 validators=[MinValidatorUniversal(20), MaxValueValidator(150)])
    waist = serializers.FloatField(allow_null=True, required=False,
                                   validators=[MinValidatorUniversal(20), MaxValueValidator(260)])
    wrist = serializers.FloatField(allow_null=True, required=False,
                                   validators=[MinValidatorUniversal(10), MaxValueValidator(40)])
    neck = serializers.FloatField(allow_null=True, required=False,
                                  validators=[MinValidatorUniversal(20), MaxValueValidator(120)])
    heart_rate_alone = serializers.IntegerField(allow_null=True, required=False,
                                                validators=[MinValidatorUniversal(40), MaxValueValidator(280)])
    blood_pressure_sys = serializers.IntegerField(allow_null=True, required=False,
                                                  validators=[MinValidatorUniversal(80), MaxValueValidator(320)])
    blood_saturation = serializers.IntegerField(
        allow_null=True, required=False,
        min_value=30, max_value=100
    )
    blood_pressure_dia = serializers.IntegerField(allow_null=True, required=False,
                                                  validators=[MinValidatorUniversal(40), MaxValueValidator(230)])
    cholesterol = serializers.FloatField(allow_null=True, required=False,
                                         validators=[MinValidatorUniversal(0.3), MaxValueValidator(9)])
    glucose = serializers.FloatField(allow_null=True, required=False,
                                     validators=[MinValidatorUniversal(2.5), MaxValueValidator(14)])
    daily_activity_level = serializers.FloatField()
    smoker = serializers.BooleanField(allow_null=True, required=False)
    measuring_system = serializers.IntegerField(allow_null=True, required=False)
    country = serializers.IntegerField(allow_null=True, required=False)
    locale = serializers.CharField(allow_null=True, required=False)

    class Meta:
        model = HealthData
        fields = [
            'gender', 'birth_date', 'country', 'height',
            'weight', 'hip', 'waist', 'wrist',
            'heart_rate_alone', 'blood_pressure_sys', 'blood_pressure_dia',
            'blood_saturation', 'cholesterol', 'glucose',
            'smoker', 'locale', 'neck', 'daily_activity_level',
            'measuring_system'
        ]

    def update(self, instance, validated_data):
        # Update model
        resp = super(HealthDataSerializerVersion2, self).update(instance, validated_data)
        # Get empty fields from model
        # FIXME
        data_filled = no_data(instance.user)
        if not data_filled:
            data = HealthData.objects.filter(id=instance.id).values().first()
            sended_data = copy.deepcopy(data)
            sended_data["user_id"] = instance.id
            sended_data["birth_date"] = sended_data["birth_date"].strftime("%d.%m.%Y")
            sended_data["user_email"] = instance.user.email

            post_health_data.delay(sended_data)
        return resp


class HealthDataHistorySerializer(DynamicFieldsModelSerializer):

    measurement_system = serializers.ReadOnlyField(source='get_measuring_system_display')

    class Meta:
        model = HealthDataHistory
        fields = '__all__'


class CardioSerializer(serializers.ModelSerializer):
    class Meta:
        model = CardioActivity
        fields = ['measuring_date', 'blood_pressure_sys',
                  'blood_pressure_dia', 'heart_rate_alone']

    def save(self, **kwargs):
        resp = super(CardioSerializer, self).save(**kwargs)
        return resp


class DeviceSerializer(serializers.ModelSerializer):

    def to_internal_value(self, data):
        try:
            device_data = data['device']
        except:
            raise exceptions.ParseError(detail=_("device data not found or not separate block in json."))
        return super().to_internal_value(device_data)

    class Meta:
        model = Device
        fields = ["device_uuid", "os_name", "os_version",
                  "device_model", "app_version"]


class PasswordResetSerializer(serializers.Serializer):
    """
    Serializer for requesting a password reset e-mail.
    """
    email = serializers.EmailField()
    app_version = serializers.CharField(required=False, default="BMI Disease Tracker")

    password_reset_form_class = PasswordResetForm

    def get_email_options(self):
        """Override this method to change default e-mail options"""
        return {}

    def validate_email(self, value):
        # Create PasswordResetForm with the serializer
        self.reset_form = self.password_reset_form_class(data=self.initial_data)
        if not self.reset_form.is_valid():
            raise serializers.ValidationError(self.reset_form.errors)

        return value

    def save(self):
        request = self.context.get('request')
        # Set some values to trigger the send_email method.
        if "app_version" in self.initial_data:
            app_bmi = "AntiCorona Virus" if "covid" in self.initial_data["app_version"] else "BMI Disease Tracker"
        else:
            app_bmi = "BMI Disease Tracker"

        extra_email_context = {
            'fullurlstatic': request.build_absolute_uri('/static/'),
            'host': request.get_host(),
            'protocol': request.scheme,
            'app_bmi': app_bmi,
        }

        opts = {
            'use_https': request.is_secure(),
            'from_email': getattr(settings, 'DEFAULT_FROM_EMAIL'),
            'request': request,
            'email_template_name': 'email/password_reset_email.html',
            'html_email_template_name': 'email/password_reset_email.html',
            'extra_email_context': extra_email_context
        }

        opts.update(self.get_email_options())
        self.reset_form.save(**opts)


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Serializer for requesting a password reset e-mail.
    """
    new_password1 = serializers.CharField(max_length=128)
    new_password2 = serializers.CharField(max_length=128)
    uid = serializers.CharField()
    token = serializers.CharField()

    set_password_form_class = SetPasswordForm

    def custom_validation(self, attrs):
        pass

    def validate(self, attrs):
        self._errors = {}

        # Decode the uidb64 to uid to get User object
        try:
            uid = force_text(uid_decoder(attrs['uid']))
            self.user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise ValidationError({'uid': ['Invalid value']})

        self.custom_validation(attrs)
        # Construct SetPasswordForm instance
        self.set_password_form = self.set_password_form_class(
            user=self.user, data=attrs
        )
        if not self.set_password_form.is_valid():
            raise serializers.ValidationError(self.set_password_form.errors)
        if not default_token_generator.check_token(self.user, attrs['token']):
            raise ValidationError({'token': ['Invalid value']})

        return attrs

    def save(self):
        return self.set_password_form.save()


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(max_length=128)
    new_password1 = serializers.CharField(max_length=128)
    new_password2 = serializers.CharField(max_length=128)

    set_password_form_class = SetPasswordForm

    def __init__(self, *args, **kwargs):
        self.old_password_field_enabled = getattr(
            settings, 'OLD_PASSWORD_FIELD_ENABLED', False
        )
        self.logout_on_password_change = getattr(
            settings, 'LOGOUT_ON_PASSWORD_CHANGE', False
        )
        super(PasswordChangeSerializer, self).__init__(*args, **kwargs)

        if not self.old_password_field_enabled:
            self.fields.pop('old_password')

        self.request = self.context.get('request')
        self.user = getattr(self.request, 'user', None)

    def validate_old_password(self, value):
        invalid_password_conditions = (
            self.old_password_field_enabled,
            self.user,
            not self.user.check_password(value)
        )

        if all(invalid_password_conditions):
            err_msg = _("Your old password was entered incorrectly. Please enter it again.")
            raise serializers.ValidationError(err_msg)
        return value

    def validate(self, attrs):
        self.set_password_form = self.set_password_form_class(
            user=self.user, data=attrs
        )

        if not self.set_password_form.is_valid():
            raise serializers.ValidationError(self.set_password_form.errors)
        return attrs

    def save(self):
        self.set_password_form.save()
        if not self.logout_on_password_change:
            from django.contrib.auth import update_session_auth_hash
            update_session_auth_hash(self.request, self.user)


class DiseaseRiskSerializer(serializers.ModelSerializer):
    message = serializers.DictField()
    recomendation = serializers.DictField()
    class Meta:
        model = DiseaseRisk
        fields = ['icd_id', 'risk_string', 'message', 'risk_percents', 'recomendation']


class DiseaseRiskSerializerView(serializers.ModelSerializer):
    class Meta:
        model = DiseaseRisk
        fields = ['icd_id', 'risk_string', 'message', 'risk_percents', 'recomendation']


class CommonRecomendationsSerializer(serializers.ModelSerializer):
    message_short = serializers.DictField()
    message_long = serializers.DictField()

    class Meta:
        model = CommonRecomendations
        fields = ['message_short', 'message_long', 'importance_level']


class CommonRecomendationsSerializerView(serializers.ModelSerializer):
    class Meta:
        model = CommonRecomendations
        fields = ['message_short', 'message_long', 'importance_level']


class ResultSerializer(serializers.ModelSerializer):
    obesity_level = serializers.DictField()
    common_risk_level = serializers.DictField()
    body_type = serializers.DictField()
    disease_risk = DiseaseRiskSerializer(many=True)
    common_recomendations = CommonRecomendationsSerializer(many=True)

    class Meta:
        model = Result
        fields = ['bmi', 'obesity_level', 'ideal_weight', 'base_metabolism', 'calories_to_low_weight',
                  'waist_to_hip_proportion', 'passport_age', 'common_risk_level', 'prognostic_age',
                  'fat_percent', 'fat_category', 'body_type', 'unfilled', 'disease_risk', 'common_recomendations',
                  'CVD', 'diabetes']

    def to_internal_value(self, data):
        logger.info('Information incoming!')
        self.dashboard = HealthData.objects.filter(pk=data['user_id']).first()
        try:
            Result.objects.filter(dashboard=self.dashboard).delete()
        except:
            logger.exception('Something went wrong with old_result!')
        try:
            result_data = data['user_calc_data']
        except:
            logger.exception('Wrong parse user_calc_data!')
            raise exceptions.ParseError(detail=_("user_calc_data should be a separate block in json."))
        return super().to_internal_value(result_data)

    def create(self, validated_data):
        risks_data = validated_data.pop('disease_risk')
        recomendations_data = validated_data.pop('common_recomendations')
        result = Result.objects.create(dashboard=self.dashboard, **validated_data)
        for risk in risks_data:
            DiseaseRisk.objects.create(result=result, **risk)
        for recomendation in recomendations_data:
            CommonRecomendations.objects.create(result=result, **recomendation)
        logger.info('Result create!')
        return result

class ResultSerializerView(serializers.ModelSerializer):
    obesity_level = serializers.CharField()
    common_risk_level = serializers.CharField()
    body_type = serializers.CharField()
    disease_risk = DiseaseRiskSerializerView(many=True)
    common_recomendations = CommonRecomendationsSerializerView(many=True)

    class Meta:
        model = Result
        fields = ['bmi', 'obesity_level', 'ideal_weight', 'base_metabolism', 'calories_to_low_weight',
                  'waist_to_hip_proportion', 'passport_age', 'common_risk_level', 'prognostic_age',
                  'fat_percent', 'body_type', 'unfilled', 'disease_risk', 'common_recomendations']

    def to_representation(self, instance):
        data = super(ResultSerializerView, self).to_representation(instance)

        if data['unfilled'] is None:
            data = {'Error': 'Data is not filled'}
            return data

        data['fat_percent'] = data['fat_percent'].split(',')[0]
        return data


class ResultSerializerVersion2(serializers.ModelSerializer):
    bmi = serializers.ListField()
    obesity_level = serializers.ListField()
    fat_percent = serializers.ListField()
    common_risk_level = serializers.ListField()
    disease_risk = DiseaseRiskSerializerView(many=True)
    common_recomendations = CommonRecomendationsSerializerView(many=True)

    class Meta:
        model = Result
        fields = ['bmi', 'obesity_level', 'ideal_weight', 'base_metabolism', 'calories_to_low_weight',
                  'waist_to_hip_proportion', 'passport_age', 'common_risk_level', 'prognostic_age',
                  'fat_percent', 'body_type', 'unfilled', 'disease_risk', 'common_recomendations', 'CVD']

    def to_representation(self, instance):
        if not instance or not instance.bmi:
            locale = self.context.get('locale')
            user_id = self.context.get('user_id')
            data = unfilled_data_error(locale, user_id)
            return data
        instance = marker(instance)
        data = super(ResultSerializerVersion2, self).to_representation(instance)
        data = marker_1(data)
        return data


class ResultDataSerializer(serializers.ModelSerializer):

    disease_risk = DiseaseRiskSerializerView(many=True)
    common_recomendations = CommonRecomendationsSerializerView(many=True)

    class Meta:
        model = Result
        fields = ['bmi', 'obesity_level', 'ideal_weight', 'base_metabolism', 'calories_to_low_weight',
                  'waist_to_hip_proportion', 'passport_age', 'common_risk_level', 'prognostic_age',
                  'fat_percent', 'fat_category', 'body_type', 'CVD', 'unfilled', 'disease_risk', 'common_recomendations']

    def to_representation(self, instance):
        if not instance or not instance.bmi:
            locale = self.context.get('locale')
            user_id = self.context.get('user_id')
            data = unfilled_data_error(locale, user_id)
            return data

        data = super(ResultDataSerializer, self).to_representation(instance)
        data = add_descriptions(data)

        return data


class RecomendationsSerializerRu(serializers.ModelSerializer):
    name = serializers.CharField(max_length=500, source='name_ru')
    class Meta:
        model = Recomendations
        fields = ['name']

class RecomendationsSerializerEn(serializers.ModelSerializer):
    name = serializers.CharField(max_length=500, source='name_en')
    class Meta:
        model = Recomendations
        fields = ['name']

class DiseaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Disease
        fields = ['disease_blood_pressure', 'disease_heart_rate', 'disease_obesity']


class UserProfileSerializer(serializers.ModelSerializer):
    height = serializers.FloatField(validators=[MinValueValidator(50), MaxValueValidator(260)])
    class Meta:
        model = HealthData
        fields = ['birth_date', 'country', 'gender', 'height', 'smoker', 'measuring_system']


class MedCardSerializer(serializers.ModelSerializer):
    weight = serializers.FloatField(allow_null=True, required=False,
                                    validators=[MinValidatorUniversal(20), MaxValueValidator(600)])
    hip = serializers.FloatField(allow_null=True, required=False,
                                 validators=[MinValidatorUniversal(20), MaxValueValidator(150)])
    waist = serializers.FloatField(allow_null=True, required=False,
                                   validators=[MinValidatorUniversal(20), MaxValueValidator(260)])
    wrist = serializers.FloatField(allow_null=True, required=False,
                                   validators=[MinValidatorUniversal(10), MaxValueValidator(40)])
    neck = serializers.FloatField(allow_null=True, required=False,
                                  validators=[MinValidatorUniversal(20), MaxValueValidator(120)])
    heart_rate_alone = serializers.IntegerField(allow_null=True, required=False,
                                                validators=[MinValidatorUniversal(40), MaxValueValidator(280)])
    blood_pressure_sys = serializers.IntegerField(allow_null=True, required=False,
                                                  validators=[MinValidatorUniversal(80), MaxValueValidator(320)])
    blood_pressure_dia = serializers.IntegerField(allow_null=True, required=False,
                                                  validators=[MinValidatorUniversal(40), MaxValueValidator(230)])
    cholesterol = serializers.FloatField(allow_null=True, required=False,
                                         validators=[MinValidatorUniversal(0.3), MaxValueValidator(9)])
    glucose = serializers.FloatField(allow_null=True, required=False,
                                     validators=[MinValidatorUniversal(2.5), MaxValueValidator(14)])

    class Meta:
        model = HealthData
        fields = ['weight', 'hip', 'waist', 'wrist', 'neck', 'heart_rate_alone', 'daily_activity_level',
                  'blood_pressure_sys', 'blood_pressure_dia', 'cholesterol', 'glucose']

    def update(self, instance, validated_data):
        resp = super(MedCardSerializer, self).update(instance, validated_data)
        sended_data = HealthData.objects.filter(id=instance.id).values().first()
        sended_data["user_id"] = instance.id
        if "birth_date" in sended_data:
            if sended_data["birth_date"] and sended_data["birth_date"] != "null":
                sended_data["birth_date"] = sended_data["birth_date"].strftime("%d.%m.%Y")
        post_health_data.delay(sended_data)
        return resp







