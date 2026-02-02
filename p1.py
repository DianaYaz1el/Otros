import tkinter as tk
from tkinter import messagebox, scrolledtext
import subprocess

def hacer_ping():
    host = entry_host.get().strip()
    if not host:
        messagebox.showwarning(
            "Dato faltante",
            "Ingresa la IP (192.168.x.x) o el hostname (por ejemplo rpidiana.local)."
        )
        return

    text_salida.delete("1.0", tk.END)

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
                "La IP o el hostname son alcanzables."
            )
        else:
            messagebox.showerror(
                "Ping fallido",
                "No se obtuvo respuesta.\n\n"
                "Posibles causas:\n"
                "- La Raspberry no está encendida.\n"
                "- No está conectada a la misma red.\n"
                "- La IP o el hostname son incorrectos."
            )
    except Exception as e:
        messagebox.showerror("Error al hacer ping", str(e))


def conectar_ssh():
    usuario = entry_user.get().strip()
    host = entry_host.get().strip()

    if not usuario or not host:
        messagebox.showwarning(
            "Datos faltantes",
            "Ingresa el usuario SSH y la IP/hostname de la Raspberry."
        )
        return

    comando_ssh = f"ssh {usuario}@{host}"

    try:
        # Abre una NUEVA ventana de cmd con la sesión SSH
        subprocess.Popen(
            f'start cmd /k "{comando_ssh}"',
            shell=True
        )
    except Exception as e:
        messagebox.showerror("Error al abrir SSH", str(e))


ventana = tk.Tk()
ventana.title("Conexión a Raspberry Pi (Ping / SSH)")
ventana.geometry("650x420")

frame_datos = tk.Frame(ventana)
frame_datos.pack(padx=10, pady=10, fill="x")

tk.Label(frame_datos, text="Usuario SSH:").grid(row=0, column=0, sticky="e")
entry_user = tk.Entry(frame_datos)
entry_user.grid(row=0, column=1, sticky="we", padx=5)
entry_user.insert(0, "diana")

tk.Label(
    frame_datos,
    text="Ingresa la IP (192.168.x.x) o el hostname (por ejemplo rpidiana.local):",
    anchor="e",
    justify="right",
    wraplength=260
).grid(row=1, column=0, sticky="e")
entry_host = tk.Entry(frame_datos)
entry_host.grid(row=1, column=1, sticky="we", padx=5)
entry_host.insert(0, "rpidiana.local")

frame_datos.columnconfigure(1, weight=1)

frame_botones = tk.Frame(ventana)
frame_botones.pack(padx=10, pady=5, fill="x")

btn_ping = tk.Button(frame_botones, text="Hacer PING", width=15, command=hacer_ping)
btn_ping.pack(side="left", padx=5)

btn_ssh = tk.Button(frame_botones, text="Conectar por SSH", width=18, command=conectar_ssh)
btn_ssh.pack(side="left", padx=5)

text_salida = scrolledtext.ScrolledText(ventana, height=12)
text_salida.pack(padx=10, pady=10, fill="both", expand=True)

ventana.mainloop()
