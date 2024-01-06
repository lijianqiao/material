from django.http import HttpResponse
from .models import MaterialRequestModel, MaterialRequestItem, DepartmentModel
from pyecharts import options as opts
from pyecharts.charts import Pie, Page


def rose_chart_view(request):
    page = Page()
    user = request.user
    is_superuser = user.is_superuser

    # 根据用户角色筛选部门
    if is_superuser:
        departments = DepartmentModel.objects.all()
    else:
        departments = DepartmentModel.objects.filter(materialadminmodel__user=user)

    for department in departments:
        # 获取每个部门的物料申请数据
        requests = MaterialRequestModel.objects.filter(department=department)
        material_counts = {}
        total_materials = 0  # 用于计算申请总数
        for req in requests:
            for item in MaterialRequestItem.objects.filter(request=req):
                material_name = item.material.material.model  # 按物料型号分类
                quantity = item.quantity
                material_counts[material_name] = material_counts.get(material_name, 0) + quantity
                total_materials += quantity  # 累加申请总数

        # # 如果部门没有物料申请，跳过这个部门
        # if not material_counts:
        #     continue

        # 准备图表数据
        if material_counts:
            categories = list(material_counts.keys())
            values = list(material_counts.values())
            c = (
                Pie()
                .add(
                    "",
                    [list(z) for z in zip(categories, values)],
                    radius=["30%", "75%"],
                    center=["50%", "50%"],
                    rosetype="radius",
                )
                .set_global_opts(
                    title_opts=opts.TitleOpts(title=f"{department.name} 物料申请总数：{total_materials}"),
                    toolbox_opts=opts.ToolboxOpts(is_show=True),
                    legend_opts=opts.LegendOpts(orient="vertical", pos_top="15%", pos_left="80%"),
                )
            )
        else:
            c = (
                Pie()
                .set_global_opts(
                    title_opts=opts.TitleOpts(title=f"{department.name} 物料申请总数：无数据")
                )
            )

        page.add(c)

    return HttpResponse(page.render_embed())
