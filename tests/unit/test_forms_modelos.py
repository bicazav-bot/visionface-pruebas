"""Pruebas unitarias de formularios y modelo."""
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from detector.forms import ImagenForm, VideoForm
from detector.models import Deteccion

pytestmark = pytest.mark.unit


def _archivo(nombre, contenido=b"x"):
    return SimpleUploadedFile(nombre, contenido)


@pytest.mark.parametrize("nombre", ["foto.jpg", "FOTO.JPEG", "a.png", "b.webp", "c.bmp"])
def test_imagen_form_acepta_extensiones_validas(nombre):
    assert ImagenForm(files={"archivo": _archivo(nombre)}).is_valid()


@pytest.mark.parametrize("nombre", ["doc.pdf", "video.mp4", "sin_extension"])
def test_imagen_form_rechaza_extensiones(nombre):
    form = ImagenForm(files={"archivo": _archivo(nombre)})
    assert not form.is_valid()
    assert "Formato no permitido" in form.errors["archivo"][0]


def test_imagen_form_requiere_archivo():
    assert not ImagenForm(files={}).is_valid()


@pytest.mark.parametrize("nombre", ["v.mp4", "v.avi", "v.mov", "v.mkv", "v.webm"])
def test_video_form_acepta_extensiones_validas(nombre):
    assert VideoForm(files={"archivo": _archivo(nombre)}).is_valid()


def test_video_form_rechaza_imagen():
    assert not VideoForm(files={"archivo": _archivo("foto.jpg")}).is_valid()


def test_rechaza_archivo_demasiado_grande(settings):
    settings.MAX_UPLOAD_MB = 0
    form = ImagenForm(files={"archivo": _archivo("foto.jpg", b"12345")})
    assert not form.is_valid()
    assert "supera" in form.errors["archivo"][0]


@pytest.mark.django_db
def test_modelo_str_y_orden():
    a = Deteccion.objects.create(tipo="imagen", nombre_archivo="a.jpg", rostros=2)
    b = Deteccion.objects.create(tipo="video", nombre_archivo="b.mp4", rostros=1)
    assert str(a) == "Imagen a.jpg: 2 rostro(s)"
    assert list(Deteccion.objects.all()) == [b, a]   # más reciente primero
