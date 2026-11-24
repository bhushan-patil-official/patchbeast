from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.decorators import api_view, throttle_classes
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle

from modules.newsletter import services

from .serializers import OkSerializer, SubscribeSerializer, TokenSerializer


class NewsletterThrottle(AnonRateThrottle):
    scope = "newsletter"


@extend_schema(request=SubscribeSerializer, responses=OkSerializer, tags=["newsletter"])
@api_view(["POST"])
@throttle_classes([NewsletterThrottle])
def subscribe(request):
    ser = SubscribeSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    if ser.validated_data.get("website"):  # honeypot tripped: pretend success
        return Response({"ok": True})
    try:
        services.subscribe(
            ser.validated_data["email"], source="web", game=ser.validated_data.get("game") or None
        )
    except services.NewsletterDisabled:
        return Response({"ok": False}, status=404)
    return Response({"ok": True})


@extend_schema(request=TokenSerializer, responses=OkSerializer, tags=["newsletter"])
@api_view(["POST"])
@throttle_classes([NewsletterThrottle])
def confirm(request):
    ser = TokenSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    ok = services.confirm(ser.validated_data["token"])
    return Response({"ok": ok}, status=200 if ok else 404)


@extend_schema(
    request=TokenSerializer,
    parameters=[OpenApiParameter("token", str, required=False)],
    responses=OkSerializer,
    tags=["newsletter"],
)
@api_view(["POST", "GET"])
@throttle_classes([NewsletterThrottle])
def unsubscribe(request):
    """POST (page button / RFC 8058 one-click). GET shows a minimal confirmation for plain mail-client links."""
    token = (
        request.data.get("token") if request.method == "POST" else request.query_params.get("token")
    )
    ok = bool(token) and services.unsubscribe(str(token))
    return Response({"ok": ok}, status=200 if ok else 404)
