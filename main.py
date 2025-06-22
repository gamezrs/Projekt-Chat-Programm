#!/usr/bin/env python3
# Imports aller benötigten Module
import sys
import toml
from multiprocessing import Manager, Queue, Process, set_start_method

from .processes.discovery_service import peer_discovery  # Discovery via UDP-Broadcast
from .processes.network_communication import stream_handler  # TCP-basiertes Messaging
from .processes.user_interface import run_cli  # Kommandozeilen-Interface

# Main-Funktion, wird beim Skriptstart ausgeführt
def main():
    """
    @brief   Initialisiert IPC und startet Hintergrundprozesse.
    @details
      - Setzt unter Windows den "spawn"-Modus für Multiprocessing.
      - Bestimmt den Pfad zur Konfigurationsdatei (argv[1] oder Default).
      - Erstellt Manager und drei Queues für Logs, Discovery- und Datenverkehr.
      - Startet die Prozesse peer_discovery und stream_handler.
      - Startet das CLI-Frontend und beendet Prozesse bei Unterbrechung.
    @return  None
    """
    #  Windows-spezifische Startmethode, um Fork-Issues zu vermeiden
    set_start_method('spawn', force=True)

    #  Config-Pfad aus Argument oder Standardwert
    cfg_path = sys.argv[1] if len(sys.argv) > 1 else 'config.toml'

    #  Manager für geteilte Peer-Daten (Name → (IP, Port))
    manager = Manager()
    peers = manager.dict()

    #  Queues für Interprozesskommunikation
    log_queue  = Queue()  # Log- und Statusmeldungen für CLI
    cmd_queue  = Queue()  # Discovery-Befehle (JOIN, WHO, LEAVE)
    data_queue = Queue()  # Chat- und Bildnachrichten (MSG, IMG)

    #  Prozesse starten
    disc_proc = Process(target=peer_discovery, args=(log_queue, cmd_queue, cfg_path, peers))
    net_proc  = Process(target=stream_handler,  args=(log_queue, data_queue, cfg_path, peers))
    disc_proc.start()
    net_proc.start()

    #  CLI starten und bei Abbruch Prozesse beenden
    try:
        run_cli(log_queue, cmd_queue, data_queue, cfg_path)
    except KeyboardInterrupt:
        print('\n[INFO] Abbruch durch Nutzer, stoppe Dienste...')
    finally:
        disc_proc.terminate()  # Discovery-Service stoppen
        net_proc.terminate()   # Netzwerk-Handler stoppen
        disc_proc.join()       # Auf sauberes Beenden warten
        net_proc.join()
        print('[INFO] Alle Prozesse wurden beendet.')

if __name__ == '__main__':
    main()