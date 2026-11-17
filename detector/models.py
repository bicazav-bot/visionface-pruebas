from django.db import models


class Deteccion(models.Model):
    """Guarda cada análisis para mostrarlo en el historial."""
    tipo = models.CharField(max_length=10)        # "Imagen" o "Video"
    archivo = models.CharField(max_length=255)
    rostros = models.IntegerField(default=0)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-id"]   # el más reciente primero

    def __str__(self):
        return f"{self.tipo} {self.archivo}: {self.rostros} rostro(s)"
