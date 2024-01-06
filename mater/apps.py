from django.apps import AppConfig


class MaterConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "mater"
    verbose_name = "物料管理"

    def ready(self):
        import mater.signals
