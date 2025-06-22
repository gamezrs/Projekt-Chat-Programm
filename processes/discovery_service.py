# Module für Socket-Kommunikation und Konfigurationshandling
import socket
import toml
import time

# Discovery-Service: Endlosschleife für UDP-Broadcasts
def peer_discovery(log_queue, cmd_queue, cfg_path, peers):
    """
    @brief   Lauscht auf UDP-Port, verwaltet Peer-Liste und sendet
             Discovery-Nachrichten (JOIN, WHO, LEAVE).
    @return  None
    """
    # Konfiguration der Kommunikationsports laden
    cfg       = toml.load(cfg_path)
    me        = cfg['user']
    udp_port  = cfg['udp_port']
    tcp_port  = cfg['tcp_port']

    # Eigene IP-Adresse ermitteln & ins Mapping aufnehmen
    hostname = socket.gethostname()
    my_ip    = socket.gethostbyname(hostname)
    peers[me] = (my_ip, tcp_port)
    log_queue.put(f"[DISC] Ich={me}@{my_ip}:{tcp_port}")

    # UDP-Socket konfigurieren (Broadcast & ReuseAddr)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', udp_port))  # an alle Interfaces binden
    sock.setblocking(False)

    known = {me: peers[me]}  # lokale Kopie der Peer-Liste

    while True:
        # 1) Eingehende Discovery-Nachrichten verarbeiten
        try:
            data, sender = sock.recvfrom(2048)
            text = data.decode().strip()
            log_queue.put(f"[DISC] {text} von {sender}")
            parts = text.split()
            cmd = parts[0]

            if cmd == 'JOIN' and len(parts) == 3:
                name, port = parts[1], int(parts[2])
                if name != me:
                    known[name] = (sender[0], port)
                    peers[name]  = known[name]
                    log_queue.put(f"[DISC] {name} beigetreten: {sender[0]}:{port}")

            elif cmd == 'WHO':
                # Liste bekannter Peers zurücksenden
                payload = ','.join(f"{n}:{ip}:{p}" for n,(ip,p) in known.items())
                sock.sendto(f"KNOWUSERS {payload}".encode(), sender)

            elif cmd == 'LEAVE' and len(parts) == 2:
                name = parts[1]
                known.pop(name, None)
                peers.pop(name, None)
                log_queue.put(f"[DISC] {name} hat das Netz verlassen")

            elif cmd == 'KNOWUSERS':
                # Peer-Liste anhand des Broadcasts aktualisieren
                for entry in text[len('KNOWUSERS '):].split(','):
                    n, h, p = entry.split(':')
                    peers[n] = (h, int(p))
                log_queue.put('[DISC] Peer-Liste aktualisiert via KNOWUSERS')

        except BlockingIOError:
            # kein Paket eingetroffen
            pass

        # 2) Ausgehende Discovery-Befehle senden
        if not cmd_queue.empty():
            out = cmd_queue.get()
            sock.sendto(out.encode(), ('<broadcast>', udp_port))
            if out.startswith('LEAVE'):
                # zusätzlich direkt an bekannte Peers
                for n,(ip,_) in known.items():
                    if n != me:
                        sock.sendto(out.encode(), (ip, udp_port))
        time.sleep(0.1)