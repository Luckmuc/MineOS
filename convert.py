import json
import sys
from mnemonic import Mnemonic
from bip32 import BIP32, HARDENED_INDEX

# Funktion zum Generieren einer Bitcoin-Adresse aus einem Mnemonic
def generate_bc1_address(mnemonic):
    mnemo = Mnemonic("english")
    
    # Entschlüsselung des Mnemonics zu einem Seed
    seed = mnemo.to_seed(mnemonic, passphrase="")
    
    # Erstelle den BIP32-Root-Key
    bip32 = BIP32.from_seed(seed)
    
    # Generiere den Pfad m/44'/0'/0'/0/0 (BIP44 Standard für Bitcoin)
    bip32_child_key = bip32.get_child(44 + HARDENED_INDEX) \
                          .get_child(0 + HARDENED_INDEX) \
                          .get_child(0 + HARDENED_INDEX) \
                          .get_child(0) \
                          .get_child(0)
    
    # Erhalte die Adresse
    return bip32_child_key.address()

# Funktion zum Verarbeiten der JSON-Datei
def process_json_file(file_path):
    try:
        with open(file_path, 'r') as file:
            mnemonics = [json.loads(line.strip())["mnemonic"] for line in file.readlines()]
        
        total = len(mnemonics)
        for idx, mnemonic in enumerate(mnemonics):
            bc1_address = generate_bc1_address(mnemonic)
            sys.stdout.write(f"\rFortschritt: {idx+1}/{total} Adressen generiert: {bc1_address}")
            sys.stdout.flush()
        
        print("\nFertig! Alle Adressen wurden generiert.")
    
    except Exception as e:
        print(f"Fehler beim Verarbeiten der Datei: {e}")

if __name__ == "__main__":
    # Geben Sie hier den Pfad zur JSON-Datei ein
    json_file_path = "mnemonics.json"
    
    process_json_file(json_file_path)
