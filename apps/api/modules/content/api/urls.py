from django.urls import path

from . import views

urlpatterns = [
    path("games/", views.games_list),
    path("games/<slug:slug>/", views.game_hub),
    path("games/<slug:slug>/patches/", views.game_patches),
    path("games/<slug:slug>/patches/<slug:platform>/<str:version>/", views.patch_detail),
    path("games/<slug:slug>/videos/", views.game_videos),
    path("games/<slug:slug>/changes/", views.GameChangesList.as_view()),
    path("games/<slug:slug>/requirements/", views.game_requirements),
    path("ticker/", views.ticker),
    path("news/", views.NewsList.as_view()),
    path("feed/", views.FeedList.as_view()),
    path("sitemap/", views.sitemap),
]
