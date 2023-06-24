from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import sqlite3
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import requests
from dateutil.parser import parse


znaleziono_date = False

while not znaleziono_date:
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute('SELECT * FROM data')
    rows = c.fetchall()
    conn.close()

    for row in rows:
        date_str = row[3]  # Pobierz datę z kolumny parametr3
        date_obj = parse(date_str)  # Konwertuj ciąg znaków na obiekt datetime

        now = datetime.now()  # Pobierz aktualny czas
        time_diff = date_obj - now  # Oblicz różnicę czasu

        if timedelta(minutes=0) < time_diff <= timedelta(minutes=2):  # Sprawdź, czy do daty brakuje 2 minut
            print(f"Brakuje 5 minut do {date_str}!")
            if len(rows) == 1:
                znaleziono_date = True
            id_record = row[0]
            parametr1 = row[1]
            parametr2 = row[2]
            attacktype = row[4]

            data = date_str
            dt = datetime.strptime(data, '%Y-%m-%dT%H:%M:%S.%f')

            options = Options()
            options.add_argument('--user-data-dir=/path/to/user-data')
            options.add_argument('--profile-directory=Default')
            options.add_extension("windscribe.crx")
            driver = webdriver.Chrome(options=options)
            X = parametr1
            Y = parametr2
            godzina = dt.hour
            minuta = dt.minute
            sekunda = dt.second
            ms = dt.microsecond / 1000
            ms2 = str(ms)
            godzina2 = str(godzina)
            minuta2 = str(minuta)

            if sekunda < 10:
                sekunda2 = str(0) + str(sekunda)
            else:
                sekunda2 = str(sekunda)

            if minuta < 10:
                minuta2 = str(0) + str(minuta2)
            else:
                minuta2 = str(minuta)

            time.sleep(1)
            driver.get("https://plemiona.pl")

            time.sleep(1)
            print(driver.title)


            try:
                challenge_container = driver.find_element(By.CLASS_NAME, "challenge-container")
                print("Element o klasie 'challenge-container' został znaleziony.")
            except:
                print("Element o klasie 'challenge-container' nie został znaleziony.")

            try:
                iframe = driver.find_element(By.XPATH, "//iframe[@title='Main content of the hCaptcha challenge']")
                print("Element został znaleziony.")
            except Exception as e:
                print("Element nie został znaleziony.")

            time.sleep(1)
            try:
                logout_link = driver.find_element(By.XPATH, "//a[@href='/page/logout']")
                print("Found the logout link")
            except:
                print("Logout link not found")

            try:
                challenge_container = driver.find_element_by_xpath("//span[text()='Świat 182']")

                challenge_container.click()
                print("Guzik swiata znaleziony.")
            except:
                print("Guzik swiata nie został znaleziony.")

            try:
                challenge_container = driver.find_element(By.CLASS_NAME, "world_button_active")
                print("Znaleziono swiat 185")
                challenge_container.click()
            except:
                print("Nie znaleziono swiata 185")

            time.sleep(2)
            try:
                challenge_container = driver.find_element(By.CLASS_NAME, "popup_box_close")
                print("Zamknieto POPUP")
                challenge_container.click()
            except:
                print("POPUP nie pojawil sie")

            # /////////////////////////////////////
            time.sleep(2)
            try:
                element = driver.find_element(By.XPATH, '//a[contains(text(), "Kombinowany ")]')
                element.click()
                time.sleep(1)
            except:
                print("NIe znaleziono kombinowania")
            # Pobierz aktualny adres URL strony
            current_url = driver.current_url

            response = requests.get(current_url)

            print(current_url)

            if response.status_code == 200:
                html_content = response.text
            else:
                print("Błąd podczas pobierania strony. Kod statusu:", response.status_code)

            html = html_content

            # Pobierz kod źródłowy strony
            html_content = driver.page_source

            # Przetwarzanie kodu HTML za pomocą BeautifulSoup
            soup = BeautifulSoup(html_content, "html.parser")

            villages = soup.find_all("tr", class_="nowrap")
            for village in villages:
                # Pobieranie identyfikatora wioski
                village_id = village.find("span", class_="quickedit-vn")["data-id"]

                # Pobieranie koordynatów wioski
                village_coordinates_raw = village.find("span", class_="quickedit-label").text
                village_coordinates = village_coordinates_raw.split('(')[1].split(')')[0]

                if village_coordinates == parametr1:
                    print("ID wioski:", village_id)
                    print("Koordynaty wioski:", village_coordinates)
                    driver.get("https://pl182.plemiona.pl/game.php?village=" + village_id + "&screen=place")

            time.sleep(2)

            if attacktype == "OFF":

                topy = driver.find_element(By.ID, "units_entry_all_axe").text
                topy = topy[1:-1]

                lk = driver.find_element(By.ID, "units_entry_all_light").text
                lk = lk[1:-1]
                taran = driver.find_element(By.ID, "units_entry_all_ram").text
                taran = taran[1:-1]
                lukinakoniu = driver.find_element(By.ID, "units_entry_all_marcher").text
                lukinakoniu = lukinakoniu[1:-1]
                zwiad = driver.find_element(By.ID, "units_entry_all_spy").text
                zwiad = zwiad[1:-1]

                print(int(topy))
                print(int(lk))
                print(int(taran))
                print(int(lukinakoniu))
                print(int(zwiad))
                if int(taran) < 21:
                    taran = 0
                if int(zwiad) < 10:
                    zwiad = 0
                else:
                    zwiad = 10
                topyinput = driver.find_element(By.ID, "unit_input_axe")
                topyinput.send_keys(int(topy) - 200)
                lkinput = driver.find_element(By.ID, "unit_input_light")
                lkinput.send_keys(int(lk) - 100)
                raminput = driver.find_element(By.ID, "unit_input_ram")
                raminput.send_keys(int(taran) - 20)
                raminput = driver.find_element(By.ID, "unit_input_marcher")
                raminput.send_keys(int(lukinakoniu))
                zwiadinput = driver.find_element(By.ID, "unit_input_spy")
                zwiadinput.send_keys(int(zwiad))

                time.sleep(3)
            elif attacktype == "FAKE":

                try:
                    # Szukanie elementu z tekstem "hfghg" i klasą "quickbar_link"
                    #element = driver.find_element(By.XPATH, "//a[@class='quickbar_link' and contains(.,'PLEMSY')]")
                    element = driver.find_element(By.XPATH, '//a[@class="quickbar_link" and contains(., "PLEMSY")]')
                    #element = driver.find_element(By.CSS_SELECTOR,'.quickbar_link[data-hash="5aeacdb8fdbe6255c2bd7e1e423408c8"]')
                    element.click()
                    time.sleep(1)
                except:
                    # Teraz możemy wykonać operacje na znalezionym elemencie, np. kliknąć go
                    element.click()

            time.sleep(2)


            def slow_type(element, text, delay=0.1):
                """Wpisuje powoli tekst do danego elementu z określonym opóźnieniem."""
                for character in text:
                    element.send_keys(character)
                    time.sleep(delay)
            try:
                challenge_container = driver.find_element(By.CLASS_NAME, "target-input-field")
                challenge_container.clear()
                print("Znaleziono pole ")
                time.sleep(2)
                slow_type(challenge_container, parametr2, delay=0.2)
                time.sleep(2)
            except:
                print("Nie znaleziono buttona attack")

            time.sleep(1)
            try:
                challenge_container = driver.find_element(By.ID, "target_attack")
                print("Znaleziono button attack ")
                challenge_container.click()
            except:
                print("Nie znaleziono buttona attack")

            time.sleep(2)

            target_time = godzina2 + ":" + minuta2 + ":" + sekunda2
            script="let input='"+target_time+"';let inputMs='"+ms2+"';let delayTime = parseInt(localStorage.delayTime);if (isNaN(delayTime)) {delayTime = 0;localStorage.delayTime = JSON.stringify(delayTime);}delayTime = 0;let delay = parseInt(delayTime) + parseInt(inputMs);let serverTime;attInterval = setInterval(function () {serverTime = document.getElementById('serverTime').textContent;if (serverTime >= input) {setTimeout(function () { document.getElementById('troop_confirm_submit').click(); }, delay);clearInterval(attInterval);}}, 5);"
            driver.execute_script(script)

            time.sleep(2)


            def wait_until(hour, minute, second):
                now = datetime.now()
                target_time = now.replace(hour=hour, minute=minute, second=second, microsecond=0)

                if now > target_time:
                    # Jeśli czas docelowy już minął, ustaw na następny dzień
                    target_time += timedelta(days=1)

                # Oblicz czas oczekiwania w sekundach
                wait_seconds = (target_time - now).total_seconds()
                time.sleep(wait_seconds)

            if sekunda < 55:
                sekunda += 5
            else:
                sekunda = (sekunda + 5) % 60
                if minuta < 59:
                    minuta += 1
                else:
                    minuta = 0
                    godzina = (godzina + 1) % 24

            wait_until(godzina, minuta, sekunda)

            print("WYSŁANO ATAK")

            conn = sqlite3.connect('data.db')
            c = conn.cursor()
            c.execute("DELETE FROM data WHERE id = ?", (id_record,))
            conn.commit()
            conn.close()
            driver.quit()

    if not znaleziono_date:
        time.sleep(10)  # Poczekaj 10s przed kolejnym sprawdzeniem
