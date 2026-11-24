from django.conf import settings
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views.decorators.http import require_GET
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view
from rest_framework.response import Response

from modules.platform import services
from modules.platform.api.serializers import PublicConfigSerializer


@require_GET
def healthz(request: HttpRequest) -> JsonResponse:
    result = services.health_checks()
    return JsonResponse(result, status=200 if result["ok"] else 503)


@require_GET
def metrics(request: HttpRequest) -> HttpResponse:
    token = settings.PB["METRICS_TOKEN"]
    if not token or request.headers.get("Authorization") != f"Bearer {token}":
        return HttpResponse(status=404)
    from modules.content.models import Article
    from modules.sources.models import Source

    spent, cap = services.spend_today()
    lines = [
        f"pb_kill_switch {int(services.kill_switch_on())}",
        f"pb_llm_spend_usd {spent}",
        f"pb_llm_cap_usd {cap}",
        f"pb_5xx_last_5m {services.current_5xx()}",
        f"pb_sources_failing {Source.objects.filter(enabled=True, health='failing').count()}",
    ]
    for st in Article.Status.values:
        lines.append(f'pb_articles{{status="{st}"}} {Article.objects.filter(status=st).count()}')
    return HttpResponse("\n".join(lines) + "\n", content_type="text/plain; version=0.0.4")


@extend_schema(responses=PublicConfigSerializer, tags=["config"])
@api_view(["GET"])
def public_config(request):
    return Response(
        {
            "flags": services.all_flags(),
            "contact_email": settings.PB["CONTACT_EMAIL"],
            "kill_switch": services.kill_switch_on(),
        }
    )
