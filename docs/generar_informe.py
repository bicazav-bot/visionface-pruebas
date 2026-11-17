"""Genera el informe final (DOCX) sobre la plantilla institucional UNEMI.

Uso:  python docs/generar_informe.py <plantilla.docx> <salida.docx> <url_github>
Requiere: python-docx
"""
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

RAIZ = Path(__file__).resolve().parent.parent
EVID = RAIZ / "evidencias"
CAPT = EVID / "capturas"
AZUL = RGBColor(0x1B, 0x3A, 0x6B)
NARANJA = "F08A24"
FUENTE = "Arial"

plantilla, salida, URL = sys.argv[1], sys.argv[2], sys.argv[3]
doc = Document(plantilla)
P = doc.paragraphs

INTEGRANTES = [
    "Bravo Yépez Dana Anaelys",
    "Dávila Briones Kevin Saúl",
    "Díaz Macas Dayana Mishelle",
    "Icaza Vergara Billy Mauricio",
    "Zúñiga Lozano Ayelen Romina",
]

# ---------------------------------------------------------------- portada
def llenar(indice, texto):
    runs = P[indice].runs
    runs[1].text = texto
    for r in runs[2:]:
        r.text = ""

llenar(10, "Pruebas de calidad y documentación técnica y de usuario del aplicativo web "
           "VisionFace (Django + OpenCV)")
r = P[11].runs
r[1].text = INTEGRANTES[0]
for nombre in INTEGRANTES[1:]:
    r[1].add_break()
    r[1].add_text(nombre)
llenar(12, "Construcción de Software")
llenar(13, "Ing. Jonathan Eduardo Merino Gavilanes")
llenar(14, "Sábado, 21 de noviembre de 2026")
llenar(15, "Agosto 2026 a Noviembre 2026")
# Compacta un poco la portada para que los 5 autores quepan en una página.
for i in (0, 4, 6, 9, 16):
    P[i].paragraph_format.space_after = Pt(0)
    P[i].paragraph_format.space_before = Pt(0)
    for run in P[i].runs:
        run.font.size = Pt(4)
for i in range(10, 16):
    P[i].paragraph_format.space_before = Pt(4)
    P[i].paragraph_format.space_after = Pt(4)

# Los párrafos de contenido se insertan antes del último párrafo de la plantilla
# (que contiene los elementos gráficos de la sección 2).
ANCLA = P[-1]._p
for p in P[18:21] + P[1:4]:  # párrafos vacíos sobrantes de la plantilla (sin gráficos)
    assert not p._p.xpath(".//w:drawing")
    p._p.getparent().remove(p._p)


def _insertar(elemento):
    ANCLA.addprevious(elemento)
    return elemento


def parrafo(texto="", negrita=False, alineado=WD_ALIGN_PARAGRAPH.JUSTIFY, tam=11,
            espacio=6, color=None, cursiva=False):
    p = doc.add_paragraph()
    _insertar(p._p)
    p.alignment = alineado
    p.paragraph_format.space_after = Pt(espacio)
    p.paragraph_format.line_spacing = 1.15
    if alineado != WD_ALIGN_PARAGRAPH.JUSTIFY:
        p.paragraph_format.first_line_indent = Cm(0)
    if texto:
        _texto(p, texto, negrita, tam, color, cursiva)
    return p


def _texto(p, texto, negrita=False, tam=11, color=None, cursiva=False):
    # Admite **negrita** en línea.
    partes = texto.split("**")
    for i, parte in enumerate(partes):
        if not parte:
            continue
        run = p.add_run(parte)
        run.font.name = FUENTE
        run.font.size = Pt(tam)
        run.bold = negrita or (i % 2 == 1)
        run.italic = cursiva
        if color:
            run.font.color.rgb = color
    return p


def titulo(texto, nivel=1):
    p = doc.add_paragraph(style=f"Heading {nivel}")
    _insertar(p._p)
    p.paragraph_format.space_before = Pt(14 if nivel == 1 else 10)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(texto)
    run.font.name = FUENTE
    run.font.size = Pt({1: 15, 2: 13, 3: 11.5}[nivel])
    run.font.bold = True
    run.font.color.rgb = AZUL
    return p


def vineta(texto, nivel=0):
    p = parrafo(espacio=3)
    p.paragraph_format.left_indent = Cm(0.9 + 0.6 * nivel)
    p.paragraph_format.first_line_indent = Cm(-0.45)
    _texto(p, "•  " if nivel == 0 else "–  ")
    _texto(p, texto)
    return p


def salto_pagina():
    p = parrafo(espacio=0)
    p.add_run().add_break(WD_BREAK.PAGE)


def codigo(texto, tam=8):
    """Bloque de código monoespaciado con fondo gris."""
    for linea in texto.rstrip("\n").split("\n"):
        p = parrafo(alineado=WD_ALIGN_PARAGRAPH.LEFT, espacio=0)
        p.paragraph_format.line_spacing = 1.0
        p.paragraph_format.left_indent = Cm(0.2)
        pPr = p._p.get_or_add_pPr()
        shd = OxmlElement("w:shd")
        shd.set(qn("w:val"), "clear")
        shd.set(qn("w:color"), "auto")
        shd.set(qn("w:fill"), "F2F4F8")
        pPr.append(shd)
        p.paragraph_format.first_line_indent = Cm(0)
        run = p.add_run(linea.replace("\t", "    ") or " ")
        run.font.name = "Consolas"
        run._element.rPr.rFonts.set(qn("w:eastAsia"), "Consolas")
        run.font.size = Pt(tam)
    parrafo(espacio=4)


_figura = [0]
_tabla = [0]


def figura(ruta, pie, ancho_cm=15.5):
    _figura[0] += 1
    p = parrafo(alineado=WD_ALIGN_PARAGRAPH.CENTER, espacio=2)
    p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(str(ruta), width=Cm(ancho_cm))
    parrafo(f"Figura {_figura[0]}. {pie}", alineado=WD_ALIGN_PARAGRAPH.CENTER, tam=9,
            cursiva=True, espacio=10)


def _bordes(tabla):
    tblPr = tabla._tbl.tblPr
    bordes = OxmlElement("w:tblBorders")
    for lado in ("top", "left", "bottom", "right", "insideH", "insideV"):
        b = OxmlElement(f"w:{lado}")
        b.set(qn("w:val"), "single")
        b.set(qn("w:sz"), "4")
        b.set(qn("w:color"), "B8C2D6")
        bordes.append(b)
    tblPr.append(bordes)


def _sombrear(celda, color):
    tcPr = celda._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), color)
    tcPr.append(shd)


def tabla(encabezado, filas, anchos_cm, pie=None, tam=9):
    if pie:
        _tabla[0] += 1
        p = parrafo(f"Tabla {_tabla[0]}. {pie}", tam=9, cursiva=True, espacio=3,
                    alineado=WD_ALIGN_PARAGRAPH.LEFT)
        p.paragraph_format.keep_with_next = True
    t = doc.add_table(rows=1, cols=len(encabezado))
    _insertar(t._tbl)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    _bordes(t)
    for fila_datos, es_encabezado in [(encabezado, True)] + [(f, False) for f in filas]:
        fila = t.rows[0] if es_encabezado else t.add_row()
        for i, valor in enumerate(fila_datos):
            celda = fila.cells[i]
            celda.width = Cm(anchos_cm[i])
            fmt = celda.paragraphs[0].paragraph_format
            fmt.space_after = Pt(0)
            fmt.first_line_indent = Cm(0)
            fmt.left_indent = Cm(0)
            celda.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.LEFT
            run = celda.paragraphs[0].add_run(str(valor))
            run.font.name = FUENTE
            run.font.size = Pt(tam)
            if es_encabezado:
                run.bold = True
                run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
                _sombrear(celda, "1B3A6B")
            elif str(valor) in ("Aprobada", "PASSED"):
                run.font.color.rgb = RGBColor(0x1E, 0x7B, 0x34)
                run.bold = True
    grid = t._tbl.tblGrid
    for col, ancho in zip(grid.findall(qn("w:gridCol")), anchos_cm):
        col.set(qn("w:w"), str(int(Cm(ancho).twips)))
    # Repetir encabezado en cada página.
    trPr = t.rows[0]._tr.get_or_add_trPr()
    h = OxmlElement("w:tblHeader")
    h.set(qn("w:val"), "true")
    trPr.append(h)
    parrafo(espacio=6)
    return t


def indice():
    p = parrafo(alineado=WD_ALIGN_PARAGRAPH.LEFT)
    run = p.add_run()
    for tipo, texto in (("begin", None), (None, 'TOC \\o "1-2" \\h \\z \\u'), ("separate", None)):
        if tipo:
            f = OxmlElement("w:fldChar")
            f.set(qn("w:fldCharType"), tipo)
            run._r.append(f)
        else:
            instr = OxmlElement("w:instrText")
            instr.set(qn("xml:space"), "preserve")
            instr.text = texto
            run._r.append(instr)
    run2 = p.add_run("Actualice el índice (clic derecho → Actualizar campos).")
    run2.font.size = Pt(9)
    fin = OxmlElement("w:fldChar")
    fin.set(qn("w:fldCharType"), "end")
    p.add_run()._r.append(fin)


def leer(ruta):
    return (RAIZ / ruta).read_text(encoding="utf-8")


# ---------------------------------------------------------------- resultados JUnit
junit = ET.parse(EVID / "resultados_junit.xml").getroot()
casos = []
for tc in junit.iter("testcase"):
    estado = "Aprobada"
    if tc.find("failure") is not None or tc.find("error") is not None:
        estado = "Fallida"
    elif tc.find("skipped") is not None:
        estado = "Omitida"
    modulo = tc.get("classname").replace("tests.", "")
    casos.append((modulo, tc.get("name"), f"{float(tc.get('time')):.3f}", estado))
total = len(casos)
aprobadas = sum(1 for c in casos if c[3] == "Aprobada")


def contar(prefijo):
    return sum(1 for c in casos if c[0].startswith(prefijo))


N_UNIT, N_INT, N_FUN = contar("unit"), contar("integration"), contar("functional")
assert aprobadas == total, "Hay pruebas fallidas: revise evidencias/resultados_junit.xml"

# ================================================================ CONTENIDO
p = parrafo("Índice", negrita=True, tam=15, color=AZUL, alineado=WD_ALIGN_PARAGRAPH.LEFT, espacio=10)
p.paragraph_format.first_line_indent = Cm(0)
indice()
salto_pagina()

titulo("1. Introducción")
parrafo("El presente informe documenta la **Práctica 4 de la Unidad 4** de la asignatura Construcción "
        "de Software. Sobre el aplicativo web **VisionFace**, desarrollado con el framework Django y la "
        "biblioteca de visión por computadora OpenCV, se diseñaron y ejecutaron pruebas de calidad en "
        "tres niveles (unitarias, de integración y funcionales) y se elaboró la documentación técnica y "
        "de usuario del sistema.")
parrafo("VisionFace permite subir una imagen o un video, detecta los rostros presentes mediante un "
        "clasificador Haar en cascada, muestra el resultado marcado sobre la imagen y guarda un "
        "historial de los análisis. Las pruebas se automatizaron con pytest, pytest-django y Selenium, "
        "siguiendo el enfoque de automatización de pruebas y desarrollo incremental descrito por "
        "Pressman (2005).")
parrafo(f"Repositorio del código fuente: **{URL}**")

titulo("2. Objetivos")
titulo("2.1. Objetivo general", 2)
parrafo("Aplicar pruebas de calidad (unitarias, de integración y funcionales) al aplicativo web "
        "VisionFace y generar documentación técnica y de usuario que facilite la comprensión, el uso "
        "y el mantenimiento del sistema.")
titulo("2.2. Objetivos específicos", 2)
vineta("Diseñar y ejecutar pruebas unitarias sobre las funciones críticas del módulo de detección con OpenCV.")
vineta("Implementar pruebas de integración que validen el flujo de la aplicación a través de las rutas principales de Django.")
vineta("Validar con pruebas funcionales automatizadas los casos de uso clave: inicio, detección en imagen, detección en video y visualización en la interfaz.")
vineta("Documentar los requisitos, la instalación, la ejecución, la estructura del proyecto y el uso del sistema.")

titulo("3. Descripción del aplicativo")
parrafo("VisionFace es una aplicación web monolítica construida con Django 6.1 bajo el patrón "
        "Modelo-Vista-Plantilla (MVT). La lógica de visión por computadora está aislada en el módulo "
        "detector/vision.py, que no depende de Django; esto permite probarla de forma unitaria y "
        "reutilizarla desde las vistas web y desde la API JSON.")
tabla(["Componente", "Responsabilidad"], [
    ["detector/vision.py", "Decodificar imágenes, detectar rostros (Haar), dibujar recuadros, codificar en Base64 y procesar videos cuadro a cuadro."],
    ["detector/forms.py", "Validar la extensión y el tamaño máximo (50 MB) de los archivos subidos."],
    ["detector/views.py", "Vistas de inicio, imagen, video, historial y endpoint /api/detectar/."],
    ["detector/models.py", "Modelo Deteccion: tipo, archivo, número de rostros, cuadros analizados, tiempo y fecha."],
    ["detector/templates/", "Interfaz HTML (plantilla base, formularios, resultados e historial)."],
], [4.5, 11.5], "Componentes principales del sistema")

titulo("4. Sesión 1: pruebas unitarias y de integración")
titulo("4.1. Estrategia y herramientas", 2)
parrafo("Las pruebas se organizaron en la carpeta tests/ con un subdirectorio por nivel y se "
        "clasificaron con marcadores de pytest (unit, integration, functional), de modo que cada "
        "nivel puede ejecutarse por separado. Las imágenes de prueba son muestras oficiales del "
        "repositorio de OpenCV: messi5.jpg (un rostro frontal) y baboon.jpg (sin rostros humanos). "
        "Los videos de prueba se generan automáticamente en el fixture conftest.py a partir de esas "
        "imágenes, aplicando un pequeño desplazamiento por cuadro para simular movimiento de cámara.")
tabla(["Herramienta", "Versión", "Uso"], [
    ["pytest", "9.2.0", "Motor de pruebas, fixtures y parametrización"],
    ["pytest-django", "4.14.0", "Base de datos de prueba, cliente HTTP y servidor en vivo"],
    ["pytest-cov", "7.1.0", "Medición de cobertura de código"],
    ["Selenium", "4.53.0", "Automatización del navegador (Microsoft Edge, modo headless)"],
    ["OpenCV", "4.14.0", "Clasificador Haar haarcascade_frontalface_default.xml"],
], [3.5, 2.5, 10], "Herramientas utilizadas")

titulo("4.2. Pruebas unitarias", 2)
parrafo(f"Se implementaron **{N_UNIT} pruebas unitarias**. Se centran en las funciones críticas del "
        "módulo de detección con OpenCV y, de forma complementaria, en los formularios de validación y el modelo.")
tabla(["Función / clase", "Casos verificados"], [
    ["cargar_clasificador()", "El clasificador Haar se carga sin errores y se reutiliza (caché)."],
    ["decodificar_imagen()", "Decodifica JPG y PNG; rechaza bytes vacíos y datos corruptos."],
    ["detectar_rostros()", "Detecta 1 rostro en messi5.jpg, 0 en baboon.jpg y en imagen negra; acepta escala de grises; las cajas quedan dentro de la imagen; el tamaño mínimo filtra; rechaza imagen nula y escala ≤ 1."],
    ["dibujar_detecciones()", "No modifica la imagen original, dibuja el recuadro verde, devuelve copia si no hay rostros."],
    ["imagen_a_base64()", "Genera data URI JPEG (firma FF D8) y PNG válidos."],
    ["procesar_video()", "Video con rostros: 30 cuadros, 6 analizados (paso 5), 100 % con rostro. Video sin rostros: 0 %. Respeta el límite de cuadros; rechaza archivos inexistentes, no-video y parámetros inválidos."],
    ["ImagenForm / VideoForm", "Aceptan solo extensiones permitidas, exigen archivo y limitan el tamaño."],
    ["Modelo Deteccion", "Representación en texto y orden descendente por fecha."],
], [4.2, 11.8], "Cobertura funcional de las pruebas unitarias")
parrafo("Fragmento representativo (detección sobre la imagen de muestra y procesamiento de video):", espacio=3)
codigo('''def test_detecta_un_rostro(self, bytes_con_rostro):
    rostros = vision.detectar_rostros(vision.decodificar_imagen(bytes_con_rostro))
    assert len(rostros) == 1
    x, y, w, h = rostros[0]
    assert w >= 30 and h >= 30

def test_video_con_rostros(self, video_con_rostros):
    r = vision.procesar_video(video_con_rostros, max_cuadros=300, paso=5)
    assert r.cuadros_totales == 30
    assert r.cuadros_analizados == 6
    assert r.porcentaje_con_rostros == 100.0''')
figura(CAPT / "consola_unitarias.png", f"Ejecución de las pruebas unitarias: {N_UNIT} aprobadas (pytest -m unit).")

titulo("4.3. Pruebas de integración", 2)
parrafo(f"Se implementaron **{N_INT} pruebas de integración** con el cliente de pruebas de Django. "
        "Cada prueba recorre la cadena completa URL → vista → formulario → OpenCV → base de datos → "
        "plantilla, sin simular (mock) ninguno de sus componentes.")
tabla(["Prueba", "Flujo validado", "Resultado esperado"], [
    ["Rutas principales (x4)", "GET a /, /imagen/, /video/, /historial/", "HTTP 200 y plantilla correcta"],
    ["Ruta inexistente", "GET /no-existe/", "HTTP 404"],
    ["Flujo imagen con rostro", "POST /imagen/ con messi5.jpg", "1 rostro, imagen anotada y registro en BD"],
    ["Flujo imagen sin rostro", "POST /imagen/ con baboon.jpg", "0 rostros y mensaje informativo"],
    ["Imagen corrupta / extensión inválida", "POST con datos inválidos", "Mensaje de error, sin registro en BD"],
    ["Flujo video", "POST /video/ con video generado", "30 cuadros, máx. 1 rostro, registro tipo video"],
    ["Video inválido", "POST /video/ con datos no-video", "Error «No se pudo abrir el video»"],
    ["Historial e inicio", "Dos análisis y consulta posterior", "Ambos archivos listados; resumen 2 análisis / 1 rostro"],
    ["API JSON (x4)", "POST/GET /api/detectar/", "JSON con cajas; 405 en GET; 400 sin archivo o corrupto"],
], [4.2, 5.6, 6.2], "Casos de prueba de integración")
figura(CAPT / "consola_integracion.png", f"Ejecución de las pruebas de integración: {N_INT} aprobadas (pytest -m integration).")

titulo("4.4. Reporte inicial de resultados y cobertura", 2)
tabla(["Nivel", "Pruebas", "Aprobadas", "Fallidas"], [
    ["Unitarias", N_UNIT, N_UNIT, 0],
    ["Integración", N_INT, N_INT, 0],
    ["Funcionales", N_FUN, N_FUN, 0],
    ["Total", total, aprobadas, total - aprobadas],
], [5, 3.5, 3.5, 3.5], "Resumen de ejecución de la suite completa")
tabla(["Módulo", "Sentencias", "Sin cubrir", "Cobertura"], [
    ["detector/vision.py", 91, 4, "96 %"],
    ["detector/views.py", 69, 0, "100 %"],
    ["detector/forms.py", 20, 0, "100 %"],
    ["detector/models.py", 17, 0, "100 %"],
    ["Otros (admin, apps, urls, migraciones)", 19, 0, "100 %"],
    ["Total", 216, 4, "98 %"],
], [6.5, 3, 3, 3], "Cobertura de código (pytest-cov)")
parrafo("Las 4 líneas sin cubrir de vision.py corresponden a ramas defensivas que solo se ejecutan "
        "ante fallos internos de OpenCV (por ejemplo, que el archivo del clasificador no exista o que "
        "cv2.imencode falle), escenarios que no pueden provocarse con entradas normales.")
figura(CAPT / "consola_cobertura.png", "Suite completa con medición de cobertura: 68 pruebas aprobadas, 98 % de cobertura.")
parrafo("**Análisis.** Durante la primera ejecución fallaron 8 pruebas: el preprocesamiento con "
        "ecualización de histograma (cv2.equalizeHist) generaba un falso positivo en messi5.jpg "
        "(2 rostros en lugar de 1), y dos registros creados en el mismo instante no tenían un orden "
        "determinista. Se eliminó la ecualización y se añadió el identificador como criterio de "
        "desempate en el orden del modelo. Tras la corrección, la suite completa se ejecuta sin "
        "errores. Esto muestra el valor de las pruebas automatizadas: detectaron un defecto de "
        "precisión del detector que no era evidente en la interfaz.")
parrafo("Los logs completos se encuentran en el repositorio: evidencias/log_unit.txt, "
        "evidencias/log_integration.txt, evidencias/log_functional.txt, evidencias/reporte_pruebas.log "
        "y evidencias/resultados_junit.xml (formato JUnit).")

titulo("5. Sesión 2: pruebas funcionales")
parrafo(f"Se automatizaron **{N_FUN} casos de uso** con Selenium WebDriver sobre Microsoft Edge en modo "
        "headless. pytest-django levanta un servidor real (live_server) con una base de datos de "
        "prueba; el navegador interactúa con la interfaz como lo haría un usuario (clics, selección de "
        "archivos, lectura de resultados) y cada caso guarda una captura de pantalla como evidencia.")
tabla(["ID", "Caso de uso", "Pasos", "Resultado esperado", "Estado"], [
    ["CU01", "Inicio", "Abrir la URL raíz", "Título, encabezado y contador en 0", "Aprobada"],
    ["CU02", "Navegación", "Usar botones y menú", "Cada enlace lleva a su ruta", "Aprobada"],
    ["CU03", "Detección en imagen", "Subir messi5.jpg y analizar", "1 rostro, imagen anotada, tabla de coordenadas", "Aprobada"],
    ["CU04", "Imagen sin rostros", "Subir baboon.jpg", "0 rostros y mensaje informativo", "Aprobada"],
    ["CU05", "Detección en video", "Subir video y procesar", "6 cuadros analizados, 6 con rostro, cuadro destacado", "Aprobada"],
    ["CU06", "Archivo no permitido", "Subir un .txt", "Mensaje «Formato no permitido»", "Aprobada"],
    ["CU07", "Historial", "Analizar y abrir historial", "Registro listado; contador de inicio ≥ 1", "Aprobada"],
], [1.2, 2.8, 3.4, 6.4, 2.2], "Casos de prueba funcionales")
figura(CAPT / "consola_funcionales.png", f"Ejecución de las pruebas funcionales: {N_FUN} aprobadas (pytest -m functional).")
figura(CAPT / "cu03b_resultado_imagen.png", "CU03: detección de un rostro en imagen, capturada por Selenium.", 14)
figura(CAPT / "cu05_resultado_video.png", "CU05: resumen de la detección en video, capturado por Selenium.", 12)
figura(CAPT / "cu06_error_formato.png", "CU06: validación de un archivo con formato no permitido.", 12)

# ---------------------------------------------------------------- sesión 3
titulo("6. Sesión 3: documentación técnica")
titulo("6.1. Requisitos", 2)
titulo("Requisitos funcionales", 3)
tabla(["ID", "Requisito"], [
    ["RF01", "El sistema permite subir una imagen (JPG, PNG, BMP, WEBP) y detecta los rostros presentes."],
    ["RF02", "El sistema muestra la imagen original y la imagen con los rostros enmarcados, junto con sus coordenadas."],
    ["RF03", "El sistema permite subir un video (MP4, AVI, MOV, MKV, WEBM) y analiza un cuadro de cada cinco (máx. 300 cuadros)."],
    ["RF04", "El sistema muestra el resumen del video y el cuadro con más rostros detectados."],
    ["RF05", "El sistema registra cada análisis y lo muestra en el historial y en el resumen de inicio."],
    ["RF06", "El sistema expone una API JSON (POST /api/detectar/) para la detección en imágenes."],
    ["RF07", "El sistema rechaza archivos con formato no permitido, corruptos o mayores a 50 MB con un mensaje claro."],
], [1.5, 14.5], "Requisitos funcionales")
titulo("Requisitos no funcionales y de software", 3)
tabla(["Elemento", "Detalle"], [
    ["Sistema operativo", "Windows 10/11, Linux o macOS"],
    ["Lenguaje", "Python 3.12 o superior"],
    ["Framework web", "Django 6.1.3"],
    ["Visión por computadora", "opencv-python-headless 4.14.0.94 y NumPy 2.x (la serie 5.x de OpenCV ya no incluye los clasificadores Haar)"],
    ["Base de datos", "SQLite 3 (incluida en Python)"],
    ["Pruebas", "pytest 9.2, pytest-django 4.14, pytest-cov 7.1, Selenium 4.53 y Microsoft Edge"],
    ["Hardware mínimo", "CPU de 2 núcleos, 4 GB de RAM, 500 MB libres en disco"],
], [4, 12], "Requisitos de software y hardware")

titulo("6.2. Instalación", 2)
vineta("Clonar el repositorio y entrar en la carpeta del proyecto.")
vineta("Crear y activar un entorno virtual de Python.")
vineta("Instalar las dependencias y crear la base de datos.")
codigo(f'''git clone {URL}.git
cd {URL.rstrip("/").split("/")[-1]}
python -m venv .venv
.\\.venv\\Scripts\\activate        # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate''', 9)

titulo("6.3. Ejecución", 2)
codigo('''python manage.py runserver
# Abrir en el navegador: http://127.0.0.1:8000/''', 9)
tabla(["Ruta", "Descripción"], [
    ["/", "Inicio: resumen de análisis y últimos registros"],
    ["/imagen/", "Formulario de detección en imágenes"],
    ["/video/", "Formulario de detección en videos"],
    ["/historial/", "Historial de análisis (últimos 100)"],
    ["/api/detectar/", "API JSON, método POST, campo «archivo»"],
    ["/admin/", "Administración de Django (requiere python manage.py createsuperuser)"],
], [3.5, 12.5], "Rutas del sistema")
parrafo("Ejecución de las pruebas:", espacio=3)
codigo('''pytest                  # suite completa (68 pruebas)
pytest -m unit          # unitarias
pytest -m integration   # integración
pytest -m functional    # funcionales con Selenium (guarda capturas en evidencias/capturas)
pytest --cov=detector --cov-report=term-missing   # cobertura''', 9)

titulo("6.4. Estructura de directorios", 2)
codigo('''visionface/
├── config/                   # Configuración Django (settings.py, urls.py, wsgi.py, asgi.py)
├── detector/                 # Aplicación principal
│   ├── vision.py             # Núcleo OpenCV (detección de rostros)
│   ├── views.py              # Vistas web y API
│   ├── forms.py              # Validación de archivos
│   ├── models.py             # Modelo Deteccion
│   ├── urls.py               # Rutas de la aplicación
│   ├── admin.py              # Registro en el panel de administración
│   ├── migrations/           # Migraciones de base de datos
│   ├── templates/detector/   # base, inicio, imagen, video, historial, _tabla
│   └── static/detector/      # estilos.css
├── tests/
│   ├── conftest.py           # Fixtures compartidas (imágenes y videos)
│   ├── fixtures/             # messi5.jpg, baboon.jpg
│   ├── unit/                 # test_vision.py, test_forms_modelos.py
│   ├── integration/          # test_rutas_y_flujo.py
│   └── functional/           # test_casos_de_uso.py
├── evidencias/               # Logs, JUnit XML y capturas
├── docs/                     # Informe (PDF/DOCX) y su generador
├── manage.py
├── pytest.ini
├── requirements.txt
└── README.md''', 8.5)

titulo("6.5. Funcionamiento interno de la detección", 2)
parrafo("El clasificador Haar en cascada recorre la imagen en escala de grises con ventanas de "
        "distintos tamaños. Se usan los parámetros scaleFactor = 1.1 (cada escala es 10 % mayor), "
        "minNeighbors = 5 (una región debe confirmarse en 5 ventanas vecinas para aceptarse como "
        "rostro, lo que reduce los falsos positivos) y minSize = 30 × 30 píxeles. En los videos se "
        "analiza un cuadro de cada cinco para equilibrar precisión y tiempo de respuesta.")

titulo("6.6. Pruebas realizadas", 2)
parrafo(f"Se ejecutaron **{total} pruebas automatizadas** ({N_UNIT} unitarias, {N_INT} de integración "
        f"y {N_FUN} funcionales) con **{aprobadas} aprobadas y {total - aprobadas} fallidas**, y una "
        "cobertura de código del 98 %. El detalle de cada prueba está en el Anexo A y su código "
        "fuente completo en el Anexo B.")

# ---------------------------------------------------------------- manual de usuario
titulo("7. Documentación de usuario")
titulo("7.1. Pantalla de inicio", 2)
parrafo("Al abrir la aplicación se muestra la pantalla de inicio con dos accesos directos "
        "(**Analizar imagen** y **Analizar video**), los contadores de análisis realizados y de "
        "rostros detectados, y la tabla de los últimos cinco análisis. La barra superior permite "
        "navegar en todo momento a Inicio, Imagen, Video e Historial.")
figura(CAPT / "cu01_inicio.png", "Pantalla de inicio sin análisis previos.", 14)

titulo("7.2. Detectar rostros en una imagen", 2)
vineta("Pulse **Analizar imagen** o la opción **Imagen** del menú.")
vineta("Pulse **Elegir archivo** y seleccione una fotografía (JPG, PNG, BMP o WEBP de hasta 50 MB).")
vineta("Pulse **Detectar rostros** y espere el resultado.")
figura(CAPT / "cu03a_formulario_imagen.png", "Formulario de carga de imágenes.", 12)
parrafo("**Explicación de resultados.** El sistema indica cuántos rostros encontró, el nombre del "
        "archivo, sus dimensiones y el tiempo de procesamiento. A la izquierda se muestra la imagen "
        "original y a la derecha la misma imagen con cada rostro enmarcado en verde y numerado "
        "(#1, #2…). La tabla inferior indica la posición (X, Y) de la esquina superior izquierda de "
        "cada recuadro y su ancho y alto en píxeles.")
figura(CAPT / "cu03b_resultado_imagen.png", "Resultado de la detección: un rostro encontrado y enmarcado.", 14)
parrafo("Si la imagen no contiene rostros frontales, el contador muestra 0 y aparece el mensaje "
        "«No se encontraron rostros frontales en la imagen». El detector está entrenado para "
        "rostros de frente; los perfiles, rostros muy pequeños (menos de 30 px) o muy inclinados "
        "pueden no detectarse.")
figura(CAPT / "cu04_imagen_sin_rostros.png", "Imagen sin rostros humanos: el sistema informa 0 detecciones.", 11)

titulo("7.3. Detectar rostros en un video", 2)
vineta("Pulse **Analizar video** o la opción **Video** del menú.")
vineta("Seleccione un video (MP4, AVI, MOV, MKV o WEBM de hasta 50 MB) y pulse **Procesar video**.")
vineta("Espere a que termine el análisis; el tiempo depende de la duración y la resolución del video.")
parrafo("**Explicación de resultados.** Tres tarjetas resumen el análisis: los cuadros analizados "
        "frente al total leído, cuántos de ellos contienen al menos un rostro (y su porcentaje) y el "
        "máximo de rostros detectados en un mismo cuadro. Debajo se muestra el cuadro con más rostros "
        "ya enmarcado y, al desplegar **Detecciones por cuadro**, el número de rostros de cada cuadro "
        "analizado.")
figura(CAPT / "cu05_resultado_video.png", "Resultado del análisis de un video.", 12)

titulo("7.4. Historial", 2)
parrafo("La opción **Historial** lista los últimos 100 análisis con su fecha, tipo (imagen o "
        "video), nombre del archivo, rostros detectados, cuadros analizados y tiempo de "
        "procesamiento. Los contadores de la pantalla de inicio se actualizan automáticamente.")
figura(CAPT / "cu07a_historial.png", "Historial de análisis.", 13)
figura(CAPT / "cu07b_inicio_con_datos.png", "Pantalla de inicio con análisis registrados.", 13)

titulo("7.5. Mensajes de error", 2)
tabla(["Mensaje", "Causa", "Solución"], [
    ["Formato no permitido", "La extensión del archivo no es de imagen o video admitida", "Convertir el archivo a un formato admitido"],
    ["El archivo no es una imagen válida", "Archivo dañado o con extensión incorrecta", "Abrir la imagen en otro programa y guardarla de nuevo"],
    ["No se pudo abrir el video", "Video dañado o con un códec no soportado", "Convertir a MP4 (H.264) o AVI"],
    ["El archivo supera 50 MB", "Tamaño mayor al límite configurado", "Reducir la resolución o recortar el video"],
], [4.3, 5.7, 6], "Mensajes de error y soluciones")

# ---------------------------------------------------------------- cierre
titulo("8. Conclusiones")
vineta(f"Se implementaron y ejecutaron {total} pruebas automatizadas en los tres niveles solicitados, todas aprobadas, con una cobertura del 98 % del código de la aplicación.")
vineta("Aislar la lógica de OpenCV en un módulo independiente de Django facilitó las pruebas unitarias y permitió reutilizarla en las vistas web y en la API.")
vineta("Las pruebas detectaron un falso positivo causado por la ecualización de histograma, que se corrigió antes de la entrega; sin pruebas automatizadas este defecto habría pasado inadvertido.")
vineta("Las pruebas funcionales con Selenium generan sus propias capturas, de modo que la evidencia se reproduce con un solo comando y la documentación de usuario se mantiene actualizada.")
titulo("9. Recomendaciones")
vineta("Ejecutar pytest antes de cada commit e integrarlo en un flujo de integración continua (por ejemplo, GitHub Actions).")
vineta("Evaluar detectores basados en redes neuronales (por ejemplo, el módulo DNN de OpenCV) para mejorar la detección de rostros de perfil o muy pequeños.")
vineta("Procesar los videos largos en segundo plano (por ejemplo, con Celery) para no bloquear la petición web.")
titulo("10. Referencias bibliográficas")
for ref in [
    "Pressman, R. S. (2005). Ingeniería del software: un enfoque práctico (6.ª ed.). McGraw-Hill.",
    "Django Software Foundation. (2026). Django documentation: Testing tools. https://docs.djangoproject.com/en/stable/topics/testing/",
    "OpenCV. (2026). Cascade Classifier. https://docs.opencv.org/4.x/db/d28/tutorial_cascade_classifier.html",
    "pytest-dev. (2026). pytest documentation. https://docs.pytest.org/",
    "Selenium Project. (2026). Selenium WebDriver documentation. https://www.selenium.dev/documentation/webdriver/",
    "Viola, P., & Jones, M. (2001). Rapid object detection using a boosted cascade of simple features. Proceedings of IEEE CVPR, 1, 511–518.",
]:
    p = parrafo(ref, alineado=WD_ALIGN_PARAGRAPH.LEFT, espacio=4)
    p.paragraph_format.left_indent = Cm(1)
    p.paragraph_format.first_line_indent = Cm(-1)

# ---------------------------------------------------------------- anexos
salto_pagina()
titulo("Anexo A. Detalle de ejecución de las pruebas")
parrafo("Generado a partir de evidencias/resultados_junit.xml.", tam=9, cursiva=True)
tabla(["Módulo", "Prueba", "Tiempo (s)", "Estado"],
      [[m.replace("test_", "").replace(".py", ""), n, t, e] for m, n, t, e in casos],
      [4.2, 8.3, 1.7, 1.8], "Resultado individual de las pruebas", tam=7)

titulo("Anexo B. Código fuente de las pruebas")
for archivo in ["tests/conftest.py", "tests/unit/test_vision.py", "tests/unit/test_forms_modelos.py",
                "tests/integration/test_rutas_y_flujo.py", "tests/functional/test_casos_de_uso.py",
                "pytest.ini"]:
    titulo(archivo, 2)
    codigo(leer(archivo), 7)

titulo("Anexo C. Módulo de detección (detector/vision.py)")
codigo(leer("detector/vision.py"), 7)

doc.save(salida)
print("Informe generado:", salida, f"({total} pruebas, {aprobadas} aprobadas)")
