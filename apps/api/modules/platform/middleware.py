from .services import count_5xx


class ServerErrorCounterMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            response = self.get_response(request)
        except Exception:
            count_5xx()
            raise
        if response.status_code >= 500 and request.path != "/healthz":
            count_5xx()
        return response
