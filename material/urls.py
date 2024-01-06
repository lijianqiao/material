"""
-*- coding: utf-8 -*-
 @Author: lee
 @ProjectName: material
 @Email: lijianqiao2906@live.com
 @FileName: urls.py
 @DateTime: 2024/1/2 10:21
 @Docs: 总路由
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf.urls.static import static
from django.conf import settings
from django.shortcuts import redirect
from django.views.generic import RedirectView
from django.views.static import serve as static_serve

favicon_view = RedirectView.as_view(
    url='/static/admin/simpleui-x/img/favicon.ico', permanent=True)

urlpatterns = [
    path("admin/", admin.site.urls),
    path('mater/', include('mater.urls')),
    re_path(r'^media/(?P<path>.*)$', static_serve,
            {'document_root': settings.MEDIA_ROOT}, name='media'),
    re_path(r'favicon\.ico$', favicon_view),
    path('', lambda request: redirect('admin/', permanent=True)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
