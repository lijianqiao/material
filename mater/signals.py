"""
-*- coding: utf-8 -*-
 @Author: lee
 @ProjectName: material
 @Email: lijianqiao2906@live.com
 @FileName: signals.py
 @DateTime: 2024/1/3 13:19
 @Docs:  处理库存存量及日志查询
"""
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import (AuditLog, MaterialRequestModel, DepartmentMaterialStock, BaseModel, DepartmentModel,
                     UserDepartment, MaterialTypeModel, MaterialModel, MaterialAdminModel, MaterialRequestItem,
                     DeviceType, DepartmentDevice, EnvironmentalEquipmentLog)


@receiver(post_save, sender=MaterialRequestModel)
def update_stock(sender, instance, created, **kwargs):
    """
    物料申请保存后的信号处理器。
    作用：在物料申请状态变为 'passed' 时，扣减相应物料的库存。
    参数：
        sender - 发送信号的模型类。
        instance - 被保存的物料申请实例。
        created - 指示实例是否为新创建。
    """
    if instance.approval_status == 'passed':
        # 检查审批状态是否有变更
        if created or (getattr(instance, '_MaterialRequestModel__original_approval_status', None) != 'passed'):
            for item in instance.materialrequestitem_set.all():
                # 需要确保 material 字段是 DepartmentMaterialStock 的实例
                department_stock = DepartmentMaterialStock.objects.get(department=instance.department,
                                                                       material=item.material.material)
                if item.quantity > department_stock.quantity:
                    raise ValueError(f"无法扣减库存，因为物料 {item.material.material.code} 的存量不足")
                department_stock.quantity -= item.quantity
                department_stock.save()


@receiver(post_save, sender=BaseModel)
@receiver(post_save, sender=DepartmentModel)
@receiver(post_save, sender=UserDepartment)
@receiver(post_save, sender=MaterialTypeModel)
@receiver(post_save, sender=MaterialModel)
@receiver(post_save, sender=DepartmentMaterialStock)
@receiver(post_save, sender=MaterialAdminModel)
@receiver(post_save, sender=MaterialRequestModel)
@receiver(post_save, sender=MaterialRequestItem)
@receiver(post_save, sender=DeviceType)
@receiver(post_save, sender=DepartmentDevice)
@receiver(post_save, sender=EnvironmentalEquipmentLog)
def audit_log_save_update(sender, instance, created, **kwargs):
    action = 'Created' if created else 'Updated'
    content_type = ContentType.objects.get_for_model(instance)
    # 检查是否存在 'creator' 属性
    user = instance.creator if hasattr(instance, 'creator') else None

    # 如果存在用户，则创建日志
    if user:
        AuditLog.objects.create(
            user=user,
            action=action,
            content=f"{content_type} id {instance.id} was {action}"
        )


@receiver(post_delete, sender=BaseModel)
@receiver(post_delete, sender=DepartmentModel)
@receiver(post_delete, sender=UserDepartment)
@receiver(post_delete, sender=MaterialTypeModel)
@receiver(post_delete, sender=MaterialModel)
@receiver(post_delete, sender=DepartmentMaterialStock)
@receiver(post_delete, sender=MaterialAdminModel)
@receiver(post_delete, sender=MaterialRequestModel)
@receiver(post_delete, sender=MaterialRequestItem)
@receiver(post_delete, sender=DeviceType)
@receiver(post_delete, sender=DepartmentDevice)
@receiver(post_delete, sender=EnvironmentalEquipmentLog)
def audit_log_delete(sender, instance, **kwargs):
    content_type = ContentType.objects.get_for_model(instance)
    # 检查是否存在 'creator' 属性
    user = instance.creator if hasattr(instance, 'creator') else None

    # 如果存在用户，则创建日志
    if user:
        AuditLog.objects.create(
            user=user,
            action='Deleted',
            content=f"{content_type} id {instance.id} was Deleted"
        )
