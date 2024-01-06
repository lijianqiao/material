"""
-*- coding: utf-8 -*-
 @Author: lee
 @ProjectName: material
 @Email: lijianqiao2906@live.com
 @FileName: urls.py
 @DateTime: 2024/1/2 10:21
 @Docs: 物料路由
"""
from django.urls import path
from . import views

app_name = 'mater'

urlpatterns = [
    path('rose_chart_view/', views.rose_chart_view, name='rose_chart_view'),
]
