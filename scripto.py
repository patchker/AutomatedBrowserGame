import json
import re
import sqlite3
import time
from datetime import datetime, timedelta
import numpy as np
import requests
from bs4 import BeautifulSoup
from dateutil.parser import parse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.wait import WebDriverWait
import app
from selenium.common.exceptions import NoSuchElementException

cookies = [
{'name' : 'remember_optout', 'value' : '0'},
{'name' : 'pl_auth', 'value' : 'a4194bdb3f70:21e4b391789d0cbc408cbc7f7d96055352862a68d633c67fb042fb0be8104d6e'},
{'name' : 'PHPSESSID', 'value' : 'n92foeajau1a52njm8ibgsaef0m1hqdp00099icmc4130dqv'},
{'name' : 'ref', 'value' : 'start'},
{'name' : 'cid', 'value' : '1486828514'}]


def wait_until(hour, minute, second):
    now = datetime.now()
    target_time = now.replace(hour=hour, minute=minute, second=second, microsecond=0)

    if now > target_time:
        # Jeśli czas docelowy już minął, ustaw na następny dzień
        target_time += timedelta(days=1)

    # Oblicz czas oczekiwania w sekundach
    wait_seconds = (target_time - now).total_seconds()
    time.sleep(wait_seconds)


# obliczanie ilości jednostek w ataku
def calculate_total(dictionary):
    total = 0
    unit_size = {'spear': 1, 'sword': 1, 'axe': 1, 'archer': 1, 'spy': 2, 'light': 4, 'heavy': 6,
                 'ram': 5,
                 'catapult': 8}
    for key, value in dictionary.items():
        total += value * unit_size.get(key, 1)
    return total


def slow_type(element, text, delay=0.05):
    for character in text:
        element.send_keys(character)
        time.sleep(delay)


# pobieranie ilości aktualnych wojsk
def collect_and_assign_units(driver):
    units_dict = {
        "spear": "units_entry_all_spear",
        "sword": "units_entry_all_sword",
        "axe": "units_entry_all_axe",
        "archer": "units_entry_all_archer",
        "spy": "units_entry_all_spy",
        "light": "units_entry_all_light",
        "marcher": "units_entry_all_marcher",
        "heavy": "units_entry_all_heavy",
        "ram": "units_entry_all_ram",
        "catapult": "units_entry_all_catapult",
        "snob": "units_entry_all_snob"
    }

    units = {}
    for unit, id in units_dict.items():
        text = driver.find_element(By.ID, id).text
        text = text[1:-1]  # usuń nawiasy
        units[unit] = int(text)
    return units


# WYBÓR JEDNOSTEK DLA FAKE
def fake_units(units2, capacity):
    unit_size = {'spear': 1, 'sword': 1, 'axe': 1, 'archer': 1, 'spy': 2, 'light': 4, 'heavy': 6, 'ram': 5,
                 'catapult': 8}
    units = {k: v for k, v in units2.items() if k not in ['snob', 'marcher']}

    # Wstępne ustawienie jednostek do ataku
    attack_units = {}

    # Wybór taranów lub katapult jako pierwszych, jeżeli są dostępne
    if units.get('ram', 0) > 0 and capacity >= unit_size['ram']:
        attack_units['ram'] = 1
        capacity -= unit_size['ram']
        units['ram'] -= 1
        if 'catapult' in units:
            units.pop('catapult', None)  # Usunięcie katapult z listy, jeżeli wybrano już taran
    elif units.get('catapult', 0) > 0 and capacity >= unit_size['catapult']:
        attack_units['catapult'] = 1
        capacity -= unit_size['catapult']
        units.pop('catapult', None)  # Usunięcie katapult z listy, aby nie były dodawane ponownie

    if units.get('spy', 0) > 0 and capacity >= unit_size['spy']:
        attack_units['spy'] = 1
        capacity -= unit_size['spy']
        units['spy'] -= 1

    total_units = sum(units.values())
    unit_probs = {unit: units[unit] / total_units for unit in units}
    unit_list = list(units.keys())

    while capacity > 0 and total_units > 0:
        unit = np.random.choice(unit_list, p=[unit_probs[u] for u in unit_list])
        if units[unit] > 0 and capacity >= unit_size[unit]:
            if unit in attack_units:
                attack_units[unit] += 1
            else:
                attack_units[unit] = 1
            capacity -= unit_size[unit]
            units[unit] -= 1
            total_units -= 1

            if units[unit] == 0:
                units.pop(unit, None)

            unit_probs = {unit: units[unit] / total_units for unit in units if
                          units[unit] > 0}  # Update the probabilities
            unit_list = list(unit_probs.keys())  # Update the unit list
    return attack_units


# WYBÓR JEDNOSTEK DLA BURZAKÓW
def burzak_units(driver, number):
    units_dict = {
        "axe": "units_entry_all_axe",
        "spear": "units_entry_all_spear",
        "light": "units_entry_all_light",
        "ram": "units_entry_all_ram",
        "marcher": "units_entry_all_marcher",
        "spy": "units_entry_all_spy",
        "heavy": "units_entry_all_heavy",
        "catapult": "units_entry_all_catapult"
    }

    units = {}
    units_chosen = {}
    for unit, id in units_dict.items():
        text = driver.find_element(By.ID, id).text
        text = text[1:-1]  # usuń nawiasy
        units[unit] = int(text)

    if units['heavy'] > 50:
        units_chosen['heavy'] = 50
    elif units['axe'] > 100:
        units_chosen['axe'] = 50
    elif units['light'] > 100:
        units_chosen['light'] = 50
    elif units['spear'] > 100:
        units_chosen['spear'] = 50

    units_chosen['catapult'] = number
    return units_chosen


# WYBÓR JEDNOSTEK DLA OFFOW
def off_units(driver, posiadane):
    units_dict = {
        "axe": "units_entry_all_axe",
        "light": "units_entry_all_light",
        "ram": "units_entry_all_ram",
        "marcher": "units_entry_all_marcher",
        "spy": "units_entry_all_spy",
    }

    units = {}
    units_chosen = {}
    for unit, id in units_dict.items():
        text = driver.find_element(By.ID, id).text
        text = text[1:-1]  # usuń nawiasy
        units[unit] = int(text)

    if units['ram'] < 21:
        units_chosen['ram'] = 0
    else:
        units_chosen['ram'] = posiadane['ram'] - 20

    if units['spy'] < 10:
        units_chosen['spy'] = 0
    else:
        units_chosen['spy'] = 10

    units_chosen['axe'] = posiadane['axe'] - 300
    units_chosen['light'] = posiadane['light'] - 150
    units_chosen['spy'] = 10
    units_chosen['marcher'] = posiadane['marcher']
    return units_chosen


# WYBÓR JEDNOSTEK DLA FAKE GRUBASA
def fake_grubas_units(driver, posiadane):
    units_dict = {
        "axe": "units_entry_all_axe",
        "light": "units_entry_all_light",
        "spear": "units_entry_all_spear",
        "heavy": "units_entry_all_heavy",
        "snob": "units_entry_all_snob",
    }

    units = {}
    units_chosen = {}
    for unit, id in units_dict.items():
        text = driver.find_element(By.ID, id).text
        text = text[1:-1]  # usuń nawiasy
        units[unit] = int(text)

    if units['heavy'] > 50:
        units_chosen['heavy'] = 25
    elif units['axe'] > 100:
        units_chosen['axe'] = 50
    elif units['light'] > 25:
        units_chosen['light'] = 25
    elif units['spear'] > 100:
        units_chosen['spear'] = 50

    units_chosen['snob'] = 1
    return units_chosen


def enter_units(driver, units):
    for unit, count in units.items():
        try:
            input_field = driver.find_element(By.ID, "unit_input_" + unit)
            input_field.clear()
            input_field.send_keys(str(count))
        except Exception as e:
            print(str(e))
            print(f'Nie mogę znaleźć pola dla jednostki: {unit}')


def send_attack(id_record, parametr1, parametr2, attacktype, url, massorsingle, data):
    try:
        print("[LAUNCHING AN ATTACK]: ID:", id_record, "A: ", parametr1, "B: ", parametr2, "C: ", attacktype, "D: ",
              url, "E: ", massorsingle)

        options = Options()
        options.add_argument("--start-minimized")
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537")
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        driver = webdriver.Chrome(options=options)

        dt = datetime.strptime(data, '%Y-%m-%dT%H:%M:%S.%f')
        godzina = dt.hour
        minuta = dt.minute
        sekunda = dt.second
        ms = dt.microsecond / 1000
        minuta2 = str(minuta)

        if godzina < 10:
            godzina2 = str(0) + str(godzina)
        else:
            godzina2 = str(godzina)
        if sekunda < 10:
            sekunda2 = str(0) + str(sekunda)
        else:
            sekunda2 = str(sekunda)

        if minuta < 10:
            minuta2 = str(0) + str(minuta2)
        else:
            minuta2 = str(minuta)

        driver.implicitly_wait(1)  # sekundy
        if massorsingle == "1":

            driver.implicitly_wait(1)  # sekundy
            driver.get("https://plemiona.pl")

            driver.implicitly_wait(1)  # sekundy
            for cookie in cookies:
                driver.add_cookie(cookie)
            print("[AFTER COOKIES]")
            driver.refresh()
            driver.implicitly_wait(1)  # sekundy
            driver.get(url)

            try:
                challenge_container = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//span[text()='Świat 182']")))
                challenge_container.click()
                driver.get(url)

            except:
                return False, "E.04 - Nie znaleziono swiata 182", 0, "Brak"

            try:
                challenge_container = driver.find_element(By.CLASS_NAME, "challenge-container")
                return False, "E.01 - Znaleziono captcha", 0, "Brak"
            except:
                pass

            try:
                iframe = driver.find_element(By.XPATH, "//iframe[@title='Main content of the hCaptcha challenge']")
                return False, "E.02 - Znaleziono captcha", 0, "Brak"
            except Exception as e:
                pass


        else:
            driver.get("https://plemiona.pl")
            driver.implicitly_wait(1)  # sekundy
            for cookie in cookies:
                driver.add_cookie(cookie)
            print("[AFTER COOKIES]")
            driver.refresh()

            try:
                challenge_container = driver.find_element(By.CLASS_NAME, "challenge-container")
                return False, "E.01 - Znaleziono captcha", 0, "Brak"
            except:
                pass

            try:
                iframe = driver.find_element(By.XPATH, "//iframe[@title='Main content of the hCaptcha challenge']")
                return False, "E.02 - Znaleziono captcha", 0, "Brak"
            except Exception as e:
                pass

            driver.implicitly_wait(1)  # sekundy
            try:
                logout_link = driver.find_element(By.XPATH, "//a[@href='/page/logout']")
            except:
                return False, "E.03 - Wylogowano ze strony", 0, "Brak"

            try:
                challenge_container = driver.find_element(By.XPATH, "//span[text()='Świat 182']")

                challenge_container.click()
            except:
                return False, "E.04 - Nie znaleziono swiata 182", 0, "Brak"

            try:
                challenge_container = driver.find_element(By.CLASS_NAME, "popup_box_close")
                challenge_container.click()
            except:
                pass

            try:
                element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, '//a[contains(text(), "Kombinowany ")]'))
                )
                element.click()
            except Exception as e:
                pass
            finally:
                driver.quit()

            try:
                element = driver.find_element(By.CLASS_NAME, "group-menu-item")
                element.click()
            except:
                pass

            current_url = driver.current_url
            response = requests.get(current_url)

            if response.status_code == 200:
                html_content = response.text
            html_content = driver.page_source
            soup = BeautifulSoup(html_content, "html.parser")
            try:
                villages = soup.find_all("tr", class_="nowrap")
                for village in villages:
                    village_id = village.find("span", class_="quickedit-vn")["data-id"]
                    village_coordinates_raw = village.find("span", class_="quickedit-label").text
                    village_coordinates = village_coordinates_raw.split('(')[1].split(')')[0]

                    if village_coordinates == parametr1:
                        driver.get("https://pl182.plemiona.pl/game.php?village=" + village_id + "&screen=place")
                        break
                else:
                    return False, "E.07 - Nie znaleziono wioski atakującego o podanych koordynatach", 0, "Brak"
            except:
                return False, "E.07 - Błąd pobierania id wiosek", 0, "Brak"

        if attacktype == "OFF":
            try:
                units = collect_and_assign_units(driver)
            except:
                return False, "E.08 - Błąd pobierania aktualnych jednostek", 0, "Brak"
            try:
                attack_units = off_units(driver, units)
                print("OFF UNITS: ", attack_units)
            except:
                return False, "E.09 - Błąd podczas generowania offowych jednostek", 0, "Brak"
            try:
                enter_units(driver, attack_units)
                size = calculate_total(attack_units)
            except:
                return False, "E.09 - Błąd podczas wpisywania offowych jednostek", 0, "Brak"

        elif attacktype == "FAKE":
            try:
                try:
                    driver.implicitly_wait(1)  # sekundy
                    challenge_container = driver.find_element(By.CLASS_NAME, "village-delete")
                except NoSuchElementException:
                    # czynności do wykonania, gdy element nie zostanie znaleziony
                    driver.implicitly_wait(1)  # sekundy
                    challenge_container = driver.find_element(By.CLASS_NAME, "target-input-field")
                    challenge_container.clear()
                    slow_type(challenge_container, parametr2, delay=0.1)
                    driver.implicitly_wait(1)  # sekundy

                units = collect_and_assign_units(driver)
                if units['spear'] > 0:
                    pik = driver.find_element(By.ID, "unit_input_spear")
                    slow_type(pik, "1", delay=0.2)
                elif units['axe'] > 0:
                    top = driver.find_element(By.ID, "unit_input_axe")
                    slow_type(top, "1", delay=0.2)
                if units['ram'] < 1 and units['catapult'] < 1:
                    return False, "E.10a - Brak maszyn do wysłania fake", 0, "Brak"

                element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "target_attack")))
                driver.execute_script("arguments[0].click();", element)
                text = driver.find_element(By.CLASS_NAME, "error_box").text
                match = re.search(r'co najmniej (\d+) mieszka', text)
                if match:
                    min_population = int(match.group(1))
                    print(f'Minimalna liczba mieszkańców: {min_population}')
                    capacity = min_population
                    print("Units", units)
                    time.sleep(1)
                    attack_units = fake_units(units, capacity)
                    print("FAKE UNITS: ", attack_units)
                    size = calculate_total(attack_units)
                    enter_units(driver, attack_units)
            except:
                return False, "E.10b - Błąd podczas uzywania skryptu fake", 0, "Brak"


        elif attacktype[:6] == "BURZAK":
            try:
                parts = attacktype.split(' - ')
                number = int(parts[1])
                building = parts[2]
                building = building.strip()
                attack_units = burzak_units(driver, number)
                print("BURZAK UNITS:", attack_units)
                enter_units(driver, attack_units)
                size = calculate_total(attack_units)
            except:
                return False, "E.16 - Błąd podczas burzaka", 0, "Brak"


        elif attacktype == "FAKE SZLACHCIC":
            try:
                units = collect_and_assign_units(driver)
                attack_units = fake_grubas_units(driver, units)
                enter_units(driver, attack_units)
                print("FAKE GRUBAS UNITS:", attack_units)
                size = calculate_total(attack_units)
            except:
                return False, "E.14 - Błąd podczas FAKE SZLACHCICA", 0, "Brak"


        elif attacktype == "SZLACHCIC":
            try:
                return False, "E.15 - SZLACHCIC", 0, "Brak"
            except:
                pass

        try:
            element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "target_attack")))
            driver.execute_script("arguments[0].click();", element)

        except:
            return False, "E.12 - Błąd jeszcze na placu", 0, "Brak"

        try:
            challenge_container = driver.find_element(By.ID, "troop_confirm_submit")
        except:
            return False, "E.13 - Błędny cel lub jednostki", 0, "Brak"

        try:
            challenge_container = driver.find_element(By.NAME, "building")
            select = Select(challenge_container)
            select.select_by_visible_text(building)
        except:
            pass

        driver.implicitly_wait(1)  # sekundy
        target_time = f"{godzina2}:{minuta2}:{sekunda2}"
        delayTime = 0
        print("[WAITING]")
        try:
            while True:
                serverTime_element = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.ID, "serverTime"))
                )
                serverTime = serverTime_element.text
                if serverTime >= target_time:
                    print("[PRÓBA WYSŁANIA ATAKU]")
                    # Rozpocznij odliczanie, a następnie kliknij przycisk, podobnie jak w JavaScript
                    time.sleep((delayTime + ms) / 1000)  # delayTime + ms2, konwersja ms2 na sekundy
                    submit_button = driver.find_element(By.ID, 'troop_confirm_submit')
                    submit_button.click()
                    break

                time.sleep(0.005)
        except:
            return False, "GÓWNO", 0, "Brak"

        driver.implicitly_wait(1)  # sekundy

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

        try:
            challenge_container = driver.find_element(By.CLASS_NAME, "command-cancel")
            conn = sqlite3.connect('data.db')
            c = conn.cursor()
            c.execute("DELETE FROM data WHERE id = ?", (id_record,))
            conn.commit()

            driver.quit()
            return True, "Success", attack_units, size

        except:
            return False, "E.19 - Błąd skryptu wysyłającego atak", 0, "Brak"


    except Exception as e:
        return False, str(e), 0, "Brak"


def scripto():
    znaleziono_date = False
    while not znaleziono_date:

        # sprawdzanie stanu serwera
        conn = sqlite3.connect('data.db')
        c = conn.cursor()
        c.execute('SELECT status FROM server_status')
        server_status = c.fetchone()
        if server_status[0] == 'inactive':
            print("Serwer został zatrzymany.")
            break
        conn.close()

        conn = sqlite3.connect('data.db')
        c = conn.cursor()
        c.execute('SELECT * FROM data')
        rows = c.fetchall()

        for row in rows:
            date_str = row[3]
            date_obj = parse(date_str)
            now = datetime.now()
            time_diff = date_obj - now
            id_record = row[0]
            parametr1 = row[1]
            parametr2 = row[2]
            attacktype = row[4]
            url = row[5]
            massorsingle = row[6]
            data = date_str

            if timedelta(minutes=0) < time_diff <= timedelta(minutes=1):  # Sprawdź, czy do daty brakuje 1 minut
                if len(rows) == 1:
                    znaleziono_date = True
                is_successful, message, attack_units, size = send_attack(id_record, parametr1, parametr2, attacktype,
                                                                         url, massorsingle, data)

                if is_successful:
                    print("Wysłano atak pomyślnie!")
                    conn = sqlite3.connect('data.db')
                    c = conn.cursor()
                    attack_units_json = json.dumps(attack_units)

                    c.execute(
                        "INSERT INTO wyslane(parametr1, parametr2, data, attacktype,size, units) VALUES (?, ?, ?, ?,?,?)",
                        (parametr1, parametr2, data, attacktype, size, attack_units_json))
                    conn.commit()
                else:
                    print("Nie udało się wysłać ataku. Powód:", message)
                    conn = sqlite3.connect('data.db')
                    c = conn.cursor()
                    c.execute(
                        "INSERT INTO niewyslane(parametr1, parametr2, data, attacktype, reason, url, massorsingle) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (parametr1, parametr2, data, attacktype, message, url, massorsingle))
                    c.execute("DELETE FROM data WHERE id = ?", (id_record,))
                    conn.commit()

        conn.close()
        if not znaleziono_date:
            time.sleep(10)

    return True, "Zakończono działanie programu."
