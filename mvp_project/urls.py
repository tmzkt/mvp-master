"""mvp_project URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
# for laguage switcher
from django.conf.urls.i18n import i18n_patterns

from rest_framework.documentation import include_docs_urls
from rest_framework_swagger.views import get_swagger_view

from api.views import ResultCreateView
from .yasg import urlpatterns as doc_urls

API_TITLE = 'InTime Digital API'
API_DESCRIPTION = 'A Web API for In Time Digital Biotech Corp. services.'


urlpatterns_swagger = [
    path('api/v1/', include('api.urls', namespace='v1')),
    path('api/v2/', include('api.urls', namespace='v2')),
]

schema_view = get_swagger_view(title=API_TITLE, patterns=urlpatterns_swagger)

urlpatterns = urlpatterns_swagger + [
    # without localization
    path('api/docs/', schema_view),
    path('api/schema/', include_docs_urls(title=API_TITLE, description=API_DESCRIPTION)),
    path('i18n/', include('django.conf.urls.i18n')),  # переключатель языка
    path('admin/', admin.site.urls),
    path('api-auth/', include('rest_framework.urls')),
    path('api/v1/set_result/', ResultCreateView.as_view()),
    path('social-auth/', include('social_django.urls', namespace='social')),
]

urlpatterns += doc_urls

urlpatterns += i18n_patterns(
    # User management
    path('', include('landing.urls', namespace='landing')),
    path('account/', include('users.urls')),
    # path('social-auth/', include('social_django.urls', namespace='social')),
    # Local apps
    path('shop/', include('shop.urls', namespace='shop')),
    path('web/', include('pages.urls', namespace='pages')), #старый роут смотрел на корень ''
    path('web/', include('cms.urls', namespace='cms')), #старый роут смотрел на корень ''
    path('publication/', include('publication.urls', namespace='publication')),
)


# if settings.DEBUG:
#     urlpatterns += [
#         path('__debug__/', include(debug_toolbar.urls)),
#     ]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
