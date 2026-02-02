import sys
import time
import cv2
import serial
import serial.tools.list_ports
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider, QPushButton,
    QComboBox, QCheckBox, QSpinBox, QGroupBox, QFrame
)
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt, QTimer

# =========================
# CONFIGURACIÓN
# =========================
VIDEO_PATH = r"C:\Users\diana\Pyton_microcontroladores\simulacion.mp4"  # Carga automática
BAUD_RATE = 115200
ANCHO_MAX_VIDEO = 900
TIMER_MS = 30  # ~33fps

class MotorVideoUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Control de Motor + Simulación por Video")
        # Estado
        self.ser = None
        self.video = None
        self.video_path = VIDEO_PATH
        self.total_frames = 0
        self.fps = 30.0
        self.frame_pos = 0.0
        self.last_sent_speed = None
        self.invert_dir = False
        self.estop = False  # Paro de emergencia

        # UI
        self._build_ui()
        self._apply_style()

        # Timers
        self.play_timer = QTimer(self)
        self.play_timer.setInterval(TIMER_MS)
        self.play_timer.timeout.connect(self._tick_video)

        self.send_timer = QTimer(self)
        self.send_timer.setInterval(30)  # anti-flood serial
        self.send_timer.timeout.connect(self._send_pending_speed)
        self.pending_speed = None

        # Cargar video de inmediato y arrancar reproducción
        self._open_video(self.video_path)
        self.play_timer.start()

    # ---------- UI ----------
    def _build_ui(self):
        main = QVBoxLayout(self)
        main.setContentsMargins(16, 16, 16, 16)
        main.setSpacing(12)

        # ====== Panel de Conexión ======
        conn_box = QGroupBox("")#Conexión"
        conn_outer = QVBoxLayout(conn_box)
        conn_frame = self._card_frame()
        conn_layout = QHBoxLayout(conn_frame)
        conn_layout.setContentsMargins(12, 8, 12, 8)

        self.port_combo = QComboBox()
        self.refresh_btn = QPushButton("Actualizar")
        self.connect_btn = QPushButton("Conectar")
        self.disconnect_btn = QPushButton("Desconectar")
        self.disconnect_btn.setEnabled(False)
        self.status_lbl = QLabel("Estado: Desconectado")
        self.status_lbl.setObjectName("statusBad")

        conn_layout.addWidget(QLabel("Puerto:"))
        conn_layout.addWidget(self.port_combo, 1)
        conn_layout.addWidget(self.refresh_btn)
        conn_layout.addWidget(self.connect_btn)
        conn_layout.addWidget(self.disconnect_btn)
        conn_layout.addStretch(1)
        conn_layout.addWidget(self.status_lbl, 0, Qt.AlignRight)

        conn_outer.addWidget(conn_frame)
        main.addWidget(conn_box)

        self.refresh_btn.clicked.connect(self._fill_ports)
        self.connect_btn.clicked.connect(self._connect_serial)
        self.disconnect_btn.clicked.connect(self._disconnect_serial)
        self._fill_ports()

        # ====== Video (autocarga) ======
        video_box = QGroupBox("")#Simulación por Video
        video_outer = QVBoxLayout(video_box)
        video_frame = self._card_frame()
        video_layout = QVBoxLayout(video_frame)
        video_layout.setContentsMargins(12, 8, 12, 12)

        self.video_label = QLabel("​")#Cargando video…
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setMinimumHeight(340)
        self.video_label.setStyleSheet("background:#111; color:#888; border:1px solid #333;")
        video_layout.addWidget(self.video_label)

        video_outer.addWidget(video_frame)
        main.addWidget(video_box)

        # ====== Controles ======
        ctrl_box = QGroupBox("")#Controles
        ctrl_outer = QVBoxLayout(ctrl_box)
        ctrl_frame = self._card_frame()
        ctrl_layout = QVBoxLayout(ctrl_frame)
        ctrl_layout.setContentsMargins(12, 8, 12, 12)
        ctrl_layout.setSpacing(10)

        # --- Fila superior de controles ---
        row_top = QHBoxLayout()

        self.estop_btn = QPushButton("PARO DE EMERGENCIA")
        self.estop_btn.setObjectName("estop")
        self.estop_btn.setMinimumHeight(56)
        self.estop_btn.setMinimumWidth(220)
        self.estop_btn.clicked.connect(self._trigger_estop)

        self.reset_btn = QPushButton("RESET")
        self.reset_btn.setObjectName("reset")
        self.reset_btn.setMinimumHeight(56)
        self.reset_btn.setMinimumWidth(160)
        self.reset_btn.clicked.connect(self._reset_estop)

        # Título y caja de velocidad
        speed_col = QVBoxLayout()
        speed_title = QLabel("Velocidad")
        speed_title.setObjectName("speedTitle")
        self.speed_big = QLabel("0")
        self.speed_big.setObjectName("speedBox")
        self.speed_big.setAlignment(Qt.AlignCenter)
        speed_col.addWidget(speed_title)
        speed_col.addWidget(self.speed_big)

        self.stop_btn = QPushButton("Parar (0)")
        self.stop_btn.setMinimumHeight(50)
        self.stop_btn.clicked.connect(lambda: self.speed_slider.setValue(0))

        row_top.addWidget(self.estop_btn)
        row_top.addWidget(self.reset_btn)
        row_top.addStretch(1)
        row_top.addLayout(speed_col)
        row_top.addSpacing(8)
        row_top.addWidget(self.stop_btn)

        ctrl_layout.addLayout(row_top)

        # Slider de velocidad
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(-255, 255)
        self.speed_slider.setValue(0)
        self.speed_slider.valueChanged.connect(self._on_speed_change)
        ctrl_layout.addWidget(self.speed_slider)

        # Fila inferior: zona muerta / invertir sentido
        row_bottom = QHBoxLayout()
        row_bottom.addWidget(QLabel("Zona muerta (%)"))
        self.dead_spin = QSpinBox()
        self.dead_spin.setRange(0, 50)
        self.dead_spin.setValue(4)
        row_bottom.addWidget(self.dead_spin)

        self.invert_chk = QCheckBox("Invertir sentido")
        self.invert_chk.stateChanged.connect(lambda _: setattr(self, "invert_dir", self.invert_chk.isChecked()))
        row_bottom.addWidget(self.invert_chk)
        row_bottom.addStretch(1)
        ctrl_layout.addLayout(row_bottom)

        ctrl_outer.addWidget(ctrl_frame)
        main.addWidget(ctrl_box)

        # Nota
        foot = QLabel("La simulacion se mueve automáticamente según la velocidad (dirección/rapidez). Al cerrar se envía 0.")
        foot.setStyleSheet("color:#aaa;")
        main.addWidget(foot)

    def _card_frame(self):
        f = QFrame()
        f.setObjectName("card")
        return f

    def _apply_style(self):
        self.setStyleSheet("""
            QWidget { background:#0e0e10; color:#e6e6e6; font-size:14px; }
            /* QGroupBox como sección con banda */
            QGroupBox {
                border: 1px solid #263041;
                border-radius: 12px;
                margin-top: 28px;     /* espacio para el título-banda */
                background: #0f1623;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 12px;
                top: -14px;
                padding: 6px 12px;
                border-radius: 10px;
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                            stop:0 #0f172a, stop:1 #1b2942);
                color: #cfe8ff;
                font-weight: 700;
                letter-spacing: 0.3px;
            }

            /* Tarjeta interna */
            QFrame#card {
                background:#111827;
                border:1px solid #273449;
                border-radius:12px;
            }

            /* Controles */
            QPushButton {
                background:#1f2937; border:1px solid #374151;
                border-radius:10px; padding:10px 14px;
            }
            QPushButton:hover { background:#273449; }

            QPushButton#estop { background:#b91c1c; border-color:#7f1d1d; color:white; font-weight:800; }
            QPushButton#estop:hover { background:#ef4444; }
            QPushButton#reset { background:#065f46; border-color:#064e3b; color:#e6fff5; font-weight:800; }

            QComboBox, QSpinBox {
                background:#0f172a; border:1px solid #374151;
                border-radius:8px; padding:6px 8px;
            }

            /* Slider */
            QSlider::groove:horizontal { height:8px; background:#374151; border-radius:4px; }
            QSlider::handle:horizontal { width:18px; background:#93c5fd; border:1px solid #2563eb; margin:-6px 0; border-radius:9px; }

            /* Display de velocidad como tarjeta oscura */
            QLabel#speedBox {
                background:#0b1220; border:1px solid #1f2a3b;
                border-radius:10px; padding:6px 12px; min-width: 84px;
                color:#e6e6e6; font-size:28px; font-weight:800;
            }
            QLabel#speedTitle { color:#9db4cf; font-weight:700; padding-right:6px; }
            QLabel#statusOk { color:#3fb; font-weight:600; }
            QLabel#statusBad { color:#b33; font-weight:600; }
        """)

    # ---------- Serial ----------
    def _fill_ports(self):
        self.port_combo.clear()
        ports = list(serial.tools.list_ports.comports())
        if not ports:
            self.port_combo.addItem("No hay puertos disponibles", None)
            return
        for p in ports:
            self.port_combo.addItem(f"{p.device} — {p.description}", p.device)

    def _connect_serial(self):
        if self.ser and self.ser.is_open:
            return
        dev = self.port_combo.currentData()
        if not dev:
            self._set_status("Selecciona un puerto válido.", error=True)
            return
        try:
            self.ser = serial.Serial(dev, BAUD_RATE, timeout=1)
            time.sleep(2)  # reinicio Arduino
            self._set_status(f"Conectado a {dev}", error=False)
            self.connect_btn.setEnabled(False)
            self.disconnect_btn.setEnabled(True)
            self._send_speed_now(0)  # limpieza inicial
        except serial.SerialException as e:
            self._set_status(f"Error de conexión: {e}", error=True)
            self.ser = None

    def _disconnect_serial(self):
        if self.ser and self.ser.is_open:
            try:
                self._send_speed_now(0)
                time.sleep(0.05)
                self.ser.close()
            except Exception:
                pass
        self.ser = None
        self._set_status("Desconectado", error=True)
        self.connect_btn.setEnabled(True)
        self.disconnect_btn.setEnabled(False)

    def _set_status(self, txt, error=False):
        self.status_lbl.setText(f"Estado: {txt}")
        self.status_lbl.setObjectName("statusBad" if error else "statusOk")
        # refrescar estilo cuando cambia el objectName
        self.style().unpolish(self.status_lbl)
        self.style().polish(self.status_lbl)
        self.status_lbl.update()

    # ---------- Video ----------
    def _open_video(self, path):
        if self.video:
            self.video.release()
            self.video = None

        self.video = cv2.VideoCapture(path)
        if not self.video.isOpened():
            self.video_label.setText(f"No se pudo abrir:\n{path}")
            return

        self.total_frames = int(self.video.get(cv2.CAP_PROP_FRAME_COUNT)) or 0
        self.fps = float(self.video.get(cv2.CAP_PROP_FPS)) or 30.0
        self.frame_pos = 0.0
        self._render_current_frame(overlay_speed=True)

    def _tick_video(self):
        if not self.video or self.total_frames <= 1:
            return

        speed = self._current_speed_effective()
        base_frames_per_tick = self.fps * (TIMER_MS / 1000.0)
        step = (speed / 255.0) * base_frames_per_tick

        if self.invert_dir:
            step = -step

        if self.estop:  # emergencia: congelar
            step = 0

        self.frame_pos = (self.frame_pos + step) % max(1, self.total_frames)
        self._render_current_frame(overlay_speed=True)

    def _render_current_frame(self, overlay_speed=False):
        if not self.video:
            return
        pos = max(0, min(self.total_frames - 1, int(self.frame_pos)))
        self.video.set(cv2.CAP_PROP_POS_FRAMES, pos)
        ok, frame = self.video.read()
        if not ok:
            return

        if overlay_speed:
            sp = self._current_speed_effective()
            txt = "EMERGENCIA" if self.estop else f"Vel: {sp}"
            color = (0, 0, 255) if self.estop else (255, 255, 255)
            overlay = frame.copy()
            w = 300 if self.estop else 210
            cv2.rectangle(overlay, (10, 10), (10 + w, 60), (0, 0, 0), -1)
            frame = cv2.addWeighted(overlay, 0.35, frame, 0.65, 0)
            cv2.putText(frame, txt, (20, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2, cv2.LINE_AA)

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        img = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
        pix = QPixmap.fromImage(img)
        if w > ANCHO_MAX_VIDEO:
            pix = pix.scaledToWidth(ANCHO_MAX_VIDEO, Qt.SmoothTransformation)
        self.video_label.setPixmap(pix)

    # ---------- Velocidad / envío ----------
    def _on_speed_change(self, _value):
        sp = self._current_speed_effective(raw=True)
        self.speed_big.setText(str(sp))
        self._queue_send_speed(sp)

    def _current_speed_effective(self, raw=False):
        if self.estop:
            return 0
        v = self.speed_slider.value()
        if not raw:
            dead = int(round(255 * (self.dead_spin.value() / 100.0)))
            if -dead <= v <= dead:
                v = 0
        return v

    def _queue_send_speed(self, speed):
        if speed != self.last_sent_speed:
            self.pending_speed = speed
            if not self.send_timer.isActive():
                self.send_timer.start()

    def _send_pending_speed(self):
        if self.pending_speed is None:
            self.send_timer.stop()
            return
        self._send_speed_now(self.pending_speed)
        self.pending_speed = None
        the_timer = self.send_timer
        the_timer.stop()

    def _send_speed_now(self, speed):
        if self.ser and self.ser.is_open:
            try:
                self.ser.write(f"{speed}\n".encode("utf-8"))
                self.last_sent_speed = speed
            except Exception:
                self._set_status("Error enviando datos. ¿Se desconectó el puerto?", error=True)
                self._disconnect_serial()

    # ---------- Paro de emergencia ----------
    def _trigger_estop(self):
        self.estop = True
        self.speed_slider.setEnabled(False)
        self.dead_spin.setEnabled(False)
        self.invert_chk.setEnabled(False)
        self.speed_slider.setValue(0)  # visual
        self.speed_big.setText("0")
        self._send_speed_now(0)
        self._set_status("EMERGENCIA ACTIVADA", error=True)

    def _reset_estop(self):
        self.estop = False
        self.speed_slider.setEnabled(True)
        self.dead_spin.setEnabled(True)
        self.invert_chk.setEnabled(True)
        self._set_status("Emergencia reseteada", error=False)

    # ---------- Cierre ----------
    def closeEvent(self, event):
        try:
            self._send_speed_now(0)
            time.sleep(0.05)
        except Exception:
            pass
        if self.video:
            try: self.video.release()
            except Exception: pass
        self._disconnect_serial()
        super().closeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MotorVideoUI()
    w.resize(1100, 760)
    w.show()
    sys.exit(app.exec_())
