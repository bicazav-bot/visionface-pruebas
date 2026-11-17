# Pruebas funcionales: un navegador real (Microsoft Edge) usa la aplicación
# como lo haría una persona. Cada prueba guarda una captura de pantalla.
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture
def navegador():
    opciones = webdriver.EdgeOptions()
    opciones.add_argument("--headless=new")
    opciones.add_argument("--window-size=1280,1000")
    driver = webdriver.Edge(options=opciones)
    driver.implicitly_wait(10)
    yield driver
    driver.quit()


def capturar(navegador, carpeta, nombre):
    alto = navegador.execute_script("return document.body.scrollHeight")
    navegador.set_window_size(1280, max(alto + 150, 700))
    navegador.save_screenshot(str(carpeta / f"{nombre}.png"))


def subir(navegador, url, archivo):
    navegador.get(url)
    navegador.find_element(By.ID, "id_archivo").send_keys(str(archivo))
    navegador.find_element(By.ID, "btn-analizar").click()


def test_cu1_inicio(navegador, live_server, capturas):
    navegador.get(live_server.url)
    assert "VisionFace" in navegador.title
    assert navegador.find_element(By.ID, "total-analisis").text == "0"
    capturar(navegador, capturas, "cu1_inicio")


def test_cu2_detectar_en_imagen(navegador, live_server, foto_con_rostro, capturas):
    subir(navegador, live_server.url + "/imagen/", foto_con_rostro)
    assert navegador.find_element(By.ID, "num-rostros").text == "1"
    capturar(navegador, capturas, "cu2_imagen_con_rostro")


def test_cu3_imagen_sin_rostros(navegador, live_server, foto_grande_sin_rostro, capturas):
    subir(navegador, live_server.url + "/imagen/", foto_grande_sin_rostro)
    assert navegador.find_element(By.ID, "num-rostros").text == "0"
    assert navegador.find_element(By.ID, "sin-rostros").is_displayed()
    capturar(navegador, capturas, "cu3_imagen_sin_rostros")


def test_cu4_detectar_en_video(navegador, live_server, video_con_rostro, capturas):
    subir(navegador, live_server.url + "/video/", video_con_rostro)
    assert navegador.find_element(By.ID, "analizados").text == "6"
    assert navegador.find_element(By.ID, "max-rostros").text == "1"
    capturar(navegador, capturas, "cu4_video")


def test_cu5_borrar_historial(navegador, live_server, foto_con_rostro, capturas):
    subir(navegador, live_server.url + "/imagen/", foto_con_rostro)
    navegador.find_element(By.ID, "nav-inicio").click()
    assert "messi5.jpg" in navegador.find_element(By.ID, "tabla-detecciones").text
    capturar(navegador, capturas, "cu5a_ultimos_analisis")
    navegador.find_element(By.ID, "btn-borrar").click()
    navegador.switch_to.alert.accept()           # confirma "¿Borrar todos los análisis?"
    assert navegador.find_element(By.ID, "sin-registros").is_displayed()
    assert navegador.find_element(By.ID, "total-analisis").text == "0"
    capturar(navegador, capturas, "cu5b_historial_borrado")
