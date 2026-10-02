from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import MeView, UserViewSet

# Un router n'accepte que des ViewSets ; MeView, vue générique, passe par path().
router = DefaultRouter()
router.register("users", UserViewSet, basename="user")

urlpatterns = [
    path("me/", MeView.as_view(), name="me"),
    *router.urls,
]
