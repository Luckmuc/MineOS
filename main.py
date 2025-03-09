#!/usr/bin/env python3
import threading
import time
import json
import os
import shutil
import subprocess
import sys
import random
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
compressed_file = "mnemonics.7z"
num_threads = 4
stop_requested = False
save_interval = 1000
counter_lock = threading.Lock()
global_count = 0
start_time = time.time()

def generate_random_mnemonic():
    return " ".join(random.choices(wordlist, k=num_words))

# Speichert Mnemonics fortlaufend
def save_mnemonics(mnemonic):
    with open(mnemonics_file, "a", encoding="utf-8") as f:
        json.dump({"mnemonic": mnemonic}, f)
        f.write("\n")

# Multithreading Worker
def worker():
    global global_count, stop_requested
    while not stop_requested:
        mnemonic_str = generate_random_mnemonic()

        with counter_lock:
            global_count += 1
            count = global_count

        save_mnemonics(mnemonic_str)

        elapsed = time.time() - start_time
        rate = count / elapsed if elapsed > 0 else 0
        print(Fore.MAGENTA + f"{count}: ({rate:.2f} wallets/s) {mnemonic_str}")

# Stop-Listener für Tastendruck
def listen_for_stop():
    global stop_requested
    if keyboard_available:
        print("\n[!] Drücke eine beliebige Taste zum Stoppen...")
        keyboard.read_event()
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

    compress_file()
    print("\n[+] Fertig! Mnemonics gespeichert und komprimiert.")