from django.urls import path

from . import views

app_name = "detector"

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("imagen/", views.detectar_imagen, name="imagen"),
    path("video/", views.detectar_video, name="video"),
    path("historial/", views.historial, name="historial"),
    path("api/detectar/", views.api_detectar, name="api_detectar"),
]
