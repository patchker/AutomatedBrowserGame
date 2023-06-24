from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import pickle
import time

# Opcje przeglądarki
chrome_options = Options()
#chrome_options.add_argument("--headless") # Włączenie trybu headless

# Ścieżka do ChromeDriver
#webdriver_service = Service('/path/to/chromedriver')

driver = webdriver.Chrome(options=chrome_options)

# Wejdź na stronę Tribal Wars
driver.get('https://plemiona.pl')

# Wczytaj ciasteczka z pliku
cookies = pickle.load(open("cookies.pkl", "rb"))
for cookie in cookies:
    driver.add_cookie(cookie)

# Odśwież stronę, aby ciasteczka zadziałały
driver.refresh()

time.sleep(60)

# Pamiętaj o zamknięciu przeglądarki na koniec
driver.quit()
