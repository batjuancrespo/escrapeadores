import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import gspread
from oauth2client.service_account import ServiceAccountCredentials

def scrape_racing_results():
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')

    # Use the latest version of ChromeDriver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    try:
        driver.get("https://www.racingclub.com.ar/")

        # Esperar a que el elemento esté presente
        wait = WebDriverWait(driver, 10)
        element = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "fixture__content")))

        # Obtener el texto del elemento
        texto = element.text

        # Dividir el texto en líneas
        lineas = texto.split('\n')

        # Extraer la información relevante
        fecha = lineas[0]
        torneo = lineas[1]
        equipo_local = lineas[2]
        resultado = lineas[3]
        equipo_visitante = lineas[4]

        # Crear una lista con la información extraída
        datos = [fecha, torneo, equipo_local, resultado, equipo_visitante]

        # Autenticación con Google Sheets
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
        client = gspread.authorize(creds)

        # Abrir la hoja de cálculo
        sheet = client.open('Resultados Racing').worksheet('Hoja 1')

        # Obtener todos los valores de la hoja
        valores = sheet.get_all_values()

        # Verificar si los datos ya existen en la hoja
        if datos not in valores:
            # Si los datos no existen, añadirlos a la hoja
            sheet.append_row(datos)
            print("Datos añadidos correctamente a Google Sheets.")
        else:
            print("Los datos ya existen en la hoja. No se han añadido duplicados.")

    except Exception as e:
        print(f"Error inesperado: {str(e)}")

    finally:
        driver.quit()

def main():
    max_intentos = 3
    intentos = 0

    while intentos < max_intentos:
        try:
            scrape_racing_results()
            break
        except Exception as e:
            intentos += 1
            print(f"Error inesperado (intento {intentos}/{max_intentos}): {str(e)}")
            time.sleep(5)  # Esperar 5 segundos antes de intentar de nuevo

    if intentos == max_intentos:
        print("\nSe agotaron todos los intentos. No se pudo obtener la información.")

if __name__ == "__main__":
    main()
