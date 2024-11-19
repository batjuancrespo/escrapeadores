from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
import time
import gspread
from oauth2client.service_account import ServiceAccountCredentials


def scrape_real_madrid_basketball(max_retries=3, retry_delay=5):
    url = 'https://www.flashscore.es/equipo/real-madrid/MP6gLUO7/resultados/'
    next_match_url = 'https://www.flashscore.es/equipo/real-madrid/MP6gLUO7/partidos/'

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

    driver = None
    retry_count = 0

    last_match_result = ""
    next_match_info = ""

    while retry_count < max_retries:
        try:
            if driver:
                driver.quit()

            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

            # Scrape last match result
            driver.get(url)
            wait = WebDriverWait(driver, 30)

            try:
                cookie_banner = wait.until(EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler")))
                cookie_banner.click()
                print("Banner de cookies cerrado.")
            except TimeoutException:
                print("No se encontró el banner de cookies o no fue necesario cerrarlo.")

            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "sportName")))
            print("Contenido principal cargado.")

            time.sleep(10)

            matches = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".event__match")))
            print(f"Se encontraron {len(matches)} partidos.")

            if matches:
                first_match = matches[0]

                home_team = first_match.find_element(By.CSS_SELECTOR, ".event__participant--home").text.strip()
                away_team = first_match.find_element(By.CSS_SELECTOR, ".event__participant--away").text.strip()
                home_score = first_match.find_element(By.CSS_SELECTOR, ".event__score--home").text.strip()
                away_score = first_match.find_element(By.CSS_SELECTOR, ".event__score--away").text.strip()

                last_match_result = f"{home_team} {home_score} - {away_score} {away_team}"
                print(f'\nÚltimo resultado: {last_match_result}')
            else:
                print('No se encontraron resultados de partidos.')

            # Scrape next match info
            driver.get(next_match_url)
            driver.implicitly_wait(10)

            try:
                proximo_partido = driver.find_element(By.CLASS_NAME, "event__match--scheduled")
                fecha_hora = proximo_partido.find_element(By.CLASS_NAME, "event__time").text.strip()
                home_team = proximo_partido.find_element(By.CLASS_NAME, "event__participant--home").text.strip()
                away_team = proximo_partido.find_element(By.CLASS_NAME, "event__participant--away").text.strip()

                next_match_info = f"{home_team} vs {away_team} - Fecha: {fecha_hora}"
                print(f"\nPróximo partido: {next_match_info}")
            except NoSuchElementException:
                print("No se encontró el próximo partido programado.")

            break
        except TimeoutException as e:
            print(f"Tiempo de espera agotado (intento {retry_count + 1}/{max_retries}): {e}")
            retry_count += 1
            time.sleep(retry_delay)
        except WebDriverException as e:
            print(f"Error del WebDriver (intento {retry_count + 1}/{max_retries}): {e}")
            retry_count += 1
            time.sleep(retry_delay)
        except Exception as e:
            print(f"Error inesperado (intento {retry_count + 1}/{max_retries}): {e}")
            retry_count += 1
            time.sleep(retry_delay)

    if retry_count >= max_retries:
        print("\nSe agotaron todos los intentos. No se pudo obtener la información.")

    if driver:
        driver.quit()

    return last_match_result, next_match_info


def upload_to_sheet(last_match_result, next_match_info):
    # Configura las credenciales y accede a la hoja de cálculo
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
    client = gspread.authorize(creds)

    # Abre la hoja de cálculo y selecciona la hoja 4
    sheet = client.open('ALMACEN PARA LA APP').worksheet('Hoja 4')

    # Prepara los datos con los encabezados solicitados
    last_match_data = f"Ultimo resultado R. Madrid (BAS): {last_match_result}"
    next_match_data = f"Próximo partido R. Madrid (BAS): {next_match_info}"

    # Sube el último resultado a la fila 1, columna B
    sheet.update('B1', [[last_match_data]])

    # Sube la información del próximo partido a la fila 2, columna B
    sheet.update('B2', [[next_match_data]])

    print("Datos subidos exitosamente a la hoja de cálculo.")


if __name__ == '__main__':
    last_match_result, next_match_info = scrape_real_madrid_basketball()
    if last_match_result and next_match_info:
        upload_to_sheet(last_match_result, next_match_info)
