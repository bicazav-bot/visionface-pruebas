"""Genera el informe final (DOCX) sobre la plantilla institucional UNEMI.

Uso:  python docs/generar_informe.py <plantilla.docx> <salida.docx> <url_github>
Requiere: python-docx
"""
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from docx import Document
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
    falla = tc.find("failure") is not None or tc.find("error") is not None
    archivo = tc.get("classname").split(".")[-1]
    casos.append((archivo, tc.get("name"), f"{float(tc.get('time')):.2f}", "Fallida" if falla else "Aprobada"))
total = len(casos)
aprobadas = sum(1 for c in casos if c[3] == "Aprobada")
N_UNIT = sum(1 for c in casos if c[0] == "test_unitarias")
N_INT = sum(1 for c in casos if c[0] == "test_integracion")
N_FUN = sum(1 for c in casos if c[0] == "test_funcionales")
assert aprobadas == total, "Hay pruebas fallidas"
COBERTURA = "94 %"

# ================================================================ CONTENIDO
p = parrafo("Índice", negrita=True, tam=15, color=AZUL, alineado=WD_ALIGN_PARAGRAPH.LEFT, espacio=10)
indice()
salto_pagina()

titulo("1. Introducción")
parrafo("En esta práctica se probó y documentó **VisionFace**, una aplicación web hecha con Django y "
        "OpenCV que detecta rostros en imágenes y videos. Se hicieron pruebas unitarias, de integración "
        "y funcionales con pytest y Selenium, y se escribió la documentación técnica y de usuario.")
parrafo(f"Repositorio en GitHub: **{URL}**")

titulo("2. Objetivos")
titulo("2.1. Objetivo general", 2)
parrafo("Aplicar pruebas de calidad (unitarias, de integración y funcionales) al aplicativo web y "
        "generar documentación técnica y de usuario que facilite su uso y mantenimiento.")
titulo("2.2. Objetivos específicos", 2)
vineta("Probar las funciones de detección con OpenCV por separado (pruebas unitarias).")
vineta("Probar que las rutas de Django funcionan junto con OpenCV y la base de datos (pruebas de integración).")
vineta("Probar los casos de uso desde un navegador real (pruebas funcionales).")
vineta("Documentar la instalación, la ejecución y el uso del sistema.")

titulo("3. Descripción del aplicativo")
parrafo("El usuario sube una foto o un video; el sistema busca rostros con el clasificador Haar de "
        "OpenCV, los marca con un recuadro verde y guarda el resultado en un historial. El código "
        "está dividido en pocos archivos:")
tabla(["Archivo", "Qué hace"], [
    ["detector/vision.py", "Funciones de OpenCV: leer la imagen, detectar rostros, dibujar recuadros y analizar videos."],
    ["detector/views.py", "Páginas de inicio, imagen y video, el botón para borrar el historial y la API /api/detectar/."],
    ["detector/models.py", "Tabla Deteccion: tipo, archivo, número de rostros y fecha."],
    ["detector/templates/", "Páginas HTML que ve el usuario."],
], [4.5, 11.5], "Archivos principales")
parrafo("**Corrección realizada.** Al probar con una foto de 4096 × 4074 píxeles (causa.jpeg) el "
        "sistema marcaba 3 rostros que no existían: en imágenes tan grandes el detector confunde "
        "manchas pequeñas con caras. Se corrigió reduciendo la imagen a un máximo de 800 píxeles "
        "antes de buscar rostros y volviendo a escalar las coordenadas al tamaño original. Ahora esa "
        "foto da 0 rostros y la foto de prueba con una persona sigue dando 1. Se agregó una prueba "
        "para que este error no vuelva a aparecer.")
codigo('''TAMANO_MAXIMO = 800

def detectar_rostros(imagen):
    alto, ancho = imagen.shape[:2]
    escala = min(1, TAMANO_MAXIMO / max(alto, ancho))
    pequena = cv2.resize(imagen, None, fx=escala, fy=escala)
    gris = cv2.cvtColor(pequena, cv2.COLOR_BGR2GRAY)
    rostros = clasificador.detectMultiScale(gris, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
    return [[int(valor / escala) for valor in rostro] for rostro in rostros]''', 8)

# ---------------------------------------------------------------- sesión 1
titulo("4. Sesión 1: pruebas unitarias y de integración")
parrafo("Herramientas: **pytest** (ejecuta las pruebas), **pytest-django** (base de datos de prueba "
        "y cliente web), **pytest-cov** (cobertura) y **Selenium** (navegador automático). Las imágenes "
        "de prueba son messi5.jpg (1 rostro), baboon.jpg (sin rostros) y causa.jpeg (foto grande sin "
        "rostros). El video de prueba se crea automáticamente con 30 cuadros de messi5.jpg.")

titulo("4.1. Pruebas unitarias", 2)
parrafo(f"Archivo tests/test_unitarias.py: **{N_UNIT} pruebas** sobre las funciones de vision.py.")
tabla(["Prueba", "Qué comprueba"], [
    ["test_leer_imagen_valida", "Una foto JPG se lee con su tamaño correcto (342 × 548)."],
    ["test_leer_imagen_vacia / test_leer_archivo_que_no_es_imagen", "Un archivo vacío o de texto produce un error."],
    ["test_detecta_un_rostro", "En messi5.jpg encuentra exactamente 1 rostro."],
    ["test_no_detecta_rostros_en_mandril", "En baboon.jpg no encuentra rostros."],
    ["test_foto_grande_sin_falsos_positivos", "En causa.jpeg (4096 px) no encuentra rostros falsos."],
    ["test_imagen_negra_sin_rostros", "Una imagen negra no tiene rostros."],
    ["test_dibujar_no_cambia_la_original", "El recuadro se dibuja en una copia."],
    ["test_imagen_a_texto", "La imagen se convierte a base64 para mostrarla en la web."],
    ["test_analizar_video", "Video de 30 cuadros: analiza 6 y encuentra 1 rostro en cada uno."],
    ["test_video_que_no_existe", "Un video inexistente produce un error."],
], [7, 9], "Pruebas unitarias")
figura(CAPT / "consola_unitarias.png", f"Resultado de las pruebas unitarias: {N_UNIT} aprobadas.")

titulo("4.2. Pruebas de integración", 2)
parrafo(f"Archivo tests/test_integracion.py: **{N_INT} pruebas** que envían peticiones a las rutas de "
        "Django y verifican la respuesta y lo guardado en la base de datos.")
tabla(["Prueba", "Qué comprueba"], [
    ["test_rutas_principales", "/, /imagen/ y /video/ responden 200."],
    ["test_ruta_inexistente", "Una ruta que no existe responde 404."],
    ["test_subir_imagen_con_rostro", "Subir messi5.jpg muestra 1 rostro y lo guarda en el historial."],
    ["test_subir_imagen_grande_sin_rostros", "Subir causa.jpeg muestra «No se encontraron rostros»."],
    ["test_subir_archivo_no_permitido", "Un .txt muestra «Formato no permitido» y no se guarda."],
    ["test_subir_video", "Subir un video devuelve el resumen y lo guarda como tipo Video."],
    ["test_inicio_muestra_los_analisis", "El análisis aparece en «Últimos análisis» del inicio."],
    ["test_borrar_historial", "El botón Borrar historial elimina todos los análisis y vuelve al inicio."],
    ["test_borrar_con_get_no_borra", "Abrir /borrar/ sin pulsar el botón no borra nada."],
    ["test_api_detectar", "La API devuelve JSON con 1 rostro."],
    ["test_api_sin_archivo", "La API responde 400 sin archivo y 405 con GET."],
], [6, 10], "Pruebas de integración")
parrafo("Ejemplo de prueba de integración:", espacio=3)
codigo('''def test_subir_imagen_con_rostro(client, foto_con_rostro):
    with open(foto_con_rostro, "rb") as archivo:
        respuesta = client.post("/imagen/", {"archivo": archivo})
    assert len(respuesta.context["rostros"]) == 1
    assert Deteccion.objects.get().rostros == 1''', 8)
figura(CAPT / "consola_integracion.png", f"Resultado de las pruebas de integración: {N_INT} aprobadas.")

titulo("4.3. Reporte de resultados", 2)
tabla(["Tipo de prueba", "Cantidad", "Aprobadas", "Fallidas"], [
    ["Unitarias", N_UNIT, N_UNIT, 0],
    ["Integración", N_INT, N_INT, 0],
    ["Funcionales", N_FUN, N_FUN, 0],
    ["Total", total, aprobadas, total - aprobadas],
], [5, 3.5, 3.5, 3.5], "Resumen de resultados")
parrafo(f"La cobertura de código es del **{COBERTURA}**; vision.py, el módulo de detección, está "
        "cubierto al 100 %. Los logs completos están en la carpeta evidencias/ del repositorio.")
figura(CAPT / "consola_cobertura.png", f"Ejecución de todas las pruebas con cobertura ({COBERTURA}).")

# ---------------------------------------------------------------- sesión 2
titulo("5. Sesión 2: pruebas funcionales")
parrafo(f"Archivo tests/test_funcionales.py: **{N_FUN} casos de uso** probados con Selenium. Un "
        "navegador Microsoft Edge abre la aplicación, sube los archivos, lee el resultado en pantalla "
        "y guarda una captura.")
tabla(["Caso", "Pasos", "Resultado esperado", "Estado"], [
    ["CU1 Inicio", "Abrir la página principal", "Se ve el título y el contador en 0", "Aprobada"],
    ["CU2 Imagen con rostro", "Subir messi5.jpg", "Muestra 1 rostro marcado", "Aprobada"],
    ["CU3 Imagen sin rostros", "Subir causa.jpeg", "Muestra 0 rostros y el aviso", "Aprobada"],
    ["CU4 Video", "Subir un video de 30 cuadros", "6 cuadros analizados, 1 rostro", "Aprobada"],
    ["CU5 Borrar historial", "Analizar una imagen, pulsar Borrar historial y confirmar", "La tabla queda vacía y el contador en 0", "Aprobada"],
], [3.4, 4.3, 5.8, 2.5], "Casos de prueba funcionales")
figura(CAPT / "consola_funcionales.png", f"Resultado de las pruebas funcionales: {N_FUN} aprobadas.")
figura(CAPT / "cu2_imagen_con_rostro.png", "CU2: rostro detectado en una imagen (captura de Selenium).", 13)
figura(CAPT / "cu3_imagen_sin_rostros.png", "CU3: la foto grande ya no da falsos positivos (captura de Selenium).", 13)

# ---------------------------------------------------------------- sesión 3
titulo("6. Sesión 3: documentación técnica")
titulo("6.1. Requisitos", 2)
tabla(["Elemento", "Detalle"], [
    ["Sistema operativo", "Windows 10/11, Linux o macOS"],
    ["Python", "3.12 o superior"],
    ["Librerías", "Django 6.1, opencv-python-headless 4.14, NumPy 2"],
    ["Pruebas", "pytest, pytest-django, pytest-cov, Selenium y Microsoft Edge"],
], [4, 12], "Requisitos")
titulo("6.2. Instalación", 2)
codigo(f'''git clone {URL}.git
cd {URL.rstrip("/").split("/")[-1]}
python -m venv .venv
.\\.venv\\Scripts\\activate
pip install -r requirements.txt
python manage.py migrate''', 9)
titulo("6.3. Ejecución", 2)
codigo('''python manage.py runserver
# Abrir en el navegador: http://127.0.0.1:8000/

pytest                              # todas las pruebas
pytest tests/test_unitarias.py      # solo unitarias
pytest tests/test_integracion.py    # solo integración
pytest tests/test_funcionales.py    # solo funcionales
pytest --cov=detector               # con cobertura''', 9)
titulo("6.4. Estructura de directorios", 2)
codigo('''visionface-pruebas/
├── config/            # configuración de Django
├── detector/          # aplicación
│   ├── vision.py      # detección con OpenCV
│   ├── views.py       # páginas y API
│   ├── models.py      # tabla Deteccion
│   ├── urls.py        # rutas
│   ├── templates/     # páginas HTML
│   └── static/        # estilos CSS
├── tests/             # pruebas
│   ├── conftest.py
│   ├── test_unitarias.py
│   ├── test_integracion.py
│   ├── test_funcionales.py
│   └── fixtures/      # imágenes de prueba
├── evidencias/        # logs y capturas
├── docs/              # informe
├── manage.py
└── requirements.txt''', 9)
titulo("6.5. Pruebas realizadas", 2)
parrafo(f"Se ejecutaron **{total} pruebas** ({N_UNIT} unitarias, {N_INT} de integración y {N_FUN} "
        f"funcionales): {aprobadas} aprobadas y {total - aprobadas} fallidas. La cobertura es del "
        f"{COBERTURA}. El detalle está en el Anexo A y el código en el Anexo B.")

# ---------------------------------------------------------------- usuario
titulo("7. Documentación de usuario")
titulo("7.1. Inicio", 2)
parrafo("La página de inicio muestra dos botones (**Analizar imagen** y **Analizar video**), el total "
        "de análisis, el total de rostros detectados y la tabla de últimos análisis. El menú superior lleva a "
        "Inicio, Imagen y Video.")
figura(CAPT / "cu1_inicio.png", "Página de inicio.", 13)
titulo("7.2. Analizar una imagen", 2)
vineta("Entrar en **Imagen**.")
vineta("Pulsar **Elegir archivo** y escoger una foto (JPG, PNG, BMP o WEBP).")
vineta("Pulsar **Detectar rostros**.")
parrafo("**Resultado:** se muestra cuántos rostros se encontraron, la foto original y la foto con cada "
        "rostro marcado en verde. La tabla indica la posición (X, Y) y el tamaño (ancho y alto) de cada "
        "rostro en píxeles. Si no hay rostros aparece el mensaje «No se encontraron rostros en la imagen».")
figura(CAPT / "cu2_imagen_con_rostro.png", "Resultado con un rostro detectado.", 13)
titulo("7.3. Analizar un video", 2)
vineta("Entrar en **Video**.")
vineta("Escoger un video (MP4, AVI, MOV, MKV o WEBM) y pulsar **Procesar video**.")
parrafo("**Resultado:** se muestran los cuadros analizados (uno de cada cinco), cuántos tienen rostros, "
        "el máximo de rostros en un mismo cuadro y la imagen del cuadro con más rostros.")
figura(CAPT / "cu4_video.png", "Resultado del análisis de un video.", 12)
titulo("7.4. Últimos análisis y borrar historial", 2)
parrafo("En la página de inicio, bajo **Últimos análisis**, aparecen todos los análisis con su fecha, tipo, archivo y número de rostros. Para vaciar la lista, pulse **Borrar historial** y confirme con **Aceptar**; los contadores vuelven a 0.")
figura(CAPT / "cu5a_ultimos_analisis.png", "Últimos análisis con el botón Borrar historial.", 13)
figura(CAPT / "cu5b_historial_borrado.png", "Inicio después de borrar el historial.", 13)
titulo("7.5. Mensajes de error", 2)
tabla(["Mensaje", "Qué hacer"], [
    ["Formato no permitido", "Subir un archivo de imagen o video con una extensión aceptada."],
    ["El archivo no es una imagen válida", "La imagen está dañada; guardarla de nuevo o usar otra."],
    ["No se pudo abrir el video", "Convertir el video a MP4 o AVI."],
], [5.5, 10.5], "Mensajes de error")

# ---------------------------------------------------------------- cierre
titulo("8. Conclusiones")
vineta(f"Se hicieron {total} pruebas automáticas de los tres tipos pedidos y todas pasan.")
vineta("Las pruebas con una foto real de alta resolución revelaron falsos positivos; reducir la imagen antes de detectar los eliminó.")
vineta("Separar las funciones de OpenCV en vision.py hizo que fueran fáciles de probar.")
vineta("Las pruebas con Selenium generan las capturas automáticamente, lo que sirve como evidencia.")
titulo("9. Recomendaciones")
vineta("Ejecutar pytest antes de subir cambios a GitHub.")
vineta("Para rostros de perfil o muy pequeños, probar detectores más modernos (módulo DNN de OpenCV).")
titulo("10. Referencias bibliográficas")
for ref in [
    "Pressman, R. S. (2005). Ingeniería del software: un enfoque práctico. McGraw-Hill.",
    "Django Software Foundation. (2026). Testing tools. https://docs.djangoproject.com/en/stable/topics/testing/",
    "OpenCV. (2026). Cascade Classifier. https://docs.opencv.org/4.x/db/d28/tutorial_cascade_classifier.html",
    "pytest-dev. (2026). pytest documentation. https://docs.pytest.org/",
    "Selenium Project. (2026). WebDriver. https://www.selenium.dev/documentation/webdriver/",
]:
    p = parrafo(ref, alineado=WD_ALIGN_PARAGRAPH.LEFT, espacio=4)
    p.paragraph_format.left_indent = Cm(1)
    p.paragraph_format.first_line_indent = Cm(-1)

# ---------------------------------------------------------------- anexos
salto_pagina()
titulo("Anexo A. Resultado de cada prueba")
tabla(["Archivo", "Prueba", "Tiempo (s)", "Estado"],
      [list(c) for c in casos], [3.6, 8.6, 1.9, 1.9], "Resultado individual (evidencias/resultados_junit.xml)", tam=8)
titulo("Anexo B. Código de las pruebas")
for archivo in ["tests/conftest.py", "tests/test_unitarias.py", "tests/test_integracion.py",
                "tests/test_funcionales.py"]:
    titulo(archivo, 2)
    codigo(leer(archivo), 7.5)
titulo("Anexo C. Código de detección (detector/vision.py)")
codigo(leer("detector/vision.py"), 7.5)

doc.save(salida)
print("Informe generado:", salida, f"({total} pruebas, {aprobadas} aprobadas)")
