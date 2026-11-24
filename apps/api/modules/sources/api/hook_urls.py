from django.urls import path

from .hook_views import websub_callback

urlpatterns = [path("websub/<int:source_id>/", websub_callback, name="websub-callback")]
