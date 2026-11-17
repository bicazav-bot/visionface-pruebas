"""Pruebas unitarias del módulo de detección con OpenCV (detector/vision.py)."""
import base64

import cv2
import numpy as np
import pytest

from detector import vision

pytestmark = pytest.mark.unit


class TestCargarClasificador:
    def test_carga_clasificador_haar(self):
        clasificador = vision.cargar_clasificador()
        assert not clasificador.empty()

    def test_clasificador_se_cachea(self):
        assert vision.cargar_clasificador() is vision.cargar_clasificador()


class TestDecodificarImagen:
    def test_decodifica_jpg_valido(self, bytes_con_rostro):
        imagen = vision.decodificar_imagen(bytes_con_rostro)
        assert imagen.ndim == 3 and imagen.shape[2] == 3
        assert imagen.shape[:2] == (342, 548)

    def test_decodifica_png_generado(self):
        ok, buf = cv2.imencode(".png", np.zeros((20, 30, 3), np.uint8))
        assert vision.decodificar_imagen(buf.tobytes()).shape == (20, 30, 3)

    def test_bytes_vacios_lanza_error(self):
        with pytest.raises(vision.ImagenInvalidaError, match="vacío"):
            vision.decodificar_imagen(b"")

    def test_bytes_corruptos_lanza_error(self):
        with pytest.raises(vision.ImagenInvalidaError, match="no es una imagen"):
            vision.decodificar_imagen(b"esto no es una imagen")


class TestDetectarRostros:
    def test_detecta_un_rostro(self, bytes_con_rostro):
        rostros = vision.detectar_rostros(vision.decodificar_imagen(bytes_con_rostro))
        assert len(rostros) == 1
        x, y, w, h = rostros[0]
        assert w >= 30 and h >= 30
        assert all(isinstance(v, int) for v in rostros[0])

    def test_rostro_dentro_de_los_limites(self, bytes_con_rostro):
        imagen = vision.decodificar_imagen(bytes_con_rostro)
        alto, ancho = imagen.shape[:2]
        for x, y, w, h in vision.detectar_rostros(imagen):
            assert 0 <= x and x + w <= ancho
            assert 0 <= y and y + h <= alto

    def test_imagen_sin_rostros(self, bytes_sin_rostro):
        assert vision.detectar_rostros(vision.decodificar_imagen(bytes_sin_rostro)) == []

    def test_imagen_negra_sin_rostros(self):
        assert vision.detectar_rostros(np.zeros((200, 200, 3), np.uint8)) == []

    def test_acepta_escala_de_grises(self, bytes_con_rostro):
        gris = cv2.cvtColor(vision.decodificar_imagen(bytes_con_rostro), cv2.COLOR_BGR2GRAY)
        assert len(vision.detectar_rostros(gris)) == 1

    def test_tamano_minimo_filtra_rostros_pequenos(self, bytes_con_rostro):
        imagen = vision.decodificar_imagen(bytes_con_rostro)
        assert vision.detectar_rostros(imagen, tamano_minimo=200) == []

    @pytest.mark.parametrize("valor", [None, np.array([])])
    def test_imagen_invalida_lanza_error(self, valor):
        with pytest.raises(vision.ImagenInvalidaError):
            vision.detectar_rostros(valor)

    def test_escala_invalida_lanza_error(self):
        with pytest.raises(ValueError):
            vision.detectar_rostros(np.zeros((50, 50, 3), np.uint8), escala=1.0)


class TestDibujarDetecciones:
    def test_no_modifica_la_original(self):
        original = np.zeros((100, 100, 3), np.uint8)
        salida = vision.dibujar_detecciones(original, [(10, 10, 40, 40)])
        assert original.sum() == 0
        assert salida.sum() > 0

    def test_dibuja_recuadro_verde(self):
        salida = vision.dibujar_detecciones(np.zeros((100, 100, 3), np.uint8), [(10, 20, 40, 40)])
        assert tuple(salida[40, 10]) == vision.BOX_COLOR   # borde izquierdo del recuadro

    def test_sin_rostros_devuelve_copia_identica(self):
        original = np.full((50, 50, 3), 7, np.uint8)
        salida = vision.dibujar_detecciones(original, [])
        assert salida is not original and np.array_equal(salida, original)


class TestImagenABase64:
    def test_genera_data_uri_jpeg(self):
        uri = vision.imagen_a_base64(np.zeros((10, 10, 3), np.uint8))
        assert uri.startswith("data:image/jpeg;base64,")
        assert base64.b64decode(uri.split(",", 1)[1])[:2] == b"\xff\xd8"  # firma JPEG

    def test_genera_data_uri_png(self):
        uri = vision.imagen_a_base64(np.zeros((10, 10, 3), np.uint8), ".png")
        assert uri.startswith("data:image/png;base64,")


class TestProcesarVideo:
    def test_video_con_rostros(self, video_con_rostros):
        r = vision.procesar_video(video_con_rostros, max_cuadros=300, paso=5)
        assert r.cuadros_totales == 30
        assert r.cuadros_analizados == 6
        assert r.cuadros_con_rostros == 6
        assert r.max_rostros == 1
        assert r.porcentaje_con_rostros == 100.0
        assert r.mejor_cuadro is not None
        assert [c for c, _ in r.detecciones_por_cuadro] == [0, 5, 10, 15, 20, 25]

    def test_video_sin_rostros(self, video_sin_rostros):
        r = vision.procesar_video(video_sin_rostros, paso=3)
        assert r.cuadros_con_rostros == 0
        assert r.max_rostros == 0
        assert r.porcentaje_con_rostros == 0.0

    def test_respeta_limite_de_cuadros(self, video_con_rostros):
        r = vision.procesar_video(video_con_rostros, max_cuadros=10, paso=1)
        assert r.cuadros_totales == 10 and r.cuadros_analizados == 10

    def test_archivo_inexistente(self, tmp_path):
        with pytest.raises(vision.VideoInvalidoError):
            vision.procesar_video(tmp_path / "no_existe.mp4")

    def test_archivo_no_es_video(self, tmp_path):
        falso = tmp_path / "falso.mp4"
        falso.write_bytes(b"texto plano")
        with pytest.raises(vision.VideoInvalidoError):
            vision.procesar_video(falso)

    @pytest.mark.parametrize("paso,maximo", [(0, 10), (1, 0)])
    def test_parametros_invalidos(self, video_con_rostros, paso, maximo):
        with pytest.raises(ValueError):
            vision.procesar_video(video_con_rostros, max_cuadros=maximo, paso=paso)
