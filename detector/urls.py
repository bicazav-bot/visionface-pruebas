from django.urls import path

from . import views

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("imagen/", views.imagen, name="imagen"),
    path("video/", views.video, name="video"),
    path("historial/", views.historial, name="historial"),
    path("api/detectar/", views.api_detectar, name="api_detectar"),
]
