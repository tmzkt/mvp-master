import logging
from collections import OrderedDict
from datetime import datetime

import requests
from django.contrib.auth import get_user_model
from django.contrib.staticfiles.storage import staticfiles_storage
from django.db.models import Q
from django.http import JsonResponse, Http404
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.utils.translation import activate
from django.utils.translation import get_language
from django.utils.translation import gettext_lazy as _
from django.views.decorators.debug import sensitive_post_parameters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import response, decorators, permissions, status, generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from cms.countries import COUNTRIES
from cms.models import HealthData, Result, Recomendations, CardioActivity, Disease, HealthDataHistory
from users.tasks import mail_send
from . import app_settings
from .count_deviation_cardio import count
from .exceptions import DeviceNotRegister
from .filters import cardio_recomendations, user_recomendations
from .filterset import HealthDataHistoryFilterSet
from .mixins import DeviceRegisterMixin
from .permissions import IsBase
from .serializers import UserCreateSerializer, MyTokenObtainPairSerializer, MyTokenRefreshSerializer, \
    ProfileSerializer, EmailCheckSerializer, PasswordResetSerializer, \
    PasswordResetConfirmSerializer, PasswordChangeSerializer, ResultSerializer, CardioSerializer, \
    HealthDataSerializerVersion2, RecomendationsSerializerRu, RecomendationsSerializerEn, HealthCardioSerializer, \
    ImageSerializer, DiseaseSerializer, ResultSerializerVersion2, ResultSerializerView, UserProfileSerializer, \
    MedCardSerializer, ResultDataSerializer, HealthDataHistorySerializer
from .tasks import warning_mail_send

sensitive_post_parameters_m = method_decorator(
    sensitive_post_parameters(
        'password', 'old_password', 'new_password1', 'new_password2'
    )
)

User = get_user_model()

logger = logging.getLogger('django')


class UserSignUp(DeviceRegisterMixin, generics.CreateAPIView):
    """
    IMPORTANT!
    structure of request:
    {
      "user": {
        "email": "admin@admin.ru",
        "password": "django1234"
        },
      "device": {
        "device_uuid": "676a8124-e98d-4e0e-8809-cecf0e3efdaf",
        "os_name": "ios",
        "os_version": "13.1.3",
        "device_model": "iPhone12,5",
        "app_version": "0.1.1"
        }
    }

    REQUIRED FIELDS: email, password, device_uuid, device_model
    """
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = UserCreateSerializer

    def perform_create(self, serializer):
        return serializer.save()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = self.perform_create(serializer)

        # add tokens
        refresh = RefreshToken.for_user(user)
        res = {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }
        # create HealthProfile(dashboard) for new user
        dashboard = HealthData.objects.create(user=user)
        # create results panel
        Result.objects.create(dashboard=dashboard)

        # register device
        try:
            device, _ = self.device_register(data=request.data, user=user)
            device.token = res["refresh"]
            device.save()
        except:
            raise DeviceNotRegister()

        # send confirm letter
        mail_send.delay(
            lang=get_language(),
            scheme=self.request.scheme,
            host=self.request.get_host(),
            user_id=user.id,
            app_bmi="AntiCorona Virus" if "covid" in request.data['device']['app_version'] else "BMI Disease Tracker",
        )

        headers = self.get_success_headers(serializer.data)
        return response.Response(res, status=status.HTTP_201_CREATED, headers=headers)


class UserProfile(generics.RetrieveUpdateDestroyAPIView, generics.CreateAPIView):
    """
    Info about userprofile. Read, Update, Delete methods.
    """
    queryset = User.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        """
        Returns the object the view is displaying.
        You may want to override this if you need to provide non-standard
        queryset lookups.  Eg if objects are referenced using multiple
        keyword arguments in the url conf.
        """
        queryset = self.filter_queryset(self.get_queryset())
        user = queryset.get(pk=self.request.user.id)
        # May raise a permission denied
        self.check_object_permissions(self.request, user)

        try:
            HealthData.objects.get(user_id=user)
        except HealthData.DoesNotExist:
            dashboard = HealthData.objects.create(user=user)
            Result.objects.create(dashboard=dashboard)

        return user

    def create(self, request, *args, **kwargs):
        if not request.data:
            logger.error("Not request.data")
            return response.Response({"result": "data can`t be a blanks"}, status.HTTP_400_BAD_REQUEST)
        logger.error(request.data)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return response.Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_200_OK, data={'delete': 'OK'})


class UserDashboard(generics.RetrieveUpdateAPIView):
    """
    {
  "gender": 1,
  "birth_date": "27.07.2000",
  "country": 20,
  "height": 190,
  ...
  ...
  "daily_activity_level": 1.2,
  "measuring_system": 1
}
    """
    queryset = HealthData.objects.all()
    serializer_class = HealthDataSerializerVersion2
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        """
        Returns the object the view is displaying.

        You may want to override this if you need to provide non-standard
        queryset lookups.  Eg if objects are referenced using multiple
        keyword arguments in the url conf.
        """
        queryset = self.filter_queryset(self.get_queryset())
        obj = queryset.get(user=self.request.user)
        # May raise a permission denied
        self.check_object_permissions(self.request, obj)

        return obj

    def perform_update(self, serializer):
        data = {"heart_rate_alone": self.request.data.get("heart_rate_alone"),
                "blood_pressure_sys": self.request.data.get("blood_pressure_sys"),
                "blood_pressure_dia": self.request.data.get("blood_pressure_dia"),}
        cardioactivity_serializer = CardioSerializer(data=data)
        if cardioactivity_serializer.is_valid(raise_exception=True):
            cardioactivity_serializer.save(
                health_model=self.request.user.health_data)
        else:
            logger.error("Cardioactivity update through HealthData is failed(api/views/UserDashboard)")
        return serializer.save()


class HealthDataHistoryAPIView(generics.ListAPIView):
    """
    Lists all Health History Data from the database

    ``
    Supported Filter:
        create:
            query: ?start_at=2021-10-1&end_at=2021-10-1
    ``


    Fields can be requested as per need and supported fields are:

        'cholesterol', 'blood_pressure_sys', 'blood_pressure_dia',
        'blood_saturation', 'glucose', 'heart_rate_alone',
        'weight', 'waist', 'wrist', 'neck', 'hip'
        'measuring_system'

    fields can be requested in two way

        * if only one field is required:    ?fields=cholesterol
        * if multiple fields are required:  ?fields=cholesterol, glucose

    """
    queryset = HealthDataHistory.objects.all()
    serializer_class = HealthDataHistorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = (DjangoFilterBackend, )
    filterset_class = HealthDataHistoryFilterSet

    def get_requested_fields(self):
        # Fields that are to be shown with respect to request
        ctx = super().get_serializer_context()

        requested_fields = self.request.query_params.get('fields', [])

        # Set value in list
        requested_fields = requested_fields.split(',')

        # get common fields
        valid_fields = set(requested_fields).intersection(
            set(HealthData.relevant_fields)
        )

        # Prevent error if field already contains create
        fields = {*valid_fields, 'create'}

        return list(fields)

    def get_serializer(self, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        kwargs['context'] = self.get_serializer_context()

        kwargs['fields'] = self.get_requested_fields()
        return serializer_class(*args, **kwargs)

    def get_queryset(self):
        return super().get_queryset().filter(
            health_data__user=self.request.user
        )


class IsEmailExist(generics.CreateAPIView):
    """
    Check emails to database.
    """
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = EmailCheckSerializer

    def post(self, request):
        if not request.data:
            return response.Response({"exist": "email can`t be a blank"}, status.HTTP_400_BAD_REQUEST)
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid(raise_exception=False):
            return response.Response({"exist": False}, status.HTTP_200_OK)
        return response.Response({"exist": True}, status.HTTP_200_OK)


class MyTokenObtainPairView(DeviceRegisterMixin, TokenObtainPairView):
    """
    IMPORTANT!
    structure of request:
    {
      "user": {
        "email": "admin@admin.ru",
        "password": "django1234"
        },
      "device": {
        "device_uuid": "676a8124-e98d-4e0e-8809-cecf0e3efdaf",
        "os_name": "ios",
        "os_version": "13.1.3",
        "device_model": "iPhone12,5",
        "app_version": "0.1.1"
        }
    }

    REQUIRED FIELDS: email, password, device_uuid, device_model
    """
    serializer_class = MyTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):

        # check how many devices logged in
        user = get_object_or_404(User, email=request.data['user']['email'])
        dev_list = user.device.all()
        # FIXME
        if len(dev_list) >= app_settings.MAX_NUM_DEVICES:
            message = {'detail': _('too many devices logged in. First device will be deleted')}
            dev_list[0].delete()
            # message = {'detail': _('too many devices logged in. Please log out from one of this')}
            # return response.Response(message, status=status.HTTP_401_UNAUTHORIZED)

        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            raise InvalidToken(e.args[0])

        # check or register device
        tokens = serializer.validated_data

        device, flag = self.device_register(data=request.data, user=user)
        if flag:
            # Add send warning_email about login
            warning_mail_send.delay(user.email)

        device.token = tokens["refresh"]
        device.save()

        return response.Response(tokens, status=status.HTTP_200_OK)


class MyTokenRefreshView(DeviceRegisterMixin, TokenRefreshView):
    """
    IMPORTANT!
    structure of request:
    {
      "token": {
        "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhY2Nlc3MiOiJyZWZyZXNoIiwiZXhwIjoxNTgzNTA3NTY3LCJqdGkiOiJiNzk1ZDJmNzZkMjI0N2VhYTY1N...."
    },
      "device": {
        "device_uuid": "676a8124-e98d-4e0e-8809-cecf0e3efdaf",
        "os_name": "ios",
        "os_version": "13.1.3",
        "device_model": "iPhone12,5",
        "app_version": "0.1.1"
        }
    }

    REQUIRED FIELDS: email, password, device_uuid, device_model

    Takes a refresh type JSON web token and returns an access type JSON web
    token if the refresh token is valid.
    """
    serializer_class = MyTokenRefreshSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            raise InvalidToken(e.args[0])

        # check or register device
        # user = Device.objects.get(token=request.data['token']['refresh']).user
        tokens, user = serializer.validated_data

        device, flag = self.device_register(data=request.data, user=user)
        if flag:
            # Add send warning_email about login
            warning_mail_send.delay(user.email)

        device.token = tokens["refresh"]
        device.save()

        return response.Response(tokens, status=status.HTTP_200_OK)


class PolicyIntime(generics.ListAPIView):
    """
    ##Only GET Method. Return Policy Intime Biotech LLC
    * Body: Empty
    * Locale: Define HTTP Header "Accept-Language"
    """
    permission_classes = (AllowAny,)

    def get(self, request, *args, **kwargs):
        name_policy = "docs/PrivacyPolicy_" + request.LANGUAGE_CODE + ".html"
        url = request.build_absolute_uri(staticfiles_storage.url(name_policy))
        r = requests.get(url)
        if r.status_code == status.HTTP_200_OK:
            return response.Response({"policy": r.content})
        else:
            return response.Response({"detail": "Error Policy"})


@decorators.api_view(["POST"])
@decorators.permission_classes([permissions.AllowAny])
def policy(request):
    """
    POST request with body {"locale": "ru-ru"|"en-en"}
    """
    # url = app_settings.PRIVACY_URL
    # headers = {"APIkey": app_settings.KEY_PRIVACY_POLICY}
    # r = requests.post(url, headers=headers, json=request.data)
    # resp = json.loads(r.text)
    # resp.pop('lang', None)
    # url = static('docs/PrivacyPolicy.html')
    try:
        if request.data["locale"] == "en-en" or request.data["locale"] == "en-US":
            url = request.build_absolute_uri(staticfiles_storage.url("docs/PrivacyPolicy_en.html"))
        elif request.data["locale"] == "ru-ru":
            url = request.build_absolute_uri(staticfiles_storage.url("docs/PrivacyPolicy_ru.html"))
        else:
            raise ValueError("")
        r = requests.get(url)
        resp = {"policy": r.content}
    except KeyError:
        resp = {"detail": "Key must be \"locale\""}
    except ValueError:
        resp = {"detail": "Value must be \"en\" or \"ru\""}

    return response.Response(resp)


@decorators.api_view(["POST"])
@decorators.permission_classes([permissions.AllowAny])
def genders_dict(request):
    """
    POST request with body {'locale': 'ru/en'}
    return dict with genders
    """
    # url = app_settings.GENDERS_URL
    # headers = {"APIkey": app_settings.GENDERS_KEY}
    # r = requests.post(url, headers=headers, json=request.data)
    # resp = json.loads(r.text)
    # return response.Response(resp)
    try:
        activate(request.data['locale'])
    except KeyError:
        return Response({"detail": "We need specify \"locale\""})
    genders = [("genders", [{'id': item, 'value': value} for item, value in ((1, _('Male')),
                                                                             (2, _('Female')),
                                                                             (3, _('Undefined'),
                                                                              ))])]
    return Response(OrderedDict(genders))


@decorators.api_view(["POST"])
@decorators.permission_classes([permissions.AllowAny])
def countries_dict(request):
    """
    POST request with body {'locale': 'ru/en', "short_code": false}
    return dict with countries
    """
    # url = app_settings.COUNTRIES_URL
    # headers = {"APIkey": app_settings.COUNTRIES_KEY}
    # r = requests.post(url, headers=headers, json=request.data)
    # return response.Response(r.json())
    try:
        activate(request.data['locale'])
    except KeyError:
        return Response({"detail": "We need specify \"locale\""})
    countries = [("countries", [{'id': item, 'value': value} for item, value in COUNTRIES])]
    return Response(OrderedDict(countries))


class PasswordResetView(generics.GenericAPIView):
    """
    Calls Django Auth PasswordResetForm save method.
    Accepts the following POST parameters: email
    Returns the success/fail message.
    """
    serializer_class = PasswordResetSerializer
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        # Create a serializer with request.data
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.save()

        # data = {"detail": _("Password reset e-mail has been sent.")}
        # return JsonResponse(data=data, status=status.HTTP_200_OK)
        # Return the success message with OK HTTP status
        return response.Response(
            {"detail": _("Password reset e-mail has been sent.")},
            status=status.HTTP_200_OK
        )


class PasswordResetConfirmView(generics.GenericAPIView):
    """
    Password reset e-mail link is confirmed, therefore
    this resets the user's password.
    Accepts the following POST parameters: token, uid,
        new_password1, new_password2
    Returns the success/fail message.
    """
    serializer_class = PasswordResetConfirmSerializer
    permission_classes = (AllowAny,)

    @sensitive_post_parameters_m
    def dispatch(self, *args, **kwargs):
        return super(PasswordResetConfirmView, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return response.Response(
            {"detail": _("Password has been reset with the new password.")}
        )


class PasswordChangeView(generics.GenericAPIView):
    """
    Calls Django Auth SetPasswordForm save method.
    Accepts the following POST parameters: new_password1, new_password2
    Returns the success/fail message.
    """
    serializer_class = PasswordChangeSerializer
    permission_classes = (IsAuthenticated,)

    @sensitive_post_parameters_m
    def dispatch(self, *args, **kwargs):
        return super(PasswordChangeView, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return response.Response({"detail": _("New password has been saved.")})


class ResultCreateView(generics.CreateAPIView):
    serializer_class = ResultSerializer
    permission_classes = (IsBase,)
    def create(self, data, *args, **kwargs):
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return response.Response({"result": "OK!"}, status=status.HTTP_201_CREATED, headers=headers)


class Results(generics.RetrieveAPIView):
    """
    {
      "bmi": 0,
      "obesity_level": "string",
      "ideal_weight": 0,
      "base_metabolism": 0,
      "calories_to_low_weight": 0,
      "waist_to_hip_proportion": 0,
      "passport_age": 0,
      "common_risk_level": "string",
      "prognostic_age": 0,
      "fat_percent": "string",
      "body_type": "string",
      "unfilled": "string",
      "disease_risk": [
        {
          "icd_id": 0,
          "risk_string": "string",
          "risk_percents": 0,
          "message": "string",
          "recomendation": "string"
        }
      ],
      "common_recomendations": [
        {
          "message_short": "string",
          "message_long": "string",
          "importance_level": "string"
        }
      ]
    }
    """
    queryset = Result.objects.all()
    serializer_class = ResultSerializerView
    # permission_classes = (IsAuthenticated,)

    def get_serializer_class(self):
        if self.request.version == 'v2':
            return ResultSerializerVersion2
        return ResultSerializerView

    def get_object(self):
        logger.info('Get object Result for user_id: {}!'.format(self.request.user.id))
        queryset = self.filter_queryset(self.get_queryset())
        obj = queryset.filter(dashboard=self.request.user.health_data).first()
        if not obj:
            obj = []
        # May raise a permission denied
        self.check_object_permissions(self.request, obj)

        # if obj.unfilled is None:
        #     raise Http404

        return obj

    def get_serializer_context(self):
        return {'locale': self.request.LANGUAGE_CODE, 'user_id': self.request.user.id}


class ResultsData(generics.RetrieveAPIView):
    """
    ##Only GET Method. Return Parameters:
            {
                "params": [
                    {
                        "name": str,
                        "value": int or str,
                        "color": str("#FFFFFF"),
                        "desc": str("This is the description parameter")
                    },
                ],
                "disease_risk": [
                    {
                    "icd_id": 0,
                    "risk_string": "string",
                    "risk_percents": 0,
                    "message": "string",
                    "recomendation": "string"
                    }
                ],
                "common_recomendations": [
                    {
                    "message_short": "string",
                    "message_long": "string",
                    "importance_level": "string"
                    }
                ],
                "disease_risk": [
                    {
                        "icd_id": int or str,
                        "risk_string": str,
                        "message": str,
                        "risk_percents": int,
                        "recomendation": str
                    },
                    {
                        ...
                    }
                ],
                "common_recommendations": [
                    {
                        "message_short": str,
                        "message_long": str,
                        "importance_level": str("#FFFFFF")
                    },
                    {
                        ...
                    }
                ],
            }

    """
    queryset = Result.objects.all()
    serializer_class = ResultDataSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        logger.info('{} | ResultData | In get_object!'.format(self.request.user))
        obj = self.queryset.filter(dashboard=self.request.user.health_data).first()

        if not obj:
            obj = []
        # May raise a permission denied
        self.check_object_permissions(self.request, obj)

        # if obj.unfilled is None:
        #     raise Http404

        return obj

    def get_serializer_context(self):
        return {'locale': self.request.LANGUAGE_CODE, 'user_id': self.request.user.id}


@decorators.api_view(["GET"])
@decorators.permission_classes([permissions.AllowAny])
def getfirstresulttime(request):
    '''
    {
     "timestamp": 1594814030.222324
    }
    '''
    result = {}
    timestamp = datetime.timestamp(HealthData.objects.filter(user=request.user).first().create)
    result['timestamp'] = timestamp
    # if request.version == 'v2':
    #     '''
    #     {
    #     "timestamp": 1594814030.222324,
    #      "full_version_end_date": 0
    #     }
    #     '''
    #     try:
    #         full_version_end_date = datetime.timestamp(Payment.objects.filter(user=request.user).first().end_date)
    #     except Payment.DoesNotExist:
    #         full_version_end_date = 0
    #     result['full_version_end_date'] = full_version_end_date
    #     return JsonResponse(result)
    return JsonResponse(result)


class UserCardioactivity(generics.ListAPIView):
    """
    GET Request timestamp/timestamp/
    Response body
    [
      {
        "measuring_date": "2020-08-06T08:03:09.212Z",
        "blood_pressure_sys": 0,
        "blood_pressure_dia": 0,
        "heart_rate_alone": 0
      }
    ]
    """
    queryset = CardioActivity.objects.all()
    serializer_class = CardioSerializer

    def get(self, request, *args, **kwargs):
        start_date = datetime.utcfromtimestamp(self.kwargs['start_date']).strftime('%Y-%m-%d')
        end_date = datetime.utcfromtimestamp(self.kwargs['end_date']).strftime('%Y-%m-%d')
        queryset = CardioActivity.objects.filter(health_model=self.request.user.health_data).filter(
                                                 measuring_date__date__range=(start_date, end_date))
        serializer = CardioSerializer(queryset, many=True)
        return Response(serializer.data)

class CreateUserCardioactivity(generics.CreateAPIView):
    '''
    Request
    {
      "blood_pressure_sys": 0,
      "blood_pressure_dia": 0,
      "heart_rate_alone": 0
    }
    Response body
    {
      "message_pressure": "Давление опасно высокое. Срочная медицинская помощь!",
      "message_heart_rate": "Учащенное сердцебиение. Проконсультируйтесь у врача."
    }
    '''
    permission_classes = (IsAuthenticated,)
    queryset = CardioActivity.objects.all()
    serializer_class = CardioSerializer

    def perform_create(self, serializer):
        '''Associating health_model with user'''
        healthdata_serializer = HealthCardioSerializer(
            instance=self.request.user.health_data, data=self.request.data)
        if healthdata_serializer.is_valid(raise_exception=False):
            healthdata_serializer.save()
        else:
            logger.error("HelathData update through CardioActivity is failed(api/views/UserCardioactivity)")

        return serializer.save(health_model=self.request.user.health_data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        result = count(request)
        return Response(result, status=status.HTTP_201_CREATED, headers=headers)


class UserRecomendations(generics.ListAPIView):
    '''
    [
      {
        "name": "string"
      }
    ]
    '''
    ru_serializer_class = RecomendationsSerializerRu
    en_serializer_class = RecomendationsSerializerEn
    def get_serializer_class(self):
        if self.request.LANGUAGE_CODE.startswith('ru'):
            return self.ru_serializer_class
        else:
            return self.en_serializer_class

    def list(self, request, *args, **kwargs):
        list, cat = user_recomendations(request)
        queryset = Recomendations.objects.filter(Q(pk__in=list)|Q(category__pk__in=cat))
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class CardioRecomendations(generics.ListAPIView):
    '''
    {
     "рекомендуется": [
          { "name": "string"}, ],
     "исключить": [
          { "name": "string"}, ]
    }
    '''
    ru_serializer_class = RecomendationsSerializerRu
    en_serializer_class = RecomendationsSerializerEn
    def get_serializer_class(self):
        if self.request.LANGUAGE_CODE.startswith('ru'):
            return self.ru_serializer_class
        else:
            return self.en_serializer_class

    def list(self, request, *args, **kwargs):
        cat_yes, list, cat_not = cardio_recomendations(request)
        queryset = Recomendations.objects.filter(Q(pk__in=list) | Q(category__pk__in=cat_yes))
        serializer = self.get_serializer(queryset, many=True)
        queryset_not = Recomendations.objects.filter(category__pk__in=cat_not)
        serializer_not = self.get_serializer(queryset_not, many=True)
        result = {'recommended': serializer.data, 'not recommended': serializer_not.data}
        return Response(result)


class Image(generics.RetrieveUpdateAPIView):
    """
    {
     "image": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAgA..."
    }
    """
    permission_classes = (IsAuthenticated,)
    serializer_class = ImageSerializer
    queryset = User.objects.all()
    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        obj = queryset.filter(pk=self.request.user.id).first()
        self.check_object_permissions(self.request, obj)
        return obj

class DiseaseViews(generics.CreateAPIView, generics.RetrieveUpdateAPIView):
    """
    {
      "disease_blood_pressure": 4,
      "disease_heart_rate": 2,
      "disease_obesity": 3
    }
    """
    permission_classes = (IsAuthenticated,)
    serializer_class = DiseaseSerializer
    queryset = Disease.objects.all()
    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        filter_kwargs = {'user': self.request.user}
        try:
            obj = get_object_or_404(queryset, **filter_kwargs)
        except Http404:
            obj = []
        self.check_object_permissions(self.request, obj)
        return obj

    def perform_create(self, serializer):
        return serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        serializer.save(user=self.request.user)


class ProfileUser(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = (IsAuthenticated,)
    queryset = HealthData.objects.all()

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        obj = queryset.get(user=self.request.user)
        self.check_object_permissions(self.request, obj)
        return obj


class MedCard(generics.RetrieveUpdateAPIView):
    serializer_class = MedCardSerializer
    permission_classes = (IsAuthenticated,)
    queryset = HealthData.objects.all()

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        obj = queryset.get(user=self.request.user)
        self.check_object_permissions(self.request, obj)
        return obj

    def perform_update(self, serializer):
        data = {"heart_rate_alone": self.request.data["heart_rate_alone"],
                "blood_pressure_sys": self.request.data["blood_pressure_sys"],
                "blood_pressure_dia": self.request.data["blood_pressure_dia"],}
        cardioactivity_serializer = CardioSerializer(data = data)
        if cardioactivity_serializer.is_valid(raise_exception=True):
            cardioactivity_serializer.save(
                health_model=self.request.user.health_data)
        else:
            logger.error("Cardioactivity update through HealthData is failed(api/views/UserDashboard)")
        return serializer.save()


class InformationView(generics.ListAPIView):
    """
    ##Only GET Method. Return the list of immutable data
    * Body: Empty
    * Locale: Define HTTP Header "Accept-Language"
    """
    permission_classes = (IsAuthenticated,)

    #
    def get(self, request, *args, **kwargs):
        info = [
                {"countries": [{'id': item, 'value': value} for item, value in COUNTRIES]},
                {"genders": [{'id': item, 'value': value} for item, value in ((1, _('Male')),
                                                                              (2, _('Female')),
                                                                              (3, _('Undefined')),
                                                                              )]}
                ]
        info = [("info", info)]

        return Response(OrderedDict(info))

























