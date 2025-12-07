import json
import os
import sys
from pynput import keyboard
from termcolor import colored

# ===============================================
# Gestion des touches F1 / F2
# ===============================================
def on_release(key):
    try:
        if key == keyboard.Key.f1:
            Aimbot.toggle()                    # On utilise maintenant la méthode toggle()
        elif key == keyboard.Key.f2:
            Aimbot.clean_up()                  # Arrêt propre
    except NameError:
        pass  # Aimbot pas encore importé, c’est normal au tout début


# ===============================================
# Fonction principale
# ===============================================
def main():
    global lunar
    # Plus besoin de collect_data → on le vire
    lunar = Aimbot()
    lunar.start()


# ===============================================
# Configuration sensibilité (première fois)
# ===============================================
def setup():
    path = "lib/config"
    if not os.path.exists(path):
        os.makedirs(path)

    print(colored("[INFO] La sensibilité X et Y en jeu doit être IDENTIQUE", "yellow"))
    
    def ask(prompt):
        while True:
            try:
                return float(input(prompt))
            except ValueError:
                print(colored("[!] Entre seulement le nombre (ex: 6.9)", "red"))

    xy_sens = ask("Sensibilité X/Y en jeu : ")
    targeting_sens = ask("Sensibilité ADS / Visée (doit être identique à la visée) : ")

    config = {
        "xy_sens": xy_sens,
        "targeting_sens": targeting_sens,
        "xy_scale": 10 / xy_sens,
        "targeting_scale": 1000 / (targeting_sens * xy_sens)
    }

    with open("lib/config/config.json", "w") as f:
        json.dump(config, f, indent=4)

    print(colored("[INFO] Configuration sensibilité terminée !", "green"))


# ===============================================
# Lancement du script
# ===============================================
if __name__ == "__main__":
    os.system('cls' if os.name == 'nt' else 'clear')
    os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

    print(colored('''
  _    _   _ _   _    _    ____     _     ___ _____ _____ 
 | |  | | | | \ | |  / \  |  _ \   | |   |_ _|_   _| ____|
 | |  | | | |  \| | / _ \ | |_) |  | |    | |  | | |  _|  
 | |__| |_| | |\  |/ ___ \|  _ <   | |___ | |  | | | |___ 
 |_____\___/|_| \_/_/   \_\_| \_\  |_____|___| |_| |_____|
                                                                         
(Neural Network Aimbot)''', "green"))
    
    print(colored("Version AMD RX 6600 + DirectML – Full GPU activé !", "cyan"))
    print(colored("F1 = Activer/Désactiver | F2 = Quitter", "yellow"))
    print()

    # Configuration sensibilité si besoin
    if not os.path.exists("lib/config/config.json") or "setup" in sys.argv:
        if not os.path.exists("lib/config/config.json"):
            print(colored("[!] Aucun fichier de sensibilité trouvé", "red"))
        setup()

    # Import après la config (évite les erreurs si le fichier est créé maintenant)
    from lib.aimbot import Aimbot

    # Démarrage du listener clavier
    listener = keyboard.Listener(on_release=on_release)
    listener.start()

    # Lancement de l'aimbot
    main()