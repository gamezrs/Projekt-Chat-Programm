# Standardmodule importieren
import threading
import time
import toml
import os
from pathlib import Path

# Hauptfunktion: CLI-Loop
def run_cli(log_queue, cmd_queue, data_queue, cfg_path):
    """
    @brief   Liest Nutzereingaben, zeigt Logs und sendet Befehle an Services.

    @param log_queue  Queue[str]           Liefert status- und Fehlerausgaben.
    @param cmd_queue  Queue[str]           Sendet Discovery-Kommandos.
    @param data_queue Queue[str|bytes]     Sendet Chat- und Bilddaten.
    @param cfg_path   str                  Pfad zur Konfigurationsdatei.
    @return           None
    """
    # Begrüßung inklusive genutzter Config-Datei
    print(f"SimpleChat CLI gestartet mit config: {cfg_path}")
    print("> Tippe 'help' für eine Liste der Befehle\n")

    # Thread zum asynchronen Ausgeben aller Log-Nachrichten
    def log_reader():
        while True:
            entry = log_queue.get()  # blockiert bis Log-Eintrag ankommt
            print(entry)
    threading.Thread(target=log_reader, daemon=True).start()

    # Endlos-Loop für Benutzerbefehle
    while True:
        try:
            parts = input('> ').strip().split()
            if not parts:
                continue  # ignoriert leere Eingaben
            cmd, *args = parts

            # Hilfe ausgeben
            if cmd == 'help':
                print('Befehle: join, who, msg, leave, contacts, config, set, img, exit')

            # JOIN: Netzwerkbeitritt
            elif cmd == 'join':
                cfg = toml.load(cfg_path)
                cmd_queue.put(f"JOIN {cfg['user']} {cfg['tcp_port']}")

            # WHO: Peers abfragen
            elif cmd == 'who':
                cmd_queue.put('WHO')

            # MSG: Textnachricht senden
            elif cmd == 'msg':
                if len(args) < 2:
                    print('Benutzung: msg <user> <text>')
                else:
                    target, text = args[0], ' '.join(args[1:])
                    data_queue.put(f"MSG {target} {text}")

            # LEAVE: Netzwerk verlassen
            elif cmd == 'leave':
                cfg = toml.load(cfg_path)
                cmd_queue.put(f"LEAVE {cfg['user']}")

            # contacts: Kontakte aktualisieren
            elif cmd == 'contacts':
                cmd_queue.put('WHO')

            # config: aktuelle Einstellungen anzeigen
            elif cmd == 'config':
                cfg = toml.load(cfg_path)
                for key, val in cfg.items():
                    print(f"{key} = {val}")

            # set: einzelnen Parameter ändern
            elif cmd == 'set':
                if len(args) < 2:
                    print('Benutzung: set <key> <value>')
                else:
                    key, val = args[0], ' '.join(args[1:])
                    cfg = toml.load(cfg_path)
                    if key in cfg:
                        orig = cfg[key]
                        # Typangleichung an bestehenden Wert
                        if isinstance(orig, bool): val = val.lower() in ('true','1')
                        elif isinstance(orig, int): val = int(val)
                    cfg[key] = val
                    with open(cfg_path, 'w') as f:
                        toml.dump(cfg, f)
                    print(f"[OK] {key} gesetzt auf {val}")

            # IMG: Bildübertragung starten
            elif cmd == 'img':
                if len(args) != 2:
                    print('Benutzung: img <user> <pfad>')
                else:
                    target, path = args
                    if not os.path.isfile(path):
                        print(f'Datei nicht gefunden: {path}')
                    else:
                        blob = Path(path).read_bytes()
                        data_queue.put(f"IMG {target} {len(blob)}")
                        time.sleep(0.1)  # kurz warten auf ACK
                        data_queue.put(blob)

            # exit: CLI beenden
            elif cmd == 'exit':
                print('Verlasse CLI. Bis bald!')
                break

            # unbekanntes Kommando
            else:
                print(f"Unbekanntes Kommando: '{cmd}'. Tippe 'help'!")

        except (EOFError, KeyboardInterrupt):
            print('\n[INFO] CLI durch Nutzer beendet.')
            break