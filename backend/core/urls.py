from django.urls import path

from .views import LivenessView, ReadinessView

urlpatterns = [
    path("health/", LivenessView.as_view(), name="health"),
    path("ready/", ReadinessView.as_view(), name="ready"),
]
