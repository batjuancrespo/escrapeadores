from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time


def scrape_racing_results():
    url_resultado = 'https://www.flashscore.es/equipo/racing-santander/nVpEwOrl/resultados/'
    url_proximo_partido = 'https://www.flashscore.es/equipo/racing-santander/nVpEwOrl/partidos/'

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    # Variable para almacenar los resultados
    result_text = ""
    next_match_text = ""

    try:
        # Extraer el último resultado
        driver.get(url_resultado)
        wait = WebDriverWait(driver, 30)

        # Cerrar banner de cookies si aparece
        try:
            cookie_banner = wait.until(EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler")))
            cookie_banner.click()
        except TimeoutException:
            pass

        # Esperar a que cargue el contenido principal
        try:
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "sportName")))
        except TimeoutException:
            print("Tiempo de espera agotado al cargar el contenido principal.")
            return

        time.sleep(10)

        # Buscar los partidos
        try:
            matches = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".event__match")))

            if matches:
                first_match = matches[0]
                home_team = first_match.find_element(By.CSS_SELECTOR,
                                                     ".event__homeParticipant .wcl-name_N76Hr").text.strip()
                away_team = first_match.find_element(By.CSS_SELECTOR,
                                                     ".event__awayParticipant .wcl-name_N76Hr").text.strip()
                home_score = first_match.find_element(By.CLASS_NAME, "event__score--home").text.strip()
                away_score = first_match.find_element(By.CLASS_NAME, "event__score--away").text.strip()

                # Formato solicitado
                result_text = f"Último resultado Racing: {home_team} {home_score} - {away_score} {away_team}"
                print(result_text)
            else:
                print('No se encontraron resultados de partidos.')
        except TimeoutException:
            print("No se pudieron encontrar los elementos de los partidos.")
        except NoSuchElementException as e:
            print(f"No se pudo encontrar un elemento específico: {e}")

        # Extraer el próximo partido
        driver.get(url_proximo_partido)
        driver.implicitly_wait(10)

        try:
            proximo_partido = driver.find_element(By.CLASS_NAME, "event__match--scheduled")
            fecha_hora = proximo_partido.find_element(By.CLASS_NAME, "event__time").text.strip()
            home_team = proximo_partido.find_element(By.CLASS_NAME, "event__homeParticipant").text.strip()
            away_team = proximo_partido.find_element(By.CLASS_NAME, "event__awayParticipant").text.strip()

            next_match_text = f"Próximo partido: {home_team} vs {away_team} - Fecha: {fecha_hora}"
            print(next_match_text)
        except NoSuchElementException:
            print("No se encontró el próximo partido programado.")

    except WebDriverException as e:
        print(f'Error del WebDriver: {e}')
    except Exception as e:
        print(f'Error inesperado: {e}')

    finally:
        driver.quit()

    # Subir los datos a Google Sheets
    update_google_sheet(result_text, next_match_text)


def update_google_sheet(result_text, next_match_text):
    # Configura el acceso a Google Sheets
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/spreadsheets",
             "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]

    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)

    # Abre la hoja y selecciona Hoja 4
    sheet = client.open("ALMACEN PARA LA APP").worksheet("Hoja 4")

    # Escribe el último resultado en la fila 3, columna 1
    if result_text:
        sheet.update_cell(5, 1, result_text)
        print("Último resultado actualizado en Google Sheets.")

    # Escribe el próximo partido en la fila 4, columna 1
    if next_match_text:
        sheet.update_cell(6, 1, next_match_text)
        print("Próximo partido actualizado en Google Sheets.")


if __name__ == '__main__':
    scrape_racing_results()
