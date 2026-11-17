# VisionFace: detección de rostros con Django y OpenCV

Aplicativo web que detecta rostros en **imágenes** y **videos** usando el clasificador Haar en cascada de OpenCV.
Incluye pruebas **unitarias**, de **integración** y **funcionales**.

**Universidad Estatal de Milagro (UNEMI)**, Facultad de Ciencias e Ingeniería, Carrera de Ingeniería de Software
Asignatura: Construcción de Software · Práctica 4 (Unidad 4) · Periodo agosto–noviembre 2026

**Integrantes:** Dana Anaelys Bravo Yépez · Kevin Saúl Dávila Briones · Dayana Mishelle Díaz Macas · Billy Mauricio Icaza Vergara · Ayelen Romina Zúñiga Lozano

---

## Requisitos

| Componente | Versión |
|---|---|
| Python | 3.12 o superior |
| Django | 6.1 |
| OpenCV (`opencv-python-headless`) | 4.14 (la serie 5.x ya no incluye los clasificadores Haar) |
| NumPy | 2.x |
| Microsoft Edge | Solo para las pruebas funcionales (Selenium descarga el driver automáticamente) |

## Instalación

```powershell
git clone <url-del-repositorio>
cd <carpeta-del-repositorio>
python -m venv .venv
.\.venv\Scripts\activate          # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
```

## Ejecución

```powershell
python manage.py runserver
```

Abrir <http://127.0.0.1:8000/>.

| Ruta | Descripción |
|---|---|
| `/` | Inicio: resumen y últimos análisis |
| `/imagen/` | Subir una imagen y detectar rostros |
| `/video/` | Subir un video y analizar sus cuadros |
| `/historial/` | Historial de análisis |
| `/api/detectar/` | API JSON (POST, campo `archivo`) |
| `/admin/` | Panel de administración de Django |

Ejemplo de uso de la API:

```powershell
curl -F "archivo=@tests/fixtures/messi5.jpg" http://127.0.0.1:8000/api/detectar/
```

## Pruebas

```powershell
pytest                       # todas (68 pruebas)
pytest -m unit               # solo unitarias
pytest -m integration        # solo integración
pytest -m functional         # solo funcionales (Selenium + Edge, guarda capturas)
pytest --cov=detector        # con cobertura
```

Resultado de la última ejecución: **68 pruebas aprobadas, 0 fallidas, cobertura del 98 %**.
Los logs y las capturas están en [`evidencias/`](evidencias/).

## Estructura del proyecto

```
├── config/                  # Configuración de Django (settings, urls, wsgi)
├── detector/                # Aplicación principal
│   ├── vision.py            # Núcleo OpenCV: decodificar, detectar, dibujar, procesar video
│   ├── views.py             # Vistas: inicio, imagen, video, historial, API
│   ├── forms.py             # Validación de archivos (extensión y tamaño)
│   ├── models.py            # Modelo Deteccion (historial)
│   ├── templates/detector/  # Plantillas HTML
│   └── static/detector/     # Estilos CSS
├── tests/
│   ├── conftest.py          # Fixtures: imágenes de prueba y videos generados
│   ├── fixtures/            # Imágenes de muestra de OpenCV (con y sin rostro)
│   ├── unit/                # Pruebas unitarias
│   ├── integration/         # Pruebas de integración
│   └── functional/          # Pruebas funcionales (Selenium)
├── evidencias/              # Logs, resultados JUnit y capturas de pantalla
├── docs/                    # Informe final (PDF y DOCX)
├── requirements.txt
└── pytest.ini
```

## Documentación

El informe con la documentación técnica y de usuario está en [`docs/`](docs/).
