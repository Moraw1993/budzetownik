from rest_framework.views import APIView


class PrivateAPIView(APIView):
    """Prevent browsers and proxies from caching authenticated application data."""

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        response["Cache-Control"] = "no-store"
        return response
