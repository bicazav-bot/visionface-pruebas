# Pruebas unitarias: cada función de detector/vision.py por separado.
import numpy as np
import pytest

from detector import vision


def test_leer_imagen_valida(foto_con_rostro):
    imagen = vision.leer_imagen(foto_con_rostro.read_bytes())
    assert imagen.shape == (342, 548, 3)


def test_leer_imagen_vacia():
    with pytest.raises(ValueError):
        vision.leer_imagen(b"")


def test_leer_archivo_que_no_es_imagen():
    with pytest.raises(ValueError):
        vision.leer_imagen(b"esto es texto")


def test_detecta_un_rostro(foto_con_rostro):
    imagen = vision.leer_imagen(foto_con_rostro.read_bytes())
    rostros = vision.detectar_rostros(imagen)
    assert len(rostros) == 1


def test_no_detecta_rostros_en_mandril(foto_sin_rostro):
    imagen = vision.leer_imagen(foto_sin_rostro.read_bytes())
    assert vision.detectar_rostros(imagen) == []


def test_foto_grande_sin_falsos_positivos(foto_grande_sin_rostro):
    imagen = vision.leer_imagen(foto_grande_sin_rostro.read_bytes())
    assert vision.detectar_rostros(imagen) == []


def test_imagen_negra_sin_rostros():
    negra = np.zeros((300, 300, 3), np.uint8)
    assert vision.detectar_rostros(negra) == []


def test_dibujar_no_cambia_la_original():
    original = np.zeros((100, 100, 3), np.uint8)
    marcada = vision.dibujar_rostros(original, [[10, 10, 50, 50]])
    assert original.sum() == 0
    assert marcada.sum() > 0


def test_imagen_a_texto():
    texto = vision.imagen_a_texto(np.zeros((10, 10, 3), np.uint8))
    assert texto.startswith("data:image/jpeg;base64,")


def test_analizar_video(video_con_rostro):
    resultado = vision.analizar_video(video_con_rostro)
    assert resultado["cuadros"] == 30
    assert resultado["analizados"] == 6        # un cuadro de cada 5
    assert resultado["con_rostros"] == 6
    assert resultado["max_rostros"] == 1


def test_video_que_no_existe(tmp_path):
    with pytest.raises(ValueError):
        vision.analizar_video(tmp_path / "no_existe.mp4")
