import socket
import serial

# --- CONFIGURACIÓN ---
SERIAL_PORT = "/dev/ttyACM0"
BAUDRATE    = 9600

HOST = "0.0.0.0"
PORT = 5001
# ----------------------

def clamp(x, lo=0, hi=180):
    return max(lo, min(hi, x))

def main():
    ser = serial.Serial(SERIAL_PORT, BAUDRATE, timeout=1)
    print(f"Conectado a Arduino en {SERIAL_PORT} a {BAUDRATE} baudios")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen(10)  # <- más backlog, menos “Error de conexión”
        print(f"Servidor SERVO escuchando en {HOST}:{PORT}...")

        while True:
            conn, addr = s.accept()
            with conn:
                conn.settimeout(1.5)
                # leer TODO lo que llegue en esa conexión (tu cliente manda y cierra)
                chunks = []
                while True:
                    try:
                        data = conn.recv(4096)
                    except socket.timeout:
                        break
                    if not data:
                        break
                    chunks.append(data)

                if not chunks:
                    continue

                texto = b"".join(chunks).decode("utf-8", errors="ignore")
                # procesar línea por línea: "sid ang"
                for line in texto.splitlines():
                    line = line.strip()
                    if not line:
                        continue

                    parts = line.split()
                    if len(parts) != 2:
                        print(f"Línea no válida: {line!r}")
                        continue

                    try:
                        sid = int(parts[0])
                        ang = int(parts[1])
                    except ValueError:
                        print(f"Datos no válidos: {line!r}")
                        continue

                    ang = clamp(ang, 0, 180)

                    # Mandar al Arduino en el MISMO formato: "sid ang\n"
                    ser.write(f"{sid} {ang}\n".encode("utf-8"))
                    print(f"RX {addr}: servo={sid} ang={ang}")

if __name__ == "__main__":
    main()
