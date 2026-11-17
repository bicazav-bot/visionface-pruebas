from django.db import models


class Deteccion(models.Model):
    """Registro histórico de cada análisis realizado."""

    TIPO_IMAGEN = "imagen"
    TIPO_VIDEO = "video"
    TIPOS = [(TIPO_IMAGEN, "Imagen"), (TIPO_VIDEO, "Video")]

    tipo = models.CharField(max_length=10, choices=TIPOS)
    nombre_archivo = models.CharField(max_length=255)
    rostros = models.PositiveIntegerField(default=0)
    cuadros_analizados = models.PositiveIntegerField(default=1)
    duracion_ms = models.PositiveIntegerField(default=0)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha", "-id"]
        verbose_name = "detección"
        verbose_name_plural = "detecciones"

    def __str__(self):
        return f"{self.get_tipo_display()} {self.nombre_archivo}: {self.rostros} rostro(s)"
