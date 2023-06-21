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
(id INTEGER PRIMARY KEY AUTOINCREMENT, parametr1 TEXT, parametr2 TEXT, parametr3 TEXT, parametr4 TEXT, parametr5 TEXT, parametr6 TEXT )''')
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
    c.execute("CREATE TABLE IF NOT EXISTS server_status (id INTEGER PRIMARY KEY, status TEXT)")
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
        wynik = uruchom_moj_skrypt()

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

        c.execute("UPDATE data SET parametr1=?, parametr2=?, parametr3=?, parametr4=? WHERE id=?",
                  (parametr1, parametr2, parametr3, parametr4, id))
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
    c.execute("INSERT INTO data (parametr1, parametr2, parametr3, parametr4, parametr5, parametr6) VALUES (?, ?, ?,?,?,?)",
              (parametr1, parametr2, parametr3, parametr4, parametr5, "0"))
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
                    else:
                        attack['type'] = 'OFF'




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

    for attack in attacks:
        print(attack)

    return render_template('table_page.html', table_data=attacks)

@app.route('/add_to_db2', methods=['POST'])
def add_to_db2():
    types = request.form.getlist('type')
    dates = request.form.getlist('date')
    from_villages = request.form.getlist('from_village')
    targets = request.form.getlist('target')
    urls = request.form.getlist('url')
    massorsingle = request.form.getlist('massorsingle')

    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    for i in range(len(types)):
        type = types[i]
        date = dates[i]
        from_village = from_villages[i]
        target = targets[i]
        url = urls[i]  # przypisujemy url
        massorsingle2 = massorsingle[i]  # przypisujemy url

        c.execute("INSERT INTO data (parametr4, parametr3, parametr1, parametr2, parametr5,parametr6) VALUES (?, ?, ?, ?, ?,?)",(type, date, from_village, target, url, massorsingle2))  # dodajemy url do zapytania SQL
    conn.commit()
    conn.close()


    return redirect(url_for('lista'))
@app.route('/add_to_db', methods=['POST'])
def add_to_db():
    types = request.form.getlist('type')
    dates = request.form.getlist('date')
    from_villages = request.form.getlist('from_village')
    targets = request.form.getlist('target')
    urls = request.form.getlist('url')  # dodajemy odczytywanie url
    print(urls)

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

            c.execute("INSERT INTO data (parametr4, parametr3, parametr1, parametr2, parametr5,parametr6) VALUES (?, ?, ?, ?, ?,?)",
                      (type, attack_time, from_village, target, url,"1"))  # dodajemy url do zapytania SQL
    conn.commit()
    conn.close()

    return redirect(url_for('lista'))




def uruchom_moj_skrypt():
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute("UPDATE server_status SET status = 'active' WHERE id = 1")
    conn.commit()
    conn.close()
    is_successful, message = scripto.scripto()

    if is_successful:
        return message
    else:
        return f"Błąd: {message}"


if __name__ == '__main__':
    CORS(app)
    app.run()
