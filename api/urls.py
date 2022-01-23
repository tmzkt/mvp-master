from django.urls import path, re_path, include
from .views import *

app_name = 'v1'

urlpatterns = [
    path('isemailexist/', IsEmailExist.as_view()),
    path('profile/', UserProfile.as_view()),
    path('dashboard/', UserDashboard.as_view()),
    path('data-history/', HealthDataHistoryAPIView.as_view()),
    path('signup/', UserSignUp.as_view(), name='signup'),
    path('token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', MyTokenRefreshView.as_view(), name='token_refresh'),
    path('password/reset/', PasswordResetView.as_view(), name='rest_password_reset'),
    path('password/reset/confirm/', PasswordResetConfirmView.as_view(), name='rest_password_reset_confirm'),
    path('password/change/', PasswordChangeView.as_view(), name='rest_password_change'),
    path('policy/', policy),
    path('policy-intime/', PolicyIntime.as_view(), name='policy'),
    path('result/', Results.as_view(), name='result'),
    path('resultdata/', ResultsData.as_view(), name='resultdata'),
    path('countries/', countries_dict),
    path('genders/', genders_dict),
    path('getfirstresulttime/', getfirstresulttime),
    path('user_cardioactivity/create/', CreateUserCardioactivity.as_view()),
    path('user_cardioactivity/<int:start_date>/<int:end_date>/', UserCardioactivity.as_view()),
    path('recomendations/', UserRecomendations.as_view()),
    path('image/', Image.as_view(), name='image'),
    path('disease/', DiseaseViews.as_view()),
    path('cardio_recomendations/', CardioRecomendations.as_view()),
    path('user_profile/', ProfileUser.as_view()),
    path('med_card/', MedCard.as_view()),
    path('info/', InformationView.as_view(), name='info'),
    path('login/', include('rest_social_auth.urls_jwt_pair')),
    path('login/', include('rest_social_auth.urls_session')),
]
