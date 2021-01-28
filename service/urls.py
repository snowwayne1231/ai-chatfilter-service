"""service URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
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
from django.contrib import admin
from django.urls import path, include
from django.http import Http404, HttpResponse, JsonResponse
from django.views.static import serve
from service import instance
from .views import ServiceJSONDataAPIView, ServiceUploadAPIView, ServiceRemoveAPIView
import os


def read_model_path(request, name):
    main_service = instance.get_main_service(is_admin=True)
    if name == 'pinyin':
        _path = main_service.get_pinyin_model_path()
    elif name == 'grammar':
        _path = main_service.get_grammar_model_path()
    elif name == 'english':
        _path = main_service.get_english_model_path()
    else:
        raise Http404('Model Not Found.')

    if _path:
        return serve(request, os.path.basename(_path), os.path.dirname(_path))
    else:
        return Http404('Model Path Not Found.')


def read_data_path(request, name):
    main_service = instance.get_main_service(is_admin=True)
    result_data = None
    if name == 'vocabulary':
        result_data = main_service.get_vocabulary_data()
    elif name == 'modelversion':
        result_data = main_service.get_model_versions()

    if result_data:
        return JsonResponse(result_data, safe=False)
    else:
        raise Http404('Data Not Found.')




urlpatterns = [
    path('chat/', include('chat.urls')),
    path('admin/', admin.site.urls),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
    path('api/model/<slug:name>', read_model_path),
    path('api/data/<slug:name>', read_data_path),
    path('api/jsondata/<slug:name>', ServiceJSONDataAPIView.as_view()),
    path('api/upload/<slug:name>', ServiceUploadAPIView.as_view()),
    path('api/remove/<slug:name>/<slug:id>', ServiceRemoveAPIView.as_view()),
    # path(r'^django-rq/', include('django_rq.urls')),
    path('ai/', include('ai.urls')),
]
