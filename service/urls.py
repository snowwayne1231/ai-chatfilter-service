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
from .views import ServiceAPIView
from service import instance
from django.http import FileResponse, HttpResponse

# main_service = instance.get_main_service(is_admin=True)

# def read_pinyin_file(request):
#     _file = main_service.get_pinyin_model_file()
#     print('_file: ', _file)
#     return HttpResponse(_file, content_type='application/octet-stream')


urlpatterns = [
    path('chat/', include('chat.urls')),
    path('admin/', admin.site.urls),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
    path('api/upload/', ServiceAPIView.as_view()),
    # path('api/model/pinyin', read_pinyin_file),
]
