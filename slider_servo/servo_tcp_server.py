import socket
import serial

# --- CONFIGURACIÓN ---
SERIAL_PORT = "/dev/ttyACM0"   # puerto del Arduino en la Raspberry
BAUDRATE    = 9600

HOST = "0.0.0.0"   # escucha en todas las interfaces
PORT = 5001        # pon el mismo en tu interfaz de Windows (entry_port)
# ----------------------

def main():
    # Abrir puerto serie con el Arduino
    ser = serial.Serial(SERIAL_PORT, BAUDRATE, timeout=1)
    print(f"Conectado a Arduino en {SERIAL_PORT} a {BAUDRATE} baudios")

    # Crear socket servidor TCP
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen(1)
        print(f"Servidor SERVO escuchando en {HOST}:{PORT}...")

        while True:
            conn, addr = s.accept()
            with conn:
                print(f"Conexión desde {addr}")

                data = conn.recv(1024)
                if not data:
                    continue

                try:
                    texto = data.decode("utf-8").strip()
                    angulo = int(texto)
                except ValueError:
                    print(f"Datos no válidos: {data!r}")
                    continue

                # Limitar 0–180
                angulo = max(0, min(180, angulo))
                print(f"Enviando al Arduino (servo): {angulo}")

                # Mandar al Arduino como texto + salto de línea
                ser.write(f"{angulo}\n".encode("utf-8"))

if __name__ == "__main__":
    main()
