import base64
import os
import random
import string
import threading
import time
import tkinter as tk
from tkinter import filedialog

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

SALT_SIZE = 16
KDF_ITERATIONS = 480_000
MAGIC = b"FLCK1"

BG = "#000000"
PANEL_BG = "#001005"
GREEN = "#00ff41"
BRIGHT_GREEN = "#7dffb3"
DIM_GREEN = "#0a3d1a"
RED = "#ff2b2b"
FONT = ("Consolas", 11)
FONT_SMALL = ("Consolas", 9)
FONT_BOLD = ("Consolas", 12, "bold")

USER_NAME = "JATIN"
WIDTH, HEIGHT = 860, 620

ASCII_BANNER = r"""
██╗  ██╗ █████╗  ██████╗██╗  ██╗    ███╗   ██╗██╗███╗   ██╗     ██╗ █████╗
██║  ██║██╔══██╗██╔════╝██║ ██╔╝    ████╗  ██║██║████╗  ██║     ██║██╔══██╗
███████║███████║██║     █████╔╝     ██╔██╗ ██║██║██╔██╗ ██║     ██║███████║
██╔══██║██╔══██║██║     ██╔═██╗     ██║╚██╗██║██║██║╚██╗██║██   ██║██╔══██║
██║  ██║██║  ██║╚██████╗██║  ██╗    ██║ ╚████║██║██║ ╚████║╚█████╔╝██║  ██║
╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝    ╚═╝  ╚═══╝╚═╝╚═╝  ╚═══╝ ╚════╝ ╚═╝  ╚═╝
"""

BOOT_LINES = [
    "[BOOT] initializing kernel modules ...",
    "[BOOT] mounting secure volume /vault ...",
    "[BOOT] loading AES-CBC + HMAC-SHA256 cipher suite ...",
    "[BOOT] loading PBKDF2-HMAC key derivation engine (480000 rounds) ...",
    f"[AUTH] operator identity confirmed: {USER_NAME}",
    "[BOOT] establishing secure terminal session ...",
    "[ OK ] system ready.",
]


def derive_key(passphrase: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=KDF_ITERATIONS)
    return base64.urlsafe_b64encode(kdf.derive(passphrase.encode("utf-8")))


class MatrixRain(tk.Canvas):
    """Falling-code background effect."""

    CHARS = string.ascii_uppercase + string.digits + "@#$%&<>/\\"

    def __init__(self, master, width, height, **kw):
        super().__init__(master, width=width, height=height, bg=BG, highlightthickness=0, **kw)
        self.width = width
        self.height = height
        self.font_size = 14
        self.cols = width // self.font_size
        self.drops = [random.randint(-30, 0) for _ in range(self.cols)]
        self._running = True
        self.animate()

    def stop(self):
        self._running = False

    def animate(self):
        if not self._running:
            return
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
        self.after(55, self.animate)


class BootScreen(tk.Frame):
    """Fake boot-up sequence shown before the main terminal."""

    def __init__(self, master, on_done):
        super().__init__(master, bg=BG, width=WIDTH, height=HEIGHT)
        self.on_done = on_done
        self.text = tk.Text(self, bg=BG, fg=GREEN, insertbackground=GREEN, font=("Consolas", 12),
                             relief="flat", bd=0, highlightthickness=0)
        self.text.pack(fill="both", expand=True, padx=40, pady=40)
        self.text.configure(state="disabled")
        self.after(300, lambda: self._type_lines(0))

    def _type_lines(self, idx):
        if idx >= len(BOOT_LINES):
            self.after(500, self.on_done)
            return
        self._type_line(BOOT_LINES[idx], 0, idx)

    def _type_line(self, line, pos, idx):
        self.text.configure(state="normal")
        if pos == 0:
            self.text.insert("end", "\n")
        if pos < len(line):
            self.text.insert("end", line[pos])
            self.text.see("end")
            self.text.configure(state="disabled")
            self.after(8, lambda: self._type_line(line, pos + 1, idx))
        else:
            self.text.configure(state="disabled")
            self.after(120, lambda: self._type_lines(idx + 1))


class FileLockerGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{USER_NAME}'S VAULT // FILE ENCRYPTOR")
        self.configure(bg=BG)
        self.geometry(f"{WIDTH}x{HEIGHT}")
        self.resizable(False, False)
        self.selected_file = None
        self.status_var = tk.StringVar(value="IDLE")
        self.cursor_visible = True

        self.boot = BootScreen(self, self.show_main)
        self.boot.pack(fill="both", expand=True)

    # ---------- boot -> main ----------
    def show_main(self):
        self.boot.destroy()
        self.build_main_ui()

    def build_main_ui(self):
        self.rain = MatrixRain(self, WIDTH, HEIGHT)
        self.rain.place(x=0, y=0)

        overlay = tk.Frame(self, bg=BG)
        overlay.place(x=0, y=0, width=WIDTH, height=HEIGHT)

        # ---- header ----
        tk.Label(overlay, text=ASCII_BANNER, fg=GREEN, bg=BG, font=("Consolas", 9), justify="left").pack(pady=(8, 0))
        tk.Label(overlay, text=f"OPERATOR: {USER_NAME}    |    CLEARANCE: ROOT    |    CIPHER: AES + HMAC-SHA256",
                 fg=BRIGHT_GREEN, bg=BG, font=FONT_SMALL).pack(pady=(0, 10))

        body = tk.Frame(overlay, bg=BG)
        body.pack(fill="both", expand=True, padx=20, pady=(0, 15))

        # ---- left: system status sidebar ----
        sidebar = tk.Frame(body, bg=PANEL_BG, highlightbackground=DIM_GREEN, highlightthickness=1, width=230)
        sidebar.pack(side="left", fill="y", padx=(0, 12))
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text="┌─ SYSTEM STATUS ─┐", fg=GREEN, bg=PANEL_BG, font=FONT_SMALL).pack(pady=(12, 6))
        self.status_labels = {}
        for key, val in [
            ("MODE", "STANDBY"),
            ("KDF", "PBKDF2-HMAC-SHA256"),
            ("ROUNDS", f"{KDF_ITERATIONS:,}"),
            ("CIPHER", "AES-128-CBC+HMAC"),
            ("SESSION", "ACTIVE"),
        ]:
            row = tk.Frame(sidebar, bg=PANEL_BG)
            row.pack(fill="x", padx=12, pady=3, anchor="w")
            tk.Label(row, text=f"{key}:", fg=DIM_GREEN, bg=PANEL_BG, font=FONT_SMALL, width=8, anchor="w").pack(side="left")
            lbl = tk.Label(row, text=val, fg=GREEN, bg=PANEL_BG, font=FONT_SMALL, anchor="w", wraplength=130, justify="left")
            lbl.pack(side="left")
            self.status_labels[key] = lbl

        tk.Label(sidebar, text="└──────────────────┘", fg=GREEN, bg=PANEL_BG, font=FONT_SMALL).pack(pady=(10, 6))

        tk.Label(sidebar, text="LAST TARGET:", fg=DIM_GREEN, bg=PANEL_BG, font=FONT_SMALL).pack(pady=(20, 2), padx=12, anchor="w")
        self.target_label = tk.Label(sidebar, text="none", fg=GREEN, bg=PANEL_BG, font=FONT_SMALL,
                                      wraplength=200, justify="left")
        self.target_label.pack(padx=12, anchor="w")

        self.blink_label = tk.Label(sidebar, text="● STANDBY", fg=DIM_GREEN, bg=PANEL_BG, font=FONT_SMALL)
        self.blink_label.pack(side="bottom", pady=12)
        self._blink()

        # ---- right: main console ----
        console = tk.Frame(body, bg=BG)
        console.pack(side="left", fill="both", expand=True)

        file_frame = tk.Frame(console, bg=BG)
        file_frame.pack(fill="x")
        self.file_label = tk.Label(file_frame, text="[ NO FILE SELECTED ]", fg=GREEN, bg="#001a05",
                                    font=FONT, anchor="w", relief="solid", bd=1, padx=8, pady=6)
        self.file_label.pack(side="left", fill="x", expand=True)
        self._make_button(file_frame, "BROWSE", self.browse_file).pack(side="left", padx=(8, 0))

        pass_frame = tk.Frame(console, bg=BG)
        pass_frame.pack(pady=15, fill="x")
        tk.Label(pass_frame, text="PASSKEY >", fg=GREEN, bg=BG, font=FONT).pack(side="left")
        self.pass_entry = tk.Entry(pass_frame, show="*", bg="#001a05", fg=GREEN, insertbackground=GREEN,
                                    font=FONT, relief="solid", bd=1)
        self.pass_entry.pack(side="left", fill="x", expand=True, padx=8)

        btn_frame = tk.Frame(console, bg=BG)
        btn_frame.pack(pady=6)
        self._make_button(btn_frame, "ENCRYPT FILE", self.encrypt_action, width=18).pack(side="left", padx=10)
        self._make_button(btn_frame, "DECRYPT FILE", self.decrypt_action, width=18).pack(side="left", padx=10)

        # progress bar
        prog_frame = tk.Frame(console, bg=BG)
        prog_frame.pack(fill="x", pady=(10, 0))
        tk.Label(prog_frame, textvariable=self.status_var, fg=DIM_GREEN, bg=BG, font=FONT_SMALL).pack(anchor="w")
        self.progress_canvas = tk.Canvas(prog_frame, height=16, bg="#001005", highlightbackground=DIM_GREEN,
                                          highlightthickness=1)
        self.progress_canvas.pack(fill="x", pady=(4, 0))
        self.progress_bar = self.progress_canvas.create_rectangle(0, 0, 0, 16, fill=GREEN, width=0)

        tk.Label(console, text="LOG OUTPUT:", fg=DIM_GREEN, bg=BG, font=FONT).pack(anchor="w", pady=(15, 0))
        self.log = tk.Text(console, height=13, bg="#000000", fg=GREEN, insertbackground=GREEN,
                            font=("Consolas", 10), relief="solid", bd=1)
        self.log.pack(pady=(5, 0), fill="both", expand=True)
        self.log.configure(state="disabled")

        self.print_log(f">>> WELCOME, {USER_NAME}. VAULT SYSTEM ONLINE.")
        self.print_log(">>> AWAITING TARGET FILE...")

    # ---------- visuals ----------
    def _blink(self):
        self.cursor_visible = not self.cursor_visible
        color = GREEN if self.cursor_visible else DIM_GREEN
        text = "● " + self.status_var.get()
        self.blink_label.config(text=text, fg=color)
        self.after(600, self._blink)

    def _set_progress(self, fraction):
        w = self.progress_canvas.winfo_width() or 400
        self.progress_canvas.coords(self.progress_bar, 0, 0, w * fraction, 16)

    def _run_progress(self, label, steps=18, delay=0.03):
        """Animate a fake progress sweep for dramatic effect."""
        self.status_var.set(label)
        for i in range(steps + 1):
            frac = i / steps
            self.after(0, self._set_progress, frac)
            time.sleep(delay)
        self.after(0, self._set_progress, 0)
        self.status_var.set("IDLE")

    def _make_button(self, parent, text, command, width=12):
        return tk.Button(parent, text=text, command=lambda: threading.Thread(target=command, daemon=True).start(),
                          bg="#001a05", fg=GREEN, activebackground=GREEN, activeforeground=BG,
                          font=FONT_BOLD, relief="solid", bd=1, width=width, cursor="hand2")

    def print_log(self, msg):
        self.log.configure(state="normal")
        self.log.insert("end", msg + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    # ---------- actions ----------
    def browse_file(self):
        path = filedialog.askopenfilename()
        if path:
            self.selected_file = path
            self.file_label.config(text=os.path.basename(path))
            self.target_label.config(text=os.path.basename(path))
            self.print_log(f">>> TARGET ACQUIRED: {path}")

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

        self.print_log(">>> DERIVING KEY (PBKDF2-HMAC-SHA256, 480000 ROUNDS)...")
        self._run_progress("ENCRYPTING...")

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
        self.target_label.config(text=os.path.basename(new_path))
        self.print_log(f">>> FILE ENCRYPTED -> {new_path}")
        self.print_log(">>> OPEN IT IN A TEXT EDITOR TO VIEW SCRAMBLED DATA.")

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
        self._run_progress("DECRYPTING...")

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
        self.target_label.config(text=os.path.basename(new_path))
        self.print_log(f">>> ACCESS GRANTED. FILE DECRYPTED -> {new_path}")


if __name__ == "__main__":
    app = FileLockerGUI()
    app.mainloop()


# Code to run the GUI: python "C:\Users\Jatin Gupta\Downloads\File_Encryptor\file_locker.py"