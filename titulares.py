import os
import json
import logging
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests
from bs4 import BeautifulSoup

# Configura el registro de errores
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Lee las credenciales desde la variable de entorno
try:
    credentials_json = os.getenv("GOOGLE_CREDENTIALS")
    if not credentials_json:
        raise ValueError("No se encontraron credenciales en la variable de entorno GOOGLE_CREDENTIALS.")
    with open("credentials.json", "w") as f:
        f.write(credentials_json)
    logging.info("Credenciales de Google cargadas correctamente.")
except Exception as e:
    logging.error(f"Error al cargar credenciales: {e}")
    raise

# Configuración de Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
client = gspread.authorize(creds)

# Abre la hoja de Google Sheets
spreadsheet = client.open("ALMACEN PARA LA APP")
hoja1 = spreadsheet.get_worksheet(0)  # Accede a la primera hoja
hoja2 = spreadsheet.get_worksheet(1)  # Accede a la segunda hoja

# Lista de sitios y sus selectores para Hoja1
sitios_hoja1 = [
    {"nombre": "El Diario Montañés", "url": "https://www.eldiariomontanes.es/", "selector": "h2"},
    {"nombre": "El Mundo", "url": "https://www.elmundo.es/", "selector": ".ue-c-cover-content__headline"},
    {"nombre": "El País", "url": "https://elpais.com/", "selector": ".c_t"}
]

# Lista de sitios y sus selectores para Hoja2
sitios_hoja2 = [
    {"nombre": "AS", "url": "https://as.com/", "selector": "h2"},
    {"nombre": "Marca", "url": "https://www.marca.com/", "selector": "h2"},
    {"nombre": "Estadio Deportivo", "url": "https://www.estadiodeportivo.com/", "selector": "h2"}
]

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36"
}

# Función para obtener titulares de cada sitio
def obtener_titulares(url, selector):
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Verifica errores HTTP
        soup = BeautifulSoup(response.text, "html.parser")
        # Filtra y obtiene solo titulares que tengan más de 2 palabras
        titulares = [titular.text.strip() for titular in soup.select(selector) if len(titular.text.split()) > 2]
        return titulares[:10]  # Obtén solo los primeros 10 titulares válidos
    except Exception as e:
        logging.error(f"Error obteniendo titulares de {url}: {e}")
        return []

# Escribe los titulares en Hoja1 de Google Sheets
try:
    hoja1.clear()  # Limpia el contenido anterior de la Hoja1
    datos_hoja1 = []  # Lista para almacenar datos de Hoja1
    for sitio in sitios_hoja1:
        titulares = obtener_titulares(sitio["url"], sitio["selector"])
        for titular in titulares:
            datos_hoja1.append([sitio["nombre"], titular])  # Añade la fuente y el titular a la lista
    if datos_hoja1:
        hoja1.update('A1:B{}'.format(len(datos_hoja1)), datos_hoja1)  # Actualiza la hoja de una sola vez
        logging.info("Titulares de Hoja1 enviados correctamente a Google Sheets.")
    else:
        logging.warning("No se encontraron titulares para Hoja1.")
except Exception as e:
    logging.error(f"Error al escribir titulares en Hoja1: {e}")

# Escribe los titulares en Hoja2 de Google Sheets
try:
    hoja2.clear()  # Limpia el contenido anterior de la Hoja2
    datos_hoja2 = []  # Lista para almacenar datos de Hoja2
    for sitio in sitios_hoja2:
        titulares = obtener_titulares(sitio["url"], sitio["selector"])
        for titular in titulares:
            datos_hoja2.append([sitio["nombre"], titular])  # Añade la fuente y el titular a la lista
    if datos_hoja2:
        hoja2.update('A1:B{}'.format(len(datos_hoja2)), datos_hoja2)  # Actualiza la hoja de una sola vez
        logging.info("Titulares de Hoja2 enviados correctamente a Google Sheets.")
    else:
        logging.warning("No se encontraron titulares para Hoja2.")
except Exception as e:
    logging.error(f"Error al escribir titulares en Hoja2: {e}")
