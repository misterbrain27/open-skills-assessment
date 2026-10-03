from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import LoginView, LogoutView, MeView, RefreshView, UserViewSet

# Un router n'accepte que des ViewSets ; MeView, vue générique, passe par path().
router = DefaultRouter()
router.register("users", UserViewSet, basename="user")

urlpatterns = [
    path("me/", MeView.as_view(), name="me"),
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/refresh/", RefreshView.as_view(), name="token_refresh"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    *router.urls,
]
