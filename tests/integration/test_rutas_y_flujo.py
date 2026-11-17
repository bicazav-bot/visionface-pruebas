"""Pruebas de integración: rutas de Django + vistas + OpenCV + base de datos."""
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from detector.models import Deteccion

pytestmark = [pytest.mark.integration, pytest.mark.django_db]


@pytest.mark.parametrize("nombre,plantilla", [
    ("detector:inicio", "detector/inicio.html"),
    ("detector:imagen", "detector/imagen.html"),
    ("detector:video", "detector/video.html"),
    ("detector:historial", "detector/historial.html"),
])
def test_rutas_principales_responden_200(client, nombre, plantilla):
    respuesta = client.get(reverse(nombre))
    assert respuesta.status_code == 200
    assert plantilla in [t.name for t in respuesta.templates]


def test_ruta_inexistente_404(client):
    assert client.get("/no-existe/").status_code == 404


def test_archivos_estaticos_enlazados(client):
    assert b"detector/estilos.css" in client.get("/").content


def test_flujo_imagen_con_rostro(client, bytes_con_rostro):
    archivo = SimpleUploadedFile("messi.jpg", bytes_con_rostro, content_type="image/jpeg")
    respuesta = client.post(reverse("detector:imagen"), {"archivo": archivo})
    assert respuesta.status_code == 200
    assert len(respuesta.context["rostros"]) == 1
    assert respuesta.context["anotada_b64"].startswith("data:image/jpeg;base64,")
    registro = Deteccion.objects.get()
    assert (registro.tipo, registro.nombre_archivo, registro.rostros) == ("imagen", "messi.jpg", 1)


def test_flujo_imagen_sin_rostro(client, bytes_sin_rostro):
    archivo = SimpleUploadedFile("mandril.jpg", bytes_sin_rostro)
    respuesta = client.post(reverse("detector:imagen"), {"archivo": archivo})
    assert respuesta.context["rostros"] == []
    assert b"No se encontraron rostros" in respuesta.content
    assert Deteccion.objects.get().rostros == 0


def test_imagen_corrupta_muestra_error_y_no_guarda(client):
    archivo = SimpleUploadedFile("roto.jpg", b"no soy una imagen")
    respuesta = client.post(reverse("detector:imagen"), {"archivo": archivo})
    assert respuesta.status_code == 200
    assert "no es una imagen" in respuesta.content.decode()
    assert Deteccion.objects.count() == 0


def test_extension_invalida_no_guarda(client):
    archivo = SimpleUploadedFile("doc.pdf", b"%PDF")
    respuesta = client.post(reverse("detector:imagen"), {"archivo": archivo})
    assert "Formato no permitido" in respuesta.content.decode()
    assert Deteccion.objects.count() == 0


def test_flujo_video(client, video_con_rostros):
    with open(video_con_rostros, "rb") as f:
        respuesta = client.post(reverse("detector:video"), {"archivo": f})
    assert respuesta.status_code == 200
    resultado = respuesta.context["resultado"]
    assert resultado.cuadros_totales == 30
    assert resultado.max_rostros == 1
    registro = Deteccion.objects.get()
    assert registro.tipo == "video" and registro.cuadros_analizados == resultado.cuadros_analizados


def test_video_invalido(client):
    archivo = SimpleUploadedFile("falso.mp4", b"no es video")
    respuesta = client.post(reverse("detector:video"), {"archivo": archivo})
    assert "No se pudo abrir el video" in respuesta.content.decode()
    assert Deteccion.objects.count() == 0


def test_historial_e_inicio_reflejan_detecciones(client, bytes_con_rostro, bytes_sin_rostro):
    client.post(reverse("detector:imagen"), {"archivo": SimpleUploadedFile("uno.jpg", bytes_con_rostro)})
    client.post(reverse("detector:imagen"), {"archivo": SimpleUploadedFile("dos.jpg", bytes_sin_rostro)})
    historial = client.get(reverse("detector:historial")).content.decode()
    assert "uno.jpg" in historial and "dos.jpg" in historial
    inicio = client.get(reverse("detector:inicio"))
    assert inicio.context["resumen"] == {"total": 2, "rostros": 1}


class TestApi:
    url = "/api/detectar/"

    def test_api_devuelve_json(self, client, bytes_con_rostro):
        r = client.post(self.url, {"archivo": SimpleUploadedFile("m.jpg", bytes_con_rostro)})
        assert r.status_code == 200
        datos = r.json()
        assert datos["ok"] is True and datos["rostros"] == 1
        assert set(datos["cajas"][0]) == {"x", "y", "w", "h"}
        assert (datos["ancho"], datos["alto"]) == (548, 342)

    def test_api_rechaza_get(self, client):
        assert client.get(self.url).status_code == 405

    def test_api_sin_archivo_400(self, client):
        r = client.post(self.url, {})
        assert r.status_code == 400 and r.json()["ok"] is False

    def test_api_imagen_corrupta_400(self, client):
        r = client.post(self.url, {"archivo": SimpleUploadedFile("x.png", b"basura")})
        assert r.status_code == 400
