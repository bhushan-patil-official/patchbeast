"""WebSub receiver: GET = subscription verification handshake, POST = push notification."""

from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseNotFound
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from modules.sources.fetchers import websub
from modules.sources.models import Source


@csrf_exempt
@require_http_methods(["GET", "POST"])
def websub_callback(request, source_id: int):
    source = Source.objects.filter(id=source_id, type=Source.Type.WEBSUB, enabled=True).first()
    if not source:
        return HttpResponseNotFound()
    secret = (source.config or {}).get("secret", "")
    if request.method == "GET":
        challenge = request.GET.get("hub.challenge")
        topic = request.GET.get("hub.topic", "")
        if not challenge or topic != websub.topic_url(source.config.get("channel_id", "")):
            return HttpResponseNotFound()
        return HttpResponse(challenge, content_type="text/plain")
    body = request.body
    sig = request.headers.get("X-Hub-Signature-256") or request.headers.get("X-Hub-Signature", "")
    if not secret or not websub.verify_signature(body, sig, secret):
        return HttpResponse(status=202)  # per spec: ack but ignore bad signatures
    try:
        items = websub.parse_notification(body)
    except Exception:
        return HttpResponseBadRequest()
    from modules.ingest import services as ingest

    ingest.ingest_items(source, items)
    return HttpResponse(status=204)
