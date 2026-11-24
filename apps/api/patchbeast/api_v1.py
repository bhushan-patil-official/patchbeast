"""Mounts each module's router under /api/v1/. Phase 2/3 modules add one line here."""

from django.urls import include, path

urlpatterns = [
    path("", include("modules.games.api.urls")),
    path("", include("modules.content.api.urls")),
    path("newsletter/", include("modules.newsletter.api.urls")),
    path("", include("modules.platform.api.urls")),
]
