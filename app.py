from flask import Flask, render_template, request, redirect, url_for
import re
from flask import request, jsonify
from bs4 import BeautifulSoup
import time
import sqlite3
import requests
from dateutil.parser import parse
import random
from selenium.webdriver.support.ui import Select
from datetime import datetime, timedelta
from flask_cors import CORS
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

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
(id INTEGER PRIMARY KEY AUTOINCREMENT, parametr1 TEXT, parametr2 TEXT, parametr3 TEXT, parametr4 TEXT)''')
    # Dodaj na początku kodu, np. po otwarciu połączenia z bazą danych
    c.execute('''
        CREATE TABLE IF NOT EXISTS wyslane (
            id INTEGER PRIMARY KEY,
            parametr1 TEXT,
            parametr2 TEXT,
            data TEXT,
            attacktype TEXT
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS niewyslane (
            id INTEGER PRIMARY KEY,
            parametr1 TEXT,
            parametr2 TEXT,
            data TEXT,
            attacktype TEXT,
            reason TEXT
        )
    ''')

    conn.commit()
    conn.close()


@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
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
    return render_template('lista.html', rekordy=rekordy)


@app.route('/wyslane')
def wyslane():
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute('SELECT * FROM wyslane order by data')
    rekordy = c.fetchall()
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
    record = record[1:-1]

    if record:
        # Wstawianie rekordu do tabeli 'wyslane'
        c.execute('''
            INSERT INTO data (parametr1, parametr2, parametr3, parametr4)
            VALUES (?, ?, ?, ?)
        ''', record)

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
    c.execute("INSERT INTO data (parametr1, parametr2, parametr3, parametr4) VALUES (?, ?, ?,?)",
              (parametr1, parametr2, parametr3, parametr4))
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


@app.route('/add_to_db', methods=['POST'])
def add_to_db():
    types = request.form.getlist('type')
    dates = request.form.getlist('date')
    from_villages = request.form.getlist('from_village')
    targets = request.form.getlist('target')

    conn = sqlite3.connect("data.db")
    c = conn.cursor()

    # Lista przechowująca wszystkie wcześniej wylosowane czasy ataków
    attack_times = []

    for i in range(len(types)):
        print(i)
        type = types[i]
        date = dates[i]
        print("Date: ",date)
        from_village = from_villages[i]
        target = targets[i]

        date_str, start_time_str, end_time_str = date.split(' ')

        start_time = datetime.strptime(date_str + ' ' + start_time_str, '%Y-%m-%d %H:%M:%S')
        end_time = datetime.strptime(date_str + ' ' + end_time_str, '%Y-%m-%d %H:%M:%S')

        # Jeżeli end_time jest wcześniejszy niż start_time, dodajemy jeden dzień do end_time
        if end_time < start_time:
            end_time += timedelta(days=1)

        print("Start time:",start_time)
        print("End time: ",end_time)
        time_range = end_time - start_time
        if time_range.total_seconds() > 0:
            # Losowanie czasu ataku, który nie jest zbyt bliski wcześniej wylosowanym czasom


            while True:
                random_seconds = random.randrange(int(time_range.total_seconds()))
                random_time = start_time + timedelta(seconds=random_seconds)
                # Sprawdzanie, czy wylosowany czas ataku nie jest zbyt bliski żadnemu z wcześniej wylosowanych czasów
                if all(abs((random_time - old_time).total_seconds()) >= 60 for old_time in attack_times):
                    break  # Jeśli wylosowany czas ataku jest odpowiednio oddalony, przerywamy pętlę
            attack_times.append(random_time)  # Dodajemy wylosowany czas ataku do listy

            attack_time = random_time.strftime('%Y-%m-%dT%H:%M:%S.%f')
            attack_time = attack_time[:-3]
            print(attack_time)

            c.execute("INSERT INTO data (parametr4, parametr3, parametr1, parametr2) VALUES (?, ?, ?, ?)",
                      (type, attack_time, from_village, target))
    conn.commit()
    conn.close()

    return redirect(url_for('lista'))


def uruchom_moj_skrypt():
    is_successful, message = scripto()

    if is_successful:
        return message
    else:
        return f"Błąd: {message}"

def scripto():
    def send_attack():
        try:
            id_record = row[0]
            parametr1 = row[1]
            parametr2 = row[2]
            attacktype = row[4]


            data = date_str
            dt = datetime.strptime(data, '%Y-%m-%dT%H:%M:%S.%f')

            # Ustaw logowanie dla przeglądarki
            d = DesiredCapabilities.CHROME
            d['goog:loggingPrefs'] = {'browser': 'ALL'}
            options = Options()
            options.add_argument('--user-data-dir=/path/to/user-data')
            options.add_argument('--profile-directory=Default')
            options.add_argument("--start-minimized")
            options.add_extension("windscribe.crx")
            #options.add_argument('--headless')
            #options.add_argument('--no-sandbox')

            options.add_argument(
                "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537")

            driver = webdriver.Chrome(desired_capabilities=d, options=options)
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
                challenge_container = driver.find_element(By.XPATH, "//span[text()='Świat 182']")
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

            try:
                element = driver.find_element(By.CLASS_NAME,"group-menu-item")
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

            elif attacktype[:6] == "BURZAK":

                try:

                    # Rozdzielamy tekst na części używając ' - ' jako separatora
                    parts = attacktype.split(' - ')

                    # Pierwsza część (indeks 0) to "BURZAK", druga część (indeks 1) to "200", trzecia część (indeks 2) to "Zagroda"

                    # Przekształcamy "200" na liczbę
                    number = int(parts[1])

                    # Trzecia część to "Zagroda", więc to przypisujemy do zmiennej "building"
                    building = parts[2]

                    topy = driver.find_element(By.ID, "units_entry_all_axe").text
                    topy = topy[1:-1]
                    pik = driver.find_element(By.ID, "units_entry_all_spear").text
                    pik = pik[1:-1]

                    lk = driver.find_element(By.ID, "units_entry_all_light").text
                    lk = lk[1:-1]
                    taran = driver.find_element(By.ID, "units_entry_all_ram").text
                    taran = taran[1:-1]
                    lukinakoniu = driver.find_element(By.ID, "units_entry_all_marcher").text
                    lukinakoniu = lukinakoniu[1:-1]
                    zwiad = driver.find_element(By.ID, "units_entry_all_spy").text
                    zwiad = zwiad[1:-1]
                    ciezka = driver.find_element(By.ID, "units_entry_all_heavy").text
                    ciezka = ciezka[1:-1]
                    katapulty = driver.find_element(By.ID, "units_entry_all_catapult").text
                    katapulty = katapulty[1:-1]

                    if int(ciezka)>50:
                        heavyinput = driver.find_element(By.ID, "unit_input_heavy")
                        heavyinput.send_keys(50)
                    elif int(topy)>100:
                        topyinput = driver.find_element(By.ID, "unit_input_axe")
                        topyinput.send_keys(50)
                    elif int(lk)>100:
                        lkinput = driver.find_element(By.ID, "unit_input_light")
                        lkinput.send_keys(50)
                    elif int(pik)>100:
                        pikinput = driver.find_element(By.ID, "unit_input_spear")
                        pikinput.send_keys(50)

                    katapultyinput = driver.find_element(By.ID, "unit_input_catapult")
                    katapultyinput.send_keys(number)
                    time.sleep(1)

                except:
                    return False, "E.16 - Błąd podczas burzaka"

            elif attacktype == "FAKE SZLACHCIC":

                try:
                    topy = driver.find_element(By.ID, "units_entry_all_axe").text
                    topy = topy[1:-1]
                    pik = driver.find_element(By.ID, "units_entry_all_spear").text
                    pik = pik[1:-1]
                    lk = driver.find_element(By.ID, "units_entry_all_light").text
                    lk = lk[1:-1]
                    ciezka = driver.find_element(By.ID, "units_entry_all_heavy").text
                    ciezka = ciezka[1:-1]

                    if int(ciezka)>50:
                        heavyinput = driver.find_element(By.ID, "unit_input_heavy")
                        heavyinput.send_keys(25)
                    elif int(topy)>100:
                        topyinput = driver.find_element(By.ID, "unit_input_axe")
                        topyinput.send_keys(50)
                    elif int(lk)>25:
                        lkinput = driver.find_element(By.ID, "unit_input_light")
                        lkinput.send_keys(25)
                    elif int(pik)>100:
                        pikinput = driver.find_element(By.ID, "unit_input_spear")
                        pikinput.send_keys(50)

                    szlachcicinput = driver.find_element(By.ID, "unit_input_snob")
                    szlachcicinput.send_keys(1)
                    time.sleep(1)


                except:
                    return False, "E.14 - Błąd podczas FAKE SZLACHCICA"

            elif attacktype == "SZLACHCIC":

                try:
                    return False, "E.15 - SZLACHCIC"
                except:
                    pass

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
                element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "target_attack")))
                driver.execute_script("arguments[0].click();", element)

            except:
                return False, "E.12 - Błąd jeszcze na placu"

            try:
                challenge_container = driver.find_element(By.ID, "troop_confirm_submit")
            except:
                return False, "E.13 - Błędny cel lub jednostki"

            try:
                challenge_container = driver.find_element(By.NAME, "building")
                # Utwórz obiekt Select
                select = Select(challenge_container)
                # Wybierz opcję za pomocą widocznego tekstu
                select.select_by_visible_text(building)
            except:
                pass


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

            try:
                challenge_container = driver.find_element(By.ID, "command-data-form")
                conn = sqlite3.connect('data.db')
                c = conn.cursor()
                c.execute("DELETE FROM data WHERE id = ?", (id_record,))
                conn.commit()


                driver.quit()
                return True, "Success"

            except:
                return False, "E.19 - Błąd skryptu wysyłającego atak"


        except Exception as e:
            return False, str(e)


    znaleziono_date = False
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
                    c.execute("INSERT INTO wyslane(parametr1, parametr2, data, attacktype) VALUES (?, ?, ?, ?)",
                              (parametr1, parametr2, data, attacktype))
                    conn.commit()
                else:
                    print("Nie udało się wysłać ataku. Powód:", message)
                    # Dodaj informacje o ataku do tabeli 'niewyslane'
                    conn = sqlite3.connect('data.db')
                    c = conn.cursor()
                    c.execute(
                        "INSERT INTO niewyslane(parametr1, parametr2, data, attacktype, reason) VALUES (?, ?, ?, ?, ?)",
                        (parametr1, parametr2, data, attacktype, message))
                    c.execute("DELETE FROM data WHERE id = ?", (id_record,))
                    conn.commit()

        conn.close()
        if not znaleziono_date:
            time.sleep(10)  # Poczekaj 10s przed kolejnym sprawdzeniem

    return True, "Zakończono działanie programu."


if __name__ == '__main__':
    app.run()
    CORS(app)  # umożliwić CORS
