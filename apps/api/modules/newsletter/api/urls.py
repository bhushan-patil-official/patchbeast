from django.urls import path

from . import views

urlpatterns = [
    path("subscribe/", views.subscribe),
    path("confirm/", views.confirm),
    path("unsubscribe/", views.unsubscribe),
]
