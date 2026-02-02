import socket
import tkinter as tk
from tkinter import messagebox
import math
import os

import cv2
from PIL import Image, ImageTk

# ---- Matplotlib 3D embebido ----
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

# --------- COLORES (Deep Sea Blue - Tech) ----------
COLOR_FONDO       = "#060B1A"
COLOR_PANEL       = "#0B1530"
COLOR_BORDE       = "#1A2B57"
COLOR_ACENTO      = "#1D4ED8"
COLOR_TEXTO       = "#EAF0FF"
COLOR_TEXTO_SUAVE = "#A9B7E6"
COLOR_CANVAS_BG   = "#081026"

BTN_OK            = "#22C55E"
BTN_BAD           = "#EF4444"
BTN_NEUTRO        = "#334155"
# ---------------------------------------------------

# RANGO REAL DEL GRIPPER (SERVO 2)
GRIP_MIN = 65
GRIP_MAX = 125

VIDEO_DIR = r"C:\Users\diana\Pyton_microcontroladores\vs_code_py\.vscode\slider_servo\videos"
#C:\Users\diana\Pyton_microcontroladores\vs_code_py\.vscode\slider_servo\videos

VID_BASE   = os.path.join(VIDEO_DIR, "mno.mp4")     # Servo θ1 (Base)
VID_GRIP   = os.path.join(VIDEO_DIR, "mno2.mp4")    # Servo θ2 (gripper)
VID_ELB_1  = os.path.join(VIDEO_DIR, "mno3.mp4")    # Servo codo (vista 1)
VID_ELB_2  = os.path.join(VIDEO_DIR, "mno33.mp4")   # Servo codo (vista 2)

CONNECTED = False

# ------------------ TCP ------------------
def set_status(text, color):
    status_lbl.config(text=text, fg=color)

def update_buttons():
    if CONNECTED:
        btn_connect.config(state="disabled")
        btn_disconnect.config(state="normal")
    else:
        btn_connect.config(state="normal")
        btn_disconnect.config(state="disabled")

def get_ip_port():
    ip = entry_ip.get().strip()
    port_str = entry_port.get().strip()

    if not ip:
        messagebox.showwarning("Falta IP", "Ingresa la IP de la Raspberry Pi.")
        return None, None
    if not port_str:
        messagebox.showwarning("Falta puerto", "Ingresa el puerto (por ejemplo 5001).")
        return None, None
    try:
        port = int(port_str)
    except ValueError:
        messagebox.showerror("Error", "El puerto debe ser un número entero.")
        return None, None
    return ip, port

def connect_now():
    global CONNECTED
    ip, port = get_ip_port()
    if ip is None:
        return

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1.5)
            s.connect((ip, port))
        CONNECTED = True
        set_status("Estado: Conectado", BTN_OK)
    except OSError as e:
        CONNECTED = False
        set_status("Estado: No se pudo conectar", BTN_BAD)
        messagebox.showerror("No conecta", f"No se pudo conectar a {ip}:{port}\n\n{e}")

    update_buttons()

def disconnect_now():
    global CONNECTED
    CONNECTED = False
    set_status("Estado: Desconectado (no se envía)", COLOR_TEXTO_SUAVE)
    update_buttons()

def send_tcp_batch(cmds) -> bool:
    """
    Abre UNA sola conexión y manda todas las líneas:
      cmds = [(sid, ang), (sid, ang), ...]
    Esto evita el 'Error de conexión' por saturación de conexiones.
    """
    if not CONNECTED:
        return False

    ip, port = get_ip_port()
    if ip is None:
        return False

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.7)
            s.connect((ip, port))
            payload = "".join(f"{sid} {ang}\n" for sid, ang in cmds).encode("utf-8")
            s.sendall(payload)
        return True
    except OSError:
        return False

# ------------------ VIDEO PREVIEW ------------------
class VideoPreview:
    def __init__(self, parent, video_path: str, title="Vista", w=640, h=360):
        self.video_path = video_path
        self.w = w
        self.h = h

        self.title_lbl = tk.Label(parent, text=title, bg=COLOR_PANEL, fg=COLOR_TEXTO_SUAVE,
                                  font=("Segoe UI", 9, "bold"))
        self.title_lbl.pack(anchor="w", padx=10, pady=(10, 6))

        self.view = tk.Label(parent, bg=COLOR_CANVAS_BG)
        self.view.pack(padx=10, pady=(0, 10))

        self.cap = None
        self.frame_count = 0
        self._photo = None
        self._pending = None

        self._open_video()
        self.show_angle(90)

    def _open_video(self):
        if not os.path.exists(self.video_path):
            self.view.config(text="Video no encontrado", fg=BTN_BAD)
            return
        self.cap = cv2.VideoCapture(self.video_path)
        if not self.cap.isOpened():
            self.view.config(text="No se pudo abrir", fg=BTN_BAD)
            self.cap = None
            return
        fc = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.frame_count = max(fc, 1)

    def show_angle(self, ang: int):
        if self._pending is not None:
            self.view.after_cancel(self._pending)
        self._pending = self.view.after(35, lambda: self._render(ang))

    def _render(self, ang: int):
        self._pending = None
        if self.cap is None:
            return

        ang = max(0, min(180, int(ang)))
        idx = int(round((ang / 180.0) * (self.frame_count - 1)))
        idx = max(0, min(self.frame_count - 1, idx))

        self.cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ok, frame = self.cap.read()
        if not ok or frame is None:
            return

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame).resize((self.w, self.h))
        self._photo = ImageTk.PhotoImage(img)
        self.view.config(image=self._photo, text="")

def grip_to_video_angle(g: int) -> int:
    """
    Remapea el rango real 65..125 a 0..180 para que el video del gripper
    use toda su animación aunque el servo esté limitado.
    """
    g = max(GRIP_MIN, min(GRIP_MAX, int(g)))
    span = (GRIP_MAX - GRIP_MIN)
    if span <= 0:
        return 90
    v = int(round((g - GRIP_MIN) * 180.0 / span))
    return max(0, min(180, v))

# ------------------ ROBOT 3D + CINEMÁTICA ------------------
class Robot3D:
    def __init__(self, parent, w=520, h=420):
        self.wrap = tk.Frame(parent, bg=COLOR_PANEL)
        self.wrap.pack(fill="both", expand=True, padx=10, pady=10)

        self.fig = Figure(figsize=(w/100, h/100), dpi=100, facecolor=COLOR_CANVAS_BG)
        self.ax = self.fig.add_subplot(111, projection="3d")

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.wrap)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        # Parámetros geométricos (AJUSTA A TU ROBOT)
        self.L1 = 140.0  # primer eslabón (desde base hasta codo)
        self.L2 = 120.0  # segundo eslabón (desde codo hasta efector)
        self.h  = 40.0   # altura del pedestal

        self.theta1 = 90
        self.theta2 = 90
        self.grip   = 90

        self.last_x = 0.0
        self.last_y = 0.0
        self.last_z = 0.0

        self.reset_view()
        self.draw()

    def reset_view(self):
        self.view_elev = 20
        self.view_azim = 35

    def _style_axes(self):
        ax = self.ax
        ax.set_facecolor(COLOR_CANVAS_BG)

        ax.xaxis.pane.set_facecolor((0, 0, 0, 0))
        ax.yaxis.pane.set_facecolor((0, 0, 0, 0))
        ax.zaxis.pane.set_facecolor((0, 0, 0, 0))

        ax.tick_params(colors=COLOR_TEXTO_SUAVE, labelsize=8)
        ax.set_xlabel("X", color=COLOR_TEXTO_SUAVE, labelpad=6)
        ax.set_ylabel("Y", color=COLOR_TEXTO_SUAVE, labelpad=6)
        ax.set_zlabel("Z", color=COLOR_TEXTO_SUAVE, labelpad=6)
        ax.grid(True, alpha=0.20)

    def set_angles(self, t1, t2, grip):
        self.theta1 = int(t1)
        self.theta2 = int(t2)
        self.grip   = int(grip)
        self.draw()

    def fk_points(self):
        """
        Modelo 2 GDL:
        - Base (theta1): yaw alrededor de Z
        - Codo (theta2): 0..180 con 90 = recto
        Link1 vertical, Link2 se dobla en el plano que apunta según yaw.
        """
        yaw = math.radians(self.theta1 - 90)          # yaw en Z
        alpha = math.radians(90.0 - self.theta2)      # 90=recto => alpha=0

        p0 = (0.0, 0.0, 0.0)                          # base suelo
        p_base = (0.0, 0.0, self.h)                   # pedestal
        p1 = (0.0, 0.0, self.h + self.L1)             # codo

        vx_local = self.L2 * math.sin(alpha)
        vz_local = self.L2 * math.cos(alpha)

        vx = vx_local * math.cos(yaw)
        vy = vx_local * math.sin(yaw)
        vz = vz_local

        p2 = (p1[0] + vx, p1[1] + vy, p1[2] + vz)

        # dirección del efector (para gripper)
        ux, uy, uz = 0.0, 0.0, 1.0
        norm = math.sqrt(vx*vx + vy*vy + vz*vz)
        if norm > 1e-9:
            ux, uy, uz = vx/norm, vy/norm, vz/norm

        return p0, p_base, p1, p2, yaw, (ux, uy, uz)

    def draw(self):
        ax = self.ax
        ax.cla()
        self._style_axes()

        p0, p_base, p1, p2, yaw, (ux, uy, uz) = self.fk_points()

        self.last_x, self.last_y, self.last_z = p2[0], p2[1], p2[2]

        span = max(260, int(self.L1 + self.L2 + self.h + 120))
        ax.set_xlim(-span, span)
        ax.set_ylim(-span, span)
        ax.set_zlim(0, span + 80)

        ax.view_init(elev=self.view_elev, azim=self.view_azim)

        # Base disco
        R = 60
        angs = [i * 2 * math.pi / 80 for i in range(81)]
        xs = [R * math.cos(a) for a in angs]
        ys = [R * math.sin(a) for a in angs]
        zs = [0 for _ in angs]
        ax.plot(xs, ys, zs, linewidth=2, color=COLOR_BORDE)

        # Flecha yaw
        ax.quiver(0, 0, 0, math.cos(yaw)*R, math.sin(yaw)*R, 0,
                  color=COLOR_TEXTO_SUAVE, linewidth=2, arrow_length_ratio=0.18)

        # Pedestal
        ax.plot([p0[0], p_base[0]], [p0[1], p_base[1]], [p0[2], p_base[2]],
                linewidth=6, color=COLOR_BORDE)

        # Links correctos
        ax.plot([p_base[0], p1[0]], [p_base[1], p1[1]], [p_base[2], p1[2]],
                linewidth=7, color=COLOR_ACENTO)
        ax.plot([p1[0], p2[0]], [p1[1], p2[1]], [p1[2], p2[2]],
                linewidth=7, color="#2F7BFF")

        # Juntas
        ax.scatter([p_base[0], p1[0], p2[0]],
                   [p_base[1], p1[1], p2[1]],
                   [p_base[2], p1[2], p2[2]],
                   s=55, c=COLOR_PANEL, edgecolors=COLOR_TEXTO_SUAVE, linewidths=1.8)

        # Gripper visual con rango real 65..125
        g = max(GRIP_MIN, min(GRIP_MAX, int(self.grip)))
        span_g = (GRIP_MAX - GRIP_MIN) if (GRIP_MAX - GRIP_MIN) != 0 else 1
        grip_norm = (g - GRIP_MIN) / span_g  # 0=open, 1=closed

        max_gap = 28.0
        min_gap = 4.0
        gap = max_gap - grip_norm * (max_gap - min_gap)

        sx = -math.sin(yaw)
        sy =  math.cos(yaw)
        sz = 0.0

        finger_len = 35.0
        f1a = (p2[0] + sx*gap, p2[1] + sy*gap, p2[2] + sz*gap)
        f1b = (f1a[0] + ux*finger_len, f1a[1] + uy*finger_len, f1a[2] + uz*finger_len)

        f2a = (p2[0] - sx*gap, p2[1] - sy*gap, p2[2] - sz*gap)
        f2b = (f2a[0] + ux*finger_len, f2a[1] + uy*finger_len, f2a[2] + uz*finger_len)

        ax.plot([f1a[0], f1b[0]], [f1a[1], f1b[1]], [f1a[2], f1b[2]],
                linewidth=4, color=COLOR_TEXTO)
        ax.plot([f2a[0], f2b[0]], [f2a[1], f2b[1]], [f2a[2], f2b[2]],
                linewidth=4, color=COLOR_TEXTO)

        ax.text(0, 0, -10, "Base", color=COLOR_TEXTO_SUAVE, fontsize=9)

        self.canvas.draw_idle()

# ------------------ UI ------------------
class App:
    def __init__(self, root):
        self.root = root

        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()

        # VISTAS dominantes
        self.PREV_W = max(680, int(sw * 0.40))
        self.PREV_H = int(self.PREV_W * 0.56)

        # 3D (alto suficiente)
        self.ANIM_W = max(520, int(sw * 0.30))
        self.ANIM_H = max(460, int(sh * 0.50))

        self.t1 = tk.IntVar(value=90)  # Base (Servo 1)
        self.t2 = tk.IntVar(value=90)  # Codo (Servo 3)
        self.g  = tk.IntVar(value=90)  # Gripper (Servo 2)

        self._send_after = None
        self._last_sent = None  # evita re-enviar lo mismo

        root.configure(bg=COLOR_FONDO)
        root.title("Robot 2 GDL + Gripper (TCP)")

        try:
            root.state("zoomed")
        except Exception:
            root.geometry(f"{min(sw,1600)}x{min(sh,900)}")

        root.grid_rowconfigure(1, weight=1)
        root.grid_columnconfigure(0, weight=1)

        self._build_conn(row=0)
        self._build_body(row=1)

        update_buttons()
        set_status("Estado: Desconectado (no se envía)", COLOR_TEXTO_SUAVE)

        self._apply_all(previews=True, send=False)

        self.t1.trace_add("write", lambda *_: self._on_any_change())
        self.t2.trace_add("write", lambda *_: self._on_any_change())
        self.g.trace_add("write",  lambda *_: self._on_any_change())

    def _make_card(self, parent, title):
        card = tk.Frame(parent, bg=COLOR_PANEL, highlightthickness=1, highlightbackground=COLOR_BORDE)
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(1, weight=1)

        head = tk.Label(card, text=title, bg=COLOR_PANEL, fg=COLOR_TEXTO,
                        font=("Segoe UI", 11, "bold"))
        head.grid(row=0, column=0, sticky="w", padx=12, pady=(10, 8))

        content = tk.Frame(card, bg=COLOR_PANEL)
        content.grid(row=1, column=0, sticky="nsew")

        return card, content

    def _build_conn(self, row=0):
        global entry_ip, entry_port, btn_connect, btn_disconnect, status_lbl

        conn = tk.Frame(self.root, bg=COLOR_PANEL, highlightbackground=COLOR_BORDE, highlightthickness=1)
        conn.grid(row=row, column=0, sticky="ew", padx=18, pady=(18, 12))
        conn.grid_columnconfigure(8, weight=1)

        tk.Label(conn, text="Conexión con Raspberry Pi (TCP)", bg=COLOR_PANEL, fg=COLOR_ACENTO,
                 font=("Segoe UI", 12, "bold")).grid(row=0, column=0, columnspan=9,
                                                    padx=16, pady=(12, 8), sticky="w")

        tk.Label(conn, text="IP:", bg=COLOR_PANEL, fg=COLOR_TEXTO_SUAVE,
                 font=("Segoe UI", 10)).grid(row=1, column=0, padx=(16, 6), pady=8, sticky="e")
        entry_ip = tk.Entry(conn, width=16, bg=COLOR_CANVAS_BG, fg=COLOR_TEXTO,
                            insertbackground=COLOR_TEXTO, relief="flat")
        entry_ip.grid(row=1, column=1, padx=(0, 14), pady=8, sticky="w")
        entry_ip.insert(0, "192.168.0.101")

        tk.Label(conn, text="Puerto:", bg=COLOR_PANEL, fg=COLOR_TEXTO_SUAVE,
                 font=("Segoe UI", 10)).grid(row=1, column=2, padx=(8, 6), pady=8, sticky="e")
        entry_port = tk.Entry(conn, width=8, bg=COLOR_CANVAS_BG, fg=COLOR_TEXTO,
                              insertbackground=COLOR_TEXTO, relief="flat")
        entry_port.grid(row=1, column=3, padx=(0, 12), pady=8, sticky="w")
        entry_port.insert(0, "5001")

        btn_connect = tk.Button(conn, text="Conectar", command=connect_now,
                                bg=COLOR_ACENTO, fg="white", activebackground=COLOR_ACENTO,
                                relief="flat", padx=16, pady=8)
        btn_connect.grid(row=1, column=4, padx=(8, 6), pady=8, sticky="w")

        btn_disconnect = tk.Button(conn, text="Desconectar", command=disconnect_now,
                                   bg=BTN_BAD, fg="white", activebackground=BTN_BAD,
                                   relief="flat", padx=16, pady=8)
        btn_disconnect.grid(row=1, column=5, padx=(6, 12), pady=8, sticky="w")

        status_lbl = tk.Label(conn, text="Estado: —", bg=COLOR_PANEL, fg=COLOR_TEXTO_SUAVE,
                              font=("Segoe UI", 10))
        status_lbl.grid(row=2, column=0, columnspan=9, padx=16, pady=(2, 12), sticky="w")

    def _build_body(self, row=1):
        body = tk.Frame(self.root, bg=COLOR_FONDO)
        body.grid(row=row, column=0, sticky="nsew", padx=18, pady=(0, 18))

        body.grid_columnconfigure(0, weight=3)   # vistas dominan
        body.grid_columnconfigure(1, weight=1)   # panel derecho
        body.grid_rowconfigure(0, weight=1)

        # ----- IZQUIERDA: VISTAS -----
        views_card, views_content = self._make_card(
            body,
            "Vistas (4 videos) — Base, Gripper y Codo (2 vistas)"
        )
        views_card.grid(row=0, column=0, sticky="nsew", padx=(0, 12))

        views_content.grid_rowconfigure(0, weight=1)
        views_content.grid_rowconfigure(1, weight=1)
        views_content.grid_columnconfigure(0, weight=1)
        views_content.grid_columnconfigure(1, weight=1)

        c00 = tk.Frame(views_content, bg=COLOR_PANEL); c00.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        c01 = tk.Frame(views_content, bg=COLOR_PANEL); c01.grid(row=0, column=1, sticky="nsew", padx=8, pady=8)
        c10 = tk.Frame(views_content, bg=COLOR_PANEL); c10.grid(row=1, column=0, sticky="nsew", padx=8, pady=8)
        c11 = tk.Frame(views_content, bg=COLOR_PANEL); c11.grid(row=1, column=1, sticky="nsew", padx=8, pady=8)

        self.pv_base = VideoPreview(c00, VID_BASE,  title="Base (mno.mp4) → Servo 1",
                                    w=self.PREV_W, h=self.PREV_H)
        self.pv_grip = VideoPreview(c01, VID_GRIP,  title="Gripper (mno2.mp4) → Servo 2",
                                    w=self.PREV_W, h=self.PREV_H)
        self.pv_elb1 = VideoPreview(c10, VID_ELB_1, title="Codo Vista 1 (mno3.mp4) → Servo 3",
                                    w=self.PREV_W, h=self.PREV_H)
        self.pv_elb2 = VideoPreview(c11, VID_ELB_2, title="Codo Vista 2 (mno33.mp4) → Servo 3",
                                    w=self.PREV_W, h=self.PREV_H)

        # ----- DERECHA: CINEMÁTICA (valores) + sliders + 3D -----
        right = tk.Frame(body, bg=COLOR_FONDO)
        right.grid(row=0, column=1, sticky="nsew")
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(0, weight=0)  # panel cinemática
        right.grid_rowconfigure(1, weight=0)  # sliders
        right.grid_rowconfigure(2, weight=1)  # 3D

        # (0) panel de cinemática
        kine_card, kine_content = self._make_card(right, "Cinemática (valores)")
        kine_card.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        kine_content.grid_columnconfigure(0, weight=1)

        self.kine_angles = tk.Label(
            kine_content, text="Base = 90°   Codo = 90°   Gripper = 90°",
            bg=COLOR_PANEL, fg=COLOR_TEXTO, font=("Segoe UI", 10, "bold")
        )
        self.kine_angles.grid(row=0, column=0, sticky="w", padx=12, pady=(6, 4))

        self.kine_xyz = tk.Label(
            kine_content, text="Efect.: x = 0.0   y = 0.0   z = 0.0",
            bg=COLOR_PANEL, fg=COLOR_TEXTO_SUAVE, font=("Segoe UI", 10)
        )
        self.kine_xyz.grid(row=1, column=0, sticky="w", padx=12, pady=(0, 10))

        # (1) sliders
        ctrl_card, ctrl_content = self._make_card(right, "Sliders")
        ctrl_card.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        ctrl_content.grid_columnconfigure(0, weight=1)

        top_btns = tk.Frame(ctrl_content, bg=COLOR_PANEL)
        top_btns.grid(row=0, column=0, sticky="ew", padx=12, pady=(0, 6))

        btn_reset = tk.Button(top_btns, text="Reset 90°",
                              command=self.reset_90,
                              bg=BTN_NEUTRO, fg=COLOR_TEXTO,
                              activebackground=BTN_NEUTRO,
                              relief="flat", padx=14, pady=6)
        btn_reset.pack(side="left")

        btn_view = tk.Button(top_btns, text="Vista 3D original",
                             command=self.reset_view_only,
                             bg=BTN_NEUTRO, fg=COLOR_TEXTO,
                             activebackground=BTN_NEUTRO,
                             relief="flat", padx=14, pady=6)
        btn_view.pack(side="left", padx=(10, 0))

        self._add_slider(ctrl_content, "Base (Servo 1) 0–180", self.t1, row=1, vmin=0, vmax=180)
        self._add_slider(ctrl_content, "Codo (Servo 3) 0–180 (90 ≈ recto)", self.t2, row=2, vmin=0, vmax=180)
        self._add_slider(ctrl_content, f"Gripper (Servo 2) {GRIP_MIN}–{GRIP_MAX}", self.g, row=3, vmin=GRIP_MIN, vmax=GRIP_MAX)

        # (2) 3D
        anim_card, anim_content = self._make_card(right, "Cinemática (3D real)")
        anim_card.grid(row=2, column=0, sticky="nsew")
        self.robot3d = Robot3D(anim_content, w=self.ANIM_W, h=self.ANIM_H)

    def _add_slider(self, parent, label, var, row, vmin=0, vmax=180):
        wrap = tk.Frame(parent, bg=COLOR_PANEL)
        wrap.grid(row=row, column=0, sticky="ew", padx=12, pady=(4, 8))
        wrap.grid_columnconfigure(0, weight=1)

        tk.Label(wrap, text=label, bg=COLOR_PANEL, fg=COLOR_TEXTO_SUAVE,
                 font=("Segoe UI", 9)).grid(row=0, column=0, sticky="w")

        value_lbl = tk.Label(wrap, text=str(var.get()), bg=COLOR_PANEL, fg=COLOR_TEXTO,
                             font=("Segoe UI", 9, "bold"))
        value_lbl.grid(row=0, column=1, sticky="e", padx=(10, 0))

        scale = tk.Scale(wrap, from_=vmin, to=vmax, orient=tk.HORIZONTAL,
                         variable=var, showvalue=False,
                         bg=COLOR_PANEL, fg=COLOR_TEXTO,
                         highlightthickness=0, troughcolor=COLOR_CANVAS_BG,
                         sliderlength=20)
        scale.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(2, 0))

        if not hasattr(self, "_value_labels"):
            self._value_labels = []
        self._value_labels.append((var, value_lbl))

    def _update_kine_panel(self):
        t1 = int(self.t1.get())
        t2 = int(self.t2.get())
        g  = int(self.g.get())
        x, y, z = self.robot3d.last_x, self.robot3d.last_y, self.robot3d.last_z

        self.kine_angles.config(text=f"Base = {t1}°   Codo = {t2}°   Gripper = {g}°")
        self.kine_xyz.config(text=f"Efect.: x = {x:0.1f}   y = {y:0.1f}   z = {z:0.1f}")

    def reset_view_only(self):
        self.robot3d.reset_view()
        self.robot3d.draw()
        self._update_kine_panel()

    def reset_90(self):
        self.t1.set(90)
        self.t2.set(90)
        self.g.set(90)  # está dentro de 65..125
        self.robot3d.reset_view()
        self._last_sent = None
        self._apply_all(previews=True, send=True)
        set_status("Reset: 90° (Base/Codo/Gripper)", BTN_OK)

    def _on_any_change(self):
        # clamp del gripper para que nunca se salga de 65..125
        if int(self.g.get()) < GRIP_MIN:
            self.g.set(GRIP_MIN)
        elif int(self.g.get()) > GRIP_MAX:
            self.g.set(GRIP_MAX)

        for var, lbl in getattr(self, "_value_labels", []):
            lbl.config(text=str(int(var.get())))

        self._apply_all(previews=True, send=False)

        if self._send_after is not None:
            self.root.after_cancel(self._send_after)
        # un poco más lento = más estable
        self._send_after = self.root.after(220, self._send_all)

    def _apply_all(self, previews=True, send=False):
        t1 = int(self.t1.get())
        t2 = int(self.t2.get())
        g  = max(GRIP_MIN, min(GRIP_MAX, int(self.g.get())))

        self.robot3d.set_angles(t1, t2, g)
        self._update_kine_panel()

        if previews:
            self.pv_base.show_angle(t1)
            self.pv_elb1.show_angle(t2)
            self.pv_elb2.show_angle(t2)
            # para el video del gripper usamos 0..180 (remapeado)
            self.pv_grip.show_angle(grip_to_video_angle(g))

        if send:
            self._send_all()

    def _send_all(self):
        global CONNECTED
        self._send_after = None

        if not CONNECTED:
            set_status("Estado: Desconectado (no se envía)", COLOR_TEXTO_SUAVE)
            return

        t1 = int(self.t1.get())
        t2 = int(self.t2.get())
        g  = max(GRIP_MIN, min(GRIP_MAX, int(self.g.get())))

        current = (t1, t2, g)
        if self._last_sent == current:
            return

        ok = send_tcp_batch([(1, t1), (3, t2), (2, g)])

        if ok:
            self._last_sent = current
            set_status("Estado: Enviado", BTN_OK)
        else:
            # Si falló, nos desconectamos para que no esté fallando a cada rato
            CONNECTED = False
            update_buttons()
            set_status("Estado: Desconectado (falló envío)", BTN_BAD)

# ------------------ RUN ------------------
root = tk.Tk()
app = App(root)
update_buttons()
root.mainloop()

#mkdir ~/slider_servo

#cd ~/slider_servo

#mkdir templates

#mkdir static

#mkdir static/css

#mkdir static/js

#mkdir static/videos

