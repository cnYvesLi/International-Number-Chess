import socket
import threading
import json
import time
from typing import List, Dict, Optional, Tuple


BROADCAST_PORT = 54545
TCP_PORT = 54546  # Default; host may choose a free port
BROADCAST_ADDR = '<broadcast>'


class NetSession:
    def __init__(self, sock: socket.socket, role: str, side: str, peer_addr: Tuple[str, int]):
        self.sock = sock
        self.role = role  # 'host' or 'client'
        self.side = side  # 'blue' or 'red'
        self.peer_addr = peer_addr
        self._incoming: List[Dict] = []
        self._lock = threading.Lock()
        self._running = True
        self._recv_thread = threading.Thread(target=self._recv_loop, daemon=True)
        self._recv_thread.start()

    def _recv_loop(self):
        buf = b''
        try:
            while self._running:
                data = self.sock.recv(4096)
                if not data:
                    break
                buf += data
                # Simple newline-delimited JSON protocol
                while b'\n' in buf:
                    msg, buf = buf.split(b'\n', 1)
                    try:
                        payload = json.loads(msg.decode('utf-8'))
                    except Exception:
                        continue
                    with self._lock:
                        self._incoming.append(payload)
        except Exception:
            pass
        finally:
            self._running = False

    def send(self, payload: Dict):
        try:
            data = (json.dumps(payload) + '\n').encode('utf-8')
            self.sock.sendall(data)
        except Exception:
            pass

    def poll(self) -> List[Dict]:
        with self._lock:
            items = list(self._incoming)
            self._incoming.clear()
            return items

    def close(self):
        self._running = False
        try:
            self.sock.close()
        except Exception:
            pass


def get_local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return '127.0.0.1'


def start_host(room_name: str, host_side: str, tcp_port: int = TCP_PORT) -> Tuple[NetSession, threading.Thread]:
    """Start a host: TCP listener and UDP discovery responder.
    Returns (NetSession for TCP once connected, discovery thread).
    The NetSession will be initialized after client connects; until then, you can check the accept thread.
    """
    assert host_side in ('blue', 'red')
    # UDP discovery responder
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    except Exception:
        pass
    udp_sock.bind(('', BROADCAST_PORT))

    local_ip = get_local_ip()

    def discovery_loop():
        while True:
            try:
                data, addr = udp_sock.recvfrom(1024)
                if not data:
                    continue
                try:
                    msg = json.loads(data.decode('utf-8'))
                except Exception:
                    continue
                if msg.get('type') == 'discover':
                    reply = {
                        'type': 'room_info',
                        'room_name': room_name,
                        'ip': local_ip,
                        'port': tcp_port,
                        'host_side': host_side,
                    }
                    udp_sock.sendto(json.dumps(reply).encode('utf-8'), addr)
            except Exception:
                break

    discovery_thread = threading.Thread(target=discovery_loop, daemon=True)
    discovery_thread.start()

    # TCP listener
    tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    tcp_sock.bind(('', tcp_port))
    tcp_sock.listen(1)

    # Accept one client
    conn, addr = tcp_sock.accept()
    # Handshake: inform client of sides
    session = NetSession(conn, role='host', side=host_side, peer_addr=addr)
    session.send({'type': 'hello', 'host_side': host_side})
    return session, discovery_thread


def discover_rooms(timeout: float = 1.0) -> List[Dict]:
    """Broadcast a discovery message and collect room replies."""
    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    udp.settimeout(timeout)
    msg = json.dumps({'type': 'discover', 'ts': time.time()}).encode('utf-8')
    rooms: List[Dict] = []
    try:
        udp.sendto(msg, (BROADCAST_ADDR, BROADCAST_PORT))
        start = time.time()
        while time.time() - start < timeout:
            try:
                data, addr = udp.recvfrom(1024)
                info = json.loads(data.decode('utf-8'))
                if info.get('type') == 'room_info':
                    info['addr'] = addr[0]
                    rooms.append(info)
            except socket.timeout:
                break
            except Exception:
                break
    finally:
        udp.close()
    return rooms


def join_room(ip: str, port: int) -> Optional[NetSession]:
    """Join a TCP room; returns NetSession with side opposite host."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((ip, port))
        # Wait for hello
        buf = b''
        while True:
            data = s.recv(4096)
            if not data:
                raise RuntimeError('No hello from host')
            buf += data
            if b'\n' in buf:
                msg, buf = buf.split(b'\n', 1)
                hello = json.loads(msg.decode('utf-8'))
                if hello.get('type') == 'hello':
                    host_side = hello.get('host_side', 'blue')
                    client_side = 'red' if host_side == 'blue' else 'blue'
                    return NetSession(s, role='client', side=client_side, peer_addr=(ip, port))
    except Exception:
        try:
            s.close()
        except Exception:
            pass
        return None