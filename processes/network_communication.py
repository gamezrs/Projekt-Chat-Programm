# Module für Socket, Config und Dateizugriff importieren
import socket
import toml
import time
from pathlib import Path

# Stream-Handler: TCP-Server und -Client
def stream_handler(log_queue, data_queue, cfg_path, peers):
    """
    @brief   Lauscht auf TCP-Port, verarbeitet eingehende Verbindungen
             und sendet ausgehende Chat- bzw. Bilddaten.
    @return  None
    """
    # Kommunikationsdetails aus Config laden
    cfg     = toml.load(cfg_path)
    port    = cfg['tcp_port']
    me      = cfg['user']
    img_dir = cfg['img_dir']

    # Server-Socket vorbereiten (Blockzeit 0.5s)
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('', port))
    server.listen(3)
    server.settimeout(0.5)
    log_queue.put(f"[NET] TCP-Server horcht auf Port {port}")

    last_addr = None  # letzte bekannte Adresse für Bildbytes
    while True:
        # A) Eingehende Verbindungen verarbeiten
        try:
            conn, addr = server.accept()
            header = conn.recv(512)

            if header.startswith(b'IMG'):
                # Bildempfang: HEADER mit Größe, dann Rohdaten
                _tag, size_str = header.decode().split()
                size = int(size_str)
                conn.sendall(b'OK')  # ACK senden
                buf = b''
                while len(buf) < size:
                    buf += conn.recv(4096)
                out_file = Path(img_dir) / f"img_{int(time.time())}.bin"
                out_file.write_bytes(buf)
                log_queue.put(f"[NET] Bild gespeichert: {out_file}")
            else:
                # MSG oder LEAVE: Textnachricht loggen
                text = header.decode().strip()
                log_queue.put(f"[NET] Nachricht von {addr}: {text}")
            conn.close()
        except socket.timeout:
            # keine neue Verbindung
            pass

        # B) Ausgehende Nachrichten und Bilder senden
        while not data_queue.empty():
            pkt = data_queue.get()
            if isinstance(pkt, bytes):
                # Bildbytes an zuletzt initiiertes Ziel senden
                if last_addr:
                    with socket.socket() as s2:
                        s2.connect(last_addr)
                        s2.sendall(pkt)
                    log_queue.put('[NET] Bildbytes gesendet')
                continue

            # Textbasierte Kommandos parsen
            parts = pkt.split()
            cmd = parts[0]

            if cmd == 'MSG':
                # MSG <user> <text> versenden
                tgt, txt = parts[1], ' '.join(parts[2:])
                tgt_addr = peers.get(tgt)
                if tgt_addr:
                    with socket.socket() as s2:
                        s2.connect(tgt_addr)
                        s2.sendall(f"MSG {me} {txt}".encode())
                    log_queue.put(f"[NET] MSG an {tgt} gesendet")
                else:
                    log_queue.put(f"[NET] Unbekannter Empfänger: {tgt}")

            elif cmd == 'IMG':
                # IMG <user> <size> ankündigen
                tgt, size = parts[1], int(parts[2])
                tgt_addr = peers.get(tgt)
                if tgt_addr:
                    with socket.socket() as s2:
                        s2.connect(tgt_addr)
                        s2.sendall(f"IMG {size}".encode())
                        if s2.recv(2) == b'OK':
                            last_addr = tgt_addr
                    log_queue.put(f"[NET] IMG initiiert zu {tgt}")
                else:
                    log_queue.put(f"[NET] Kein IMG-Empfänger: {tgt}")

            elif cmd == 'LEAVE':
                # LEAVE per TCP an alle Peers senden
                for peer, address in peers.items():
                    if peer != me:
                        try:
                            with socket.socket() as s2:
                                s2.connect(address)
                                s2.sendall(pkt.encode())
                        except Exception:
                            pass
                log_queue.put('[NET] LEAVE an alle Peers gesendet')