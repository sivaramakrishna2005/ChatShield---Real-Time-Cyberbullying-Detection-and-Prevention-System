import socket
import customtkinter as ctk
from tkinter import filedialog
import threading
import time
import pickle
import os
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

base_dir = os.path.dirname(__file__)


class GUI:

    def __init__(self):
        self.name = ""
        self._sent_messages = set()   # track sent msgs to skip server echo

        self.Window = ctk.CTk()
        self.Window.withdraw()

        self.connect_win = ctk.CTkToplevel()
        self.connect_win.title("ChatShield — Connect")
        self.connect_win.geometry("420x400")
        self.connect_win.resizable(False, False)

        ctk.CTkLabel(self.connect_win, text="ChatShield",
                     font=ctk.CTkFont(size=32, weight="bold")).pack(pady=20)
        ctk.CTkLabel(self.connect_win, text="Enter server address shared by the host",
                     font=ctk.CTkFont(size=13), text_color="gray").pack(pady=2)

        self.hostEntry = ctk.CTkEntry(self.connect_win,
            placeholder_text="Host  (e.g. 0.tcp.ngrok.io)", width=300)
        self.hostEntry.pack(pady=10)

        self.portEntry = ctk.CTkEntry(self.connect_win,
            placeholder_text="Port  (e.g. 12345)", width=300)
        self.portEntry.pack(pady=5)

        self.connect_status = ctk.CTkLabel(self.connect_win, text="",
            font=ctk.CTkFont(size=12), text_color="#FF4C4C")
        self.connect_status.pack(pady=4)

        ctk.CTkButton(self.connect_win, text="Connect", fg_color="#0A66C2",
            width=200, command=self._do_connect).pack(pady=8)
        ctk.CTkLabel(self.connect_win, text="— or —",
            font=ctk.CTkFont(size=11), text_color="gray").pack()
        ctk.CTkButton(self.connect_win, text="Local (same machine)",
            fg_color="#333333", width=200, command=self._use_local).pack(pady=8)

        self.Window.mainloop()

    def _use_local(self):
        self.hostEntry.delete(0, "end"); self.hostEntry.insert(0, "127.0.0.1")
        self.portEntry.delete(0, "end"); self.portEntry.insert(0, "12345")
        self._do_connect()

    def _do_connect(self):
        host = self.hostEntry.get().strip()
        port = self.portEntry.get().strip()
        if not host or not port:
            self.connect_status.configure(text="Please fill in both host and port.")
            return
        try:
            port_int = int(port)
        except ValueError:
            self.connect_status.configure(text="Port must be a number.")
            return
        self.connect_status.configure(text="Connecting...", text_color="gray")
        self.connect_win.update()
        try:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.settimeout(10)
            self.server.connect((host, port_int))
            self.server.settimeout(None)
        except Exception as e:
            self.connect_status.configure(text=f"Connection failed: {e}", text_color="#FF4C4C")
            return

        try:
            self._vocab = pickle.load(open(os.path.join(base_dir, "tfidf_vector_vocabulary.pkl"), "rb"))
            self._model = pickle.load(open(os.path.join(base_dir, "LinearSVC.pkl"), "rb"))
        except Exception:
            self._vocab = None
            self._model = None

        self.connect_win.destroy()
        self._show_login()

    def _show_login(self):
        self.login = ctk.CTkToplevel()
        self.login.title("ChatShield Login")
        self.login.geometry("420x300")
        self.login.resizable(False, False)

        ctk.CTkLabel(self.login, text="Join a Room",
                     font=ctk.CTkFont(size=26, weight="bold")).pack(pady=20)

        self.userEntryName = ctk.CTkEntry(self.login,
            placeholder_text="Username", width=250)
        self.userEntryName.pack(pady=10)

        self.roomEntryName = ctk.CTkEntry(self.login,
            placeholder_text="Room ID", width=250)
        self.roomEntryName.pack(pady=10)

        ctk.CTkButton(self.login, text="Enter Chat", fg_color="#0A66C2",
            command=lambda: self.goAhead(
                self.userEntryName.get(), self.roomEntryName.get()
            )).pack(pady=20)

    def goAhead(self, username, room_id):
        if not username.strip() or not room_id.strip():
            return
        self.name = username
        self.server.send(username.encode()); time.sleep(0.1)
        self.server.send(room_id.encode())
        self.login.destroy()
        self.layout()
        threading.Thread(target=self.receive, daemon=True).start()

    def layout(self):
        self.Window.deiconify()
        self.Window.title("ChatShield")
        self.Window.geometry("620x680")

        header = ctk.CTkFrame(self.Window, fg_color="#0A66C2")
        header.pack(fill="x")
        ctk.CTkLabel(header, text="ChatShield",
                     font=ctk.CTkFont(size=22, weight="bold")).pack(pady=6)
        ctk.CTkLabel(header, text=f"Welcome {self.name}",
                     font=ctk.CTkFont(size=13)).pack(pady=4)

        self.textCons = ctk.CTkTextbox(self.Window, width=580, height=440, wrap="word")
        self.textCons.pack(pady=10)
        self.textCons.tag_config("msg_white",  foreground="white",  justify="left",
                                 lmargin1=10, lmargin2=10, rmargin=250)
        self.textCons.tag_config("msg_icon_red",    foreground="#FF4C4C")
        self.textCons.tag_config("msg_icon_orange", foreground="#FFA500")
        self.textCons.tag_config("msg_icon_green",  foreground="#00FF7F")
        self.textCons.tag_config("msg_me",     foreground="white",  justify="right",
                                 lmargin1=250, lmargin2=250, rmargin=10)
        self.textCons.tag_config("msg_system", foreground="gray",   justify="center")
        self.textCons.configure(state="disabled")

        bottom = ctk.CTkFrame(self.Window)
        bottom.pack(pady=5)
        self.entryMsg = ctk.CTkEntry(bottom, placeholder_text="Type message...", width=400)
        self.entryMsg.pack(side="left", padx=10)
        self.entryMsg.bind("<Return>", lambda e: self.sendButton(self.entryMsg.get()))
        ctk.CTkButton(bottom, text="Send", fg_color="#0A66C2", width=80,
            command=lambda: self.sendButton(self.entryMsg.get())).pack(side="left")
        ctk.CTkButton(bottom, text="File", fg_color="#444444", width=60,
            command=self._send_file).pack(side="left", padx=4)

    def timestamp(self):
        return datetime.now().strftime("%H:%M")

    def display_user_message(self, sender, message, status):
        self.textCons.configure(state="normal")
        self.textCons.insert("end", f"\n{sender} [{self.timestamp()}]\n", "msg_white")
        self.textCons.insert("end", message + " ", "msg_white")
        if status == "bullying":
            self.textCons.insert("end", "\U0001f6ab", "msg_icon_red")    # 🚫
        elif status == "unknown":
            self.textCons.insert("end", "\u26a0", "msg_icon_orange")     # ⚠
        else:
            self.textCons.insert("end", "\u2713", "msg_icon_green")      # ✓
        self.textCons.insert("end", "\n\n")
        self.textCons.configure(state="disabled")
        self.textCons.see("end")

    def display_my_message(self, message, status):
        self.textCons.configure(state="normal")
        self.textCons.insert("end", f"\nYou [{self.timestamp()}]\n{message} ", "msg_me")
        if status == "bullying":
            self.textCons.insert("end", "\U0001f6ab", "msg_icon_red")    # 🚫
        elif status == "unknown":
            self.textCons.insert("end", "\u26a0", "msg_icon_orange")     # ⚠
        else:
            self.textCons.insert("end", "\u2713", "msg_icon_green")      # ✓
        self.textCons.insert("end", "\n\n")
        self.textCons.configure(state="disabled")
        self.textCons.see("end")

    def sendButton(self, msg):
        if not msg.strip():
            return
        self.msg = msg
        self.entryMsg.delete(0, "end")
        threading.Thread(target=self.sendMessage, daemon=True).start()

    def receive(self):
        system_messages = ["Welcome to chat room", "New Group created"]
        while True:
            try:
                message = self.server.recv(1024).decode()

                if message in system_messages:
                    self.textCons.configure(state="normal")
                    self.textCons.insert("end", f"\n{message}\n\n", "msg_system")
                    self.textCons.configure(state="disabled")
                    continue

                if message == "FILE":
                    file_name = self.server.recv(1024).decode()
                    lenOfFile = self.server.recv(1024).decode()
                    send_user = self.server.recv(1024).decode()
                    if os.path.exists(file_name):
                        os.remove(file_name)
                    total = 0
                    with open(file_name, 'wb') as f:
                        while str(total) != lenOfFile:
                            data = self.server.recv(1024)
                            total += len(data)
                            f.write(data)
                    self.textCons.configure(state="normal")
                    self.textCons.insert("end",
                        f"\n\U0001f4ce {send_user} sent: {file_name}\n\n", "msg_system")
                    self.textCons.configure(state="disabled")
                    continue

                # Server blocked MY message
                if "Your message was blocked" in message:
                    self.textCons.configure(state="normal")
                    self.textCons.insert("end", f"\n\u26a0 {message}\n\n", "msg_icon_orange")
                    self.textCons.configure(state="disabled")
                    continue

                # Server hid someone else's bullying message
                if "Bullying message hidden" in message:
                    self.textCons.configure(state="normal")
                    self.textCons.insert("end", f"\n\U0001f6ab {message}\n\n", "msg_icon_red")
                    self.textCons.configure(state="disabled")
                    continue

                # Normal chat message
                if message.startswith("<") and ">" in message:
                    sender = message.split(">")[0][1:]
                    body   = message.split(">")[1].strip()

                    # Skip echo of our own messages
                    if sender == self.name and body in self._sent_messages:
                        self._sent_messages.discard(body)
                        continue

                    self.display_user_message(sender, body, "non-bullying")
                else:
                    self.textCons.configure(state="normal")
                    self.textCons.insert("end", f"\n{message}\n\n", "msg_system")
                    self.textCons.configure(state="disabled")

            except Exception as e:
                print(f"[RECEIVE ERROR] {e}")
                self.server.close()
                break

    def sendMessage(self):
        try:
            self.server.send(self.msg.encode())
        except Exception as e:
            print(f"[SEND ERROR] {e}")
            return

        self._sent_messages.add(self.msg)
        status = self._classify_local(self.msg)
        self.display_my_message(self.msg, status)

    def _send_file(self):
        file_path = filedialog.askopenfilename()
        if not file_path:
            return
        file_name = os.path.basename(file_path)
        file_size = str(os.path.getsize(file_path))
        try:
            self.server.send("FILE".encode());               time.sleep(0.1)
            self.server.send(f"client_{file_name}".encode()); time.sleep(0.1)
            self.server.send(file_size.encode());            time.sleep(0.1)
            with open(file_path, "rb") as f:
                data = f.read(1024)
                while data:
                    self.server.send(data)
                    data = f.read(1024)
            self.textCons.configure(state="normal")
            self.textCons.insert("end", f"\n\U0001f4ce You sent: {file_name}\n\n", "msg_system")
            self.textCons.configure(state="disabled")
        except Exception as e:
            print(f"[FILE ERROR] {e}")

    def _classify_local(self, text):
        if self._model is None or self._vocab is None:
            return "unknown"
        try:
            tfidf = TfidfVectorizer(vocabulary=self._vocab)
            data  = tfidf.fit_transform([text.strip()])
            pred  = self._model.predict(data)
            return "bullying" if int(pred[0]) == 1 else "non-bullying"
        except Exception:
            return "unknown"


if __name__ == "__main__":
    g = GUI()