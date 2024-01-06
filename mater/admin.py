import pandas as pd
from django import forms
from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.admin import DateFieldListFilter, SimpleListFilter
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.db.models import F
from import_export.admin import ImportExportModelAdmin
from pub.resources import (DepartmentMaterStockResource, MaterialTypeResource,
                           MaterialResource, EnvironmentalEquipmentResource)
from .models import (BaseModel, DepartmentModel, MaterialTypeModel, MaterialModel, UserDepartment,
                     MaterialAdminModel, MaterialRequestModel, MaterialRequestItem, DepartmentMaterialStock, DeviceType,
                     EnvironmentalEquipmentLog, DepartmentDevice, AuditLog)
from pub.import_export import ExportAction


class UserChoiceField(forms.ModelChoiceField):
    """
    获取用户的完整姓名
    """

    def label_from_instance(self, obj):
        # 返回想要显示的格式
        return f"{obj.username}-{obj.last_name}{obj.first_name}"


class BaseAdmin(admin.ModelAdmin):
    """
    基础管理员界面。
    作用：提供通用的管理员界面配置，包括列表过滤器、只读字段和分页设置。
    """
    list_filter = (('created_at', DateFieldListFilter),)
    readonly_fields = ['creator', 'created_at']
    list_per_page = 20  # 设置每页显示20条记录

    def save_model(self, request, obj, form, change):
        if not obj.pk:  # 检查是否为新创建的对象
            obj.creator = request.user  # 设置创建人
        super().save_model(request, obj, form, change)

    def creator_name(self, obj):
        return f"{obj.creator.last_name}{obj.creator.first_name}"

    creator_name.short_description = '创建人'


class CreatorNameFilter(admin.SimpleListFilter):
    title = '创建人'  # 过滤器的标题
    parameter_name = 'creator'  # 过滤器用于URL查询的参数名

    def lookups(self, request, model_admin):
        # 返回过滤选项列表
        creators = set([c.creator for c in model_admin.model.objects.all()])
        return [(c.id, f"{c.last_name}{c.first_name}") for c in creators]

    def queryset(self, request, queryset):
        # 返回过滤后的queryset
        if self.value():
            return queryset.filter(creator__id__exact=self.value())
        return queryset


@admin.register(BaseModel)
class BaseModelAdmin(BaseAdmin):
    """
    基地模型的管理员界面。
    作用：自定义基地模型在管理员界面中的显示，包括展示字段、搜索字段等。
    """
    list_display = ['name', 'creator_name', 'created_at']
    search_fields = ['name']


@admin.register(DepartmentModel)
class DepartmentModelAdmin(BaseAdmin):
    """
    部门模型的管理员界面。
    作用：自定义部门模型在管理员界面中的显示，包括展示字段、搜索字段和列表过滤器。
    """
    list_display = ['name', 'base', 'creator_name', 'created_at']
    search_fields = ['name', 'base__name']
    list_filter = ['base']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('base')


@admin.register(UserDepartment)
class UserDepartmentAdmin(admin.ModelAdmin):
    """
    用户部门关系管理员界面。
    作用：管理用户与部门之间的关系。
    字段：
        user - 关联的用户。
        department - 用户所属的部门。
    """
    list_display = ['user', 'department']
    search_fields = ['user__username', 'department__name']
    list_filter = ['department']


@admin.register(MaterialTypeModel)
class MaterialTypeModelAdmin(BaseAdmin, ImportExportModelAdmin):
    """
    物料类型模型的管理员界面。
    作用：自定义物料类型模型在管理员界面中的显示，包括展示字段和搜索字段。
    """
    resource_class = MaterialTypeResource
    list_display = ['name', 'creator_name', 'created_at', 'notes']
    search_fields = ['name']


@admin.register(MaterialModel)
class MaterialModelAdmin(BaseAdmin, ImportExportModelAdmin):
    """
    物料模型的管理员界面。
    作用：自定义物料模型在管理员界面中的显示，包括展示字段、搜索字段和列表过滤器。
    特别之处：包含自定义的搜索结果处理逻辑，以及物料图片预览功能。
    """
    resource_class = MaterialResource
    list_display = ['code', 'material_type', 'model', 'unit', 'creator_name', 'created_at']
    search_fields = ['code', 'model', 'material_type__name']
    list_filter = ('material_type__name', 'model', CreatorNameFilter, ('created_at', DateFieldListFilter),)
    readonly_fields = ['qr_code_preview', 'creator', 'created_at']

    def qr_code_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="150" id="image" />', obj.image.url)
        return "物料图片未上传"

    qr_code_preview.short_description = "物料图片预览"

    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)
        if search_term:
            queryset |= self.model.objects.filter(
                Q(code__icontains=search_term) |
                Q(model__icontains=search_term)
            )
        return queryset, use_distinct


class InventoryStatusFilter(SimpleListFilter):
    title = _('库存状态')
    parameter_name = 'inventory_status'

    def lookups(self, request, model_admin):
        return (
            ('warning', _('库存预警')),
            ('normal', _('库存正常')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'warning':
            return queryset.filter(quantity__lt=F('quantity_safety'))
        if self.value() == 'normal':
            return queryset.filter(quantity__gte=F('quantity_safety'))


class DepartmentMaterialStockForm(forms.ModelForm):
    """
    部门物料存量模型的自定义界面。
    作用：自定义部门物料存量模型在管理员界面中的显示，包括展示字段、搜索字段和列表过滤器。
    特别之处：包含自定义表单，用于验证存量不为负数。
    """

    class Meta:
        model = DepartmentMaterialStock
        fields = '__all__'

    def clean_quantity(self):
        quantity = self.cleaned_data['quantity']
        if quantity < 0:
            raise ValidationError('库存不能小于0。')

        return quantity

    def clean_quantity_safety(self):
        quantity_safety = self.cleaned_data['quantity_safety']
        if quantity_safety < 0:
            raise ValidationError('库存预警不能小于0。')
        return quantity_safety


@admin.register(DepartmentMaterialStock)
class DepartmentMaterialStockAdmin(BaseAdmin, ImportExportModelAdmin):
    """
    部门物料存量模型的管理员界面。
    作用：自定义部门物料存量模型在管理员界面中的显示，包括展示字段、搜索字段和列表过滤器。
    特别之处：包含自定义表单，用于验证存量不为负数。
    """
    resource_class = DepartmentMaterStockResource
    form = DepartmentMaterialStockForm
    list_display = ['department', 'material', 'quantity', 'quantity_safety', 'creator_name', 'created_at']
    search_fields = ['department__name', 'material__model']
    list_filter = ('department__name', 'material__model', CreatorNameFilter,
                   ('created_at', DateFieldListFilter), InventoryStatusFilter)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs  # 超级用户可以看到所有记录
        # 获取当前用户所属的部门
        user_department = UserDepartment.objects.filter(user=request.user).first()
        if user_department:
            # 过滤当前用户所属部门的库存
            return qs.filter(department=user_department.department)
        else:
            # 如果用户没有关联的部门，不显示任何记录
            return qs.none()


@admin.register(MaterialAdminModel)
class MaterialAdminModelAdmin(BaseAdmin):
    """
    物料管理员模型的管理员界面。
    作用：自定义物料管理员模型在管理员界面中的显示，包括展示字段、搜索字段和列表过滤器。
    特别之处：包含自定义的外键字段处理逻辑。
    """
    list_display = ['base', 'department', 'user', 'creator_name', 'created_at']
    search_fields = ['base__name', 'department__name', 'user__username']
    list_filter = ['base', 'department', CreatorNameFilter, ('created_at', DateFieldListFilter), ]

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "user":
            # 使用自定义的字段类
            field = UserChoiceField(queryset=User.objects.all(), label=db_field.verbose_name)
            return field
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('base', 'department')


class MaterialRequestItemInlineFormset(forms.BaseInlineFormSet):
    """
    物料申请项内联表单集。
    作用：用于物料申请模型内部，管理物料申请的具体物品项。
    特别之处：包括自定义的数据验证，确保申请的数量不超过库存。
    """

    def clean(self):
        super().clean()
        for form in self.forms:
            if not form.is_valid():
                return  # 其他验证错误已经存在

            if form.cleaned_data and not form.cleaned_data.get('DELETE'):
                quantity = form.cleaned_data.get('quantity')
                department_stock = form.cleaned_data.get('material')
                department = form.instance.request.department

                # 确保物料和部门是指定的
                if department_stock and department:
                    if quantity > department_stock.quantity:
                        form.add_error('quantity', f"存量不足，申请的数量不能超过 {department_stock.quantity} 个。")


class MaterialRequestItemInline(admin.TabularInline):
    """
    物料申请项的内联管理员界面。
    作用：在物料申请模型的管理员界面内内联显示物料申请项。
    特别之处：包含权限控制，根据物料申请的审批状态来确定是否允许添加或删除申请项。
    """
    model = MaterialRequestItem
    formset = MaterialRequestItemInlineFormset
    autocomplete_fields = ['material']  # 启用搜索框
    extra = 1

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.approval_status in ['passed', 'nopass']:
            return [f.name for f in self.model._meta.fields]  # 所有字段只读
        return super().get_readonly_fields(request, obj)

    def has_add_permission(self, request, obj=None):
        if obj and obj.approval_status in ['passed', 'nopass']:
            return False  # 禁止添加新项
        return super().has_add_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj and obj.approval_status in ['passed', 'nopass']:
            return False  # 禁止删除项
        return super().has_delete_permission(request, obj)


@admin.register(MaterialRequestModel)
class MaterialRequestModelAdmin(BaseAdmin):
    """
    物料申请模型的管理员界面。
    作用：自定义物料申请模型在管理员界面中的显示，包括展示字段、搜索字段和列表过滤器。
    特别之处：包含物料申请项的内联展示和自定义的申请物料信息显示。
    """
    list_display = ['request_number', 'department', 'applicant', 'items_info', 'approval_status', 'created_at']
    search_fields = ['request_number', 'base__name', 'department__name']
    list_filter = ['approval_status', 'base', 'department', 'applicant', ('created_at', DateFieldListFilter), ]
    readonly_fields = ['request_number', 'creator', 'created_at']
    inlines = [MaterialRequestItemInline]

    def items_info(self, obj):
        items = obj.materialrequestitem_set.all()[:1]  # 获取第一个item
        if items:
            return ", ".join([
                f"物料型号：{item.material.material.code}-{item.material.material.model}；"
                f"申请数量：{item.quantity}{item.material.material.unit}"
                for item in items
            ])
        return "无申请项"

    items_info.short_description = '申请物料信息'

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "applicant":
            # 使用自定义的字段类
            field = UserChoiceField(queryset=User.objects.all(), label=db_field.verbose_name)
            return field
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs  # 超级用户可以看到所有记录

        # 获取用户所属的部门
        try:
            user_department = UserDepartment.objects.get(user=request.user).department
        except UserDepartment.DoesNotExist:
            user_department = None

        # 如果用户有关联的部门，则只显示该部门的申请
        if user_department:
            return qs.filter(department=user_department)

        # 如果用户没有关联的部门，不显示任何申请
        return qs.none()

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if 'base' in form.base_fields:
            # 自动设置申请基地和申请部门
            user_department = UserDepartment.objects.filter(user=request.user).first()
            if user_department:
                # 根据字段名称调整
                form.base_fields['base'].queryset = BaseModel.objects.filter(id=user_department.department.base_id)
                form.base_fields['base'].initial = user_department.department.base_id
                form.base_fields['department'].queryset = DepartmentModel.objects.filter(
                    id=user_department.department_id)
                form.base_fields['department'].initial = user_department.department_id

                # 限制审批人选项为当前部门的物料管理员
                form.base_fields['approver'].queryset = MaterialAdminModel.objects.filter(
                    department=user_department.department)

        return form

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super().get_readonly_fields(request, obj)
        if obj is None:  # 如果是添加操作
            return readonly_fields + ['approval_status']
        if not request.user.is_superuser and not MaterialAdminModel.objects.filter(user=request.user).exists():
            # 如果用户不是超级管理员且不是物料管理员
            return readonly_fields + ['approval_status']
        return readonly_fields

    # 增加自定义按钮
    actions = ['export_material_requests', 'rose']

    def export_material_requests(self, request, queryset):
        filename = "material_requests.xlsx"
        return ExportAction.export_as_excel(self, request, queryset, filename)

    export_material_requests.short_description = "  物料申请导出"
    export_material_requests.icon = 'fa-solid fa-sheet-plastic'
    export_material_requests.type = 'success'

    def get_export_data(self, queryset):
        # 创建空的DataFrame
        df = pd.DataFrame()

        # 遍历queryset，提取每个物料申请及其关联的物料项
        for obj in queryset:
            for item in obj.materialrequestitem_set.all():
                row = {
                    '申请单号': obj.request_number,
                    '基地': obj.base.name if obj.base else '',
                    '部门': obj.department.name if obj.department else '',
                    '审批人': obj.approver.user.username if obj.approver else '',
                    '审批状态': obj.get_approval_status_display(),
                    '物料': item.material.model if item.material else '',
                    '数量': item.quantity,
                    '创建人': obj.creator.username if obj.creator else '',
                    '备注': obj.notes,
                }
                # 使用pd.Series来添加行以避免_append错误
                df = df._append(pd.Series(row), ignore_index=True)

        return df

    def rose(self):
        pass

    rose.short_description = "  物料申请图表"
    rose.icon = "fa-regular fa-image"
    rose.type = "warning"
    rose.action_type = 1
    rose.action_url = '/mater/rose_chart_view/'


@admin.register(DeviceType)
class DeviceTypeAdmin(BaseAdmin):
    """
    设备类型管理员界面。
    作用：管理和展示设备类型信息。
    字段：
        name - 设备名称。
        model - 设备型号。
        creator - 创建记录的用户。
        created_at - 记录创建时间。
        notes - 设备类型的备注信息。
    """
    list_display = ('name', 'model', 'creator_name', 'created_at', 'notes')
    search_fields = ('name', 'model')

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.creator = request.user
        super().save_model(request, obj, form, change)


@admin.register(DepartmentDevice)
class DepartmentDeviceAdmin(BaseAdmin):
    """
    部门设备管理员界面。
    作用：管理部门内的设备信息。
    字段：
        device_name - 设备名称。
        department - 设备所属部门。
        alias - 设备别名。
        location - 设备位置。
        device_status - 设备状态。
        notes - 设备备注信息。
        creator - 创建记录的用户。
        created_at - 记录创建时间。
    """
    list_display = ('device_name', 'department', 'alias', 'location', 'device_status', 'creator_name')
    search_fields = ('department', 'alias',)
    list_filter = ('department', 'device_status', ('created_at', DateFieldListFilter),)


@admin.register(EnvironmentalEquipmentLog)
class EnvironmentalEquipmentLogAdmin(BaseAdmin, ImportExportModelAdmin):
    """
    环保设备日志管理员界面。
    作用：管理环保设备运行日志。
    字段：
        device_type - 设备型号。
        department - 设备所属部门。
        operator - 操作员。
        start_time - 开机时间。
        stop_time - 停机时间。
        operation_status - 运行状态。
        abnormal_condition - 异常情况。
        consumable_name - 易耗件名称。
        consumable_replacement_time - 易耗件更换时间。
        notes - 备注信息。
        creator - 创建记录的用户。
        created_at - 记录创建时间。
    """
    resource_class = EnvironmentalEquipmentResource
    list_display = ('device_type', 'department', 'operator', 'start_time', 'stop_time',
                    'operation_status', 'abnormal_condition', 'creator_name', 'created_at', 'notes')
    list_filter = ('operation_status', 'department', 'device_type', ('created_at', DateFieldListFilter),)
    search_fields = ('operator', 'department__name', 'device_type__name')

    fieldsets = (
        (_('主要信息'), {
            'fields': ('device_type', 'department', 'operator', 'start_time', 'stop_time')
        }),
        (_('运行信息'), {
            'fields': ('operation_status', 'abnormal_condition')
        }),
        (_('易耗件信息'), {
            'fields': ('consumable_name', 'consumable_replacement_time')
        }),
        (_('其他信息'), {
            'fields': ('notes', 'creator', 'created_at')
        }),
    )

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.creator = request.user
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # 假设你有一个方法来获取当前用户的部门，这里我们使用DepartmentModel作为示例
        user_department = DepartmentModel.objects.filter(materialadminmodel__user=request.user).first()
        if user_department:
            # 如果用户属于某个部门，只显示该部门的记录
            return qs.filter(department=user_department)
        else:
            # 如果用户不属于任何部门或者没有被分配部门，不显示任何记录
            return qs.none()


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """
    审计日志管理员界面。
    作用：显示用户在平台上进行的所有操作的日志。
    字段：
        user - 执行操作的用户。
        action - 执行的操作类型，如创建、更新或删除。
        timestamp - 操作发生的时间。
        content - 操作的具体内容。
    """
    list_display = ('user', 'action', 'timestamp', 'content')
    search_fields = ['user__username', 'action']
    list_filter = ['action', ('timestamp', DateFieldListFilter)]
    readonly_fields = ['user', 'action', 'timestamp', 'content']

    def has_add_permission(self, request):
        # 禁止通过admin添加新的日志记录
        return False

    def has_change_permission(self, request, obj=None):
        # 禁止修改日志记录
        return False

    def has_delete_permission(self, request, obj=None):
        # 禁止删除日志记录
        return False


admin.site.site_header = '成都物料管理平台'
admin.site.site_title = '成都物料管理平台'
admin.site.index_title = '成都物料管理平台'
