"""
-*- coding: utf-8 -*-
 @Author: lee
 @ProjectName: material
 @Email: lijianqiao2906@live.com
 @FileName: import_export.py
 @DateTime: 2024/1/4 16:48
 @Docs: 用于数据导入导出-pandas
"""
from django.http import HttpResponse


class ExportAction:
    @staticmethod
    def export_as_excel(modeladmin, request, queryset, filename):
        # 调用ModelAdmin中定义的方法来获取要导出的DataFrame
        df = modeladmin.get_export_data(queryset)
        response = HttpResponse(content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        df.to_excel(response, index=False)
        return response
