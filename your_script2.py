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



def send_attack():
    try:
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

        try:
            challenge_container = driver.find_element(By.CLASS_NAME, "challenge-container")
            return False, "E.01 - Znaleziono captcha"
        except:
            pass



        try:
            iframe = driver.find_element(By.XPATH, "//iframe[@title='Main content of the hCaptcha challenge']")
            return False, "E.02 - Znaleziono captcha"
        except Exception as e:
            pass

        time.sleep(1)
        try:
            logout_link = driver.find_element(By.XPATH, "//a[@href='/page/logout']")
        except:
            return False, "E.03 - Wylogowano ze strony"

        try:
            challenge_container = driver.find_element(By.XPATH,"//span[text()='Świat 182']")
            challenge_container.click()
        except:
            return False, "E.04 - Nie znaleziono swiata 182"


        time.sleep(2)
        try:
            challenge_container = driver.find_element(By.CLASS_NAME, "popup_box_close")
            challenge_container.click()
        except:
            pass

        time.sleep(2)
        try:
            element = driver.find_element(By.XPATH, '//a[contains(text(), "Kombinowany ")]')
            element.click()
            time.sleep(1)
        except:
            return False, "E.06 - Nie znalezniono przeglądu"


        current_url = driver.current_url

        response = requests.get(current_url)


        if response.status_code == 200:
            html_content = response.text

        # Pobierz kod źródłowy strony
        html_content = driver.page_source

        # Przetwarzanie kodu HTML za pomocą BeautifulSoup
        soup = BeautifulSoup(html_content, "html.parser")
        try:

            villages = soup.find_all("tr", class_="nowrap")
            for village in villages:
                # Pobieranie identyfikatora wioski
                village_id = village.find("span", class_="quickedit-vn")["data-id"]

                # Pobieranie koordynatów wioski
                village_coordinates_raw = village.find("span", class_="quickedit-label").text
                village_coordinates = village_coordinates_raw.split('(')[1].split(')')[0]

                if village_coordinates == parametr1:
                    driver.get("https://pl182.plemiona.pl/game.php?village=" + village_id + "&screen=place")
                    break
            else:
                return False, "E.07 - Nie znaleziono wioski atakującego o podanych koordynatach"
        except:
            return False, "E.07 - Błąd pobierania id wiosek"

        time.sleep(2)

        if attacktype == "OFF":
            try:
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
            except:
                return False, "E.08 - Błąd pobierania aktualnych jednostek"


            if int(taran) < 21:
                taran = 0
            if int(zwiad) < 10:
                zwiad = 0
            else:
                zwiad = 10
            try:

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
            except:
                return False, "E.09 - Błąd wpisania jednostek"

            time.sleep(3)
        elif attacktype == "FAKE":

            try:
                # Szukanie elementu z tekstem "hfghg" i klasą "quickbar_link"
                # element = driver.find_element(By.XPATH, "//a[@class='quickbar_link' and contains(.,'PLEMSY')]")
                element = driver.find_element(By.XPATH, '//a[@class="quickbar_link" and contains(., "PLEMSY")]')
                # element = driver.find_element(By.CSS_SELECTOR,'.quickbar_link[data-hash="5aeacdb8fdbe6255c2bd7e1e423408c8"]')
                element.click()
                time.sleep(1)
            except:
                return False, "E.10 - Błąd podczas uzywania skryptu fake"

        time.sleep(2)

        def slow_type(element, text, delay=0.1):
            for character in text:
                element.send_keys(character)
                time.sleep(delay)

        try:
            challenge_container = driver.find_element(By.CLASS_NAME, "target-input-field")
            challenge_container.clear()
            time.sleep(2)
            slow_type(challenge_container, parametr2, delay=0.2)
            time.sleep(2)
        except:
            return False, "E.11 - Błąd podczas wpisywania celu"

        time.sleep(1)
        try:
            challenge_container = driver.find_element(By.ID, "target_attack")
            challenge_container.click()
        except:
            return False, "E.12 - Błąd jeszcze na placu"
        try:
            challenge_container = driver.find_element(By.ID, "troop_confirm_submit")
        except:
            return False, "E.13 - Błędny cel lub jednostki"


        time.sleep(2)

        target_time = godzina2 + ":" + minuta2 + ":" + sekunda2
        script = "let input='" + target_time + "';let inputMs='" + ms2 + "';let delayTime = parseInt(localStorage.delayTime);if (isNaN(delayTime)) {delayTime = 0;localStorage.delayTime = JSON.stringify(delayTime);}delayTime = 0;let delay = parseInt(delayTime) + parseInt(inputMs);let serverTime;attInterval = setInterval(function () {serverTime = document.getElementById('serverTime').textContent;if (serverTime >= input) {setTimeout(function () { document.getElementById('troop_confirm_submit').click(); }, delay);clearInterval(attInterval);}}, 5);"
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

        c.execute("DELETE FROM data WHERE id = ?", (id_record,))
        conn.commit()
        driver.quit()

    except Exception as e:
        return False, str(e)

    return True, "Success"


while not znaleziono_date:
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute('SELECT * FROM data')
    rows = c.fetchall()


    for row in rows:
        date_str = row[3]  # Pobierz datę z kolumny parametr3
        date_obj = parse(date_str)  # Konwertuj ciąg znaków na obiekt datetime

        now = datetime.now()  # Pobierz aktualny czas
        time_diff = date_obj - now  # Oblicz różnicę czasu
        id_record = row[0]
        parametr1 = row[1]
        parametr2 = row[2]
        attacktype = row[4]

        data = date_str
        dt = datetime.strptime(data, '%Y-%m-%dT%H:%M:%S.%f')
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

        if timedelta(minutes=0) < time_diff <= timedelta(minutes=1):  # Sprawdź, czy do daty brakuje 2 minut
            if len(rows) == 1:
                znaleziono_date = True

            is_successful, message = send_attack()
            # Sprawdź wynik
            if is_successful:
                print("Wysłano atak pomyślnie!")
                # Dodaj informacje o ataku do tabeli 'wyslane'
                conn = sqlite3.connect('data.db')
                c = conn.cursor()
                c.execute("INSERT INTO wyslane(parametr1, parametr2, data, attacktype) VALUES (?, ?, ?, ?)", (parametr1, parametr2, data, attacktype))
                conn.commit()
                conn.close()
            else:
                print("Nie udało się wysłać ataku. Powód:", message)
                # Dodaj informacje o ataku do tabeli 'niewyslane'
                conn = sqlite3.connect('data.db')
                c = conn.cursor()
                c.execute("INSERT INTO niewyslane(parametr1, parametr2, data, attacktype, reason) VALUES (?, ?, ?, ?, ?)", (parametr1, parametr2, data, attacktype, message))
                c.execute("DELETE FROM data WHERE id = ?", (id_record,))
                conn.commit()
                conn.close()

    conn.close()
    if not znaleziono_date:
        time.sleep(10)  # Poczekaj 10s przed kolejnym sprawdzeniem
