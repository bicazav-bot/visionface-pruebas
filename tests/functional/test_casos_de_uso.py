"""Pruebas funcionales (end-to-end) con Selenium sobre el servidor en vivo.

Casos de uso clave: inicio, detección en imagen, detección en video,
visualización de resultados en la interfaz e historial.
Cada prueba guarda una captura de pantalla en evidencias/capturas/.
"""
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

pytestmark = [pytest.mark.functional, pytest.mark.django_db(transaction=True)]


@pytest.fixture(scope="module")
def navegador():
    opciones = webdriver.EdgeOptions()
    opciones.add_argument("--headless=new")
    opciones.add_argument("--window-size=1280,1000")
    opciones.add_argument("--lang=es")
    driver = webdriver.Edge(options=opciones)
    driver.implicitly_wait(5)
    yield driver
    driver.quit()


def _captura(driver, carpeta, nombre):
    alto = driver.execute_script("return document.body.scrollHeight")
    driver.set_window_size(1280, max(alto + 40, 700))
    driver.save_screenshot(str(carpeta / f"{nombre}.png"))
    driver.set_window_size(1280, 1000)


def _esperar_resultado(driver):
    WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.ID, "resultado")))


def test_cu01_pagina_de_inicio(navegador, live_server, carpeta_capturas):
    navegador.get(live_server.url)
    assert "VisionFace" in navegador.title
    assert navegador.find_element(By.TAG_NAME, "h1").text == "Detección de rostros con OpenCV"
    assert navegador.find_element(By.ID, "total-analisis").text == "0"
    assert navegador.find_element(By.ID, "sin-registros").is_displayed()
    _captura(navegador, carpeta_capturas, "cu01_inicio")


def test_cu02_navegacion_menu(navegador, live_server):
    navegador.get(live_server.url)
    navegador.find_element(By.ID, "btn-imagen").click()
    assert navegador.current_url.endswith("/imagen/")
    navegador.find_element(By.ID, "nav-video").click()
    assert navegador.current_url.endswith("/video/")
    navegador.find_element(By.ID, "nav-historial").click()
    assert navegador.current_url.endswith("/historial/")
    navegador.find_element(By.ID, "logo").click()
    assert navegador.current_url.rstrip("/") == live_server.url


def test_cu03_deteccion_en_imagen(navegador, live_server, ruta_con_rostro, carpeta_capturas):
    navegador.get(live_server.url + "/imagen/")
    _captura(navegador, carpeta_capturas, "cu03a_formulario_imagen")
    navegador.find_element(By.ID, "id_archivo").send_keys(str(ruta_con_rostro))
    navegador.find_element(By.ID, "btn-analizar").click()
    _esperar_resultado(navegador)
    assert navegador.find_element(By.ID, "num-rostros").text == "1"
    imagen = navegador.find_element(By.ID, "img-anotada")
    assert navegador.execute_script("return arguments[0].naturalWidth", imagen) == 548
    filas = navegador.find_elements(By.CSS_SELECTOR, "#tabla-cajas tbody tr")
    assert len(filas) == 1
    _captura(navegador, carpeta_capturas, "cu03b_resultado_imagen")


def test_cu04_imagen_sin_rostros(navegador, live_server, ruta_sin_rostro, carpeta_capturas):
    navegador.get(live_server.url + "/imagen/")
    navegador.find_element(By.ID, "id_archivo").send_keys(str(ruta_sin_rostro))
    navegador.find_element(By.ID, "btn-analizar").click()
    _esperar_resultado(navegador)
    assert navegador.find_element(By.ID, "num-rostros").text == "0"
    assert navegador.find_element(By.ID, "sin-rostros").is_displayed()
    _captura(navegador, carpeta_capturas, "cu04_imagen_sin_rostros")


def test_cu05_deteccion_en_video(navegador, live_server, video_con_rostros, carpeta_capturas):
    navegador.get(live_server.url + "/video/")
    navegador.find_element(By.ID, "id_archivo").send_keys(str(video_con_rostros))
    navegador.find_element(By.ID, "btn-analizar").click()
    _esperar_resultado(navegador)
    assert navegador.find_element(By.ID, "cuadros-analizados").text == "6"
    assert navegador.find_element(By.ID, "cuadros-con-rostros").text == "6"
    assert navegador.find_element(By.ID, "max-rostros").text == "1"
    assert navegador.find_element(By.ID, "img-mejor-cuadro").is_displayed()
    navegador.find_element(By.TAG_NAME, "summary").click()
    assert len(navegador.find_elements(By.CSS_SELECTOR, "#tabla-cuadros tbody tr")) == 6
    _captura(navegador, carpeta_capturas, "cu05_resultado_video")


def test_cu06_archivo_no_permitido(navegador, live_server, tmp_path, carpeta_capturas):
    falso = tmp_path / "documento.txt"
    falso.write_text("hola")
    navegador.get(live_server.url + "/imagen/")
    navegador.find_element(By.ID, "id_archivo").send_keys(str(falso))
    navegador.find_element(By.ID, "btn-analizar").click()
    error = navegador.find_element(By.ID, "error")
    assert "Formato no permitido" in error.text
    _captura(navegador, carpeta_capturas, "cu06_error_formato")


def test_cu07_historial_e_inicio(navegador, live_server, ruta_con_rostro, carpeta_capturas):
    navegador.get(live_server.url + "/imagen/")
    navegador.find_element(By.ID, "id_archivo").send_keys(str(ruta_con_rostro))
    navegador.find_element(By.ID, "btn-analizar").click()
    _esperar_resultado(navegador)
    navegador.find_element(By.ID, "nav-historial").click()
    filas = navegador.find_elements(By.CSS_SELECTOR, "#tabla-detecciones tbody tr")
    assert len(filas) >= 1 and "messi5.jpg" in filas[0].text
    _captura(navegador, carpeta_capturas, "cu07a_historial")
    navegador.find_element(By.ID, "nav-inicio").click()
    assert int(navegador.find_element(By.ID, "total-analisis").text) >= 1
    _captura(navegador, carpeta_capturas, "cu07b_inicio_con_datos")
