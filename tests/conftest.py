"""Fixtures compartidas por todas las pruebas."""
from pathlib import Path

import cv2
import numpy as np
import pytest

FIXTURES = Path(__file__).parent / "fixtures"
CAPTURAS = Path(__file__).resolve().parent.parent / "evidencias" / "capturas"


@pytest.fixture(scope="session")
def ruta_con_rostro() -> Path:
    return FIXTURES / "messi5.jpg"      # 1 rostro frontal


@pytest.fixture(scope="session")
def ruta_sin_rostro() -> Path:
    return FIXTURES / "baboon.jpg"      # sin rostros humanos


@pytest.fixture(scope="session")
def bytes_con_rostro(ruta_con_rostro) -> bytes:
    return ruta_con_rostro.read_bytes()


@pytest.fixture(scope="session")
def bytes_sin_rostro(ruta_sin_rostro) -> bytes:
    return ruta_sin_rostro.read_bytes()


def _crear_video(ruta: Path, imagen: np.ndarray, cuadros: int = 30, fps: int = 10) -> Path:
    alto, ancho = imagen.shape[:2]
    escritor = cv2.VideoWriter(str(ruta), cv2.VideoWriter_fourcc(*"MJPG"), fps, (ancho, alto))
    assert escritor.isOpened(), "No se pudo crear el video de prueba"
    for i in range(cuadros):
        # Desplaza ligeramente la imagen para simular movimiento de cámara.
        m = np.float32([[1, 0, (i % 5) - 2], [0, 1, 0]])
        escritor.write(cv2.warpAffine(imagen, m, (ancho, alto), borderMode=cv2.BORDER_REPLICATE))
    escritor.release()
    return ruta


@pytest.fixture(scope="session")
def video_con_rostros(tmp_path_factory, ruta_con_rostro) -> Path:
    destino = tmp_path_factory.mktemp("videos") / "con_rostros.avi"
    return _crear_video(destino, cv2.imread(str(ruta_con_rostro)))


@pytest.fixture(scope="session")
def video_sin_rostros(tmp_path_factory, ruta_sin_rostro) -> Path:
    destino = tmp_path_factory.mktemp("videos") / "sin_rostros.avi"
    return _crear_video(destino, cv2.imread(str(ruta_sin_rostro)), cuadros=15)


@pytest.fixture(scope="session")
def carpeta_capturas() -> Path:
    CAPTURAS.mkdir(parents=True, exist_ok=True)
    return CAPTURAS
