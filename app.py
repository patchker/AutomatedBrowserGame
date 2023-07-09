import json
import re
import time
import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template
from flask import redirect, url_for
from flask import request, jsonify
from flask_cors import CORS
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import pandas as pd
from collections import defaultdict
import sqlite3
from datetime import datetime, timedelta
import math
import scripto
import os
import signal
from urllib.parse import urlparse, parse_qs
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


print("""
              _       _     _               _              
  _ __   __ _| |_ ___| |__ | | _____ _ __  (_)_ __   ___   
 | '_ \ / _` | __/ __| '_ \| |/ / _ \ '__| | | '_ \ / __|  
 | |_) | (_| | || (__| | | |   <  __/ |    | | | | | (__ _ 
 | .__/ \__,_|\__\___|_| |_|_|\_\___|_|    |_|_| |_|\___(_)
 |_|                                                
""")
app = Flask(__name__)


@app.before_first_request
def init_db():
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS data
(id INTEGER PRIMARY KEY AUTOINCREMENT, parametr1 TEXT, parametr2 TEXT, parametr3 TEXT, parametr4 TEXT, parametr5 TEXT, parametr6 TEXT, parametr7 TEXT, parametr8 TEXT, parametr9 TEXT )''')
    # Dodaj na początku kodu, np. po otwarciu połączenia z bazą danych
    c.execute('''
        CREATE TABLE IF NOT EXISTS wyslane (
            id INTEGER PRIMARY KEY,
            parametr1 TEXT,
            parametr2 TEXT,
            data TEXT,
            attacktype TEXT,
            size INT,
            units TEXT
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS niewyslane (
            id INTEGER PRIMARY KEY,
            parametr1 TEXT,
            parametr2 TEXT,
            data TEXT,
            attacktype TEXT,
            reason TEXT,
            url TEXT,
            massorsingle TEXT
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS wojska (
            id INTEGER PRIMARY KEY,
            coords TEXT,
            unit_count TEXT
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS przybywajace (
            id INTEGER PRIMARY KEY,
            defender_coords TEXT,
            attacker_coords TEXT,
            arrival_time TEXT
        )
    ''')
    # Sprawdź, czy tabela już istnieje
# check if table exists
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='server_status'")
    if not c.fetchone():
        # if table doesn't exist, create it
        c.execute("CREATE TABLE server_status (id INTEGER PRIMARY KEY, status TEXT)")
        c.execute("INSERT INTO server_status (status) VALUES (?)", ('inactive',))
    conn.commit()
    conn.close()




@app.route('/shutdown', methods=['POST'])
def shutdown():
    print("Shutting down gracefully...")
    # Aktualizacja stanu serwera w bazie danych
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute("UPDATE server_status SET status = 'inactive' WHERE id = 1")
    conn.commit()
    conn.close()
    return 'Server shutting down...'
@app.route('/status', methods=['GET'])
def status():
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute('SELECT status FROM server_status')
    server_status = c.fetchone()
    conn.close()
    return {'status': server_status[0]}

@app.route('/getDataFromSite')
def getDataFromSite():

    options = Options()
    options.add_argument('--user-data-dir=/path/to/user-data')
    options.add_argument('--profile-directory=Default')
    options.add_argument("--start-minimized")
    options.add_extension("windscribe.crx")
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')

    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537")
    driver = webdriver.Chrome(options=options)
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
        challenge_container = driver.find_element(By.XPATH, "//span[text()='Świat 182']")
        challenge_container.click()
    except:
        return False, "E.04 - Nie znaleziono swiata 182"

    try:
        challenge_container = driver.find_element(By.CLASS_NAME, "popup_box_close")
        challenge_container.click()
    except:
        pass

    try:
        element = driver.find_element(By.XPATH, '//a[contains(text(), "Kombinowany ")]')
        element.click()
        time.sleep(1)
    except:
        pass

    try:
        element = driver.find_element(By.CLASS_NAME, "group-menu-item")
        element.click()
        time.sleep(1)
    except:
        pass

    current_url = driver.current_url

    response = requests.get(current_url)

    if response.status_code == 200:
        html_content = response.text

    # Pobierz kod źródłowy strony
    html_content = driver.page_source

    # Przetwarzanie kodu HTML za pomocą BeautifulSoup
    soup = BeautifulSoup(html_content, "html.parser")


    # Szukamy wszystkich wierszy w tabeli
    rows = soup.find('table', {'id': 'combined_table'}).find_all('tr')

    # Pomijamy pierwszy wiersz, ponieważ zawiera on nagłówki
    rows = rows[1:]
    results = []
    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    # Przechodzimy przez każdy wiersz i zbieramy informacje
    for row in rows:
        # Szukamy linku do wioski, który zawiera jej nazwę i koordynaty
        village_link = row.find('a', href=True)

        # Wydobywamy koordynaty z nazwy wioski
        name_and_coords = village_link.text
        coords = name_and_coords.split('(')[-1].split(')')[0]
        x, y = coords.split('|')

        # Szukamy ilości wojsk w wiosce
        units = row.find_all('td', {'class': 'unit-item'})
        unit_counts = [int(unit.text) for unit in units if unit.text != '']

        print(f"Wioska: {name_and_coords}")
        print(f"Koordynaty: X={x}, Y={y}")
        print(f"Ilość wojsk: {unit_counts}")
        # Dodaj dane do tabeli
        c.execute("INSERT INTO wojska (coords, unit_count) VALUES (?, ?)",
                  (coords, ','.join(map(str, unit_counts))))

        print("Inserting:", coords, " ", unit_counts)

        conn.commit()

    conn.close()
    driver.quit()
    return True


@app.route('/getDataFromSite')
def getPrzybywajaceFromSite():

    options = Options()
    options.add_argument('--user-data-dir=/path/to/user-data')
    options.add_argument('--profile-directory=Default')
    options.add_argument("--start-minimized")
    options.add_extension("windscribe.crx")
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')

    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537")
    driver = webdriver.Chrome(options=options)
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
        challenge_container = driver.find_element(By.XPATH, "//span[text()='Świat 182']")
        challenge_container.click()
    except:
        return False, "E.04 - Nie znaleziono swiata 182"

    try:
        challenge_container = driver.find_element(By.CLASS_NAME, "popup_box_close")
        challenge_container.click()
    except:
        pass

    try:
        element = driver.find_element(By.ID, 'incomings_amount')
        element.click()
        time.sleep(1)
    except:
        pass

    try:
        element = driver.find_element(By.CLASS_NAME, "group-menu-item")
        element.click()
        time.sleep(1)
    except:
        pass

    current_url = driver.current_url

    response = requests.get(current_url)

    if response.status_code == 200:
        html_content = response.text

    # Pobierz kod źródłowy strony
    html_content = driver.page_source

    # Przetwarzanie kodu HTML za pomocą BeautifulSoup
    soup = BeautifulSoup(html_content, "html.parser")

    # Szukamy wszystkich wierszy w tabeli
    rows = soup.find('table', {'id': 'incomings_table'}).find_all('tr')
    print(rows)

    # Pomijamy pierwszy wiersz, ponieważ zawiera on nagłówki
    rows = rows[1:]
    results = []
    conn = sqlite3.connect("data.db")
    c = conn.cursor()

    data = []
    for row in rows[1:]:
        cols = row.find_all('td')

        try:
            target = re.search(r'\((\d+\|\d+)\)', cols[1].find('a').get_text(strip=True)).group(1)
            origin = re.search(r'\((\d+\|\d+)\)', cols[2].find('a').get_text(strip=True)).group(1)
            arrival_time_str = cols[5].get_text(strip=True)

            # Sprawdź, czy jest to data "dzisiaj" czy "jutro" i przetwórz ją odpowiednio
            if "dzisiaj" in arrival_time_str:
                date_str = datetime.today().strftime('%Y-%m-%d')
            elif "jutro" in arrival_time_str:
                date_str = (datetime.today() + timedelta(days=1)).strftime('%Y-%m-%d')
            else:
                # jeśli nie jest ani "dzisiaj" ani "jutro", po prostu zignoruj
                continue

            # Usuń "dzisiaj o " lub "jutro o " z arrival_time_str
            time_str = re.search(r'(\d+:\d+:\d+:\d+)', arrival_time_str).group(1)

            # Połącz date_str i time_str
            arrival_time = date_str + ' ' + time_str
            data.append({
                'target': target,
                'origin': origin,
                'arrival_time': arrival_time
            })
            # Dodaj dane do tabeli
            c.execute("INSERT INTO przybywajace (defender_coords, attacker_coords,arrival_time) VALUES (?, ?, ?)",
                      (target, origin, arrival_time))
            conn.commit()

            print("Inserting:", target, " ", origin," ", arrival_time)

        except IndexError:
            print("Błąd w parsowaniu wiersza.")

        #print(data)

        # Dodaj dane do tabeli
        #c.execute("INSERT INTO przybywajace (defender_coords, attacker_coords, arrival_time) VALUES (?, ?, ?)",
          #        (target_coords, source_coords, arrival_time))



       # print("Inserting:", target_coords, " ", source_coords, " ", arrival_time)


    conn.close()
    driver.quit()
    return True


@app.route('/secret')
def secret():

    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute('SELECT * FROM wojska')
    results = c.fetchall()
    conn.close()

    # Przekształć wyniki
    transformed_results = []
    for result in results:
        # Zamień ciąg znaków '0,0,0,0,0,0,0,0,0,0,0' na listę liczb [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        units_as_list = [int(x) for x in result[2].split(',')]
        transformed_result = (result[0], result[1], units_as_list)
        transformed_results.append(transformed_result)
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute('SELECT * FROM przybywajace')
    results2 = c.fetchall()
    conn.close()
    # załóżmy, że `results2` jest listą krotek
    df = pd.DataFrame(results2, columns=['ID', 'Obrońca', 'Atakujący', 'Data wejścia'])

    grouped_results = df.groupby('Obrońca')

    return render_template('secret.html', results=transformed_results, results2 = grouped_results)  # Przekazujemy wyniki do szablonu

@app.route('/secretUpdate')
def secretUpdate():
    results = getDataFromSite()
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute('SELECT * FROM wojska')
    results = c.fetchall()
    conn.close()
    # Przekształć wyniki
    transformed_results = []
    for result in results:
        # Zamień ciąg znaków '0,0,0,0,0,0,0,0,0,0,0' na listę liczb [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        units_as_list = [int(x) for x in result[2].split(',')]
        transformed_result = (result[0], result[1], units_as_list)
        transformed_results.append(transformed_result)

    print("Wypisywanie updata: ",results)
    return render_template('secret.html', results=results)  # Przekazujemy wyniki do szablonu



import random

@app.route('/fejkgen', methods=['GET', 'POST'])
def fejkgen():
    liczba = int(request.form.get('liczba'))
    lista = request.form.get('lista').split(' ')
    random.shuffle(lista)  # shuffle the targets
    data = request.form.get('data')
    target_date = datetime.strptime(data, '%Y-%m-%d')  # adjust to your datetime format
    used_start_times = []  # change this to a list

    conn = sqlite3.connect('data.db')  # connect to your sqlite3 database
    c = conn.cursor()

    c.execute("SELECT * FROM wojska")
    my_villages = c.fetchall()
    print(my_villages)
    ataki = []
    attacks_from_village = defaultdict(int)  # stores how many attacks we sent from each village

    used_attack_intervals = []  # store all used attack intervals

    for my_village in my_villages:
        my_coords = tuple(map(int, my_village[1].split('|')))
        for enemy_coords_str in lista:
            enemy_coords = tuple(map(int, enemy_coords_str.split('|')))

            # check if we can still send attacks from this village
            if attacks_from_village[my_village[0]] >= liczba:
                continue

            distance = math.sqrt((enemy_coords[0] - my_coords[0]) ** 2 + (enemy_coords[1] - my_coords[1]) ** 2)
            travel_time = timedelta(minutes=distance * 30)  # minutes

            max_attempts = 200
            for attempt in range(max_attempts):
                # generate a random arrival time between 7:00 and 22:59 on the target date
                random_hour = random.randint(7, 22)
                random_minute = random.randint(0, 59)
                arrival_time = target_date.replace(hour=random_hour, minute=random_minute)

                # calculate start time
                start_time = arrival_time - travel_time

                # calculate end time (one minute after start time)
                end_time = start_time + timedelta(minutes=1)

                # check if start time is later than current time, hasn't been used yet
                current_time = datetime.now()
                if start_time < current_time or not (7 <= arrival_time.hour <= 22):
                    # this attack cannot be launched, arrival time is not suitable
                    continue

                # check if this attack overlaps with any of the previous attacks
                if any(start_time < interval_end and end_time > interval_start for interval_start, interval_end in used_attack_intervals):
                    # this attack cannot be launched, its time interval overlaps with one of the previous attacks
                    continue

                print(f'Atak z {my_coords} na {enemy_coords} wychodzi o {start_time} i dociera o {arrival_time}')
                ataki.append({
                    'wioska': '|'.join(map(str, my_coords)),
                    'cel': '|'.join(map(str, enemy_coords)),
                    'czas': arrival_time.replace(microsecond=0).isoformat() + '.000',
                    'czas_startu': start_time.replace(microsecond=0).isoformat() + '.000',
                    'travel_time': travel_time.total_seconds() / 60
                })

                attacks_from_village[my_village[0]] += 1  # increment the number of attacks sent from this village
                lista.remove(enemy_coords_str)  # remove the selected target from the list to ensure it's not picked again
                used_attack_intervals.append((start_time, end_time))  # add the time interval to the list of used intervals

                break  # we found a target, no need to continue while loop

    return render_template('fejkgenaccept.html', ataki=ataki)  # Przekazujemy wyniki do szablonu

@app.route('/przybywajaceUpdate')
def przybywajaceUpdate():
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute('DELETE FROM przybywajace')
    conn.commit()
    conn.close()

    results = getPrzybywajaceFromSite()
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute('SELECT * FROM przybywajace')
    results2 = c.fetchall()
    conn.close()


    print("Wypisywanie updata: ",results2)
    return render_template('secret.html', results2=results2)  # Przekazujemy wyniki do szablonu


@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        global script_enabled
        script_enabled = True
        global is_stopping
        is_stopping = False
        print("[STARTED]")
        conn = sqlite3.connect('data.db')
        c = conn.cursor()
        c.execute("UPDATE server_status SET status = 'active' WHERE id = 1")
        conn.commit()
        conn.close()
        wynik = scripto()

        return render_template('wynik.html', wynik=wynik)

    # Połącz się z bazą danych
    conn = sqlite3.connect('data.db')
    c = conn.cursor()

    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute('SELECT parametr3 FROM data ORDER BY id DESC LIMIT 1')
    ostatni_atak = c.fetchone()
    c.execute('SELECT COUNT(*) FROM data')
    ilosc_niewyslanych = c.fetchone()[0]
    conn.close()

    # Przekazuj informacje do szablonu
    return render_template('index.html', ostatni_atak=ostatni_atak, ilosc_niewyslanych=ilosc_niewyslanych)


@app.route('/debug', methods=['GET', 'POST'])
def debug():
    if request.method == 'POST':
        wynik = uruchom_debug()

        return render_template('wynik.html', wynik=wynik)


    return render_template('index.html')

def uruchom_debug():
    is_successful, message = debug()

    if is_successful:
        return message
    else:
        return f"Błąd: {message}"

def debug():
    options = Options()
    options.add_argument('--user-data-dir=/path/to/user-data')
    options.add_argument('--profile-directory=Default')
    options.add_argument("--start-minimized")
    options.add_extension("windscribe.crx")
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')

    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537")
    driver = webdriver.Chrome(options=options)
    time.sleep(1)
    driver.get("https://plemiona.pl")
    time.sleep(600)

@app.route('/update_data', methods=['GET'])
def update_data():
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute('SELECT data FROM wyslane ORDER BY id DESC LIMIT 1')
    ostatni_atak = c.fetchone()

    c.execute('SELECT COUNT(*) FROM wyslane')
    ilosc_wyslanych = c.fetchone()[0]




    c.execute('SELECT COUNT(*) FROM niewyslane')
    ilosc_niewyslanych = c.fetchone()[0]

    c.execute('SELECT COUNT(*) FROM data')
    ilosc_kolejka = c.fetchone()[0]


    conn.close()

    if ostatni_atak is not None:
        ostatni_atak = [(ostatni_atak[0][-12:-4],)]
    else:
        ostatni_atak= " - "

    if ilosc_wyslanych is None:
        ilosc_wyslanych=" - "

    if ilosc_niewyslanych is None:
        ilosc_niewyslanych=" - "

    if ilosc_kolejka is None:
        ilosc_kolejka=" - "

    # zwróć dane jako JSON
    return jsonify({'ostatni_atak': ostatni_atak, 'ilosc_wyslanych': ilosc_wyslanych, 'ilosc_niewyslanych':ilosc_niewyslanych, 'ilosc_kolejka':ilosc_kolejka})


@app.route('/save', methods=['GET', 'POST'])
def save():
    return render_template('zapisz.html')


@app.route('/lista')
def lista():
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute('SELECT * FROM data order by parametr3')
    rekordy = c.fetchall()
    conn.close()

    # Zlicz różne typy ataków
    licznik_typow_atakow = {
        'FAKE': 0,
        'OFF': 0,
        'BURZAK': 0,
        'FAKE SZLACHCIC': 0,
        'SZLACHCIC': 0
    }
    for rekord in rekordy:
        typ_ataku = rekord[4]
        if typ_ataku and typ_ataku.startswith('BURZAK'):
            licznik_typow_atakow['BURZAK'] += 1
        elif typ_ataku in licznik_typow_atakow:
            licznik_typow_atakow[typ_ataku] += 1

    return render_template('lista.html', rekordy=rekordy, licznik_typow_atakow=licznik_typow_atakow)



@app.route('/wyslane')
def wyslane():
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute('SELECT * FROM wyslane order by data')
    rekordy = c.fetchall()

    for i, rekord in enumerate(rekordy):
        rekordy[i] = list(rekord)
        rekordy[i][6] = json.loads(rekordy[i][6])

    conn.close()
    return render_template('wyslane.html', rekordy=rekordy)



@app.route('/niewyslane')
def niewyslane():
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute('SELECT * FROM niewyslane order by data')
    rekordy = c.fetchall()
    conn.close()
    return render_template('niewyslane.html', rekordy=rekordy)


@app.route('/usun/<int:id>', methods=['POST'])
def usun(id):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute("DELETE FROM data WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('lista'))


@app.route('/wyslane_delete_all', methods=['POST'])
def wyslane_delete_all():
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute("DELETE FROM wyslane ")
    conn.commit()
    conn.close()
    return redirect(url_for('wyslane'))


@app.route('/burzaki_delete_all', methods=['POST'])
def burzaki_delete_all():
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute("DELETE FROM data WHERE parametr4 LIKE 'BURZAK%'")
    conn.commit()
    conn.close()
    return redirect(url_for('lista'))
@app.route('/grubasy_delete_all', methods=['POST'])
def grubasy_delete_all():
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute("DELETE FROM data where parametr4='SZLACHCIC'")
    conn.commit()
    conn.close()
    return redirect(url_for('lista'))

@app.route('/fejkgrubasy_delete_all', methods=['POST'])
def fejkgrubasy_delete_all():
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute("DELETE FROM data where parametr4='FAKE SZLACHCIC'")
    conn.commit()
    conn.close()
    return redirect(url_for('lista'))


@app.route('/niewyslane_delete_all', methods=['POST'])
def niewyslane_delete_all():
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute("DELETE FROM niewyslane ")
    conn.commit()
    conn.close()
    return redirect(url_for('niewyslane'))


@app.route('/lista_delete_all', methods=['POST'])
def lista_delete_all():
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute("DELETE FROM data ")
    conn.commit()
    conn.close()
    return redirect(url_for('lista'))


@app.route('/usun_niewyslane/<int:id>', methods=['POST'])
def usun_niewyslane(id):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute("DELETE FROM niewyslane WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('niewyslane'))


@app.route('/usun_wyslane/<int:id>', methods=['POST'])
def usun_wyslane(id):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute("DELETE FROM wyslane WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('wyslane'))


@app.route('/restore/<int:id>', methods=['POST'])
def restore(id):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()

    # Pobieranie rekordu z tabeli 'data' na podstawie id
    c.execute("SELECT * FROM niewyslane WHERE id=?", (id,))
    record = c.fetchone()
    print("Record1",record)
    record = record[1:]
    #record = record[:-2] + record[-1:]
    record = record[:4] + record[5:]

    print("Record2",record)

    if record:
        # Wstawianie rekordu do tabeli 'wyslane'
        c.execute('''
            INSERT INTO data (parametr1, parametr2, parametr3, parametr4, parametr5, parametr6)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', record)
        print("Record:",record)

        # Usuwanie rekordu z tabeli 'data'
        c.execute("DELETE FROM niewyslane WHERE id=?", (id,))

        conn.commit()
        conn.close()
    return redirect(url_for('lista'))


@app.route('/edytuj/<int:id>', methods=['GET', 'POST'])
def edytuj(id):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()

    if request.method == 'POST':
        parametr1 = request.form.get('parametr1')
        parametr2 = request.form.get('parametr2')
        parametr3 = request.form.get('parametr3')
        parametr4 = request.form.get('parametr4')
        parametr8 = request.form.get('parametr8')
        parametr9 = request.form.get('parametr9')


        # Sprawdzenie i poprawienie wartości parametr3
        try:
            dt = datetime.strptime(parametr3, "%Y-%m-%dT%H:%M:%S.%f")
        except ValueError:
            try:
                dt = datetime.strptime(parametr3, "%Y-%m-%dT%H:%M:%S.%f")
                miliseconds = dt.strftime("%f")
                while len(miliseconds) < 3:
                    miliseconds += '0'
                parametr3 = dt.strftime("%Y-%m-%dT%H:%M:%S.") + miliseconds
            except ValueError:
                dt = datetime.strptime(parametr3, "%Y-%m-%dT%H:%M:%S")
                parametr3 = dt.strftime("%Y-%m-%dT%H:%M:%S") + '.000'

        # Poprawka dla milisekund
        dt = datetime.strptime(parametr3, "%Y-%m-%dT%H:%M:%S.%f")
        miliseconds = dt.strftime("%f")[:3]
        while len(miliseconds) < 3:
            miliseconds += '0'
        parametr3 = dt.strftime("%Y-%m-%dT%H:%M:%S.") + miliseconds

        c.execute("UPDATE data SET parametr1=?, parametr2=?, parametr3=?, parametr4=?, parametr8=?, parametr9=? WHERE id=?",
                  (parametr1, parametr2, parametr3, parametr4, parametr8, parametr9, id))
        conn.commit()
        conn.close()
        return redirect(url_for('lista'))
    else:
        c.execute("SELECT * FROM data WHERE id=?", (id,))
        rekord = c.fetchone()
        conn.close()
        return render_template('edytuj.html', rekord=rekord)


@app.route('/zapisz', methods=['POST'])
def zapisz():
    parametr1 = request.form.get('parametr1')
    parametr2 = request.form.get('parametr2')
    parametr3 = request.form.get('parametr3')
    parametr4 = request.form.get('parametr4')
    parametr5 = request.form.get('parametr5')
    parametr7 = request.form.get('parametr7')
    parametr8 = request.form.get('parametr8')
    parametr9 = request.form.get('parametr9')



    # Sprawdzenie i poprawienie wartości parametr3
    try:
        dt = datetime.strptime(parametr3, "%Y-%m-%dT%H:%M:%S.%f")
    except ValueError:
        try:
            dt = datetime.strptime(parametr3, "%Y-%m-%dT%H:%M:%S.%f")
            miliseconds = dt.strftime("%f")
            while len(miliseconds) < 3:
                miliseconds += '0'
            parametr3 = dt.strftime("%Y-%m-%dT%H:%M:%S.") + miliseconds
        except ValueError:
            dt = datetime.strptime(parametr3, "%Y-%m-%dT%H:%M:%S")
            parametr3 = dt.strftime("%Y-%m-%dT%H:%M:%S") + '.000'

    # Poprawka dla milisekund
    dt = datetime.strptime(parametr3, "%Y-%m-%dT%H:%M:%S.%f")
    miliseconds = dt.strftime("%f")[:3]
    while len(miliseconds) < 3:
        miliseconds += '0'
    parametr3 = dt.strftime("%Y-%m-%dT%H:%M:%S.") + miliseconds

    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    c.execute("INSERT INTO data (parametr1, parametr2, parametr3, parametr4, parametr5, parametr6,parametr7,parametr8, parametr9) VALUES (?, ?, ?,?,?,?,?,?,?)",
              (parametr1, parametr2, parametr3, parametr4, parametr5, "0", parametr7, parametr8, parametr9))
    conn.commit()
    conn.close()

    return redirect(url_for('lista'))


@app.route('/massadding')
def massadding():
    return render_template('massadding.html')



@app.route('/process_text', methods=['POST'])
def process_text():
    text = request.form.get('input_text')

    # dzielimy tekst na linie
    lines = text.split('[*]')

    # pomiń nagłówek tabeli
    lines = lines[1:]

    attacks = []


    # iteracja przez każdą linię
    for line in lines:
        if line:
            # tworzymy słownik do przechowywania informacji o ataku
            attack = {}


            # dodajemy url do słownika
            url = re.search(r'\[url=(.*?)\]', line)
            if url:
                attack['url'] = url.group(1)
                print(attack['url'])
            attack_type_and_column = re.search(r'\[\|\].*?\[\|\](.*?)\[\|\](.*?)\[\|\]', line)
            if attack_type_and_column:
                attack_type = attack_type_and_column.group(1)
                next_column = attack_type_and_column.group(2)
                print("attack type:", attack_type)
                print("next column:", next_column)

                if 'fake gruby' in attack_type:
                    attack['type'] = 'FAKE SZLACHCIC'
                elif 'fake' in attack_type:
                    attack['type'] = 'FAKE'
                elif 'Katapulty' in attack_type:
                    units_building = attack_type.split('-')
                    attack['type'] = 'BURZAK - '+units_building[1]+" - "+units_building[2]
                else:
                    if int(next_column)>0:
                        attack['type'] = 'SZLACHCIC'
                        units = re.search(r'\[\|\](\d+)', line)
                        if units:
                            attack['units'] = int(units.group(1))
                    else:
                        attack['type'] = 'OFF'
                        # dodanie ilości jednostek do ataku typu OFF
                        units = re.search(r'\[\|\](\d+)', line)
                        if units:
                            attack['units'] = int(units.group(1))


            date_time = re.search(
                r'\[\|\](\d{4}-\d{2}-\d{2})\s*\[b\]\[color=#\w{6}\](\d{2}:\d{2}:\d{2})\[/color\]\[/b\]-\[b\]\[color=#\w{6}\](\d{2}:\d{2}:\d{2})\[/color\]\[/b\]',
                line)

            if date_time:
                date = date_time.group(1)
                time1 = date_time.group(2)
                time2 = date_time.group(3)
                attack['date'] = f'{date} {time1} {time2}'

            # koordynaty
            coords = re.findall(r'\[coord\](.*?)\[/coord\]', line)
            if coords:
                attack['from_village'] = coords[0]
                attack['target'] = coords[1]

            attacks.append(attack)

    return render_template('table_page.html', table_data=attacks)


@app.route('/add_to_db', methods=['POST'])
def add_to_db():
    types = request.form.getlist('type')
    dates = request.form.getlist('date')
    from_villages = request.form.getlist('from_village')
    targets = request.form.getlist('target')
    urls = request.form.getlist('url')  # dodajemy odczytywanie url
    units = request.form.getlist('units')
    conn = sqlite3.connect("data.db")
    c = conn.cursor()

    # Lista przechowująca wszystkie wcześniej wylosowane czasy ataków
    attack_times = []

    for i in range(len(types)):
        type = types[i]
        date = dates[i]
        from_village = from_villages[i]
        target = targets[i]
        url = urls[i]  # przypisujemy url
        units2=units[i]


        date_str, start_time_str, end_time_str = date.split(' ')

        start_time = datetime.strptime(date_str + ' ' + start_time_str, '%Y-%m-%d %H:%M:%S')
        end_time = datetime.strptime(date_str + ' ' + end_time_str, '%Y-%m-%d %H:%M:%S')

        # Jeżeli end_time jest wcześniejszy niż start_time, dodajemy jeden dzień do end_time
        if end_time < start_time:
            end_time += timedelta(days=1)

        time_range = end_time - start_time
        if time_range.total_seconds() > 0:

            while True:
                random_seconds = random.randrange(int(time_range.total_seconds()))
                random_time = start_time + timedelta(seconds=random_seconds)

                if all(abs((random_time - old_time).total_seconds()) >= 60 for old_time in attack_times):
                    break
            attack_times.append(random_time)

            attack_time = random_time.strftime('%Y-%m-%dT%H:%M:%S.%f')
            attack_time = attack_time[:-3]

            parsed_url = urlparse(url)
            query_params = parse_qs(parsed_url.query)
            source_village = query_params.get('village', [''])[0]
            target_village = query_params.get('target', [''])[0]

            c.execute("INSERT INTO data (parametr4, parametr3, parametr1, parametr2, parametr5,parametr6, parametr7,parametr8, parametr9) VALUES (?, ?, ?, ?, ?,?, ?, ?, ?)",
                      (type, attack_time, from_village, target, url,"1",units2, source_village, target_village))  # dodajemy url do zapytania SQL
    conn.commit()
    conn.close()
    return redirect(url_for('lista'))



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
            units_to_send = row[7]
            units_to_send = int(units_to_send)
            id1 = row[8]
            id2 = row[9]
            x_str, y_str = parametr2.split("|")
            x = int(x_str)
            y = int(y_str)
            koordynaty_tuple = (x, y)
            attack_units = {
            "spear": 150,
            "sword": 0,
            "axe": 0,
            "spy": 0,
            "light": 0,
            "heavy": 0,
            "ram": 0,
            "catapult": 0,
            "knight": 0,
            "snob": 0,
            }

            if timedelta(minutes=0) < time_diff <= timedelta(minutes=1):  # Sprawdź, czy do daty brakuje 1 minut
                if len(rows) == 1:
                    znaleziono_date = True
                attack_result = test_send(id1, koordynaty_tuple, "8670")
                if attack_result:
                    print("Wysłano atak pomyślnie!")
                    conn = sqlite3.connect('data.db')
                    c = conn.cursor()
                    attack_units_json = json.dumps(attack_units)

                    c.execute(
                        "INSERT INTO wyslane(parametr1, parametr2, data, attacktype,size, units) VALUES (?, ?, ?, ?,?,?)",
                        (parametr1, parametr2, data, attacktype, 6435, attack_units_json))
                    c.execute("DELETE FROM data WHERE id = ?", (id_record,))

                    conn.commit()
                else:
                    print("Nie udało się wysłać ataku. Powód:")
                    conn = sqlite3.connect('data.db')
                    c = conn.cursor()
                    c.execute(
                        "INSERT INTO niewyslane(parametr1, parametr2, data, attacktype, reason, url, massorsingle) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (parametr1, parametr2, data, attacktype, "ggfdgdf", url, massorsingle))
                    c.execute("DELETE FROM data WHERE id = ?", (id_record,))
                    conn.commit()

        conn.close()
        if not znaleziono_date:
            time.sleep(10)

    return True, "Zakończono działanie programu."



@app.route('/cookie_string', methods=['POST'])
def cookie_string():
    cookies = {}
    cookie_value = request.form.get('cookie_string')

    pairs = cookie_value.split("; ")
    for pair in pairs:
        if '=' in pair:  # Sprawdzenie, czy ciasteczko zawiera znak =
            key, value = pair.split("=")
            cookies[key] = value
        else:
            print(f"Nieprawidłowe ciasteczko: {pair}")

    # Zapisywanie do pliku
    with open('cookies.json', 'w') as f:
        json.dump(cookies, f)

    return redirect(url_for('home'))


def load_cookies():
    # Wczytywanie z pliku
    with open('cookies.json', 'r') as f:
        cookies = json.load(f)

    return cookies


# pobieranie ilości aktualnych wojsk
def collect_and_assign_units(html_content):
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
        "knight": "units_entry_all_knight",
        "snob": "units_entry_all_snob"

    }

    soup = BeautifulSoup(html_content, 'html.parser')
    units = {}
    for unit, id in units_dict.items():
        element = soup.find(id=id)
        if element is not None:
            text = element.text
            text = text[1:-1]  # usuń nawiasy
            units[unit] = int(text)
    return units



# WYBÓR JEDNOSTEK DLA FAKE
def fake_units(units2, capacity):
    unit_size = {'spear': 1, 'sword': 1, 'axe': 1, 'archer': 1, 'spy': 2, 'light': 4, 'heavy': 6, 'ram': 5,
                 'catapult': 8, 'snob': 100, 'marcher': 5, 'knight': 10 }
    units = {k: v for k, v in units2.items()}

    # Wstępne ustawienie jednostek do ataku
    attack_units = {unit: 0 for unit in units}  # Initialize all units to 0


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



def burzak_units(units, number):
    units_chosen = {unit: 0 for unit in units}  # Initialize all units to 0
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
def off_units(units):
    units_chosen = {unit: 0 for unit in units}  # Initialize all units to 0
    if units['ram'] < 21:
        units_chosen['ram'] = 0
    else:
        units_chosen['ram'] = units['ram'] - 20

    if units['spy'] < 10:
        units_chosen['spy'] = 0
    else:
        units_chosen['spy'] = 10

    units_chosen['axe'] = units['axe'] - 300
    units_chosen['light'] = units['light'] - 150
    units_chosen['spy'] = 10
    units_chosen['marcher'] = units['marcher']
    return units_chosen


# WYBÓR JEDNOSTEK DLA FAKE GRUBASA
def fake_grubas_units(units):
    units_chosen = {unit: 0 for unit in units}  # Initialize all units to 0

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

def grubas_units(posiadane, limit):
    unit_size = {'spear': 1, 'sword': 1, 'axe': 1, 'archer': 1, 'spy': 2, 'light': 4, 'marcher': 5, 'heavy': 6, 'ram': 5, 'catapult': 8, 'snob': 100}
    unit_order = [['axe', 'light', 'ram', 'marcher'], ['heavy'], ['spear', 'sword', 'archer']]

    if 'snob' in posiadane and posiadane['snob'] > 0:
        units_chosen = {'snob': 1}
        posiadane['snob'] -= 1
        limit -= unit_size['snob']
    else:
        raise ValueError("Brak jednostki 'snob' do dodania do ataku.")

    total_units = sum(posiadane[unit]*unit_size[unit] for unit in posiadane)
    if total_units < 0.5*limit:
        return False, "Dostępne jednostki stanowią mniej niż 50% limitu.", 0, "Brak"

    for unit_group in unit_order:
        group_units = sum(posiadane.get(unit, 0)*unit_size[unit] for unit in unit_group)
        while group_units > 0 and limit > 0:
            units_taken_in_this_round = 0
            for unit in unit_group:
                if unit in posiadane and posiadane[unit] > 0 and limit >= unit_size[unit]: # Ensure there's room for at least one unit of this type
                    group_ratio = posiadane[unit]*unit_size[unit] / group_units if group_units > 0 else 0
                    units_to_take = min(limit // unit_size[unit], int(group_ratio * limit // unit_size[unit]))
                    units_chosen[unit] = units_to_take
                    limit -= units_to_take * unit_size[unit]
                    group_units -= units_to_take * unit_size[unit] # Update group_units to reflect taken units
                    posiadane[unit] -= units_to_take  # Update posiadane to reflect taken units
                    units_taken_in_this_round += units_to_take
            if limit <= 0 or units_taken_in_this_round == 0:
                break  # stop if limit is reached or no units can be taken in this round

    return units_chosen

@app.route('/elo/<id1>/<id2>/<target_coords>/<attacktype>', methods=['GET'])
def elo(id1, id2,target_coords, attacktype):
    x_str, y_str = target_coords.split("|")
    x = int(x_str)
    y = int(y_str)
    koordynaty_tuple = (x, y)
    #attack_result = test_send(id1, koordynaty_tuple, id2 ,units)
    #attack_result = test_send(id1, (475,573), "8670", attacktype)
    attack_result = test_send(id1, koordynaty_tuple, id2, attacktype)

    return jsonify(success=attack_result)


def test_send(source_village, target_coords, target_id, attacktype):
    session = requests.Session()


    cookies = load_cookies()

    print(cookies)

    session.cookies.update(cookies)


    base_url = "https://pl182.plemiona.pl/game.php?village={}&screen=place&target="+target_id

    # Step 1: Zapytanie GET
    url = base_url.format(source_village)
    response = session.get(url)
    if response.status_code != 200:
        print(f"GET request failed with status code {response.status_code}")
        return False
    
    soup = BeautifulSoup(response.text, 'html.parser')
    with open("test.html", "w") as file:
        formatted_html = soup.prettify()
        file.write(formatted_html)

    # szukaj alertu
    pattern = re.compile(r"StartPage\.noticeBox\.show\('Twoja sesja wygasła\. Prosimy zalogować się jeszcze raz\.', 'error'\);")
    match = pattern.search(formatted_html)
        # sprawdź, czy alert jest wyświetlany
    if match:
        print('[INFO] LOGGED OUT, PLEASE ENTER NEW COOKIE STRING.')
        return False
    

    my_units = collect_and_assign_units(response.text)
    print(my_units)

    if attacktype=="FAKE":
        units = fake_units(my_units,110)
    elif attacktype=="OFF":
        units = off_units(my_units)
    elif attacktype[:6] == "BURZAK":
        units = burzak_units(my_units,50)
    elif attacktype == "FAKE SZLACHCIC":
        units = fake_grubas_units(my_units)
    elif attacktype == "SZLACHCIC":
        units = grubas_units(my_units)
    else:
        return False
    
    print("Units: ", units)





    input_element = soup.find('input', {'name': '6890717f4d46c2ecf6952e'})
    value = input_element['value']

    print("[GET] ", url)




    # Step 2: Pierwsze zapytanie POST
    base_url = "https://pl182.plemiona.pl/game.php?village={}&screen=place&try=confirm"
    url = base_url.format(source_village)
    data = {
        "units": value,
        "template_id": "",
        "source_village": source_village,
        # Wstaw jednostki tutaj
        "spear": units['spear'],
        "sword": units['sword'],
        "axe": units['axe'],
        "archer": units['archer'],
        "spy": units['spy'],
        "light": units['light'],
        "marcher": units['marcher'],
        "heavy": units['heavy'],
        "ram": units['ram'],
        "catapult": units['catapult'],
        "knight": units['knight'],
        "snob": units['snob'],
        "x": target_coords[0],
        "y": target_coords[1],
        "target_type": "coord",
        "input": "",
        "attack": "Aanvallen",
        "support": "Pomoc",
    }
    time.sleep(1)
    response = session.post(url, data=data)
    print("[POST] ",url)
    soup = BeautifulSoup(response.text, 'html.parser')
    formatted_html = soup.prettify()


    time.sleep(1)


    match = re.search(r'<div class="error_box">\s*<div class="content">\s*(.*?)\s*</div>', response.text, re.DOTALL)
    if match:
        error_text = match.group(1)
        print("Error text:", error_text)
        return False
    else:
        print("Error text not found.")

    match = re.search(r'&h=(\w+)', response.text)
    if match:
        h_value = match.group(1)
        print("H value:", h_value)
    else:
        print("H value not found.")
        return False


    match = re.search(r'name="ch" value="(.+?)"', response.text)
    if match:
        ch_value = match.group(1)
        print("CH value:", ch_value)
    else:
        print("CH value not found.")
        return False


    cb_value=None
    match = re.search(r'name="cb" value="(.+?)"', response.text)
    if match:
        cb_value = match.group(1)
        print("CB value:", cb_value)
    else:
        print("CB value not found.")
    


    print(f"h: {h_value}, ch: {ch_value}, cb: {cb_value}")

    if response.status_code != 200:
        print(f"POST request failed with status code {response.status_code}")
        return False

    # Step 3: Drugie zapytanie POST
    url = "https://pl182.plemiona.pl/game.php?ajaxaction=popup_command&village={}&screen=place".format(source_village)
    data = {
        "attack": "true",
        # Uzupełnij tutaj wartości ch, cb, h
        "ch": ch_value,
        "cb": cb_value,
        "y": target_coords[1],
        "source_village": source_village,
        "village": source_village,
        "attack_name": "",
        "spear": units['spear'],
        "sword": units['sword'],
        "axe": units['axe'],
        "archer": units['archer'],
        "spy": units['spy'],
        "light": units['light'],
        "marcher": units['marcher'],
        "heavy": units['heavy'],
        "ram": units['ram'],
        "catapult": units['catapult'],
        "knight": units['knight'],
        "snob": units['snob'],
        "save_default_attack_building": "1",
        "submit_confirm": "Wyślij atak",
        "building": "main",
        "h": h_value,
        "x": target_coords[0],
    }
    time.sleep(1)
    response = session.post(url, data=data)
    print("[POST] ", url)
    if response.status_code != 200:
        print(f"POST request failed with status code {response.status_code}")
        return False

    print(f"Attack has been sent from village {source_village} to coordinates {target_coords}.")
    return True


if __name__ == '__main__':
    CORS(app)
    app.run()
