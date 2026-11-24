from pathlib import Path

import httpx
import pytest
from django.core.cache import cache

from modules.games.models import Game
from modules.sources.models import Source

FIX = Path(__file__).parent / "fixtures"


@pytest.fixture(autouse=True)
def _clean_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def fixture_text():
    return lambda name: (FIX / name).read_text()


@pytest.fixture
def game(db):
    return Game.objects.create(slug="test-game", name="Test Game", hub_config={"faq": []})


@pytest.fixture
def source(game):
    return Source.objects.create(game=game, name="Example Newsroom", type="rss", url="https://news.example.com/feed.xml", official_feed=True)


@pytest.fixture
def user(db, django_user_model):
    return django_user_model.objects.create_superuser("admin", "a@example.com", "pw")


def make_client(handler) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler), follow_redirects=True)
