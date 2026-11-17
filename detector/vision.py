# Funciones de detección de rostros con OpenCV.
import base64

import cv2
import numpy as np

# Clasificador de rostros de frente que viene incluido con OpenCV.
clasificador = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

# Las imágenes grandes se reducen a este tamaño antes de buscar rostros.
# Así se evitan falsos positivos en fotos de muy alta resolución.
TAMANO_MAXIMO = 800


def leer_imagen(datos):
    """Convierte los bytes de un archivo en una imagen de OpenCV."""
    if not datos:
        raise ValueError("El archivo está vacío.")
    imagen = cv2.imdecode(np.frombuffer(datos, np.uint8), cv2.IMREAD_COLOR)
    if imagen is None:
        raise ValueError("El archivo no es una imagen válida.")
    return imagen


def detectar_rostros(imagen):
    """Devuelve una lista de rostros [x, y, ancho, alto]."""
    alto, ancho = imagen.shape[:2]
    escala = min(1, TAMANO_MAXIMO / max(alto, ancho))
    pequena = cv2.resize(imagen, None, fx=escala, fy=escala)
    gris = cv2.cvtColor(pequena, cv2.COLOR_BGR2GRAY)
    rostros = clasificador.detectMultiScale(gris, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
    # Se vuelven a escalar las coordenadas al tamaño original.
    return [[int(valor / escala) for valor in rostro] for rostro in rostros]


def dibujar_rostros(imagen, rostros):
    """Devuelve una copia de la imagen con un recuadro verde en cada rostro."""
    copia = imagen.copy()
    grosor = max(2, imagen.shape[1] // 300)
    for x, y, w, h in rostros:
        cv2.rectangle(copia, (x, y), (x + w, y + h), (0, 255, 0), grosor)
    return copia


def imagen_a_texto(imagen):
    """Convierte la imagen a texto base64 para mostrarla en la página."""
    _, buffer = cv2.imencode(".jpg", imagen)
    return "data:image/jpeg;base64," + base64.b64encode(buffer).decode()


def analizar_video(ruta, cada=5, maximo=300):
    """Analiza un cuadro de cada `cada` cuadros y devuelve un resumen."""
    video = cv2.VideoCapture(str(ruta))
    resultado = {"cuadros": 0, "analizados": 0, "con_rostros": 0,
                 "max_rostros": 0, "mejor_cuadro": None}

    while resultado["cuadros"] < maximo:
        leido, cuadro = video.read()
        if not leido:
            break
        if resultado["cuadros"] % cada == 0:
            rostros = detectar_rostros(cuadro)
            resultado["analizados"] += 1
            if rostros:
                resultado["con_rostros"] += 1
            if resultado["mejor_cuadro"] is None or len(rostros) > resultado["max_rostros"]:
                resultado["max_rostros"] = len(rostros)
                resultado["mejor_cuadro"] = dibujar_rostros(cuadro, rostros)
        resultado["cuadros"] += 1

    video.release()
    if resultado["cuadros"] == 0:
        raise ValueError("No se pudo abrir el video.")
    return resultado
