from django.urls import path
from . import views

app_name = 'pages'

urlpatterns = [
    path('', views.index, name='index'),
    path('privacy/', views.privacy, name='privacy'),
    path('terms/', views.terms, name='terms'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('application/', views.application, name='application'),
    path('antivirus/', views.antivirus, name='antivirus'),
    path('company-mission/', views.companyMission, name='company-mission'),
    path('investor-relations/', views.investorRelations, name='investor-relations'),
    path('doctor-relations/', views.doctorRelations, name='doctor-relations'),
    path('vacancies/', views.vacancies, name='vacancies'),
    path('support-research/', views.supportResearch, name='support-research'),
    path('articles/', views.articles, name='articles'),
    path('additional/', views.additional, name='additional'),
    path('articles/<slug:pubmed_id>/', views.article_detail, name='article_detail'),
    path('send-email/', views.send_email, name='send_email'),
]
