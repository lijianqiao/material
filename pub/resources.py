"""
-*- coding: utf-8 -*-
 @Author: lee
 @ProjectName: material
 @Email: lijianqiao2906@live.com
 @FileName: resources.py
 @DateTime: 2024/1/3 17:33
 @Docs:  文件导入导出
"""
import re

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from import_export.widgets import ForeignKeyWidget

from import_export import resources, fields, widgets
from mater.models import (DepartmentMaterialStock, MaterialTypeModel, DepartmentModel, MaterialModel,
                          EnvironmentalEquipmentLog, DeviceType)


def validate_creator(creator_username, row_number):
    if not User.objects.filter(username=creator_username).exists():
        return f"行{row_number + 1}: 创建人{creator_username}没找到，是不是选错创建人了？如果没有，请联系系统管理员。"
    return None


def validate_material_type_exists(material_type_name, row_number):
    if not MaterialTypeModel.objects.filter(name=material_type_name).exists():
        return f"行{row_number + 1}: 物料类型 '{material_type_name}' 不存在，请先创建这个物料类型。"
    return None


def validate_material_model(material_model, row_number):
    if not re.match(r'^[\w-]+[-\s\w\d]+$', material_model):
        return f"行{row_number + 1}: 物料型号'{material_model}'错误，正确的格式是[物料编码-物料型号]."
    return None


def validate_quantity_fields(quantity, quantity_safety, row_number):
    try:
        quantity = int(quantity)
        quantity_safety = int(quantity_safety)
        if quantity < 0 or quantity_safety < 0:
            return f"行{row_number + 1}: 库存数: {quantity} 和库存预警: {quantity_safety} 必须为大于或等于0的整数。"
    except ValueError:
        return f"行{row_number + 1}: 库存数: {quantity} 和库存预警: {quantity_safety} 必须为大于或等于0的整数。"
    return None


def validate_unit_is_not_numeric(unit, row_number):
    if any(char.isdigit() for char in unit):
        return f"行{row_number + 1}: 单位 '{unit}' 不能包含数字。"
    return None


def validate_code_model_combination(code_model_combinations, code, model, row_number):
    combination = f"{code}-{model}"
    if combination in code_model_combinations:
        return f"行{row_number + 1}: 物料编码 '{code}' 和物料型号 '{model}' 的组合在文件中重复。"
    else:
        code_model_combinations.add(combination)
    return None


class MaterialWidget(widgets.ForeignKeyWidget):
    def clean(self, value, row=None, **kwargs):
        # 用 "-" 分割 code 和 model
        parts = value.split('-')
        if len(parts) < 2:
            raise ValidationError(f"物料型号'{value}'错误，正确的格式是[物料编码-物料型号].")
        code, model = parts[0], '-'.join(parts[1:])  # 重新组合剩余部分以支持型号中的连字符
        try:
            return self.model.objects.get(code=code, model=model)
        except self.model.DoesNotExist:
            raise ValidationError(f"物料编码和型号的组合'{value}'在系统中不存在，请检查是否正确。")

    def render(self, value, obj=None):
        # 假设 value 是 MaterialModel 的实例
        if value:
            return f"{value.code}-{value.model}"
        return ""


class UserForeignKeyWidget(widgets.ForeignKeyWidget):
    def clean(self, value, row=None, **kwargs):
        if value:
            try:
                return super().clean(value, row=row)
            except User.DoesNotExist:
                raise ValidationError(f"创建人{value}没找到，是不是选错创建人了？如果没有，请联系系统管理员。")
        else:
            return None


class DepartmentMaterStockResource(resources.ModelResource):
    department = fields.Field(
        column_name='部门',
        attribute='department',
        widget=ForeignKeyWidget(DepartmentModel, 'name')
    )
    material = fields.Field(
        column_name='物料型号',
        attribute='material',
        widget=MaterialWidget(MaterialModel, 'model')
    )
    quantity = fields.Field(
        column_name='库存数',
        attribute='quantity',
    )
    quantity_safety = fields.Field(
        column_name='库存预警',
        attribute='quantity_safety',
    )
    creator = fields.Field(
        column_name='创建人(写工号,不能写名字)',
        attribute='creator',
        widget=UserForeignKeyWidget(User, 'username')
    )

    def before_import(self, dataset, using_transactions, dry_run, **kwargs):
        error_messages = []
        seen_combinations = set()
        duplicate_rows = []

        for i, row in enumerate(dataset.dict, start=1):
            department = row['部门']
            material = row['物料型号']
            if (department, material) in seen_combinations:
                duplicate_rows.append(i)
            else:
                seen_combinations.add((department, material))

            # 调用验证函数
            error_msg = validate_material_model(material, i)
            if error_msg:
                error_messages.append(error_msg)

            error_msg = validate_quantity_fields(row.get('库存数', 0), row.get('库存预警', 0), i)
            if error_msg:
                error_messages.append(error_msg)

            error_msg = validate_creator(row.get('创建人(写工号,不能写名字)', '').strip(), i)
            if error_msg:
                error_messages.append(error_msg)

        if duplicate_rows:
            error_messages.append(
                f"部门和物料型号重复，请检查上传的文件。重复的行: {', '.join(str(row) for row in duplicate_rows)}"
            )

        if error_messages:
            raise ValidationError(error_messages)

    class Meta:
        model = DepartmentMaterialStock
        exclude = ('id', 'created_at',)
        import_id_fields = ('department', 'material')


class MaterialTypeResource(resources.ModelResource):
    name = fields.Field(
        column_name='物料类型名称',
        attribute='name',
    )
    creator = fields.Field(
        column_name='创建人(写工号,不能写名字)',
        attribute='creator',
        widget=UserForeignKeyWidget(User, 'username')
    )
    notes = fields.Field(
        column_name='备注',
        attribute='notes',
    )

    def before_import(self, dataset, using_transactions, dry_run, **kwargs):
        error_messages = []

        for i, row in enumerate(dataset.dict, start=1):
            error_msg = validate_creator(row.get('创建人(写工号,不能写名字)', '').strip(), i)
            if error_msg:
                error_messages.append(error_msg)

        if error_messages:
            raise ValidationError(error_messages)

    class Meta:
        model = MaterialTypeModel
        exclude = ('id', 'created_at')
        import_id_fields = ('name',)


class MaterialResource(resources.ModelResource):
    material_type = fields.Field(
        column_name='物料类型',
        attribute='material_type',
        widget=ForeignKeyWidget(MaterialTypeModel, 'name'),
    )
    code = fields.Field(
        column_name='物料编码',
        attribute='code',
    )
    model = fields.Field(
        column_name='物料型号',
        attribute='model',
    )
    unit = fields.Field(
        column_name='单位',
        attribute='unit',
    )
    properties = fields.Field(
        column_name='产品特性',
        attribute='properties',
    )
    creator = fields.Field(
        column_name='创建人(写工号,不能写名字)',
        attribute='creator',
        widget=UserForeignKeyWidget(User, 'username')
    )
    notes = fields.Field(
        column_name='备注',
        attribute='notes',
    )

    def before_import(self, dataset, using_transactions, dry_run, **kwargs):
        error_messages = []
        code_model_combinations = set()

        for i, row in enumerate(dataset.dict, start=1):
            code = row.get('物料编码', '').strip()
            model = row.get('物料型号', '').strip()
            material_type_name = row.get('物料类型', '').strip()
            unit = row.get('单位', '').strip()

            error_msg = validate_code_model_combination(code_model_combinations, code, model, i)
            if error_msg:
                error_messages.append(error_msg)

            error_msg = validate_material_type_exists(material_type_name, i)
            if error_msg:
                error_messages.append(error_msg)

            error_msg = validate_unit_is_not_numeric(unit, i)
            if error_msg:
                error_messages.append(error_msg)

            error_msg = validate_creator(row.get('创建人(写工号,不能写名字)', '').strip(), i)
            if error_msg:
                error_messages.append(error_msg)

        if error_messages:
            raise ValidationError(error_messages)

    class Meta:
        model = MaterialModel
        exclude = ('id', 'image', 'created_at')
        import_id_fields = ('code',)


class EnvironmentalEquipmentResource(resources.ModelResource):
    device_name = fields.Field(
        column_name='设备型号',
        attribute='device_name',
        widget=ForeignKeyWidget(DeviceType, 'device_name')
    )
    device_alias = fields.Field(
        column_name='设备别名',
        attribute='device_alias',
        widget=ForeignKeyWidget(DeviceType, 'alias')
    )
    department = fields.Field(
        column_name='部门',
        attribute='department',
        widget=ForeignKeyWidget(DepartmentModel, 'name')
    )
    operator = fields.Field(
        column_name='当班人员',
        attribute='operator',
    )
    start_time = fields.Field(
        column_name='开机时间',
        attribute='start_time',
    )
    stop_time = fields.Field(
        column_name='停机时间',
        attribute='stop_time',
    )
    operation_status = fields.Field(
        column_name='运行状态',
        attribute='operation_status',
    )
    abnormal_condition = fields.Field(
        column_name='异常情况',
        attribute='abnormal_condition',
    )
    consumable_name = fields.Field(
        column_name='易耗件名称',
        attribute='consumable_name',
    )
    consumable_replacement_time = fields.Field(
        column_name='易耗件更换时间',
        attribute='consumable_replacement_time',
    )
    notes = fields.Field(
        column_name='备注',
        attribute='notes',
    )
    creator = fields.Field(
        column_name='创建人(写工号,不能写名字)',
        attribute='creator',
        widget=UserForeignKeyWidget(User, 'username')
    )

    def before_import(self, dataset, using_transactions, dry_run, **kwargs):
        error_messages = []

        for i, row in enumerate(dataset.dict, start=1):
            error_msg = validate_creator(row.get('创建人(写工号,不能写名字)', '').strip(), i)
            if error_msg:
                error_messages.append(error_msg)

        if error_messages:
            raise ValidationError(error_messages)

    class Meta:
        model = EnvironmentalEquipmentLog
        exclude = ('id', 'created_at')
        export_order = ('device_name', 'device_alias', 'department', 'operator',
                        'start_time', 'stop_time', 'operation_status', 'abnormal_condition',
                        'consumable_name', 'consumable_replacement_time', 'notes', 'creator')

    def dehydrate_device_name(self, environmental_equipment_log):
        return environmental_equipment_log.device_type.device_name

    def dehydrate_device_alias(self, environmental_equipment_log):
        return environmental_equipment_log.device_type.alias

    def dehydrate_operation_status(self, environmental_equipment_log):
        # 检查operation_status字段的值并返回相应的中文描述
        status_display = dict(EnvironmentalEquipmentLog.STATUS_CHOICES)
        return status_display.get(environmental_equipment_log.operation_status,
                                  environmental_equipment_log.operation_status)
