from pathlib import Path

from django import forms
from django.conf import settings

EXT_IMAGEN = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
EXT_VIDEO = {".mp4", ".avi", ".mov", ".mkv", ".webm"}


def _validar(archivo, extensiones):
    ext = Path(archivo.name).suffix.lower()
    if ext not in extensiones:
        raise forms.ValidationError(
            f"Formato no permitido ({ext or 'sin extensión'}). Use: {', '.join(sorted(extensiones))}."
        )
    if archivo.size > settings.MAX_UPLOAD_MB * 1024 * 1024:
        raise forms.ValidationError(f"El archivo supera {settings.MAX_UPLOAD_MB} MB.")
    return archivo


class ImagenForm(forms.Form):
    archivo = forms.FileField(label="Imagen")

    def clean_archivo(self):
        return _validar(self.cleaned_data["archivo"], EXT_IMAGEN)


class VideoForm(forms.Form):
    archivo = forms.FileField(label="Video")

    def clean_archivo(self):
        return _validar(self.cleaned_data["archivo"], EXT_VIDEO)
