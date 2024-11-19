import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import gspread
from oauth2client.service_account import ServiceAccountCredentials


# Función para procesar la tabla
def procesar_tabla(contenido_tabla):
    segmentos = contenido_tabla.split("Acta")
    resultados = []
    for segmento in segmentos:
        # Eliminar "MODIFICADOJUGADO" y el texto que le precede
        segmento_limpio = re.sub(r".*?MODIFICADOJUGADO", "", segmento, flags=re.DOTALL).strip()

        # Verificar si contiene "SELAYA"
        if "SELAYA" in segmento_limpio:
            # Unir caracteres en una sola línea, respetando las separaciones
            segmento_unido = ' '.join(segmento_limpio.split())
            resultados.append(segmento_unido)

    return resultados


# Configuración del WebDriver en modo headless
options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

# URL base
url_base = 'https://competicionesfecan.optimalwayconsulting.com/competicion/1419'

# Acceder a la página y extraer el número de jornada
driver.get(url_base)
time.sleep(5)

# Extraer el valor de la jornada
jornada_element = driver.find_element(By.CSS_SELECTOR,
                                      "#root > div > div.react-custom-container-main > div.container.container-react.fade-in > div > div:nth-child(4) > div > h2")
jornada_texto = jornada_element.text
jornada_actual = int(jornada_texto.split()[-1])

# Buscar los resultados
while jornada_actual > 0:
    url = f"{url_base}/{jornada_actual}"
    driver.get(url)
    time.sleep(5)

    # Extraer solo la primera tabla
    tabla = driver.find_element(By.XPATH, "(//table)[1]")
    contenido_tabla = tabla.text

    # Contar cuántas veces aparece "Prepartido"
    conteo_prepartido = contenido_tabla.count("Prepartido")

    # Si "Prepartido" aparece más de 3 veces, buscar en la jornada anterior
    if conteo_prepartido > 3:
        jornada_actual -= 1
    else:
        # Procesar la tabla y mostrar resultados
        resultados = procesar_tabla(contenido_tabla)
        for resultado in resultados:
            print(f"Club (JUN): {resultado}")

        # Acceso a Google Sheets
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
        client = gspread.authorize(creds)

        # Abrir la hoja de cálculo
        sheet = client.open('ALMACEN PARA LA APP').get_worksheet(3)  # Hoja 4 (índice 3)

        # Añadir resultado a la fila 8
        for i, resultado in enumerate(resultados, start=7):
            sheet.update_cell(i, 1, f"Club (JUN): {resultado}")  # Columna 1

        break

# Cerrar el navegador
driver.quit()
