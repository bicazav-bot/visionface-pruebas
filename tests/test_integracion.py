# Pruebas de integración: rutas de Django + vistas + OpenCV + base de datos.
import pytest

from detector.models import Deteccion

pytestmark = pytest.mark.django_db


def test_rutas_principales(client):
    for ruta in ["/", "/imagen/", "/video/"]:
        assert client.get(ruta).status_code == 200


def test_ruta_inexistente(client):
    assert client.get("/no-existe/").status_code == 404


def test_subir_imagen_con_rostro(client, foto_con_rostro):
    with open(foto_con_rostro, "rb") as archivo:
        respuesta = client.post("/imagen/", {"archivo": archivo})
    assert len(respuesta.context["rostros"]) == 1
    assert Deteccion.objects.get().rostros == 1


def test_subir_imagen_grande_sin_rostros(client, foto_grande_sin_rostro):
    with open(foto_grande_sin_rostro, "rb") as archivo:
        respuesta = client.post("/imagen/", {"archivo": archivo})
    assert "No se encontraron rostros" in respuesta.content.decode()


def test_subir_archivo_no_permitido(client, tmp_path):
    texto = tmp_path / "documento.txt"
    texto.write_text("hola")
    with open(texto, "rb") as archivo:
        respuesta = client.post("/imagen/", {"archivo": archivo})
    assert "Formato no permitido" in respuesta.content.decode()
    assert Deteccion.objects.count() == 0


def test_subir_video(client, video_con_rostro):
    with open(video_con_rostro, "rb") as archivo:
        respuesta = client.post("/video/", {"archivo": archivo})
    assert respuesta.context["resultado"]["max_rostros"] == 1
    assert Deteccion.objects.get().tipo == "Video"


def test_inicio_muestra_los_analisis(client, foto_con_rostro):
    with open(foto_con_rostro, "rb") as archivo:
        client.post("/imagen/", {"archivo": archivo})
    respuesta = client.get("/")
    assert "messi5.jpg" in respuesta.content.decode()
    assert respuesta.context["total"] == 1


def test_borrar_historial(client, foto_con_rostro):
    with open(foto_con_rostro, "rb") as archivo:
        client.post("/imagen/", {"archivo": archivo})
    respuesta = client.post("/borrar/")
    assert respuesta.status_code == 302          # vuelve al inicio
    assert Deteccion.objects.count() == 0


def test_borrar_con_get_no_borra(client, foto_con_rostro):
    with open(foto_con_rostro, "rb") as archivo:
        client.post("/imagen/", {"archivo": archivo})
    client.get("/borrar/")
    assert Deteccion.objects.count() == 1


def test_api_detectar(client, foto_con_rostro):
    with open(foto_con_rostro, "rb") as archivo:
        respuesta = client.post("/api/detectar/", {"archivo": archivo})
    assert respuesta.status_code == 200
    assert respuesta.json()["rostros"] == 1


def test_api_sin_archivo(client):
    assert client.post("/api/detectar/").status_code == 400
    assert client.get("/api/detectar/").status_code == 405
