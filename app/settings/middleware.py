import logging

from django.shortcuts import render

logger = logging.getLogger(__name__)


class PortalErrorMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        path = request.path
        if not (path.startswith("/portal/") or path.startswith("/login/")):
            return None

        logger.exception("Portal error at %s", path)
        try:
            return render(request, "errors/500.html", status=500)
        except Exception:
            return None
