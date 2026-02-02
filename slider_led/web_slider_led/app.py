#sudo apt update
#sudo apt install -y python3 python3-flask python3-werkzeug python3-serial
#python3 -c "import flask, werkzeug, serial; print('OK')"
#mkdir -p ~/web_pwm_arduino/templates
#mkdir -p ~/web_pwm_arduino/static/css
#cd ~/web_pwm_arduino
#nano app.py (Paso 1)

from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import check_password_hash
import serial

# -----------------------------
# LOGIN CONFIG
# -----------------------------
APP_USER = "diana"
APP_PW_HASH = "PEGA_AQUI_TU_HASH_COMPLETO"  # <-- aquí pegarás tu scrypt:...
SECRET_KEY = "cambia_esto_por_algo_largo_y_unico"

# -----------------------------
# SERIAL CONFIG (APEGADO A TU ORIGINAL)
# -----------------------------
SERIAL_PORT = "/dev/ttyACM0"
BAUDRATE = 9600
USE_SERIAL = True  # pon False si quieres correr sin Arduino conectado

app = Flask(__name__)
app.secret_key = SECRET_KEY

ser = None

def open_serial():
    global ser
    if not USE_SERIAL:
        ser = None
        print("[INFO] USE_SERIAL=False (no se abrirá puerto serial)")
        return
    try:
        ser = serial.Serial(SERIAL_PORT, BAUDRATE, timeout=1)
        print(f"Conectado a Arduino en {SERIAL_PORT} a {BAUDRATE} baudios")
    except Exception as e:
        ser = None
        print(f"[WARN] No pude abrir {SERIAL_PORT} @ {BAUDRATE}: {e}")
        print("[TIP] Revisa puertos con: ls /dev/ttyACM* /dev/ttyUSB*")

def send_to_arduino(valor: int):
    # EXACTAMENTE igual que tu server_pwm.py
    global ser
    if ser is None:
        return
    ser.write(f"{valor}\n".encode("utf-8"))

def is_logged_in():
    return session.get("logged_in") is True

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form.get("username", "").strip()
        pw = request.form.get("password", "")

        if user == APP_USER and check_password_hash(APP_PW_HASH, pw):
            session["logged_in"] = True
            return redirect(url_for("index"))
        return render_template("login.html", error="Usuario o contraseña incorrectos")

    return render_template("login.html", error=None)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/")
def index():
    if not is_logged_in():
        return redirect(url_for("login"))
    return render_template("index.html")

@app.route("/set_pwm", methods=["POST"])
def set_pwm():
    if not is_logged_in():
        return jsonify({"ok": False, "error": "No autorizado"}), 401

    data = request.get_json(silent=True) or {}
    try:
        valor = int(str(data.get("value", "")).strip())
    except Exception:
        return jsonify({"ok": False, "error": "Valor inválido"}), 400

    valor = max(0, min(255, valor))  # igual que tu original
    print(f"Enviando al Arduino: {valor}")
    send_to_arduino(valor)

    return jsonify({"ok": True, "value": valor})

if __name__ == "__main__":
    open_serial()
    app.run(host="0.0.0.0", port=5000, debug=True)


#nano templates/login.html (Paso 2)
#nano templates/index.html (Paso 3)
#nano static/css/style.css (Paso 4)
#cd ~/web_pwm_arduino
# python3 -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('12345'))"
#Modificar app.py con el hash generado
#verificar:
#grep -n "APP_PW_HASH" app.py
#Ejecutar el servidor 
#cd ~/web_pwm_arduino
#python3 app.py
#Te mostrará la IP local (por ejemplo http://192.168.0.xxx:5000).
