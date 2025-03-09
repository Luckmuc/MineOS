#!/usr/bin/env python3
import itertools
import threading
import time
import json
import os
import shutil
import subprocess
import sys
from colorama import Fore

try:
    import keyboard  # Externe Bibliothek für Keypress (pip install keyboard)
    keyboard_available = True
except ImportError:
    keyboard_available = False

# Lade BIP39-Wortliste
try:
    from mnemonic import Mnemonic
    m = Mnemonic("english")
    wordlist = m.wordlist
except ImportError:
    with open("bip39_english.txt", "r", encoding="utf-8") as f:
        wordlist = [line.strip() for line in f if line.strip()]

num_words = 12
mnemonics_file = "mnemonics.json"
position_file = "position.json"
compressed_file = "mnemonics.7z"
num_threads = 4

# Prüfe, ob Fortschritt existiert
start_position = 0
if os.path.exists(position_file):
    with open(position_file, "r", encoding="utf-8") as f:
        try:
            start_position = json.load(f).get("position", 0)
            print(f"Wiederaufnahme ab Position: {start_position}")
        except json.JSONDecodeError:
            pass

# Generiere ab gespeicherter Position
def generate_mnemonics(wordlist, num_words, start_position=0):
    gen = itertools.product(wordlist, repeat=num_words)
    for _ in range(start_position):
        next(gen, None)  # Überspringe bereits verarbeitete Kombinationen
    return gen

# Globale Variablen
gen = generate_mnemonics(wordlist, num_words, start_position)
gen_lock = threading.Lock()
counter_lock = threading.Lock()
global_count = start_position
start_time = time.time()
stop_requested = False
save_interval = 1000

# Speichert Fortschritt
def save_position(position):
    with open(position_file, "w", encoding="utf-8") as f:
        json.dump({"position": position}, f)

# Speichert Mnemonics fortlaufend
def save_mnemonics(mnemonic):
    with open(mnemonics_file, "a", encoding="utf-8") as f:
        json.dump({"mnemonic": mnemonic}, f)
        f.write("\n")

# Multithreading Worker
def worker():
    global global_count, stop_requested
    while not stop_requested:
        with gen_lock:
            try:
                mnemonic = next(gen)
            except StopIteration:
                stop_requested = True
                return
        mnemonic_str = " ".join(mnemonic)

        with counter_lock:
            global_count += 1
            count = global_count

        save_mnemonics(mnemonic_str)

        if count % save_interval == 0:
            save_position(count)

        elapsed = time.time() - start_time
        rate = count / elapsed if elapsed > 0 else 0
        print(Fore.MAGENTA + f"{count}: ({rate:.2f} wallets/s) {mnemonic_str}")

# Stop-Listener für Tastendruck
def listen_for_stop():
    global stop_requested
    if keyboard_available:
        print("\n[!] Drücke eine beliebige Taste zum Stoppen...")
        keyboard.read_event()  # Stoppt, sobald eine Taste gedrückt wird
        stop_requested = True
    else:
        print("\n[!] Kein Tastatur-Listener verfügbar. Nutze STRG+C zum Stoppen.")

# Datei komprimieren
def compress_file():
    if os.path.exists(mnemonics_file):
        print(Fore.LIGHTGREEN_EX + "\n[+] Komprimiere mnemonics.json...")
        try:
            if shutil.which("7z"):
                subprocess.run(["7z", "a", "-mx=9", compressed_file, mnemonics_file])
            elif shutil.which("xz"):
                subprocess.run(["xz", "-9", mnemonics_file])
            elif shutil.which("zip"):
                subprocess.run(["zip", "-9", f"{mnemonics_file}.zip", mnemonics_file])
            else:
                print("[-] Keine Kompressionssoftware gefunden.")
        except Exception as e:
            print(f"[-] Fehler bei der Komprimierung: {e}")

if __name__ == "__main__":
    print("Starte mit Multithreading. Drücke eine beliebige Taste zum Stoppen.")

    threads = []
    for _ in range(num_threads):
        t = threading.Thread(target=worker, daemon=True)
        t.start()
        threads.append(t)

    stop_thread = threading.Thread(target=listen_for_stop, daemon=True)
    stop_thread.start()

    try:
        for t in threads:
            t.join()
    except KeyboardInterrupt:
        print("\n[!] STRG+C erkannt. Speichern & Beenden...")
        stop_requested = True

    save_position(global_count)
    compress_file()
    print("\n[+] Fertig! Fortschritt gespeichert und komprimiert.")
