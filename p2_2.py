import socket
import tkinter as tk
from tkinter import messagebox

PORT = 5000
HOST_DEFAULT = "rpidiana.local"  # o pon aquí la IP de la Raspberry, ej. "192.168.0.110"

def enviar_comando(valor):
    host = entry_host.get().strip()
    if not host:
        messagebox.showerror("Error", "Escribe el host o IP de la Raspberry")
        return
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((host, PORT))
            s.sendall(valor.encode())
    except Exception as e:
        messagebox.showerror("Error de conexión", str(e))

root = tk.Tk()
root.title("Control LED Arduino via Raspberry")

frame = tk.Frame(root, padx=10, pady=10)
frame.pack()

tk.Label(frame, text="Host de la Raspberry:").grid(row=0, column=0, sticky="e")
entry_host = tk.Entry(frame, width=25)
entry_host.grid(row=0, column=1, padx=5, pady=5)
entry_host.insert(0, HOST_DEFAULT)

btn_on = tk.Button(
    frame, text="Encender LED (1)", width=20,
    command=lambda: enviar_comando('1')
)
btn_on.grid(row=1, column=0, padx=5, pady=10)

btn_off = tk.Button(
    frame, text="Apagar LED (0)", width=20,
    command=lambda: enviar_comando('0')
)
btn_off.grid(row=1, column=1, padx=5, pady=10)

root.mainloop()
