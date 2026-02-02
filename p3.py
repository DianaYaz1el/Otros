import tkinter as tk
from tkinter import messagebox, scrolledtext
import subprocess

def hacer_ping():
    host = entry_host.get().strip()
    if not host:
        messagebox.showwarning(
            "Dato faltante",
            "Ingresa la IP de la Raspberry Pi (por ejemplo 192.168.0.xxx)."
        )
        return

    text_salida.delete("1.0", tk.END)

    # En Windows: -n; en Linux sería -c
    comando = ["ping", "-n", "4", host]

    try:
        resultado = subprocess.run(
            comando,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore"
        )

        text_salida.insert(tk.END, f"Comando ejecutado:\n{' '.join(comando)}\n\n")
        if resultado.stdout:
            text_salida.insert(tk.END, resultado.stdout)
        if resultado.stderr:
            text_salida.insert(tk.END, "\n[STDERR]\n" + resultado.stderr)

        if resultado.returncode == 0:
            messagebox.showinfo(
                "Ping exitoso",
                "La Raspberry respondió correctamente al ping.\n\n"
                "La IP es alcanzable."
            )
        else:
            messagebox.showerror(
                "Ping fallido",
                "No se obtuvo respuesta.\n\n"
                "Posibles causas:\n"
                "- La Raspberry no está encendida.\n"
                "- No está conectada a la misma red WiFi.\n"
                "- La IP es incorrecta."
            )
    except Exception as e:
        messagebox.showerror("Error al hacer ping", str(e))


def conectar_ssh():
    usuario = entry_user.get().strip()
    host = entry_host.get().strip()

    if not usuario or not host:
        messagebox.showwarning(
            "Datos faltantes",
            "Ingresa el usuario SSH (por ejemplo diana) y la IP de la Raspberry."
        )
        return

    comando_ssh = f"ssh {usuario}@{host}"

    try:
        # Abre una nueva ventana de cmd con la sesión SSH
        subprocess.Popen(
            f'start cmd /k "{comando_ssh}"',
            shell=True
        )
    except Exception as e:
        messagebox.showerror("Error al abrir SSH", str(e))


# ---------------- INTERFAZ ----------------

ventana = tk.Tk()
ventana.title("Conexión a Raspberry Pi por IP (Ping / SSH)")
ventana.geometry("700x450")
ventana.configure(bg="#DDEEFF")  # azul muy clarito

# Marco de datos
frame_datos = tk.LabelFrame(
    ventana,
    text="Datos de conexión",
    padx=10,
    pady=10,
    bg="#DDEEFF"
)
frame_datos.pack(padx=10, pady=10, fill="x")

# Usuario SSH
tk.Label(frame_datos, text="Usuario SSH:", bg="#DDEEFF").grid(
    row=0, column=0, sticky="e", pady=5
)
entry_user = tk.Entry(frame_datos)
entry_user.grid(row=0, column=1, sticky="we", padx=5, pady=5)
entry_user.insert(0, "Nombre del Host")

# IP de la Raspberry
tk.Label(frame_datos, text="IP de la Raspberry Pi:", bg="#DDEEFF").grid(
    row=1, column=0, sticky="e", pady=5
)
entry_host = tk.Entry(frame_datos)
entry_host.grid(row=1, column=1, sticky="we", padx=5, pady=5)
entry_host.insert(0, "192.168.0.xxx")  # tu IP de wlan0

label_ayuda = tk.Label(
    frame_datos,
    text="Ejemplo: 192.168.0.xxx (IP de la Raspberry en la red WiFi 'Redes').",
    anchor="w",
    justify="left",
    bg="#DDEEFF"
)
label_ayuda.grid(row=2, column=0, columnspan=2, sticky="w", pady=5)

frame_datos.columnconfigure(1, weight=1)

# Marco de botones
frame_botones = tk.LabelFrame(
    ventana,
    text="Acciones",
    padx=10,
    pady=10,
    bg="#DDEEFF"
)
frame_botones.pack(padx=10, pady=5, fill="x")

btn_ping = tk.Button(frame_botones, text="Hacer PING", width=18, command=hacer_ping)
btn_ping.pack(side="left", padx=5)

btn_ssh = tk.Button(frame_botones, text="Conectar por SSH", width=18, command=conectar_ssh)
btn_ssh.pack(side="left", padx=5)

# Salida
text_salida = scrolledtext.ScrolledText(ventana, height=12)
text_salida.pack(padx=10, pady=10, fill="both", expand=True)

ventana.mainloop()
