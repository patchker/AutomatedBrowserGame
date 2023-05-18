from distutils.core import setup
import py2exe

# Lista plików i katalogów do dodania
files = [
    ("your_script2.py", "."),  # Dodaje your_script2.py z obecnego katalogu
    ("templates", "templates"),  # Dodaje cały katalog templates
    ("static", "static"),  # Dodaje cały katalog static
    ("windscribe.crx", "."),  # Dodaje windscribe.crx z obecnego katalogu
]

# Konfiguracja setup
setup(
    options={
        "py2exe": {
            "py_modules": ["your_script2"],
            "includes": ["flask", "your_script2"],  # Dodaje wymagane moduły
            "excludes": ["Tkinter"],  # Wyklucza niepotrzebne moduły
            "packages": ["jinja2", "markupsafe"],  # Dodaje wymagane pakiety
            "optimize": 2,  # Optymalizuje kod
            "compressed": True,  # Kompresuje wynikowy plik wykonywalny
            "bundle_files": 1,  # Tworzy jedno archiwum wynikowe
            "dll_excludes": ["MSVCP90.dll"],  # Wyklucza niepotrzebne DLL
            "includes_files": files  # Dodaje pliki i katalogi
        }
    },
    console=["app.py"],  # Skrypt do zamiany na plik wykonywalny
    zipfile=None  # Nie tworzy archiwum ZIP
)
