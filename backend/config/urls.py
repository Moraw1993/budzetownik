from django.urls import include, path
from runtime.views import health

urlpatterns = [
    path("api/health/", health, name="health"),
    path("api/auth/", include("accounts.urls")),
    path("api/invitations/", include("households.invitation_urls")),
    path("api/households/", include("households.urls")),
]
