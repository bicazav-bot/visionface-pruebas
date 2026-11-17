# Datos de prueba compartidos por todas las pruebas.
from pathlib import Path

import cv2
import pytest

CARPETA = Path(__file__).parent / "fixtures"
CAPTURAS = Path(__file__).parent.parent / "evidencias" / "capturas"


@pytest.fixture
def foto_con_rostro():
    return CARPETA / "messi5.jpg"        # tiene 1 rostro


@pytest.fixture
def foto_sin_rostro():
    return CARPETA / "baboon.jpg"        # no tiene rostros humanos


@pytest.fixture
def foto_grande_sin_rostro():
    return CARPETA / "causa.jpeg"        # 4096 px, sin rostros (antes daba falsos positivos)


@pytest.fixture
def video_con_rostro(tmp_path, foto_con_rostro):
    """Crea un video de 30 cuadros a partir de la foto con rostro."""
    imagen = cv2.imread(str(foto_con_rostro))
    alto, ancho = imagen.shape[:2]
    ruta = tmp_path / "video_prueba.avi"
    video = cv2.VideoWriter(str(ruta), cv2.VideoWriter_fourcc(*"MJPG"), 10, (ancho, alto))
    for _ in range(30):
        video.write(imagen)
    video.release()
    return ruta


@pytest.fixture
def capturas():
    CAPTURAS.mkdir(parents=True, exist_ok=True)
    return CAPTURAS
