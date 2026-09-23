#!/usr/bin/env python3
"""
file_locker_gui.py — Hacker-styled GUI for encrypting/decrypting files.

Requires: pip install cryptography
Run:      python file_locker_gui.py
"""

import base64
import os
import random
import string
import threading
import tkinter as tk
from tkinter import filedialog

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

SALT_SIZE = 16
KDF_ITERATIONS = 480_000
MAGIC = b"FLCK1"

BG = "#000000"
GREEN = "#00ff41"
DIM_GREEN = "#0a3d1a"
FONT = ("Consolas", 11)
FONT_BOLD = ("Consolas", 12, "bold")
FONT_BANNER = ("Consolas", 20, "bold")

USER_NAME = "JATIN"

ASCII_BANNER = r"""
     ____ ___ _     _____   _    _   _ _     _____ 
    |  _ \_ _| |   | ____| | |  | | | | |   |_   _|
    | |_) | || |   |  _|   | |  | | | | |     | |  
    |  _ < | || |__| |___  | |__| |_| | |___  | |  
    |_| \_\___|_____|_____| |_____\___/|_____| |_|
"""


def derive_key(passphrase: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=KDF_ITERATIONS)
    return base64.urlsafe_b64encode(kdf.derive(passphrase.encode("utf-8")))


class MatrixRain(tk.Canvas):
    """Faint falling-code background effect."""

    CHARS = string.ascii_uppercase + string.digits + "@#$%&"

    def __init__(self, master, width, height, **kw):
        super().__init__(master, width=width, height=height, bg=BG, highlightthickness=0, **kw)
        self.width = width
        self.height = height
        self.font_size = 14
        self.cols = width // self.font_size
        self.drops = [random.randint(-20, 0) for _ in range(self.cols)]
        self.after(50, self.animate)

    def animate(self):
        self.delete("all")
        for i in range(self.cols):
            x = i * self.font_size
            y = self.drops[i] * self.font_size
            ch = random.choice(self.CHARS)
            shade = random.choice([GREEN, DIM_GREEN, "#003b0f"])
            self.create_text(x, y, text=ch, fill=shade, font=("Consolas", self.font_size), anchor="nw")
            if y > self.height and random.random() > 0.975:
                self.drops[i] = 0
            else:
                self.drops[i] += 1
        self.after(60, self.animate)


class FileLockerGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{USER_NAME}'S VAULT // FILE ENCRYPTOR")
        self.configure(bg=BG)
        self.geometry("720x560")
        self.resizable(False, False)
        self.selected_file = None

        self.rain = MatrixRain(self, 720, 560)
        self.rain.place(x=0, y=0)

        overlay = tk.Frame(self, bg=BG)
        overlay.place(x=0, y=0, width=720, height=560)

        tk.Label(overlay, text=ASCII_BANNER, fg=GREEN, bg=BG, font=("Consolas", 9), justify="left").pack(pady=(10, 0))
        tk.Label(overlay, text=f"OPERATOR: {USER_NAME}", fg=GREEN, bg=BG, font=FONT_BOLD).pack(pady=(0, 5))
        tk.Label(overlay, text="[ SECURE FILE ENCRYPTION TERMINAL ]", fg=DIM_GREEN, bg=BG, font=FONT).pack(pady=(0, 15))

        # File selection
        file_frame = tk.Frame(overlay, bg=BG)
        file_frame.pack(pady=5, fill="x", padx=30)
        self.file_label = tk.Label(file_frame, text="[ NO FILE SELECTED ]", fg=GREEN, bg="#001a05",
                                    font=FONT, anchor="w", relief="solid", bd=1, padx=8, pady=6)
        self.file_label.pack(side="left", fill="x", expand=True)
        self._make_button(file_frame, "BROWSE", self.browse_file).pack(side="left", padx=(8, 0))

        # Passkey entry
        pass_frame = tk.Frame(overlay, bg=BG)
        pass_frame.pack(pady=15, fill="x", padx=30)
        tk.Label(pass_frame, text="ENTER PASSKEY >", fg=GREEN, bg=BG, font=FONT).pack(side="left")
        self.pass_entry = tk.Entry(pass_frame, show="*", bg="#001a05", fg=GREEN, insertbackground=GREEN,
                                    font=FONT, relief="solid", bd=1)
        self.pass_entry.pack(side="left", fill="x", expand=True, padx=8)

        # Action buttons
        btn_frame = tk.Frame(overlay, bg=BG)
        btn_frame.pack(pady=10)
        self._make_button(btn_frame, "ENCRYPT FILE", self.encrypt_action, width=18).pack(side="left", padx=10)
        self._make_button(btn_frame, "DECRYPT FILE", self.decrypt_action, width=18).pack(side="left", padx=10)

        # Terminal-style log
        tk.Label(overlay, text="LOG OUTPUT:", fg=DIM_GREEN, bg=BG, font=FONT).pack(anchor="w", padx=30, pady=(15, 0))
        self.log = tk.Text(overlay, height=12, bg="#000000", fg=GREEN, insertbackground=GREEN,
                            font=("Consolas", 10), relief="solid", bd=1)
        self.log.pack(padx=30, pady=(5, 15), fill="both", expand=True)
        self.log.configure(state="disabled")

        self.print_log(f">>> WELCOME, {USER_NAME}. VAULT SYSTEM ONLINE.")

    def _make_button(self, parent, text, command, width=12):
        return tk.Button(parent, text=text, command=lambda: threading.Thread(target=command).start(),
                          bg="#001a05", fg=GREEN, activebackground=GREEN, activeforeground=BG,
                          font=FONT_BOLD, relief="solid", bd=1, width=width, cursor="hand2")

    def print_log(self, msg):
        self.log.configure(state="normal")
        self.log.insert("end", msg + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def browse_file(self):
        path = filedialog.askopenfilename()
        if path:
            self.selected_file = path
            self.file_label.config(text=os.path.basename(path))
            self.print_log(f">>> FILE SELECTED: {path}")

    def encrypt_action(self):
        if not self.selected_file:
            self.print_log(">>> ERROR: NO FILE SELECTED.")
            return
        passphrase = self.pass_entry.get()
        if not passphrase:
            self.print_log(">>> ERROR: PASSKEY REQUIRED.")
            return

        with open(self.selected_file, "rb") as f:
            existing = f.read(len(MAGIC))
        if existing == MAGIC:
            self.print_log(">>> ERROR: FILE ALREADY ENCRYPTED.")
            return

        self.print_log(">>> DERIVING KEY (PBKDF2, 480000 ITERATIONS)...")
        salt = os.urandom(SALT_SIZE)
        key = derive_key(passphrase, salt)
        fernet = Fernet(key)

        with open(self.selected_file, "rb") as f:
            data = f.read()

        token = fernet.encrypt(data)

        base, ext = os.path.splitext(self.selected_file)
        ext_bytes = ext.encode("utf-8")
        new_path = base + ".txt"

        tmp_path = new_path + ".tmp"
        with open(tmp_path, "wb") as f:
            f.write(MAGIC)
            f.write(len(ext_bytes).to_bytes(1, "big"))
            f.write(ext_bytes)
            f.write(salt)
            f.write(token)
        os.replace(tmp_path, new_path)

        if new_path != self.selected_file:
            os.remove(self.selected_file)

        self.selected_file = new_path
        self.file_label.config(text=os.path.basename(new_path))
        self.print_log(f">>> FILE ENCRYPTED -> {new_path}")
        self.print_log(">>> OPEN IT IN A TEXT EDITOR TO SEE SCRAMBLED DATA.")

    def decrypt_action(self):
        if not self.selected_file:
            self.print_log(">>> ERROR: NO FILE SELECTED.")
            return
        passphrase = self.pass_entry.get()
        if not passphrase:
            self.print_log(">>> ERROR: PASSKEY REQUIRED.")
            return

        with open(self.selected_file, "rb") as f:
            raw = f.read()

        if not raw.startswith(MAGIC):
            self.print_log(">>> ERROR: FILE IS NOT ENCRYPTED (OR ALREADY UNLOCKED).")
            return

        offset = len(MAGIC)
        ext_len = raw[offset]
        offset += 1
        ext = raw[offset:offset + ext_len].decode("utf-8")
        offset += ext_len
        salt = raw[offset:offset + SALT_SIZE]
        offset += SALT_SIZE
        token = raw[offset:]

        self.print_log(">>> VERIFYING PASSKEY...")
        key = derive_key(passphrase, salt)
        fernet = Fernet(key)

        try:
            data = fernet.decrypt(token)
        except InvalidToken:
            self.print_log(">>> ACCESS DENIED. INCORRECT PASSKEY.")
            return

        base = os.path.splitext(self.selected_file)[0]
        new_path = base + ext
        tmp_path = new_path + ".tmp"
        with open(tmp_path, "wb") as f:
            f.write(data)
        os.replace(tmp_path, new_path)

        if new_path != self.selected_file:
            os.remove(self.selected_file)

        self.selected_file = new_path
        self.file_label.config(text=os.path.basename(new_path))
        self.print_log(f">>> ACCESS GRANTED. FILE DECRYPTED -> {new_path}")


if __name__ == "__main__":
    app = FileLockerGUI()
    app.mainloop()


# Code to run the GUI: python "C:\Users\Jatin Gupta\Downloads\File_Encryptor\file_locker.py"