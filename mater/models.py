from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now


class BaseModel(models.Model):
    """
    基地模型。
    作用：表示一个基地，包含名称、创建人和创建时间。
    字段：
        name - 基地的名称。
        creator - 创建该基地的用户。
        created_at - 基地的创建时间。
    """
    name = models.CharField(max_length=100, verbose_name="基地名称", unique=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, editable=False, verbose_name="创建人")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        verbose_name = "基地"
        verbose_name_plural = "基地"

    def __str__(self):
        return self.name


class DepartmentModel(models.Model):
    """
    部门模型。
    作用：表示一个部门，包含名称、所属基地、创建人和创建时间。
    字段：
        name - 部门的名称。
        base - 部门所属的基地。
        creator - 创建该部门的用户。
        created_at - 部门的创建时间。
    """
    base = models.ForeignKey(BaseModel, on_delete=models.CASCADE, verbose_name="所属基地")
    name = models.CharField(max_length=100, verbose_name="部门名称")
    creator = models.ForeignKey(User, on_delete=models.CASCADE, editable=False, verbose_name="创建人")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        verbose_name = "部门"
        verbose_name_plural = "部门"

    def __str__(self):
        return self.name


class UserDepartment(models.Model):
    """
    用户部门模型。
    作用：表示特定用户和他们所属的部门。
    字段：
        user - 用户。
        department - 用户所属的部门。
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="用户")
    department = models.ForeignKey(DepartmentModel, on_delete=models.CASCADE, verbose_name="部门")

    class Meta:
        verbose_name = "用户部门"
        verbose_name_plural = "用户部门"

    def __str__(self):
        return f"{self.user.username} ({self.department.name})"


class MaterialTypeModel(models.Model):
    """
    物料类型模型。
    作用：物料类型，包含类型名称、单位、创建人、创建时间和备注。
    字段：
        name - 物料类型名称。
        creator - 创建该物料的用户。
        created_at - 物料的创建时间。
        notes - 物料的备注信息。
    """
    name = models.CharField(max_length=100, verbose_name="物料类型名称")
    creator = models.ForeignKey(User, on_delete=models.CASCADE, editable=False, verbose_name="创建人")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    notes = models.TextField(verbose_name="备注", blank=True, null=True)

    class Meta:
        verbose_name = "物料类型"
        verbose_name_plural = "物料类型"

    def __str__(self):
        return self.name


class MaterialModel(models.Model):
    """
    物料模型。
    作用：表示一个具体的物料，包含编码、型号、单位、创建人和创建时间。
    字段：
        code - 物料的编码。
        model - 物料的型号。
        unit - 物料的单位。
        creator - 创建该物料的用户。
        created_at - 物料的创建时间。
        notes - 物料的备注信息。
        image - 物料的图片。
    """
    material_type = models.ForeignKey(MaterialTypeModel, on_delete=models.CASCADE, verbose_name="物料类型")
    code = models.CharField(max_length=100, verbose_name="物料编码")
    model = models.CharField(max_length=100, verbose_name="物料型号")
    unit = models.CharField(max_length=50, verbose_name="单位")
    properties = models.TextField(blank=True, null=True, verbose_name="产品特性")
    creator = models.ForeignKey(User, on_delete=models.CASCADE, editable=False, verbose_name="创建人")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    notes = models.TextField(verbose_name="备注", blank=True, null=True)
    image = models.ImageField(upload_to='material/', blank=True, null=True, verbose_name="物料图片")

    class Meta:
        verbose_name = "物料"
        verbose_name_plural = "物料"

    def __str__(self):
        return f"{self.code}-{self.model}"


class DepartmentMaterialStock(models.Model):
    """
    部门物料存量模型。
    作用：表示部门内物料的存量，包括部门、物料、存量、创建人和创建时间。
    字段：
        department - 存量所属的部门。
        material - 存量对应的物料。
        quantity - 物料的存量。
        creator - 创建该存量记录的用户。
        created_at - 存量记录的创建时间。
    """
    department = models.ForeignKey(DepartmentModel, on_delete=models.CASCADE, verbose_name="部门")
    material = models.ForeignKey(MaterialModel, on_delete=models.CASCADE, verbose_name="物料")
    quantity = models.IntegerField(verbose_name="库存数")
    quantity_safety = models.IntegerField(verbose_name="库存预警", default=0)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, editable=False, null=True, verbose_name="创建人")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        verbose_name = "部门物料库存"
        verbose_name_plural = "部门物料库存"
        unique_together = ('department', 'material')  # 确保每个部门的每种物料只有一个存量记录

    def __str__(self):
        return f"{self.department.name} - {self.material} - 存量: {self.quantity}"


class MaterialAdminModel(models.Model):
    """
    物料管理员模型。
    作用：表示一个物料管理员，包含所管理的基地和部门、管理员用户、创建人和创建时间。
    字段：
        base - 管理员管理的基地。
        department - 管理员管理的部门。
        user - 管理员用户。
        creator - 创建该管理员记录的用户。
        created_at - 管理员记录的创建时间。
    """
    base = models.ForeignKey(BaseModel, on_delete=models.CASCADE, verbose_name="基地")
    department = models.ForeignKey(DepartmentModel, on_delete=models.CASCADE, verbose_name="部门")
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="物料管理员")
    creator = models.ForeignKey(User, related_name='material_admin_creator', on_delete=models.CASCADE,
                                editable=False, verbose_name="创建人")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        verbose_name = "物料管理员"
        verbose_name_plural = "物料管理员"

    def __str__(self):
        return f"{self.base.name} - {self.department.name} - {self.user.last_name}{self.user.first_name}"


class MaterialRequestModel(models.Model):
    """
    物料申请模型。
    作用：表示一个物料申请，包含申请基地、部门、审批人、审批状态、创建人和创建时间。
    字段：
        base - 申请的基地。
        department - 申请的部门。
        approver - 审批该申请的物料管理员。
        approval_status - 申请的审批状态。
        creator - 创建该申请的用户。
        created_at - 申请的创建时间。
        notes - 申请的备注信息。
    """
    APPROVAL_STATUS_CHOICES = (
        ('approving', '审批中'),
        ('nopass', '未通过'),
        ('passed', '已通过'),
    )
    request_number = models.CharField(max_length=20, unique=True, verbose_name="申请单号", blank=True)
    base = models.ForeignKey(BaseModel, on_delete=models.CASCADE, verbose_name="申请基地")
    department = models.ForeignKey(DepartmentModel, on_delete=models.CASCADE, verbose_name="申请部门")
    applicant = models.CharField(max_length=50, blank=False, null=True, verbose_name="申请人")
    approver = models.ForeignKey(MaterialAdminModel, on_delete=models.CASCADE, verbose_name="审批人")
    approval_status = models.CharField(max_length=50, choices=APPROVAL_STATUS_CHOICES,
                                       default='approving', verbose_name='审批状态')
    materials = models.ManyToManyField(DepartmentMaterialStock, through='MaterialRequestItem', verbose_name="申请物料")
    creator = models.ForeignKey(User, related_name='request_creator', on_delete=models.CASCADE,
                                editable=False, verbose_name="创建人")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    notes = models.TextField(verbose_name="备注", blank=True, null=True)

    __original_approval_status = None

    def __init__(self, *args, **kwargs):
        super(MaterialRequestModel, self).__init__(*args, **kwargs)
        self.__original_approval_status = self.approval_status

        # 当创建一个新实例时生成申请单号
        if not self.pk:  # 新实例的 self.pk（即id）应该为空
            self.request_number = self.generate_request_number()

    def generate_request_number(self):
        today = now().date()  # 获取当前日期
        prefix = 'WL' + today.strftime('%Y%m%d')  # 格式化日期
        last_request = MaterialRequestModel.objects.filter(
            request_number__startswith=prefix
        ).order_by('request_number').last()

        if last_request:
            last_number = int(last_request.request_number.split(prefix)[-1])  # 获取最后的编号数字
            new_number = prefix + "{:03}".format(last_number + 1)  # 编号加1
        else:
            new_number = prefix + '001'  # 如果今天还没有编号，就从001开始
        return new_number

    def save(self, *args, **kwargs):
        # 确保在保存之前记录原始状态和单号
        if not self.pk:  # 只有当对象是新创建的时候才赋予新的单号
            if not self.request_number:  # 如果单号还没有生成
                self.request_number = self.generate_request_number()
            self.__original_approval_status = self.approval_status
        super(MaterialRequestModel, self).save(*args, **kwargs)

    class Meta:
        verbose_name = "物料申请"
        verbose_name_plural = "物料申请"

    def __str__(self):
        department_name = self.department.name if self.department else "未知部门"
        creator_name = f"{self.creator.last_name}{self.creator.first_name}" if self.creator else "未知创建人"
        return f"{department_name}-{creator_name}"


class MaterialRequestItem(models.Model):
    """
    物料申请项模型。
    作用：表示物料申请中的一个具体项，包含申请、物料和申请数量。
    字段：
        request - 对应的物料申请。
        material - 申请的物料。
        quantity - 申请的数量。
    """
    request = models.ForeignKey(MaterialRequestModel, on_delete=models.CASCADE, verbose_name="物料申请")
    material = models.ForeignKey(DepartmentMaterialStock, on_delete=models.CASCADE, verbose_name="物料")
    quantity = models.IntegerField(verbose_name="申请数量")

    class Meta:
        verbose_name = "物料申请项"
        verbose_name_plural = "物料申请项"


class DeviceType(models.Model):
    """
    设备类型模型
    """
    name = models.CharField(max_length=255, verbose_name="设备名称")
    model = models.CharField(max_length=255, unique=True,verbose_name="设备型号")
    creator = models.ForeignKey(User, related_name='created_device_types', on_delete=models.CASCADE,
                                editable=False, verbose_name="创建人")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    notes = models.TextField(blank=True, null=True, verbose_name="备注")

    def __str__(self):
        return f"{self.name}-{self.model}"

    class Meta:
        verbose_name = "设备类型"
        verbose_name_plural = "设备类型"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)


class DepartmentDevice(models.Model):
    DEVICE_STATUS_CHOICES = (
        ('normal', '正常运行'),
        ('fault', '故障状态'),
        ('repair', '维修状态'),
        ('not_used', '闲置状态'),
        ('other', '其他状态'),
    )
    device_name = models.ForeignKey(DeviceType, related_name='department_device',
                                    on_delete=models.CASCADE, verbose_name="设备名")
    alias = models.CharField(max_length=50, blank=True, null=True, verbose_name="设备别名")
    department = models.ForeignKey(DepartmentModel, related_name='department_device',
                                   on_delete=models.CASCADE, verbose_name="部门")
    location = models.CharField(max_length=255, blank=True, null=True, verbose_name="设备位置")
    device_status = models.CharField(max_length=20, choices=DEVICE_STATUS_CHOICES,
                                     default='normal', verbose_name='设备状态')
    notes = models.TextField(blank=True, null=True, verbose_name="备注")
    creator = models.ForeignKey(User, related_name='created_department_device', on_delete=models.CASCADE,
                                editable=False, verbose_name="创建人")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    def __str__(self):
        return f"{self.department}-{self.device_name}-{self.alias}"

    class Meta:
        verbose_name = "设备与部门关系"
        verbose_name_plural = "设备与部门关系"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)


class EnvironmentalEquipmentLog(models.Model):
    STATUS_CHOICES = (
        ('normal', '正常'),
        ('abnormal', '异常'),
    )
    device_type = models.ForeignKey(DepartmentDevice, on_delete=models.CASCADE, verbose_name="设备型号")
    department = models.ForeignKey(DepartmentModel, on_delete=models.CASCADE, verbose_name="部门")
    operator = models.CharField(max_length=255, verbose_name="当班人员")
    start_time = models.DateTimeField(verbose_name="开机时间")
    stop_time = models.DateTimeField(verbose_name="停机时间")
    operation_status = models.CharField(max_length=10, choices=STATUS_CHOICES, verbose_name="运行状态")
    abnormal_condition = models.TextField(blank=True, null=True, verbose_name="异常情况")
    consumable_name = models.CharField(max_length=255, blank=True, null=True, verbose_name="易耗件名称")
    consumable_replacement_time = models.DateTimeField(blank=True, null=True, verbose_name="易耗件更换时间")
    notes = models.TextField(blank=True, null=True, verbose_name="备注")
    creator = models.ForeignKey(User, related_name='equipment_log_creator', on_delete=models.CASCADE,
                                editable=False, verbose_name="创建人")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        verbose_name = "环保设备运行台账"
        verbose_name_plural = "环保设备运行台账"

    def __str__(self):
        return f"{self.device_type.alias}-{self.operator}"

    def clean(self):
        # 如果运行状态为异常，则必须填写异常情况
        if self.operation_status == 'abnormal' and not self.abnormal_condition:
            raise ValidationError({'abnormal_condition': "运行状态为异常时，必须填写异常情况。"})
        # 如果停机时间早于开机时间，则报错
        if self.stop_time and self.start_time and self.stop_time < self.start_time:
            raise ValidationError({'stop_time': "停机时间不能早于开机时间。"})

    def save(self, *args, **kwargs):
        self.full_clean()  # 调用clean方法进行验证
        super().save(*args, **kwargs)


class AuditLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=64)
    timestamp = models.DateTimeField(auto_now_add=True)
    content = models.TextField()

    def __str__(self):
        return f"{self.user.username} - {self.action} - {self.timestamp}"

    class Meta:
        verbose_name = "AuditLog日志"
        verbose_name_plural = "AuditLog日志"
