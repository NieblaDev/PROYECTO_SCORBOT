import time
import datetime
import threading
import cv2
from PIL import Image, ImageTk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox
from ttkbootstrap.widgets.scrolled import ScrolledText
from tkinter.filedialog import asksaveasfilename

from robot import ScorbotController, MockScorbotController

class AplicacionGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Scorbot Control System - Fase 1")
        self.root.geometry("1280x720")
        self.root.minsize(1280, 720)
        
        # Estado
        self.robot = ScorbotController()
        self.modo_mock = False
        
        self.cap = None
        self.camara_activa = False
        self.hilo_camara = None
        self.ultimo_frame = None
        
        # Variables de tiempo de sesión
        self.tiempo_inicio_sesion = None
        self.sesion_activa = False

        self.configurar_interfaz()
        
        # Eventos principales
        self.root.protocol("WM_DELETE_WINDOW", self.cerrar_aplicacion)
        self.root.bind("<Escape>", self.abortar_emergencia)
        
        # Iniciar bucle de temporizador
        self.actualizar_temporizador()

    def configurar_interfaz(self):
        main_frame = ttk.Frame(self.root, padding=15)
        main_frame.pack(fill=BOTH, expand=True)

        # --- PANEL SUPERIOR: CONEXIÓN Y CONFIGURACIONES ---
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=X, pady=(0, 15))
        
        # Estado
        self.lbl_estado = ttk.Label(top_frame, text="DESCONECTADO", bootstyle="inverse-danger", width=15, anchor="center", font=("Helvetica", 11, "bold"))
        self.lbl_estado.pack(side=LEFT, padx=(0, 15))

        # Opciones de puerto
        ttk.Label(top_frame, text="Puerto:", font=("Helvetica", 10)).pack(side=LEFT, padx=(0, 5))
        self.combo_puerto = ttk.Combobox(top_frame, values=[f"COM{i}" for i in range(1, 10)], width=8)
        self.combo_puerto.set("COM5")
        self.combo_puerto.pack(side=LEFT, padx=(0, 15))
        
        # Botones conexión
        self.btn_conectar = ttk.Button(top_frame, text="Conectar", command=self.click_conectar, bootstyle="primary")
        self.btn_conectar.pack(side=LEFT, padx=2)
        
        self.btn_desconectar = ttk.Button(top_frame, text="Desconectar", command=self.click_desconectar, bootstyle="outline-primary", state=DISABLED)
        self.btn_desconectar.pack(side=LEFT, padx=2)

        # Temporizador de sesión
        self.lbl_tiempo = ttk.Label(top_frame, text="Tiempo de sesión: 00:00:00", font=("Helvetica", 10, "italic"))
        self.lbl_tiempo.pack(side=LEFT, padx=(20, 0))

        # Menú configuraciones (Modo Mock)
        mock_frame = ttk.Frame(top_frame)
        mock_frame.pack(side=RIGHT, padx=(0, 10))
        self.var_mock = ttk.BooleanVar(value=False)
        self.check_mock = ttk.Checkbutton(mock_frame, text="Modo Mocking", bootstyle="round-toggle", variable=self.var_mock, command=self.toggle_mock)
        self.check_mock.pack(side=RIGHT)

        # --- CONTENIDO CENTRAL: DIVIDIDO EN DOS (CÁMARA Y TERMINAL) ---
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=BOTH, expand=True)

        # 1. PANEL IZQUIERDO: VIDEO
        left_frame = ttk.Frame(content_frame, bootstyle="dark", padding=10)
        left_frame.place(relx=0, rely=0, relwidth=0.6, relheight=1)
        
        header_camara = ttk.Frame(left_frame, bootstyle="dark")
        header_camara.pack(side=TOP, fill=X, pady=(0, 10))
        
        ttk.Label(header_camara, text="Cámara:", font=("Helvetica", 11, "bold"), bootstyle="inverse-dark").pack(side=LEFT, padx=(0, 5))
        self.combo_camaras = ttk.Combobox(header_camara, state="readonly", values=["Cámara 0", "Cámara 1", "Cámara 2", "Cámara 3"], width=10)
        self.combo_camaras.set("Cámara 0")
        self.combo_camaras.pack(side=LEFT)

        btn_encender = ttk.Button(header_camara, text="Encender", bootstyle="success", command=self.encender_camara)
        btn_encender.pack(side=LEFT, padx=(15, 5))
        
        btn_apagar = ttk.Button(header_camara, text="Apagar", bootstyle="danger", command=self.apagar_camara)
        btn_apagar.pack(side=LEFT)

        self.frame_video_container = ttk.Frame(left_frame, bootstyle="secondary")
        self.frame_video_container.pack(fill=BOTH, expand=True)
        
        self.lbl_video = ttk.Label(self.frame_video_container, text="Cámara Apagada", foreground="white", background="black", font=("Helvetica", 14), anchor="center")
        self.lbl_video.pack(fill=BOTH, expand=True)

        # 2. PANEL DERECHO: TERMINAL Y COMANDOS
        right_frame = ttk.Frame(content_frame, padding=(10, 0, 0, 0))
        right_frame.place(relx=0.6, rely=0, relwidth=0.4, relheight=1)

        # Header Terminal
        header_term = ttk.Frame(right_frame)
        header_term.pack(fill=X, pady=(0, 5))
        ttk.Label(header_term, text="Terminal de Comandos", font=("Helvetica", 12, "bold")).pack(side=LEFT)
        
        ttk.Button(header_term, text="Guardar Log", bootstyle="info-outline", command=self.guardar_log, padding=(2, 2)).pack(side=RIGHT, padx=(5, 0))
        ttk.Button(header_term, text="Limpiar", bootstyle="warning-outline", command=self.limpiar_log, padding=(2, 2)).pack(side=RIGHT)

        # Área de log de la terminal
        self.terminal_log = ScrolledText(right_frame, padding=5, height=15, font=("Consolas", 11), autohide=True)
        self.terminal_log.pack(fill=BOTH, expand=True, pady=(0, 10))
        self.terminal_log.text.config(state=DISABLED)
        self.escribir_en_terminal("=== Sistema Iniciado ===")

        # Panel de entrada de comandos
        input_frame = ttk.Labelframe(right_frame, text="Entrada de Terminal (ACL)", padding=10)
        input_frame.pack(fill=X, side=BOTTOM)

        self.text_entrada = ttk.Text(input_frame, height=3, font=("Consolas", 11))
        self.text_entrada.pack(fill=X, pady=(0, 10))
        self.text_entrada.bind("<Return>", lambda e: self.enviar_comando())

        botones_input = ttk.Frame(input_frame)
        botones_input.pack(fill=X)
        
        ttk.Button(botones_input, text="Enviar Comando", bootstyle="primary", command=self.enviar_comando).pack(side=LEFT, expand=True, fill=X, padx=(0, 5))
        ttk.Button(botones_input, text="Abortar (ESC)", bootstyle="danger", command=self.abortar_emergencia).pack(side=RIGHT, expand=True, fill=X, padx=(5, 0))


    # ==========================================
    # LÓGICA DE CONEXIÓN Y ESTADO
    # ==========================================
    def toggle_mock(self):
        if self.robot.conectado:
            self.click_desconectar()
            
        if self.var_mock.get():
            self.robot = MockScorbotController()
            self.escribir_en_terminal("Modo Mocking activado. Los comandos serán simulados.")
        else:
            self.robot = ScorbotController()
            self.escribir_en_terminal("Modo Mocking desactivado. Se usará conexión serial real.")

    def click_conectar(self):
        puerto = self.combo_puerto.get()
        self.escribir_en_terminal(f"Intentando conectar a {puerto}...")
        
        if self.robot.conectar(puerto):
            self.lbl_estado.config(text="CONECTADO", bootstyle="inverse-success")
            self.btn_conectar.config(state=DISABLED)
            self.btn_desconectar.config(state=NORMAL)
            self.combo_puerto.config(state=DISABLED)
            self.check_mock.config(state=DISABLED)
            
            self.sesion_activa = True
            self.tiempo_inicio_sesion = time.time()
            self.escribir_en_terminal("Conexión establecida con éxito.")

            self.escribir_en_terminal(self.robot.enviar_comando("|echo\r\r\r"))
        else:
            Messagebox.show_error(f"No se pudo conectar al puerto {puerto}.", "Error de conexión")
            self.escribir_en_terminal("Fallo al conectar.")

    def click_desconectar(self):
        self.robot.desconectar()
        self.lbl_estado.config(text="DESCONECTADO", bootstyle="inverse-danger")
        self.btn_conectar.config(state=NORMAL)
        self.btn_desconectar.config(state=DISABLED)
        self.combo_puerto.config(state=NORMAL)
        self.check_mock.config(state=NORMAL)
        
        self.sesion_activa = False
        self.escribir_en_terminal("Conexión cerrada.")

    def actualizar_temporizador(self):
        if self.sesion_activa and self.tiempo_inicio_sesion:
            transcurrido = int(time.time() - self.tiempo_inicio_sesion)
            td = datetime.timedelta(seconds=transcurrido)
            self.lbl_tiempo.config(text=f"Tiempo de sesión: {td}")
        else:
            self.lbl_tiempo.config(text="Tiempo de sesión: 00:00:00")
            
        self.root.after(1000, self.actualizar_temporizador)

    # ==========================================
    # LÓGICA DE TERMINAL Y COMANDOS
    # ==========================================
    def escribir_en_terminal(self, texto):
        self.terminal_log.text.config(state=NORMAL)
        self.terminal_log.text.insert(END, f"{texto}\n")
        self.terminal_log.text.see(END)
        self.terminal_log.text.config(state=DISABLED)

    def limpiar_log(self):
        self.terminal_log.text.config(state=NORMAL)
        self.terminal_log.text.delete("1.0", END)
        self.terminal_log.text.config(state=DISABLED)

    def guardar_log(self):
        filepath = asksaveasfilename(defaultextension="txt", filetypes=[("Archivos de texto", "*.txt")])
        if filepath:
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(self.terminal_log.text.get("1.0", END))
                Messagebox.show_info("Log guardado exitosamente.", "Éxito")
            except Exception as e:
                Messagebox.show_error(f"Error al guardar log: {e}", "Error")

    def enviar_comando(self, event=None):
        if not self.robot.conectado:
            Messagebox.show_warning("El robot no está conectado.", "Advertencia")
            return "break"

        comando = self.text_entrada.get("1.0", END).strip()
        self.text_entrada.delete("1.0", END)
        
        if not comando:
            return "break"

        respuesta = self.robot.enviar_comando(comando)
        
        if respuesta:
            self.escribir_en_terminal(respuesta)
            
        return "break"

    def abortar_emergencia(self, event=None):
        if self.robot.conectado:
            self.robot.abortar()
            self.escribir_en_terminal("!!! COMANDO DE ABORTO ENVIADO !!!")
        else:
            self.escribir_en_terminal("Aborto no enviado: Robot desconectado.")

    # ==========================================
    # LÓGICA DE CÁMARA
    # ==========================================
    def encender_camara(self):
        try:
            idx_str = self.combo_camaras.get()
            idx = int(idx_str.split(" ")[-1])
        except (IndexError, ValueError):
            idx = 0

        self.apagar_camara()
            
        self.cap = cv2.VideoCapture(idx)
        
        if self.cap.isOpened():
            self.camara_activa = True
            self.lbl_video.config(text="") # Limpiar texto
            
            # Iniciar hilo de lectura
            self.hilo_camara = threading.Thread(target=self._leer_camara_hilo, daemon=True)
            self.hilo_camara.start()
            
            self.actualizar_camara()
        else:
            Messagebox.show_error(f"No se pudo conectar a la Cámara {idx}.", "Error de Cámara")
            self.cap = None
            self.lbl_video.config(image='', text="Sin señal de video", background="black")

    def _leer_camara_hilo(self):
        while self.camara_activa and self.cap is not None and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                self.ultimo_frame = frame
            else:
                time.sleep(0.01)

    def apagar_camara(self):
        self.camara_activa = False 
        if hasattr(self, 'hilo_camara') and self.hilo_camara is not None:
            self.hilo_camara.join(timeout=1.0)
            self.hilo_camara = None
            
        if self.cap is not None:
            self.cap.release()
            self.cap = None
            
        self.ultimo_frame = None
        
        self.lbl_video.config(image='', text="Cámara Apagada", background="black")
        self.lbl_video.image = None

    def actualizar_camara(self):
        if not self.camara_activa or self.cap is None:
            return

        frame = self.ultimo_frame
        
        self.frame_video_container.update_idletasks()
        cam_w = self.frame_video_container.winfo_width()
        cam_h = self.frame_video_container.winfo_height()

        if frame is not None and cam_w > 10 and cam_h > 10:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img_h, img_w = frame_rgb.shape[:2]
            
            escala = min(cam_w / img_w, cam_h / img_h)
            nuevo_w = int(img_w * escala)
            nuevo_h = int(img_h * escala)
            
            if nuevo_w > 0 and nuevo_h > 0:
                frame_rgb = cv2.resize(frame_rgb, (nuevo_w, nuevo_h), interpolation=cv2.INTER_AREA)
            
            img = Image.fromarray(frame_rgb)
            imgtk = ImageTk.PhotoImage(image=img)
            self.lbl_video.image = imgtk  # Mantener referencia
            self.lbl_video.config(image=imgtk)
            
        self.root.after(30, self.actualizar_camara)

    def cerrar_aplicacion(self):
        self.apagar_camara()
        if self.robot.conectado:
            self.robot.desconectar()
        self.root.destroy()

if __name__ == "__main__":
    app_root = ttk.Window(themename="darkly") # Tema moderno oscuro de ttkbootstrap
    app = AplicacionGUI(app_root)
    app_root.mainloop()