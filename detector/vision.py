"""Módulo de visión por computadora: detección de rostros con OpenCV.

Contiene las funciones críticas del sistema. No depende de Django, por lo
que puede probarse de forma aislada (pruebas unitarias).
"""
from __future__ import annotations

import base64
from dataclasses import dataclass, field
from functools import lru_cache

import cv2
import numpy as np

CASCADE_FILE = "haarcascade_frontalface_default.xml"
BOX_COLOR = (0, 200, 0)  # BGR


class ImagenInvalidaError(ValueError):
    """Se lanza cuando los datos recibidos no son una imagen válida."""


class VideoInvalidoError(ValueError):
    """Se lanza cuando el archivo de video no puede abrirse o no tiene cuadros."""


@dataclass
class ResultadoVideo:
    cuadros_totales: int
    cuadros_analizados: int
    cuadros_con_rostros: int
    max_rostros: int
    total_detecciones: int
    fps: float
    detecciones_por_cuadro: list[tuple[int, int]] = field(default_factory=list)
    mejor_cuadro: np.ndarray | None = None

    @property
    def porcentaje_con_rostros(self) -> float:
        if self.cuadros_analizados == 0:
            return 0.0
        return round(100 * self.cuadros_con_rostros / self.cuadros_analizados, 1)


@lru_cache(maxsize=1)
def cargar_clasificador() -> cv2.CascadeClassifier:
    """Carga (una sola vez) el clasificador Haar de rostros frontales."""
    ruta = cv2.data.haarcascades + CASCADE_FILE
    clasificador = cv2.CascadeClassifier(ruta)
    if clasificador.empty():
        raise RuntimeError(f"No se pudo cargar el clasificador: {ruta}")
    return clasificador


def decodificar_imagen(datos: bytes) -> np.ndarray:
    """Convierte bytes (JPG, PNG, ...) en una imagen BGR de OpenCV."""
    if not datos:
        raise ImagenInvalidaError("El archivo está vacío.")
    arreglo = np.frombuffer(datos, dtype=np.uint8)
    imagen = cv2.imdecode(arreglo, cv2.IMREAD_COLOR)
    if imagen is None:
        raise ImagenInvalidaError("El archivo no es una imagen válida.")
    return imagen


def detectar_rostros(imagen: np.ndarray, escala: float = 1.1, vecinos: int = 5,
                     tamano_minimo: int = 30) -> list[tuple[int, int, int, int]]:
    """Devuelve la lista de rostros detectados como tuplas (x, y, ancho, alto)."""
    if imagen is None or not isinstance(imagen, np.ndarray) or imagen.size == 0:
        raise ImagenInvalidaError("Se requiere una imagen no vacía.")
    if escala <= 1.0:
        raise ValueError("El factor de escala debe ser mayor que 1.0.")
    gris = imagen if imagen.ndim == 2 else cv2.cvtColor(imagen, cv2.COLOR_BGR2GRAY)
    rostros = cargar_clasificador().detectMultiScale(
        gris, scaleFactor=escala, minNeighbors=vecinos,
        minSize=(tamano_minimo, tamano_minimo),
    )
    return [tuple(int(v) for v in r) for r in rostros]


def dibujar_detecciones(imagen: np.ndarray, rostros) -> np.ndarray:
    """Devuelve una copia de la imagen con un recuadro por cada rostro."""
    salida = imagen.copy()
    for i, (x, y, w, h) in enumerate(rostros, start=1):
        cv2.rectangle(salida, (x, y), (x + w, y + h), BOX_COLOR, 2)
        cv2.putText(salida, f"#{i}", (x, max(y - 6, 12)), cv2.FONT_HERSHEY_SIMPLEX,
                    0.5, BOX_COLOR, 1, cv2.LINE_AA)
    return salida


def imagen_a_base64(imagen: np.ndarray, formato: str = ".jpg") -> str:
    """Codifica la imagen para mostrarla en HTML (data URI)."""
    ok, buffer = cv2.imencode(formato, imagen)
    if not ok:
        raise ImagenInvalidaError("No se pudo codificar la imagen.")
    mime = "image/png" if formato == ".png" else "image/jpeg"
    return f"data:{mime};base64," + base64.b64encode(buffer.tobytes()).decode("ascii")


def procesar_video(ruta: str, max_cuadros: int = 300, paso: int = 5) -> ResultadoVideo:
    """Analiza un video cada `paso` cuadros y resume las detecciones."""
    if paso < 1 or max_cuadros < 1:
        raise ValueError("paso y max_cuadros deben ser >= 1.")
    captura = cv2.VideoCapture(str(ruta))
    if not captura.isOpened():
        raise VideoInvalidoError("No se pudo abrir el video.")
    try:
        fps = float(captura.get(cv2.CAP_PROP_FPS) or 0.0)
        indice = analizados = con_rostros = maximo = total = 0
        por_cuadro: list[tuple[int, int]] = []
        mejor = None
        while indice < max_cuadros:
            ok, cuadro = captura.read()
            if not ok:
                break
            if indice % paso == 0:
                rostros = detectar_rostros(cuadro)
                n = len(rostros)
                analizados += 1
                total += n
                por_cuadro.append((indice, n))
                if n:
                    con_rostros += 1
                if n > maximo or mejor is None:
                    maximo = max(maximo, n)
                    mejor = dibujar_detecciones(cuadro, rostros)
            indice += 1
    finally:
        captura.release()
    if indice == 0:
        raise VideoInvalidoError("El video no contiene cuadros legibles.")
    return ResultadoVideo(indice, analizados, con_rostros, maximo, total, fps, por_cuadro, mejor)
