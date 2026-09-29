from django.urls import path

from .views import CurrentUserView, LoginView, LogoutView, SetupView

urlpatterns = [
    path("setup/", SetupView.as_view(), name="account-setup"),
    path("login/", LoginView.as_view(), name="account-login"),
    path("logout/", LogoutView.as_view(), name="account-logout"),
    path("me/", CurrentUserView.as_view(), name="account-me"),
]
