import tkinter as tk
from tkinter import ttk, messagebox

import math
import cv2
import serial
import serial.tools.list_ports

from PIL import Image, ImageTk

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class InterfazServo:

    def __init__(self, ventana):

        self.ventana = ventana
        self.ventana.title(
            "Control de servo sincronizado con video"
        )

        self.ventana.geometry("1450x720")
        self.ventana.minsize(1200, 650)

        # =====================================================
        # PALETA DE COLORES
        # =====================================================

        self.COLOR_FONDO = "#F4F7FA"
        self.COLOR_PANEL = "#FFFFFF"

        self.COLOR_AZUL_OSCURO = "#12355B"
        self.COLOR_AZUL = "#2F80ED"
        self.COLOR_AZUL_CLARO = "#56CCF2"

        self.COLOR_TURQUESA = "#20C997"
        self.COLOR_AMARILLO = "#F2C94C"
        self.COLOR_NARANJA = "#F2994A"
        self.COLOR_MORADO = "#9B51E0"

        self.COLOR_TEXTO = "#1F2937"
        self.COLOR_BLANCO = "#FFFFFF"

        self.COLOR_ERROR = "#EB5757"
        self.COLOR_EXITO = "#27AE60"

        self.ventana.configure(
            bg=self.COLOR_FONDO
        )

        # =====================================================
        # VARIABLES DE ARDUINO
        # =====================================================

        self.arduino = None
        self.ultimo_angulo_enviado = None

        # =====================================================
        # VARIABLES DEL VIDEO
        # =====================================================

        self.video = None
        self.reproduciendo = False

        self.total_frames = 0
        self.fps = 30
        self.duracion_video = 0

        self.actualizando_slider = False

        # =====================================================
        # RUTA DEL VIDEO
        # =====================================================

        self.ruta_video = (
            r"C:\Users\diana\OneDrive\Escritorio"
            r"\ejercicios_Solid&Mastercam\servo.mp4"
        )

        self.longitud_vector = 5

        self.configurar_estilos()
        self.crear_interfaz()
        self.actualizar_puertos()
        self.cargar_video()

        self.ventana.protocol(
            "WM_DELETE_WINDOW",
            self.cerrar_programa
        )

    # =========================================================
    # ESTILOS
    # =========================================================

    def configurar_estilos(self):

        estilo = ttk.Style()

        try:
            estilo.theme_use("clam")
        except tk.TclError:
            pass

        estilo.configure(
            "TCombobox",
            fieldbackground=self.COLOR_BLANCO,
            background=self.COLOR_BLANCO,
            foreground=self.COLOR_TEXTO,
            padding=5
        )

        estilo.configure(
            "TSeparator",
            background=self.COLOR_AZUL_CLARO
        )

    # =========================================================
    # BOTÓN PERSONALIZADO
    # =========================================================

    def crear_boton(
        self,
        padre,
        texto,
        comando,
        color_fondo,
        color_texto="#FFFFFF",
        ancho=14,
        alto=1
    ):

        return tk.Button(
            padre,
            text=texto,
            command=comando,
            width=ancho,
            height=alto,
            bg=color_fondo,
            fg=color_texto,
            activebackground=self.oscurecer_color(
                color_fondo
            ),
            activeforeground=color_texto,
            relief="flat",
            bd=0,
            cursor="hand2",
            font=("Arial", 10, "bold"),
            padx=4,
            pady=4
        )

    def oscurecer_color(self, color):

        colores_activos = {
            "#2F80ED": "#1F6FD1",
            "#20C997": "#18A97C",
            "#F2C94C": "#D9B537",
            "#F2994A": "#D97D32",
            "#56CCF2": "#3EB5DA",
            "#9B51E0": "#8340C5",
            "#12355B": "#0B2745",
            "#EB5757": "#D64545"
        }

        return colores_activos.get(
            color,
            color
        )

    # =========================================================
    # CREAR INTERFAZ
    # =========================================================

    def crear_interfaz(self):

        titulo = tk.Label(
            self.ventana,
            text="Practica 1: Control de servomotor y representación vectorial",
            font=("Arial", 22, "bold"),
            bg=self.COLOR_FONDO,
            fg=self.COLOR_AZUL_OSCURO
        )

        titulo.pack(
            pady=8
        )

        subtitulo = tk.Label(
            self.ventana,
            text=(
                "Control por puerto COM, video y "
                "representación vectorial"
            ),
            font=("Arial", 10),
            bg=self.COLOR_FONDO,
            fg=self.COLOR_TEXTO
        )

        subtitulo.pack(
            pady=(0, 5)
        )

        contenedor = tk.Frame(
            self.ventana,
            bg=self.COLOR_FONDO
        )

        contenedor.pack(
            padx=10,
            pady=5,
            fill="both",
            expand=True
        )

        # Video con mayor protagonismo
        contenedor.grid_columnconfigure(
            0,
            weight=6
        )

        # Control
        contenedor.grid_columnconfigure(
            1,
            weight=2
        )

        # Plot pequeño
        contenedor.grid_columnconfigure(
            2,
            weight=1
        )

        contenedor.grid_rowconfigure(
            0,
            weight=1
        )

        # =====================================================
        # PANEL DEL VIDEO
        # =====================================================

        panel_video = tk.LabelFrame(
            contenedor,
            text=" Video del servomotor ",
            font=("Arial", 12, "bold"),
            bg=self.COLOR_PANEL,
            fg=self.COLOR_AZUL_OSCURO,
            bd=2,
            relief="groove",
            padx=8,
            pady=8
        )

        panel_video.grid(
            row=0,
            column=0,
            padx=6,
            pady=5,
            sticky="nsew"
        )

        self.etiqueta_video = tk.Label(
            panel_video,
            text="Cargando video...",
            bg="#101820",
            fg=self.COLOR_BLANCO,
            font=("Arial", 14),
            width=760,
            height=540
        )

        self.etiqueta_video.pack(
            fill="both",
            expand=True
        )

        self.etiqueta_tiempo = tk.Label(
            panel_video,
            text="Tiempo: 0.0 s",
            font=("Arial", 11, "bold"),
            bg=self.COLOR_PANEL,
            fg=self.COLOR_AZUL_OSCURO
        )

        self.etiqueta_tiempo.pack(
            pady=5
        )

        controles_video = tk.Frame(
            panel_video,
            bg=self.COLOR_PANEL
        )

        controles_video.pack(
            pady=4
        )

        self.boton_reproducir = self.crear_boton(
            controles_video,
            "Reproducir",
            self.reproducir_video,
            self.COLOR_TURQUESA,
            self.COLOR_BLANCO,
            14
        )

        self.boton_reproducir.grid(
            row=0,
            column=0,
            padx=5
        )

        self.boton_pausar = self.crear_boton(
            controles_video,
            "Pausar",
            self.pausar_video,
            self.COLOR_AMARILLO,
            self.COLOR_TEXTO,
            14
        )

        self.boton_pausar.grid(
            row=0,
            column=1,
            padx=5
        )

        self.boton_reiniciar = self.crear_boton(
            controles_video,
            "Reiniciar",
            self.reiniciar_video,
            self.COLOR_NARANJA,
            self.COLOR_BLANCO,
            14
        )

        self.boton_reiniciar.grid(
            row=0,
            column=2,
            padx=5
        )

        # =====================================================
        # PANEL DE CONTROL
        # =====================================================

        panel_control = tk.LabelFrame(
            contenedor,
            text=" Control del servomotor ",
            font=("Arial", 12, "bold"),
            bg=self.COLOR_PANEL,
            fg=self.COLOR_AZUL_OSCURO,
            bd=2,
            relief="groove",
            padx=15,
            pady=15
        )

        panel_control.grid(
            row=0,
            column=1,
            padx=6,
            pady=5,
            sticky="nsew"
        )

        tk.Label(
            panel_control,
            text="Selecciona el puerto COM:",
            font=("Arial", 11, "bold"),
            bg=self.COLOR_PANEL,
            fg=self.COLOR_AZUL_OSCURO
        ).pack(
            pady=(5, 8)
        )

        self.combo_puertos = ttk.Combobox(
            panel_control,
            width=23,
            state="readonly",
            font=("Arial", 10)
        )

        self.combo_puertos.pack(
            pady=5
        )

        boton_actualizar = self.crear_boton(
            panel_control,
            "Actualizar puertos COM",
            self.actualizar_puertos,
            self.COLOR_AZUL_CLARO,
            self.COLOR_AZUL_OSCURO,
            21
        )

        boton_actualizar.pack(
            pady=5
        )

        self.boton_conectar = self.crear_boton(
            panel_control,
            "Conectar Arduino",
            self.conectar_arduino,
            self.COLOR_AZUL,
            self.COLOR_BLANCO,
            21,
            2
        )

        self.boton_conectar.pack(
            pady=7
        )

        self.estado = tk.Label(
            panel_control,
            text="Arduino desconectado",
            font=("Arial", 10, "bold"),
            fg=self.COLOR_ERROR,
            bg=self.COLOR_PANEL
        )

        self.estado.pack(
            pady=7
        )

        ttk.Separator(
            panel_control,
            orient="horizontal"
        ).pack(
            fill="x",
            pady=10
        )

        tk.Label(
            panel_control,
            text="Ángulo sincronizado",
            font=("Arial", 12, "bold"),
            bg=self.COLOR_PANEL,
            fg=self.COLOR_AZUL_OSCURO
        ).pack(
            pady=4
        )

        self.valor_angulo = tk.IntVar(
            value=0
        )

        self.deslizador = tk.Scale(
            panel_control,
            from_=0,
            to=180,
            orient=tk.HORIZONTAL,
            length=220,
            resolution=1,
            variable=self.valor_angulo,
            command=self.slider_movido,
            font=("Arial", 10),
            bg=self.COLOR_PANEL,
            fg=self.COLOR_TEXTO,
            troughcolor=self.COLOR_AZUL_CLARO,
            activebackground=self.COLOR_AZUL,
            highlightthickness=0
        )

        self.deslizador.pack(
            pady=6
        )

        self.etiqueta_angulo = tk.Label(
            panel_control,
            text="0°",
            font=("Arial", 32, "bold"),
            bg=self.COLOR_PANEL,
            fg=self.COLOR_MORADO
        )

        self.etiqueta_angulo.pack(
            pady=6
        )

        tk.Label(
            panel_control,
            text=(
                "Inicio = 0°\n"
                "Mitad = 90°\n"
                "Final = 180°"
            ),
            font=("Arial", 10),
            justify="center",
            bg=self.COLOR_PANEL,
            fg=self.COLOR_TEXTO
        ).pack(
            pady=6
        )

        boton_0 = self.crear_boton(
            panel_control,
            "Ir a 0°",
            lambda: self.establecer_angulo(0),
            self.COLOR_AZUL_CLARO,
            self.COLOR_AZUL_OSCURO,
            21
        )

        boton_0.pack(
            pady=4
        )

        boton_90 = self.crear_boton(
            panel_control,
            "Ir a 90°",
            lambda: self.establecer_angulo(90),
            self.COLOR_AZUL,
            self.COLOR_BLANCO,
            21
        )

        boton_90.pack(
            pady=4
        )

        boton_180 = self.crear_boton(
            panel_control,
            "Ir a 180°",
            lambda: self.establecer_angulo(180),
            self.COLOR_MORADO,
            self.COLOR_BLANCO,
            21
        )

        boton_180.pack(
            pady=4
        )

        # =====================================================
        # PANEL DEL VECTOR
        # =====================================================

        panel_vector = tk.LabelFrame(
            contenedor,
            text=" Vector del servo ",
            font=("Arial", 11, "bold"),
            bg=self.COLOR_PANEL,
            fg=self.COLOR_AZUL_OSCURO,
            bd=2,
            relief="groove",
            padx=3,
            pady=3
        )

        panel_vector.grid(
            row=0,
            column=2,
            padx=6,
            pady=5,
            sticky="nsew"
        )

        self.figura_vector = Figure(
            figsize=(3.4, 3.6),
            dpi=100,
            facecolor=self.COLOR_PANEL
        )

        self.ax_vector = (
            self.figura_vector.add_subplot(
                111,
                projection="3d"
            )
        )

        self.canvas_vector = FigureCanvasTkAgg(
            self.figura_vector,
            master=panel_vector
        )

        self.canvas_vector.get_tk_widget().pack(
            fill="both",
            expand=True
        )

        self.etiqueta_coordenadas = tk.Label(
            panel_vector,
            text="P = (5.00, 0.00, 0.00)",
            font=("Arial", 9, "bold"),
            bg=self.COLOR_PANEL,
            fg=self.COLOR_AZUL_OSCURO
        )

        self.etiqueta_coordenadas.pack(
            pady=3
        )

        self.actualizar_vector_3d(
            0
        )

    # =========================================================
    # PUERTOS COM
    # =========================================================

    def actualizar_puertos(self):

        puertos = serial.tools.list_ports.comports()

        lista_puertos = [
            puerto.device
            for puerto in puertos
        ]

        self.combo_puertos[
            "values"
        ] = lista_puertos

        if lista_puertos:

            self.combo_puertos.set(
                "Selecciona un puerto COM"
            )

        else:

            self.combo_puertos.set(
                "No se encontraron puertos"
            )

    def conectar_arduino(self):

        if (
            self.arduino is not None
            and self.arduino.is_open
        ):

            self.arduino.close()
            self.arduino = None

            self.estado.config(
                text="Arduino desconectado",
                fg=self.COLOR_ERROR
            )

            self.boton_conectar.config(
                text="Conectar Arduino",
                bg=self.COLOR_AZUL,
                activebackground=self.oscurecer_color(
                    self.COLOR_AZUL
                )
            )

            self.ultimo_angulo_enviado = None

            return

        puerto = self.combo_puertos.get()

        if (
            puerto == ""
            or puerto == "Selecciona un puerto COM"
            or puerto == "No se encontraron puertos"
        ):

            messagebox.showwarning(
                "Selecciona el puerto COM",
                "Primero selecciona el puerto COM "
                "donde está conectado el Arduino."
            )

            return

        try:

            self.arduino = serial.Serial(
                puerto,
                9600,
                timeout=1
            )

            self.estado.config(
                text=f"Conectado en {puerto}",
                fg=self.COLOR_EXITO
            )

            self.boton_conectar.config(
                text="Desconectar Arduino",
                bg=self.COLOR_ERROR,
                activebackground=self.oscurecer_color(
                    self.COLOR_ERROR
                )
            )

            self.ultimo_angulo_enviado = None

            self.enviar_angulo_arduino(
                self.valor_angulo.get()
            )

        except serial.SerialException as error:

            messagebox.showerror(
                "Error de conexión",
                f"No se pudo abrir {puerto}.\n\n{error}"
            )

    # =========================================================
    # CARGAR VIDEO
    # =========================================================

    def cargar_video(self):

        self.video = cv2.VideoCapture(
            self.ruta_video
        )

        if not self.video.isOpened():

            self.etiqueta_video.config(
                text=(
                    "No se pudo abrir el video.\n\n"
                    "Verifica la ruta:\n\n"
                    f"{self.ruta_video}"
                ),
                image=""
            )

            return

        self.total_frames = int(
            self.video.get(
                cv2.CAP_PROP_FRAME_COUNT
            )
        )

        self.fps = self.video.get(
            cv2.CAP_PROP_FPS
        )

        if self.fps <= 0:
            self.fps = 30

        if self.total_frames > 0:

            self.duracion_video = (
                self.total_frames / self.fps
            )

        self.mostrar_frame_por_angulo(
            0
        )

    # =========================================================
    # VIDEO
    # =========================================================

    def reproducir_video(self):

        if self.video is None:
            return

        if not self.video.isOpened():
            return

        if self.reproduciendo:
            return

        frame_actual = int(
            self.video.get(
                cv2.CAP_PROP_POS_FRAMES
            )
        )

        if frame_actual >= self.total_frames - 1:

            self.video.set(
                cv2.CAP_PROP_POS_FRAMES,
                0
            )

            self.actualizar_angulo(
                0
            )

        self.reproduciendo = True

        self.actualizar_video()

    def pausar_video(self):

        self.reproduciendo = False

    def reiniciar_video(self):

        self.reproduciendo = False

        if self.video is None:
            return

        self.video.set(
            cv2.CAP_PROP_POS_FRAMES,
            0
        )

        self.actualizar_angulo(
            0
        )

        self.mostrar_frame_por_angulo(
            0
        )

    def actualizar_video(self):

        if not self.reproduciendo:
            return

        disponible, frame = self.video.read()

        if not disponible:

            self.reproduciendo = False

            self.mostrar_frame_por_angulo(
                180
            )

            self.actualizar_angulo(
                180
            )

            return

        frame_actual = int(
            self.video.get(
                cv2.CAP_PROP_POS_FRAMES
            )
        ) - 1

        frame_actual = max(
            0,
            min(
                frame_actual,
                self.total_frames - 1
            )
        )

        progreso = (
            frame_actual
            / max(
                self.total_frames - 1,
                1
            )
        )

        angulo = round(
            progreso * 180
        )

        self.mostrar_imagen(
            frame
        )

        self.actualizar_angulo(
            angulo
        )

        tiempo_actual = (
            frame_actual / self.fps
        )

        self.etiqueta_tiempo.config(
            text=(
                f"Tiempo: {tiempo_actual:.1f} s / "
                f"{self.duracion_video:.1f} s"
            )
        )

        if frame_actual >= self.total_frames - 1:

            self.reproduciendo = False

            self.actualizar_angulo(
                180
            )

            return

        retraso = max(
            1,
            int(1000 / self.fps)
        )

        self.ventana.after(
            retraso,
            self.actualizar_video
        )

    def mostrar_frame_por_angulo(self, angulo):

        if self.video is None:
            return

        if not self.video.isOpened():
            return

        progreso = angulo / 180

        frame_destino = round(
            progreso
            * max(
                self.total_frames - 1,
                0
            )
        )

        self.video.set(
            cv2.CAP_PROP_POS_FRAMES,
            frame_destino
        )

        disponible, frame = self.video.read()

        if disponible:

            self.mostrar_imagen(
                frame
            )

        tiempo_actual = (
            progreso
            * self.duracion_video
        )

        self.etiqueta_tiempo.config(
            text=(
                f"Tiempo: {tiempo_actual:.1f} s / "
                f"{self.duracion_video:.1f} s"
            )
        )

    def mostrar_imagen(self, frame):

        frame = cv2.resize(
            frame,
            (760, 540)
        )

        frame = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )

        imagen_pil = Image.fromarray(
            frame
        )

        imagen_tk = ImageTk.PhotoImage(
            image=imagen_pil
        )

        self.etiqueta_video.imagen_tk = (
            imagen_tk
        )

        self.etiqueta_video.config(
            image=imagen_tk,
            text=""
        )

    # =========================================================
    # ÁNGULO
    # =========================================================

    def slider_movido(self, valor):

        if self.actualizando_slider:
            return

        angulo = int(
            float(valor)
        )

        self.reproduciendo = False

        self.actualizar_angulo(
            angulo
        )

        self.mostrar_frame_por_angulo(
            angulo
        )

    def establecer_angulo(self, angulo):

        self.reproduciendo = False

        self.actualizar_angulo(
            angulo
        )

        self.mostrar_frame_por_angulo(
            angulo
        )

    def actualizar_angulo(self, angulo):

        angulo = max(
            0,
            min(
                180,
                int(angulo)
            )
        )

        self.actualizando_slider = True

        self.valor_angulo.set(
            angulo
        )

        self.actualizando_slider = False

        self.etiqueta_angulo.config(
            text=f"{angulo}°"
        )

        self.actualizar_vector_3d(
            angulo
        )

        self.enviar_angulo_arduino(
            angulo
        )

    # =========================================================
    # ENVIAR ÁNGULO A ARDUINO
    # =========================================================

    def enviar_angulo_arduino(self, angulo):

        if angulo == self.ultimo_angulo_enviado:
            return

        if (
            self.arduino is not None
            and self.arduino.is_open
        ):

            try:

                mensaje = f"{angulo}\n"

                self.arduino.write(
                    mensaje.encode(
                        "utf-8"
                    )
                )

                self.ultimo_angulo_enviado = (
                    angulo
                )

            except serial.SerialException:

                self.estado.config(
                    text="Se perdió la conexión",
                    fg=self.COLOR_ERROR
                )

                self.arduino = None
                self.ultimo_angulo_enviado = None

                self.boton_conectar.config(
                    text="Conectar Arduino",
                    bg=self.COLOR_AZUL
                )

    # =========================================================
    # VECTOR 3D
    # =========================================================

    def actualizar_vector_3d(self, angulo):

        theta = math.radians(
            angulo
        )

        longitud = self.longitud_vector

        x = longitud * math.cos(
            theta
        )

        y = 0

        z = longitud * math.sin(
            theta
        )

        self.ax_vector.clear()

        self.ax_vector.set_facecolor(
            "#F8FBFF"
        )

        # Base
        self.ax_vector.scatter(
            [0],
            [0],
            [0],
            s=70,
            color=self.COLOR_NARANJA
        )

        # Vector
        self.ax_vector.quiver(
            0,
            0,
            0,
            x,
            y,
            z,
            arrow_length_ratio=0.14,
            linewidth=3,
            color=self.COLOR_AZUL
        )

        # Extremo
        self.ax_vector.scatter(
            [x],
            [y],
            [z],
            s=45,
            color=self.COLOR_MORADO
        )

        # Eje X
        self.ax_vector.plot(
            [-longitud, longitud],
            [0, 0],
            [0, 0],
            linestyle="--",
            linewidth=1,
            color=self.COLOR_TURQUESA
        )

        # Eje Z
        self.ax_vector.plot(
            [0, 0],
            [0, 0],
            [0, longitud],
            linestyle="--",
            linewidth=1,
            color=self.COLOR_NARANJA
        )

        # Proyección
        self.ax_vector.plot(
            [x, x],
            [0, 0],
            [0, z],
            linestyle=":",
            color=self.COLOR_MORADO
        )

        self.ax_vector.text(
            x,
            y,
            z,
            f" P({x:.1f}, {z:.1f})",
            fontsize=7,
            color=self.COLOR_TEXTO
        )

        self.ax_vector.set_title(
            f"θ = {angulo}°",
            fontsize=10,
            fontweight="bold",
            color=self.COLOR_AZUL_OSCURO
        )

        self.ax_vector.set_xlabel(
            "X",
            fontsize=8,
            color=self.COLOR_AZUL_OSCURO
        )

        self.ax_vector.set_ylabel(
            ""
        )

        self.ax_vector.set_zlabel(
            "Z",
            fontsize=8,
            color=self.COLOR_AZUL_OSCURO
        )

        limite = longitud + 1

        self.ax_vector.set_xlim(
            -limite,
            limite
        )

        self.ax_vector.set_ylim(
            -0.5,
            0.5
        )

        self.ax_vector.set_zlim(
            0,
            limite
        )

        self.ax_vector.set_box_aspect(
            [2, 0.25, 1]
        )

        # Vista desde el eje Y
        self.ax_vector.view_init(
            elev=0,
            azim=-90
        )

        self.ax_vector.tick_params(
            labelsize=6,
            colors=self.COLOR_TEXTO
        )

        self.ax_vector.grid(
            True
        )

        self.etiqueta_coordenadas.config(
            text=(
                f"P = ({x:.2f}, "
                f"{y:.2f}, "
                f"{z:.2f})"
            )
        )

        self.canvas_vector.draw_idle()

    # =========================================================
    # CERRAR
    # =========================================================

    def cerrar_programa(self):

        self.reproduciendo = False

        if self.video is not None:

            self.video.release()

        if (
            self.arduino is not None
            and self.arduino.is_open
        ):

            self.arduino.close()

        self.ventana.destroy()


# =============================================================
# INICIAR PROGRAMA
# =============================================================

ventana = tk.Tk()

aplicacion = InterfazServo(
    ventana
)

ventana.mainloop()