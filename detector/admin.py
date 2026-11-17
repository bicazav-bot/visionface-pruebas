from django.contrib import admin

from .models import Deteccion


@admin.register(Deteccion)
class DeteccionAdmin(admin.ModelAdmin):
    list_display = ("fecha", "tipo", "nombre_archivo", "rostros", "cuadros_analizados", "duracion_ms")
    list_filter = ("tipo",)
    search_fields = ("nombre_archivo",)
