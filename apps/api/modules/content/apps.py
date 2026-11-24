from django.apps import AppConfig


class ContentConfig(AppConfig):
    name = "modules.content"
    label = "content"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self) -> None:
        from . import signals  # noqa: F401  (registers receivers)
