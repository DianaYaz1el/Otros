import socket
import tkinter as tk
from tkinter import messagebox
import math

COLOR_FONDO       = "#0b1220"
COLOR_PANEL       = "#121a2b"
COLOR_BORDE       = "#23304f"
COLOR_ACENTO      = "#2f6bff"
COLOR_TEXTO       = "#e8eefc"
COLOR_TEXTO_SUAVE = "#9fb2df"
COLOR_CANVAS_BG   = "#0e1626"

def send_tcp(sid: int, ang: int) -> bool:
    ip = entry_ip.get().strip()
    port_str = entry_port.get().strip()

    if not ip:
        messagebox.showwarning("Falta IP", "Ingresa la IP de la Raspberry Pi.")
        return False
    if not port_str:
        messagebox.showwarning("Falta puerto", "Ingresa el puerto (por ejemplo 5001).")
        return False
    try:
        port = int(port_str)
    except ValueError:
        messagebox.showerror("Error", "El puerto debe ser un número entero.")
        return False

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.4)
            s.connect((ip, port))
            s.sendall(f"{sid} {ang}\n".encode("utf-8"))
        return True
    except OSError:
        return False

def draw_gauge(canvas: tk.Canvas, ang: int, title: str):
    canvas.delete("all")
    cx, cy = 110, 110
    r = 80

    canvas.create_oval(cx-r, cy-r, cx+r, cy+r, outline=COLOR_BORDE, width=2)
    canvas.create_text(cx, 18, text=title, fill=COLOR_TEXTO, font=("Segoe UI", 10, "bold"))

    # etiquetas 0/90/180 (0 derecha, 90 arriba, 180 izquierda)
    canvas.create_text(cx+r+16, cy, text="0°", fill=COLOR_TEXTO_SUAVE, font=("Segoe UI", 9))
    canvas.create_text(cx, cy-r-14, text="90°", fill=COLOR_TEXTO_SUAVE, font=("Segoe UI", 9))
    canvas.create_text(cx-r-18, cy, text="180°", fill=COLOR_TEXTO_SUAVE, font=("Segoe UI", 9))

    rad = math.radians(ang)
    x2 = cx + r * math.cos(rad)
    y2 = cy - r * math.sin(rad)

    canvas.create_line(cx, cy, x2, y2, fill=COLOR_ACENTO, width=4, capstyle="round")
    canvas.create_oval(cx-6, cy-6, cx+6, cy+6, fill=COLOR_ACENTO, outline="")
    canvas.create_text(cx, cy+58, text=f"{ang}°", fill=COLOR_TEXTO, font=("Segoe UI", 13, "bold"))

class ServoWidget:
    def __init__(self, parent, sid: int, title: str):
        self.sid = sid
        self.after_id = None

        self.frame = tk.Frame(parent, bg=COLOR_PANEL, highlightbackground=COLOR_BORDE, highlightthickness=1)
        self.frame.pack(side="left", padx=10, pady=10)

        self.canvas = tk.Canvas(self.frame, width=220, height=220, bg=COLOR_CANVAS_BG, highlightthickness=0)
        self.canvas.pack(padx=12, pady=(12, 8))

        self.lbl = tk.Label(self.frame, text=f"Servo {sid}: 90°", bg=COLOR_PANEL, fg=COLOR_TEXTO, font=("Segoe UI", 11, "bold"))
        self.lbl.pack(padx=12, pady=(0, 8), anchor="w")

        self.slider = tk.Scale(self.frame, from_=0, to=180, orient=tk.HORIZONTAL,
                               resolution=1, length=220, showvalue=False,
                               command=self.on_move,
                               bg=COLOR_PANEL, fg=COLOR_TEXTO, highlightthickness=0,
                               troughcolor="#0e1626")
        self.slider.pack(padx=12, pady=(0, 12))
        self.slider.set(90)

        draw_gauge(self.canvas, 90, title)

    def on_move(self, value_str):
        try:
            ang = int(float(value_str))
        except ValueError:
            return

        self.lbl.config(text=f"Servo {self.sid}: {ang}°")
        draw_gauge(self.canvas, ang, f"Servo {self.sid}")

        # debounce para no saturar red
        if self.after_id is not None:
            root.after_cancel(self.after_id)
        self.after_id = root.after(120, lambda: self._send(ang))

    def _send(self, ang: int):
        ok = send_tcp(self.sid, ang)
        if ok:
            status_lbl.config(text="Estado: Enviado", fg="#7CFF9A")
        else:
            status_lbl.config(text="Estado: Error de conexión", fg="#FF7C7C")

root = tk.Tk()
root.title("Control 3 Servos (TCP)")
root.configure(bg=COLOR_FONDO)
root.minsize(820, 420)

# Panel conexión
conn = tk.Frame(root, bg=COLOR_PANEL, highlightbackground=COLOR_BORDE, highlightthickness=1)
conn.pack(fill="x", padx=18, pady=(18, 10))

tk.Label(conn, text="Conexión con Raspberry Pi (TCP)", bg=COLOR_PANEL, fg=COLOR_ACENTO,
         font=("Segoe UI", 11, "bold")).grid(row=0, column=0, columnspan=4, padx=12, pady=(10, 6), sticky="w")

tk.Label(conn, text="IP:", bg=COLOR_PANEL, fg=COLOR_TEXTO_SUAVE, font=("Segoe UI", 10)).grid(row=1, column=0, padx=(12, 6), pady=6, sticky="e")
entry_ip = tk.Entry(conn, width=16, bg="#0e1626", fg=COLOR_TEXTO, insertbackground=COLOR_TEXTO, relief="flat")
entry_ip.grid(row=1, column=1, padx=(0, 14), pady=6, sticky="w")
entry_ip.insert(0, "192.168.0.101")

tk.Label(conn, text="Puerto:", bg=COLOR_PANEL, fg=COLOR_TEXTO_SUAVE, font=("Segoe UI", 10)).grid(row=1, column=2, padx=(8, 6), pady=6, sticky="e")
entry_port = tk.Entry(conn, width=8, bg="#232324", fg=COLOR_TEXTO, insertbackground=COLOR_TEXTO, relief="flat")
entry_port.grid(row=1, column=3, padx=(0, 12), pady=6, sticky="w")
entry_port.insert(0, "5001")

status_lbl = tk.Label(conn, text="Estado: —", bg=COLOR_PANEL, fg=COLOR_TEXTO_SUAVE, font=("Segoe UI", 9))
status_lbl.grid(row=2, column=0, columnspan=4, padx=12, pady=(2, 10), sticky="w")

# Widgets servos
main = tk.Frame(root, bg=COLOR_FONDO)
main.pack(fill="both", expand=True, padx=18, pady=(6, 18))

w1 = ServoWidget(main, 1, "Servo 1")
w2 = ServoWidget(main, 2, "Servo 2")
w3 = ServoWidget(main, 3, "Servo 3")

root.mainloop()
