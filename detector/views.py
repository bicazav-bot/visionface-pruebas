import os
import tempfile
import time
from pathlib import Path

from django.conf import settings
from django.db.models import Count, Sum
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from . import vision
from .forms import ImagenForm, VideoForm
from .models import Deteccion


def inicio(request):
    resumen = Deteccion.objects.aggregate(total=Count("id"), rostros=Sum("rostros"))
    return render(request, "detector/inicio.html", {
        "resumen": resumen,
        "recientes": Deteccion.objects.all()[:5],
    })


def _analizar_imagen(archivo):
    inicio_t = time.perf_counter()
    imagen = vision.decodificar_imagen(archivo.read())
    rostros = vision.detectar_rostros(imagen)
    anotada = vision.dibujar_detecciones(imagen, rostros)
    ms = int((time.perf_counter() - inicio_t) * 1000)
    registro = Deteccion.objects.create(
        tipo=Deteccion.TIPO_IMAGEN, nombre_archivo=archivo.name,
        rostros=len(rostros), duracion_ms=ms,
    )
    return imagen, rostros, anotada, registro


def detectar_imagen(request):
    contexto = {"form": ImagenForm()}
    if request.method == "POST":
        form = ImagenForm(request.POST, request.FILES)
        contexto["form"] = form
        if form.is_valid():
            try:
                imagen, rostros, anotada, registro = _analizar_imagen(form.cleaned_data["archivo"])
                contexto.update({
                    "registro": registro,
                    "rostros": rostros,
                    "original_b64": vision.imagen_a_base64(imagen),
                    "anotada_b64": vision.imagen_a_base64(anotada),
                    "dimensiones": f"{imagen.shape[1]} x {imagen.shape[0]} px",
                })
            except vision.ImagenInvalidaError as exc:
                form.add_error("archivo", str(exc))
    return render(request, "detector/imagen.html", contexto)


def detectar_video(request):
    contexto = {"form": VideoForm()}
    if request.method == "POST":
        form = VideoForm(request.POST, request.FILES)
        contexto["form"] = form
        if form.is_valid():
            archivo = form.cleaned_data["archivo"]
            sufijo = Path(archivo.name).suffix.lower()
            fd, ruta = tempfile.mkstemp(suffix=sufijo)
            try:
                with os.fdopen(fd, "wb") as destino:
                    for trozo in archivo.chunks():
                        destino.write(trozo)
                inicio_t = time.perf_counter()
                resultado = vision.procesar_video(
                    ruta, max_cuadros=settings.VIDEO_MAX_FRAMES, paso=settings.VIDEO_FRAME_STEP,
                )
                ms = int((time.perf_counter() - inicio_t) * 1000)
                registro = Deteccion.objects.create(
                    tipo=Deteccion.TIPO_VIDEO, nombre_archivo=archivo.name,
                    rostros=resultado.max_rostros,
                    cuadros_analizados=resultado.cuadros_analizados, duracion_ms=ms,
                )
                contexto.update({
                    "registro": registro,
                    "resultado": resultado,
                    "mejor_b64": vision.imagen_a_base64(resultado.mejor_cuadro)
                    if resultado.mejor_cuadro is not None else None,
                })
            except vision.VideoInvalidoError as exc:
                form.add_error("archivo", str(exc))
            finally:
                os.remove(ruta)
    return render(request, "detector/video.html", contexto)


def historial(request):
    return render(request, "detector/historial.html", {
        "detecciones": Deteccion.objects.all()[:100],
    })


@require_POST
def api_detectar(request):
    """Endpoint JSON: recibe `archivo` (imagen) y devuelve los rostros detectados."""
    form = ImagenForm(request.POST, request.FILES)
    if not form.is_valid():
        return JsonResponse({"ok": False, "errores": form.errors.get_json_data()}, status=400)
    try:
        imagen, rostros, _, registro = _analizar_imagen(form.cleaned_data["archivo"])
    except vision.ImagenInvalidaError as exc:
        return JsonResponse({"ok": False, "errores": {"archivo": [{"message": str(exc)}]}}, status=400)
    return JsonResponse({
        "ok": True,
        "id": registro.id,
        "rostros": len(rostros),
        "cajas": [dict(zip("xywh", r)) for r in rostros],
        "ancho": int(imagen.shape[1]),
        "alto": int(imagen.shape[0]),
        "duracion_ms": registro.duracion_ms,
    })
