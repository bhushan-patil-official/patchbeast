from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView

from modules.platform.api.views import healthz, metrics

admin.site.site_header = "Patchbeast"
admin.site.site_title = "Patchbeast admin"

urlpatterns = [
    path("healthz", healthz, name="healthz"),
    path("metrics", metrics, name="metrics"),
    path("admin/", admin.site.urls),
    path("hooks/", include("modules.sources.api.hook_urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/v1/", include("patchbeast.api_v1")),
]
