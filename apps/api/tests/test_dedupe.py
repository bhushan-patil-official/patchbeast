import pytest

from modules.common.urlutils import normalise_url, registrable_domain
from modules.content.models import Article
from modules.ingest import services
from modules.sources.ports import RawItem


@pytest.mark.parametrize("a,b", [
    ("https://www.Example.com/a/b/?utm_source=x&b=2&a=1#frag", "http://example.com/a/b?a=1&b=2"),
    ("https://example.com/a/?fbclid=zzz", "https://example.com/a"),
    ("https://example.com:443/", "https://example.com/"),
])
def test_normalise_url_collapses_variants(a, b):
    assert normalise_url(a) == normalise_url(b)


def test_normalise_rejects_non_http():
    with pytest.raises(ValueError):
        normalise_url("javascript:alert(1)")


def test_registrable_domain():
    assert registrable_domain("https://www.news.example.co.uk/x") == "example.co.uk"
    assert registrable_domain("https://a.b.example.com") == "example.com"


def test_simhash_near_duplicates_close_and_different_far():
    a = services.simhash64("Studio delays PC version to March 2027 citing optimisation work and extra polish")
    b = services.simhash64("Studio delays PC version to March 2027, citing optimisation work and extra polish!")
    c = services.simhash64("Hotfix 1.0.3 fixes crash on startup for players with older graphics drivers installed")
    assert services.hamming(a, b) <= 3 < services.hamming(a, c)
    assert services.to_unsigned(services.to_signed(a)) == a


def item(url, title, lead="lead text about something happening with the game today"):
    return RawItem(title=title, url=url, lead=lead)


def test_exact_url_dedupe(source):
    s1 = services.ingest_items(source, [item("https://news.example.com/a?utm_source=x", "A thing happened to the game")], dispatch=False)
    s2 = services.ingest_items(source, [item("https://www.news.example.com/a/", "A thing happened to the game")], dispatch=False)
    assert (s1.new, s2.new, s2.exact_dup) == (1, 0, 1)


def test_near_duplicate_same_outlet_skipped_other_outlet_kept_as_corroboration(source):
    t = "Studio delays PC version to March 2027 citing optimisation work"
    lead = "The studio said the extra time is needed for optimisation and polish on the PC edition"
    ingest = lambda u: services.ingest_items(source, [item(u, t, lead)], dispatch=False)
    assert ingest("https://news.example.com/1").new == 1
    assert ingest("https://news.example.com/2").near_dup_skipped == 1  # same registrable domain => repost
    other = ingest("https://other-outlet.org/x")
    assert other.new == 1
    first = Article.objects.get(source_url="https://news.example.com/1")
    from modules.content.models import Evidence

    assert Evidence.objects.filter(subject_kind="article", subject_id=first.pk, domain="other-outlet.org").exists()
    assert Article.objects.get(source_url="https://other-outlet.org/x").review_reason.startswith("possible duplicate")


def test_ingest_stores_no_source_text(source):
    services.ingest_items(source, [item("https://news.example.com/z", "A distinctive headline about launches", "SECRET LEAD TEXT that must never be stored")], dispatch=False)
    a = Article.objects.get()
    assert "SECRET LEAD" not in " ".join(str(getattr(a, f.name)) for f in a._meta.fields)
