import os
import tempfile

from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt

from . import vision
from .models import Deteccion

IMAGENES = (".jpg", ".jpeg", ".png", ".bmp", ".webp")
VIDEOS = (".mp4", ".avi", ".mov", ".mkv", ".webm")


def inicio(request):
    detecciones = Deteccion.objects.all()
    contexto = {
        "total": detecciones.count(),
        "total_rostros": sum(d.rostros for d in detecciones),
        "detecciones": detecciones,
    }
    return render(request, "detector/inicio.html", contexto)


def imagen(request):
    contexto = {}
    if request.method == "POST":
        archivo = request.FILES.get("archivo")
        if archivo is None or not archivo.name.lower().endswith(IMAGENES):
            contexto["error"] = "Formato no permitido. Use JPG, PNG, BMP o WEBP."
        else:
            try:
                foto = vision.leer_imagen(archivo.read())
                rostros = vision.detectar_rostros(foto)
                Deteccion.objects.create(tipo="Imagen", archivo=archivo.name, rostros=len(rostros))
                contexto["nombre"] = archivo.name
                contexto["rostros"] = rostros
                contexto["original"] = vision.imagen_a_texto(foto)
                contexto["marcada"] = vision.imagen_a_texto(vision.dibujar_rostros(foto, rostros))
            except ValueError as error:
                contexto["error"] = str(error)
    return render(request, "detector/imagen.html", contexto)


def video(request):
    contexto = {}
    if request.method == "POST":
        archivo = request.FILES.get("archivo")
        if archivo is None or not archivo.name.lower().endswith(VIDEOS):
            contexto["error"] = "Formato no permitido. Use MP4, AVI, MOV, MKV o WEBM."
        else:
            # OpenCV necesita el video en un archivo, así que se guarda uno temporal.
            temporal = tempfile.NamedTemporaryFile(suffix=os.path.splitext(archivo.name)[1], delete=False)
            for parte in archivo.chunks():
                temporal.write(parte)
            temporal.close()
            try:
                resultado = vision.analizar_video(temporal.name)
                Deteccion.objects.create(tipo="Video", archivo=archivo.name, rostros=resultado["max_rostros"])
                contexto["nombre"] = archivo.name
                contexto["resultado"] = resultado
                contexto["mejor_cuadro"] = vision.imagen_a_texto(resultado["mejor_cuadro"])
            except ValueError as error:
                contexto["error"] = str(error)
            finally:
                os.remove(temporal.name)
    return render(request, "detector/video.html", contexto)


def borrar(request):
    """Borra todos los análisis guardados y vuelve al inicio."""
    if request.method == "POST":
        Deteccion.objects.all().delete()
    return redirect("inicio")


@csrf_exempt   # la API se usa desde fuera del navegador (curl, Postman)
def api_detectar(request):
    """Recibe una imagen por POST y responde con los rostros en formato JSON."""
    if request.method != "POST":
        return JsonResponse({"error": "Use el método POST."}, status=405)
    archivo = request.FILES.get("archivo")
    if archivo is None:
        return JsonResponse({"error": "Falta el campo 'archivo'."}, status=400)
    try:
        foto = vision.leer_imagen(archivo.read())
    except ValueError as error:
        return JsonResponse({"error": str(error)}, status=400)
    rostros = vision.detectar_rostros(foto)
    Deteccion.objects.create(tipo="Imagen", archivo=archivo.name, rostros=len(rostros))
    return JsonResponse({"rostros": len(rostros), "posiciones": rostros})
