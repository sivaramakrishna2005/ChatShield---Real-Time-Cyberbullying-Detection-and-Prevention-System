import socket
from _thread import *
import sys
from collections import defaultdict as df
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
import time
import os

# ── Ngrok + QR ────────────────────────────────────────────────────────────────
try:
    from pyngrok import ngrok, conf
    NGROK_AVAILABLE = True
except ImportError:
    NGROK_AVAILABLE = False
    print("[WARNING] pyngrok not installed. Run: pip install pyngrok")

try:
    import qrcode
    QR_AVAILABLE = True
except ImportError:
    QR_AVAILABLE = False
# ──────────────────────────────────────────────────────────────────────────────

# ── Your ngrok authtoken (get free from https://ngrok.com) ───────────────────
NGROK_AUTH_TOKEN = "3C1TFq3f00tCg7U5FR7YVYp4rpk_5CGvdG22YbVjqnUnN1ua4L"
# ──────────────────────────────────────────────────────────────────────────────

base_dir = os.path.dirname(__file__)

# ── Load model ONCE at startup (Bug 3 fix) ────────────────────────────────────
model = pickle.load(open(os.path.join(base_dir, "LinearSVC.pkl"), 'rb'))

with open(os.path.join(base_dir, "stopwords.txt"), "r", encoding="utf-8") as f:
    _stopwords = f.read().split("\n")

_vocab = pickle.load(open(os.path.join(base_dir, "tfidf_vector_vocabulary.pkl"), "rb"))
# ──────────────────────────────────────────────────────────────────────────────

bullying_categories = {
    "Insult":      ["idiot", "stupid", "dumb", "loser", "useless"],
    "Threat":      ["kill", "die", "destroy", "beat"],
    "Hate Speech": ["hate", "racist"],
    "Harassment":  ["ugly", "fat", "noob", "trash"]
}


def detect_bullying_type(message):
    msg = message.lower()
    for category, words in bullying_categories.items():
        for word in words:
            if word in msg:
                return category
    return "Toxic Language"


def print_qr(text):
    if not QR_AVAILABLE:
        return
    qr = qrcode.QRCode(border=1)
    qr.add_data(text)
    qr.make(fit=True)
    qr.print_ascii(invert=True)


def start_ngrok(port):
    if not NGROK_AVAILABLE:
        return None, None

    if not NGROK_AUTH_TOKEN or NGROK_AUTH_TOKEN == "3C1TFq3f00tCg7U5FR7YVYp4rpk_5CGvdG22YbVjqnUnN1ua4":
        print("[ngrok] No authtoken set — skipping tunnel. Running locally only.")
        return None, None

    try:
        conf.get_default().auth_token = NGROK_AUTH_TOKEN
        print("\n[ngrok] Starting tunnel...")
        tunnel = ngrok.connect(port, "tcp")
        public_url = tunnel.public_url
        address    = public_url.replace("tcp://", "")
        ngrok_host, ngrok_port = address.rsplit(":", 1)
        ngrok_port = int(ngrok_port)
        return ngrok_host, ngrok_port
    except Exception as e:
        print(f"[ngrok] Tunnel failed: {e}")
        print("[ngrok] Server will still run locally on 127.0.0.1")
        return None, None


class Server:

    def __init__(self):
        self.rooms  = df(list)
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def accept_connections(self, ip_address, port):
        self.ip_address = ip_address
        self.port       = port

        self.server.bind((self.ip_address, int(self.port)))
        self.server.listen(100)

        ngrok_host, ngrok_port = start_ngrok(port)

        print("\n" + "="*54)
        print("  ChatShield Server is RUNNING")
        print("="*54)

        if ngrok_host and ngrok_port:
            connect_str = f"{ngrok_host}:{ngrok_port}"
            print(f"\n  Share this with others to connect:")
            print(f"\n      HOST : {ngrok_host}")
            print(f"      PORT : {ngrok_port}")
            print(f"\n  One-line address:  {connect_str}")
            print("\n  Scan QR code to copy address:\n")
            print_qr(connect_str)
        else:
            print(f"\n  Local only: {ip_address}:{port}")
            print("  Install pyngrok and add authtoken for remote access.")

        print("\n" + "="*54 + "\n")

        while True:
            connection, address = self.server.accept()
            print(f"[+] {address[0]}:{address[1]} connected")
            start_new_thread(self.clientThread, (connection,))

        self.server.close()

    def clientThread(self, connection):
        try:
            user_id = connection.recv(1024).decode().replace("User ", "")
            room_id = connection.recv(1024).decode().replace("Join ", "")
        except Exception as e:
            print(f"[ERROR] Handshake failed: {e}")
            connection.close()
            return

        if room_id not in self.rooms:
            connection.send("New Group created".encode())
        else:
            connection.send("Welcome to chat room".encode())

        self.rooms[room_id].append(connection)

        while True:
            try:
                message = connection.recv(1024)
                pred      = 0
                bully_type = None

                if message:
                    if message.decode() == "FILE":
                        self.broadcastFile(connection, room_id, user_id)
                    else:
                        pred, bully_type = self.prettyPrinter(message.decode())
                        message_to_send  = f"<{user_id}> {message.decode()}"
                        self.broadcast(message_to_send, connection, room_id, pred, bully_type)
                else:
                    self.remove(connection, room_id)

            except Exception as e:
                print(f"[DISCONNECT] {repr(e)}")
                self.remove(connection, room_id)
                break

    def broadcastFile(self, connection, room_id, user_id):
        file_name = connection.recv(1024).decode()
        lenOfFile = connection.recv(1024).decode()

        for client in self.rooms[room_id]:
            if client != connection:
                try:
                    client.send("FILE".encode());    time.sleep(0.1)
                    client.send(file_name.encode()); time.sleep(0.1)
                    client.send(lenOfFile.encode()); time.sleep(0.1)
                    client.send(user_id.encode())
                except:
                    client.close()
                    self.remove(client, room_id)

        total = 0
        while str(total) != lenOfFile:
            data   = connection.recv(1024)
            total += len(data)
            for client in self.rooms[room_id]:
                if client != connection:
                    try:
                        client.send(data)
                        time.sleep(0.1)
                    except:
                        client.close()
                        self.remove(client, room_id)

    def prettyPrinter(self, data_1):
        # Uses pre-loaded vocab + stopwords — no disk I/O per message
        tfidf_vector = TfidfVectorizer(stop_words=_stopwords, lowercase=True, vocabulary=_vocab)
        data_2       = tfidf_vector.fit_transform([data_1])
        pred         = model.predict(data_2)

        if pred == 0:
            print("[ML] Non-bullying")
            return 0, None
        else:
            bully_type = detect_bullying_type(data_1)
            print(f"[ML] Bullying detected: {bully_type}")
            return 1, bully_type

    def broadcast(self, message_to_send, connection, room_id, pred, bully_type):
        for client in self.rooms[room_id]:
            try:
                if pred == 0:
                    client.send(message_to_send.encode())
                else:
                    if client == connection:
                        msg = f"Your message was blocked.\nType: {bully_type}"
                    else:
                        msg = f"Bullying message hidden.\nType: {bully_type}"
                    client.send(msg.encode())
            except:
                client.close()
                self.remove(client, room_id)

    def remove(self, connection, room_id):
        if connection in self.rooms[room_id]:
            self.rooms[room_id].remove(connection)


if __name__ == "__main__":
    ip_address = "0.0.0.0"   # Listen on all interfaces so ngrok can reach it
    port       = 12345

    s = Server()
    s.accept_connections(ip_address, port)