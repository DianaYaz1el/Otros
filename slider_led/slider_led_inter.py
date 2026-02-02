import socket
import tkinter as tk
from tkinter import messagebox

# ==========================
#  RUTAS DE LAS IMÁGENES
# ==========================
RUTA_BASE = r"C:\Users\diana\Pyton_microcontroladores\ImagenesInterfaces\leds_Intensidades"
RUTA_LED_APAGADO = RUTA_BASE + r"\led_apagado.png"
RUTA_LED_BAJO    = RUTA_BASE + r"\led_bajo.png"
RUTA_LED_MEDIO   = RUTA_BASE + r"\led_medio.png"
RUTA_LED_ALTO    = RUTA_BASE + r"\led_alto.png"

# ==========================
#  FUNCIONES LÓGICA
# ==========================

def actualizar_imagen_led(valor):
    """Cambia la imagen del LED según el valor (0-255)."""
    v = int(valor)

    if v <= 63:
        imagen = img_apagado
    elif v <= 127:
        imagen = img_bajo
    elif v <= 191:
        imagen = img_medio
    else:
        imagen = img_alto

    label_led.config(image=imagen)
    label_led.image = imagen   # mantener referencia


def enviar_valor(valor_str):
    """Se llama cada vez que se mueve el slider."""
    ip = entry_ip.get().strip()
    port_str = entry_port.get().strip()

    if not ip:
        messagebox.showwarning("Falta IP", "Ingresa la IP de la Raspberry Pi.")
        return

    if not port_str:
        messagebox.showwarning("Falta puerto", "Ingresa el puerto (por ejemplo 5000).")
        return

    try:
        port = int(port_str)
    except ValueError:
        messagebox.showerror("Error", "El puerto debe ser un número entero.")
        return

    try:
        valor = int(float(valor_str))
    except ValueError:
        return

    # Actualizar imagen según brillo
    actualizar_imagen_led(valor)

    # Enviar a la Raspberry
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((ip, port))
            mensaje = f"{valor}\n"
            s.sendall(mensaje.encode("utf-8"))
    except OSError as e:
        print(f"Error al conectar con la Raspberry: {e}")


# ==========================
#  INTERFAZ GRÁFICA
# ==========================

# Colores en hexadecimal
COLOR_FONDO      = "#1e1e2f"
COLOR_PANEL      = "#5D5DDA"
COLOR_ACENTO     = "#e7b3ae"
COLOR_TEXTO      = "#ffffff"
COLOR_TEXTO_SUAVE = "#c3c3d7"
COLOR_SLIDER_BG  = "#464691"

root = tk.Tk()
root.title("Control de Brillo LED")
root.configure(bg=COLOR_FONDO)

# Evitar que la ventana sea demasiado pequeña
root.minsize(480, 360)

# ------- Panel de conexión (arriba) -------
frame_conn = tk.Frame(root, bg=COLOR_PANEL, bd=1, relief="solid")
frame_conn.pack(fill="x", padx=15, pady=(15, 10))

title_conn = tk.Label(
    frame_conn,
    text="Conexión con Raspberry Pi",
    bg=COLOR_PANEL,
    fg=COLOR_ACENTO,
    font=("Segoe UI", 11, "bold")
)
title_conn.grid(row=0, column=0, columnspan=4, padx=10, pady=(8, 4), sticky="w")

label_ip = tk.Label(
    frame_conn,
    text="IP:",
    bg=COLOR_PANEL,
    fg=COLOR_TEXTO_SUAVE,
    font=("Segoe UI", 10)
)
label_ip.grid(row=1, column=0, padx=(10, 5), pady=6, sticky="e")

entry_ip = tk.Entry(
    frame_conn,
    width=16,
    bg="#181824",
    fg=COLOR_TEXTO,
    insertbackground=COLOR_TEXTO,  # color del cursor
    relief="flat"
)
entry_ip.grid(row=1, column=1, padx=(0, 15), pady=6, sticky="w")
entry_ip.insert(0, "192.168.0.101")

label_port = tk.Label(
    frame_conn,
    text="Puerto:",
    bg=COLOR_PANEL,
    fg=COLOR_TEXTO_SUAVE,
    font=("Segoe UI", 10)
)
label_port.grid(row=1, column=2, padx=(10, 5), pady=6, sticky="e")

entry_port = tk.Entry(
    frame_conn,
    width=8,
    bg="#181824",
    fg=COLOR_TEXTO,
    insertbackground=COLOR_TEXTO,
    relief="flat"
)
entry_port.grid(row=1, column=3, padx=(0, 10), pady=6, sticky="w")
entry_port.insert(0, "5000")

# ------- Panel del slider (centro) -------
frame_slider = tk.Frame(root, bg=COLOR_FONDO)
frame_slider.pack(fill="x", padx=15, pady=(5, 10))

label_brillo = tk.Label(
    frame_slider,
    text="Brillo del LED",
    bg=COLOR_FONDO,
    fg=COLOR_TEXTO,
    font=("Segoe UI", 12, "bold")
)
label_brillo.pack(pady=(5, 2))

label_rango = tk.Label(
    frame_slider,
    text="0 = apagado   ·   255 = máximo",
    bg=COLOR_FONDO,
    fg=COLOR_TEXTO_SUAVE,
    font=("Segoe UI", 9)
)
label_rango.pack(pady=(0, 8))

# Frame para que el slider tenga fondo diferente
slider_container = tk.Frame(frame_slider, bg=COLOR_SLIDER_BG, bd=0, relief="flat")
slider_container.pack(padx=20, pady=(0, 10), fill="x")

slider = tk.Scale(
    slider_container,
    from_=0,
    to=255,
    orient=tk.HORIZONTAL,
    resolution=1,
    length=340,
    command=enviar_valor,
    bg=COLOR_SLIDER_BG,
    fg=COLOR_TEXTO,
    highlightthickness=0,
    troughcolor="#101019",
    showvalue=True
)
slider.pack(padx=10, pady=10)

# ------- Panel de imagen (abajo) -------
frame_led = tk.Frame(root, bg=COLOR_FONDO)
frame_led.pack(pady=(5, 15))

subtitle_led = tk.Label(
    frame_led,
    text="Estado visual del LED",
    bg=COLOR_FONDO,
    fg=COLOR_TEXTO_SUAVE,
    font=("Segoe UI", 10)
)
subtitle_led.pack(pady=(0, 6))

# Cargar imágenes
img_apagado = tk.PhotoImage(file=RUTA_LED_APAGADO)
img_bajo    = tk.PhotoImage(file=RUTA_LED_BAJO)
img_medio   = tk.PhotoImage(file=RUTA_LED_MEDIO)
img_alto    = tk.PhotoImage(file=RUTA_LED_ALTO)

label_led = tk.Label(frame_led, bg=COLOR_FONDO, image=img_apagado)
label_led.image = img_apagado
label_led.pack()

# Valor inicial
slider.set(0)
actualizar_imagen_led(0)

root.mainloop()
