# VisionFace: detección de rostros con Django y OpenCV

Aplicación web que detecta rostros en **imágenes** y **videos** con el clasificador Haar de OpenCV.
Incluye pruebas **unitarias**, de **integración** y **funcionales**.

**UNEMI**, Ingeniería de Software · Construcción de Software · Práctica 4 · Agosto–noviembre 2026

**Integrantes:** Dana Anaelys Bravo Yépez · Kevin Saúl Dávila Briones · Dayana Mishelle Díaz Macas · Billy Mauricio Icaza Vergara · Ayelen Romina Zúñiga Lozano

## Instalación

```powershell
git clone https://github.com/bicazav-bot/visionface-pruebas.git
cd visionface-pruebas
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
```

## Ejecución

```powershell
python manage.py runserver
```

Abrir <http://127.0.0.1:8000/>. Páginas: Inicio (`/`, con los últimos análisis y el botón **Borrar historial**), Imagen (`/imagen/`), Video (`/video/`) y API (`POST /api/detectar/` con el campo `archivo`).

## Pruebas

```powershell
pytest                              # todas (27 pruebas)
pytest tests/test_unitarias.py      # unitarias
pytest tests/test_integracion.py    # integración
pytest tests/test_funcionales.py    # funcionales (necesita Microsoft Edge)
pytest --cov=detector               # con cobertura
```

Última ejecución: **27 pruebas aprobadas, 0 fallidas, 94 % de cobertura**. Logs y capturas en [`evidencias/`](evidencias/).

## Estructura

```
config/            configuración de Django
detector/
  vision.py        detección con OpenCV
  views.py         páginas y API
  models.py        tabla Deteccion
  templates/       páginas HTML
tests/
  test_unitarias.py
  test_integracion.py
  test_funcionales.py
  fixtures/        imágenes de prueba
evidencias/        logs y capturas
docs/              informe en Word
```
