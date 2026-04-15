"""
ChatShield — Lightweight Guest Client
======================================
For devices that DON'T have the full project.

Requirements (only these two):
    pip install customtkinter

Usage:
    python join.py
"""

import socket
import customtkinter as ctk
from tkinter import filedialog
import threading
import time
import os
from datetime import datetime

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class GuestClient:

    def __init__(self):
        self.name = ""
        self._sent_messages = set()   # track messages we sent to skip echo

        self.Window = ctk.CTk()
        self.Window.withdraw()

        # ── Connect screen ─────────────────────────────────────────────────
        self.connect_win = ctk.CTkToplevel()
        self.connect_win.title("ChatShield — Join")
        self.connect_win.geometry("440x420")
        self.connect_win.resizable(False, False)

        ctk.CTkLabel(
            self.connect_win,
            text="ChatShield",
            font=ctk.CTkFont(size=32, weight="bold")
        ).pack(pady=20)

        ctk.CTkLabel(
            self.connect_win,
            text="Enter the HOST and PORT shared by the host",
            font=ctk.CTkFont(size=13),
            text_color="gray"
        ).pack(pady=2)

        self.hostEntry = ctk.CTkEntry(
            self.connect_win,
            placeholder_text="Host  (e.g. 0.tcp.ngrok.io  or  127.0.0.1)",
            width=320
        )
        self.hostEntry.pack(pady=10)

        self.portEntry = ctk.CTkEntry(
            self.connect_win,
            placeholder_text="Port  (e.g. 12345)",
            width=320
        )
        self.portEntry.pack(pady=5)

        self.status_label = ctk.CTkLabel(
            self.connect_win,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="#FF4C4C"
        )
        self.status_label.pack(pady=4)

        ctk.CTkButton(
            self.connect_win,
            text="Connect",
            fg_color="#0A66C2",
            width=220,
            command=self._do_connect
        ).pack(pady=10)

        ctk.CTkLabel(
            self.connect_win,
            text="— or connect locally —",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        ).pack()

        ctk.CTkButton(
            self.connect_win,
            text="Same machine  (127.0.0.1:12345)",
            fg_color="#2a2a2a",
            width=220,
            command=self._use_local
        ).pack(pady=8)

        self.Window.mainloop()

    # ── Helpers ────────────────────────────────────────────────────────────

    def _use_local(self):
        self.hostEntry.delete(0, "end")
        self.hostEntry.insert(0, "127.0.0.1")
        self.portEntry.delete(0, "end")
        self.portEntry.insert(0, "12345")
        self._do_connect()

    def _do_connect(self):
        host = self.hostEntry.get().strip()
        port = self.portEntry.get().strip()

        if not host or not port:
            self.status_label.configure(
                text="Please enter both Host and Port.", text_color="#FF4C4C"
            )
            return

        try:
            port_int = int(port)
        except ValueError:
            self.status_label.configure(
                text="Port must be a number.", text_color="#FF4C4C"
            )
            return

        self.status_label.configure(text="Connecting...", text_color="gray")
        self.connect_win.update()

        try:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.settimeout(12)
            self.server.connect((host, port_int))
            self.server.settimeout(None)
        except Exception as e:
            self.status_label.configure(
                text=f"Failed: {e}", text_color="#FF4C4C"
            )
            return

        self.connect_win.destroy()
        self._show_login()

    # ── Login screen ───────────────────────────────────────────────────────

    def _show_login(self):
        self.login = ctk.CTkToplevel()
        self.login.title("ChatShield — Join Room")
        self.login.geometry("420x300")
        self.login.resizable(False, False)

        ctk.CTkLabel(
            self.login,
            text="Join a Room",
            font=ctk.CTkFont(size=26, weight="bold")
        ).pack(pady=20)

        self.userEntry = ctk.CTkEntry(
            self.login, placeholder_text="Your username", width=260
        )
        self.userEntry.pack(pady=10)

        self.roomEntry = ctk.CTkEntry(
            self.login, placeholder_text="Room ID  (must match host's room)", width=260
        )
        self.roomEntry.pack(pady=10)

        self.login_status = ctk.CTkLabel(
            self.login, text="", font=ctk.CTkFont(size=12), text_color="#FF4C4C"
        )
        self.login_status.pack(pady=2)

        ctk.CTkButton(
            self.login,
            text="Enter Chat",
            fg_color="#0A66C2",
            width=200,
            command=self._join_room
        ).pack(pady=14)

    def _join_room(self):
        username = self.userEntry.get().strip()
        room_id  = self.roomEntry.get().strip()

        if not username or not room_id:
            self.login_status.configure(text="Please fill in both fields.")
            return

        self.name = username

        try:
            self.server.send(username.encode())
            time.sleep(0.1)
            self.server.send(room_id.encode())
        except Exception as e:
            self.login_status.configure(text=f"Send error: {e}")
            return

        self.login.destroy()
        self._build_chat()

        threading.Thread(target=self._receive_loop, daemon=True).start()

    # ── Chat UI ────────────────────────────────────────────────────────────

    def _build_chat(self):
        self.Window.deiconify()
        self.Window.title("ChatShield")
        self.Window.geometry("620x680")

        header = ctk.CTkFrame(self.Window, fg_color="#0A66C2")
        header.pack(fill="x")

        ctk.CTkLabel(
            header, text="ChatShield",
            font=ctk.CTkFont(size=22, weight="bold")
        ).pack(pady=6)

        ctk.CTkLabel(
            header, text=f"Welcome {self.name}",
            font=ctk.CTkFont(size=13)
        ).pack(pady=4)

        self.chatbox = ctk.CTkTextbox(
            self.Window, width=580, height=450, wrap="word"
        )
        self.chatbox.pack(pady=10)

        self.chatbox.tag_config(
            "msg_other", foreground="white", justify="left",
            lmargin1=10, lmargin2=10, rmargin=250
        )
        self.chatbox.tag_config(
            "msg_me", foreground="white", justify="right",
            lmargin1=250, lmargin2=250, rmargin=10
        )
        self.chatbox.tag_config("system",  foreground="gray",    justify="center")
        self.chatbox.tag_config("red",     foreground="#FF4C4C", justify="center")
        self.chatbox.tag_config("green",   foreground="#00FF7F")
        self.chatbox.tag_config("orange",  foreground="#FFA500")
        self.chatbox.configure(state="disabled")

        bottom = ctk.CTkFrame(self.Window)
        bottom.pack(pady=5)

        self.msgEntry = ctk.CTkEntry(
            bottom, placeholder_text="Type a message...", width=400
        )
        self.msgEntry.pack(side="left", padx=10)
        self.msgEntry.bind("<Return>", lambda e: self._send_text(self.msgEntry.get()))

        ctk.CTkButton(
            bottom, text="Send", fg_color="#0A66C2", width=80,
            command=lambda: self._send_text(self.msgEntry.get())
        ).pack(side="left")

        ctk.CTkButton(
            bottom, text="File", fg_color="#444444", width=60,
            command=self._send_file
        ).pack(side="left", padx=4)

    # ── Messaging ──────────────────────────────────────────────────────────

    def _ts(self):
        return datetime.now().strftime("%H:%M")

    def _append(self, text, tag):
        self.chatbox.configure(state="normal")
        self.chatbox.insert("end", text, tag)
        self.chatbox.configure(state="disabled")
        self.chatbox.see("end")

    def _show_incoming(self, sender, body):
        self.chatbox.configure(state="normal")
        self.chatbox.insert("end", f"\n{sender} [{self._ts()}]\n", "msg_other")
        self.chatbox.insert("end", body + " ", "msg_other")
        self.chatbox.insert("end", "\u2713\n\n", "green")   # ✓
        self.chatbox.configure(state="disabled")
        self.chatbox.see("end")

    def _show_mine(self, text):
        self.chatbox.configure(state="normal")
        self.chatbox.insert("end", f"\nYou [{self._ts()}]\n{text} ", "msg_me")
        self.chatbox.insert("end", "\u2713\n\n", "green")   # ✓
        self.chatbox.configure(state="disabled")
        self.chatbox.see("end")

    def _show_blocked_mine(self, reason):
        """Replace the optimistic sent message with a blocked notice."""
        self.chatbox.configure(state="normal")
        self.chatbox.insert("end", f"\n\u26a0 {reason}\n\n", "orange")   # ⚠
        self.chatbox.configure(state="disabled")
        self.chatbox.see("end")

    def _show_blocked_incoming(self, reason):
        self.chatbox.configure(state="normal")
        self.chatbox.insert("end", f"\n\U0001f6ab {reason}\n\n", "red")  # 🚫
        self.chatbox.configure(state="disabled")
        self.chatbox.see("end")

    def _send_text(self, msg):
        if not msg.strip():
            return
        self.msgEntry.delete(0, "end")
        self._pending_msg = msg
        threading.Thread(target=self._do_send, daemon=True).start()

    def _do_send(self):
        msg = self._pending_msg
        try:
            self.server.send(msg.encode())
            # Track this message so we skip the server's echo back to us
            self._sent_messages.add(msg)
            self._show_mine(msg)
        except Exception as e:
            self._append(f"\n[Error sending: {e}]\n\n", "red")

    def _receive_loop(self):
        system_msgs = ["Welcome to chat room", "New Group created"]

        while True:
            try:
                message = self.server.recv(1024).decode()

                if not message:
                    break

                # ── System notifications ───────────────────────────────────
                if message in system_msgs:
                    self._append(f"\n{message}\n\n", "system")
                    continue

                # ── Incoming file ──────────────────────────────────────────
                if message == "FILE":
                    file_name = self.server.recv(1024).decode()
                    lenOfFile = self.server.recv(1024).decode()
                    send_user = self.server.recv(1024).decode()
                    if os.path.exists(file_name):
                        os.remove(file_name)
                    total = 0
                    with open(file_name, "wb") as f:
                        while str(total) != lenOfFile:
                            data   = self.server.recv(1024)
                            total += len(data)
                            f.write(data)
                    self._append(
                        f"\n\U0001f4ce {send_user} sent: {file_name}\n\n", "system"
                    )
                    continue

                # ── Server blocked MY message (sender warning) ─────────────
                if "Your message was blocked" in message:
                    # Extract type if present  e.g. "Your message was blocked.\nType: Threat"
                    lines = message.replace("Your message was blocked.", "").strip()
                    reason = lines if lines else "Your message was blocked"
                    self._show_blocked_mine(f"Your message was blocked. {reason}")
                    continue

                # ── Server hid someone else's bullying message ─────────────
                if "Bullying message hidden" in message:
                    lines = message.replace("Bullying message hidden.", "").strip()
                    reason = lines if lines else ""
                    self._show_blocked_incoming(f"Bullying message hidden. {reason}")
                    continue

                # ── Normal chat message  <username> text ───────────────────
                if message.startswith("<") and ">" in message:
                    sender = message.split(">")[0][1:]
                    body   = message.split(">")[1].strip()

                    # Skip echo of our own messages
                    if sender == self.name and body in self._sent_messages:
                        self._sent_messages.discard(body)
                        continue

                    self._show_incoming(sender, body)

                else:
                    # Unknown / fallback system message
                    self._append(f"\n{message}\n\n", "system")

            except Exception as e:
                self._append(f"\n[Disconnected: {e}]\n\n", "red")
                break

    def _send_file(self):
        file_path = filedialog.askopenfilename()
        if not file_path:
            return
        file_name = os.path.basename(file_path)
        file_size = str(os.path.getsize(file_path))
        try:
            self.server.send("FILE".encode());                  time.sleep(0.1)
            self.server.send(f"client_{file_name}".encode());  time.sleep(0.1)
            self.server.send(file_size.encode());               time.sleep(0.1)
            with open(file_path, "rb") as f:
                data = f.read(1024)
                while data:
                    self.server.send(data)
                    data = f.read(1024)
            self._append(f"\n\U0001f4ce You sent: {file_name}\n\n", "system")
        except Exception as e:
            self._append(f"\n[File error: {e}]\n\n", "red")


if __name__ == "__main__":
    GuestClient()