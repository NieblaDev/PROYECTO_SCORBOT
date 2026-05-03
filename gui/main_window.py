import threading
import time
import cv2
from PIL import Image, ImageTk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox
from tkinter.filedialog import asksaveasfilename

from core.robot_control import ScorbotController
from core.protocol import ACLCommands
from gui.components import TerminalWidget
import utils.config as config
from utils.logger import SessionLogger

class AplicacionGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Scorbot Control System")
        self.root.geometry(config.WINDOW_SIZE)
        self.root.minsize(*config.MIN_WINDOW_SIZE)
        
        try:
            self.root.iconbitmap(config.ICON_PATH)
        except:
            pass 

        self.robot = ScorbotController(callback_recepcion=self.actualizar_texto_recibido)
        self.cap = None
        self.camara_activa = False
        
        # Candado para encolar comandos y evitar colisiones
        self.lock_envio = threading.Lock()
        
        self.configurar_interfaz()
        self.root.protocol("WM_DELETE_WINDOW", self.cerrar_aplicacion)
        self.root.bind("<Escape>", self.abortar_emergencia)

    def configurar_interfaz(self):
        main_frame = ttk.Frame(self.root, padding=15)
        main_frame.pack(fill=BOTH, expand=True)

        # --- PANEL SUPERIOR ---
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=X, pady=(0, 10))
        
        self.lbl_estado = ttk.Label(top_frame, text="DESCONECTADO", bootstyle="inverse-danger", width=15, anchor="center")
        self.lbl_estado.pack(side=LEFT, padx=(0, 15))

        self.combo_puerto = ttk.Combobox(top_frame, values=[f"COM{i}" for i in range(1, 10)], width=10)
        self.combo_puerto.set(config.DEFAULT_PORT)
        self.combo_puerto.pack(side=LEFT, padx=(0, 5))
        
        ttk.Button(top_frame, text="Conectar", command=self.click_conectar, bootstyle="primary").pack(side=LEFT, padx=2)
        ttk.Button(top_frame, text="Desconectar", command=self.click_desconectar, bootstyle="outline-primary").pack(side=LEFT, padx=2)

        # --- SISTEMA DE PESTAÑAS ---
        self.notebook = ttk.Notebook(main_frame, bootstyle="dark")
        self.notebook.pack(fill=BOTH, expand=True)

        self.tab_principal = ttk.Frame(self.notebook)
        self.tab_terminal = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_principal, text="Control Visual")
        self.notebook.add(self.tab_terminal, text="Terminal ACL")

        self._armar_tab_principal()
        self._armar_tab_terminal()

    def _armar_tab_principal(self):
        # --- PANEL IZQUIERDO: VIDEO ---
        self.frame_video = ttk.Frame(self.tab_principal, bootstyle="dark")
        self.frame_video.place(relx=0, rely=0, relwidth=0.6, relheight=1)
        
        header_camara = ttk.Frame(self.frame_video, bootstyle="dark")
        header_camara.pack(side=TOP, fill=X, padx=10, pady=5)
        
        ttk.Label(header_camara, text="Cámara:", font=("Helvetica", 10, "bold"), bootstyle="inverse-dark").pack(side=LEFT, padx=(0, 5))
        self.combo_camaras = ttk.Combobox(header_camara, state="readonly", values=["Cámara 0", "Cámara 1", "Cámara 2", "Cámara 3"], width=10)
        self.combo_camaras.set("Cámara 0")
        self.combo_camaras.pack(side=LEFT)

        self.lbl_video = ttk.Label(self.frame_video, text="Cámara Apagada", foreground="gray")
        self.lbl_video.place(relx=0.5, rely=0.5, anchor="center")
        
        btn_frame = ttk.Frame(self.frame_video, bootstyle="dark")
        btn_frame.pack(side=BOTTOM, fill=X, padx=10, pady=10)
        ttk.Button(btn_frame, text="Encender", bootstyle="success", command=self.encender_camara).pack(side=RIGHT, padx=5)
        ttk.Button(btn_frame, text="Apagar", bootstyle="danger", command=self.apagar_camara).pack(side=RIGHT)

        # --- PANEL DERECHO: TEXTOS Y COMANDOS ---
        textos_frame = ttk.Frame(self.tab_principal)
        textos_frame.place(relx=0.6, rely=0, relwidth=0.4, relheight=1)

        self.term_main = TerminalWidget(textos_frame, "Datos Recibidos")
        self.term_main.pack(fill=BOTH, expand=True, pady=(0, 5), padx=(10, 0))
        self.term_main.write("Inicio de terminal...\n")

        # Botones de Log
        frame_botones_reci = ttk.Frame(textos_frame)
        frame_botones_reci.pack(fill=X, pady=(0, 10), padx=(10, 0))
        ttk.Button(frame_botones_reci, text="Guardar Log", bootstyle="primary", command=self.click_guardar_log).pack(side=LEFT, expand=True, fill=X, padx=(0, 5))
        ttk.Button(frame_botones_reci, text="Limpiar Log", bootstyle="warning", command=self.click_borrar_log).pack(side=RIGHT, expand=True, fill=X, padx=(5, 0))

        # Indicador de estado de envío
        header_enviados = ttk.Frame(textos_frame)
        header_enviados.pack(fill=X, pady=(0, 5), padx=(10, 0))
        ttk.Label(header_enviados, text="Datos Enviados", font=("Helvetica", 10, "bold")).pack(side=LEFT)
        self.lbl_resultado = ttk.Label(header_enviados, text="Esperando comandos...", bootstyle="secondary", font=("Helvetica", 10, "italic"))
        self.lbl_resultado.pack(side=LEFT, padx=(15, 0))

        # Área de entrada
        self.TextEnviar = ttk.Text(textos_frame, height=2, font=("Consolas", 11), undo=True)
        self.TextEnviar.pack(fill=X, pady=(0, 5), padx=(10, 0))
        self.TextEnviar.bind("<Return>", lambda e: self.enviar_desde_gui(self.TextEnviar))

        # Botones de acción
        frame_botones_env = ttk.Frame(textos_frame)
        frame_botones_env.pack(fill=X, pady=(0, 10), padx=(10, 0))
        ttk.Button(frame_botones_env, text="Enviar (Enter)", bootstyle="primary", command=lambda: self.enviar_desde_gui(self.TextEnviar)).pack(side=LEFT, expand=True, fill=X, padx=(0, 5))
        ttk.Button(frame_botones_env, text="Abortar (Esc)", bootstyle="danger", command=self.abortar_emergencia).pack(side=RIGHT, expand=True, fill=X, padx=(5, 0))

    def _armar_tab_terminal(self):
        self.term_hyper = TerminalWidget(self.tab_terminal, "", font=("Consolas", 12), bootstyle="dark")
        self.term_hyper.pack(fill=BOTH, expand=True, padx=10, pady=(10, 5))
        self.term_hyper.write("SCORBOT ER-IX HYPERTERMINAL MODE...\n")

        input_frame = ttk.Frame(self.tab_terminal)
        input_frame.pack(fill=X, padx=10, pady=(0, 10))

        ttk.Label(input_frame, text="> ", font=("Consolas", 14, "bold")).pack(side=LEFT, padx=(5, 2))
        
        self.EntryTerminalIn = ttk.Entry(input_frame, font=("Consolas", 12))
        self.EntryTerminalIn.pack(side=LEFT, fill=X, expand=True)
        self.EntryTerminalIn.bind("<Return>", lambda e: self.enviar_desde_gui(self.EntryTerminalIn))

        ttk.Button(input_frame, text="Enviar", bootstyle="primary", command=lambda: self.enviar_desde_gui(self.EntryTerminalIn)).pack(side=LEFT, padx=(5, 0))

    # ==========================================
    # LÓGICA DE EVENTOS Y CONTROLADORES
    # ==========================================
    def actualizar_texto_recibido(self, texto):
        self.root.after(0, lambda: self.term_main.write(texto))
        self.root.after(0, lambda: self.term_hyper.write(texto))

    def mostrar_resultado(self, mensaje, estilo="success"):
        self.lbl_resultado.config(text=mensaje, bootstyle=estilo)
        self.root.after(3000, lambda: self.lbl_resultado.config(text="Esperando comandos...", bootstyle="secondary"))

    def click_conectar(self):
        puerto = self.combo_puerto.get()
        if self.robot.conectar(puerto):
            self.lbl_estado.config(text="CONECTADO", bootstyle="inverse-success")
        else:
            Messagebox.show_error("Error de conexión serial", "Error")

    def click_desconectar(self):
        self.robot.desconectar()
        self.lbl_estado.config(text="DESCONECTADO", bootstyle="inverse-danger")

    def enviar_desde_gui(self, widget_origen):
        if not self.robot.conectado:
            return "break"

        if isinstance(widget_origen, ttk.Entry):
            comando = widget_origen.get().strip()
            widget_origen.delete(0, END)
        else:
            comando = widget_origen.get("1.0", END).strip()
            widget_origen.delete("1.0", END)
        
        if not comando: return "break"

        # ¡USAMOS LA COLA! Esto garantiza el orden perfecto.
        self.robot.encolar_comando(comando)
        return "break"

    def abortar_emergencia(self, event=None):
        if self.robot.conectado:
            self.robot.abortar()
            self.mostrar_resultado("¡ABORTAR OPERACIÓN ENVIADO!", "danger")

    def click_guardar_log(self):
        filepath = asksaveasfilename(defaultextension="txt", filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
        if filepath:
            contenido = self.term_main.get_content()
            if SessionLogger.save_log(filepath, contenido):
                Messagebox.show_info("Log guardado exitosamente.", "Éxito")
            else:
                Messagebox.show_error("Error al escribir el archivo.", "Error")
    
    def click_borrar_log(self):
        self.term_main.write("", clear=True)
        self.term_main.write("Inicio de terminal...\n")
        self.term_hyper.write("", clear=True)
        self.term_hyper.write("SCORBOT ER-IX HYPERTERMINAL MODE...\n")

    # ==========================================
    # LÓGICA DE VISIÓN (CÁMARA)
    # ==========================================
    def encender_camara(self):
        try:
            idx_str = self.combo_camaras.get()
            idx = int(idx_str.split(" ")[-1])
        except (IndexError, ValueError):
            idx = 0

        self.camara_activa = False
        if self.cap is not None:
            self.cap.release()
            
        self.cap = cv2.VideoCapture(idx)
        
        if self.cap.isOpened():
            self.camara_activa = True
            self.actualizar_camara()
        else:
            Messagebox.show_error(f"No se pudo conectar a la Cámara {idx}.", "Error de Hardware")
            self.cap = None
            self.lbl_video.configure(text="Sin señal de video.", foreground="red")

    def apagar_camara(self):
        self.camara_activa = False 
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        
        self.lbl_video.configure(image='', text="Cámara Apagada", foreground="gray")
        self.lbl_video.image = None

    def actualizar_camara(self):
        if not self.camara_activa or self.cap is None:
            return

        ret, frame = self.cap.read()
        
        self.frame_video.update_idletasks()
        cam_w = self.frame_video.winfo_width()
        cam_h = self.frame_video.winfo_height()

        if ret and cam_w > 10 and cam_h > 10:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img_h, img_w = frame_rgb.shape[:2]
            
            escala = min(cam_w / img_w, cam_h / img_h)
            nuevo_w = int(img_w * escala)
            nuevo_h = int(img_h * escala)
            
            if nuevo_w > 0 and nuevo_h > 0:
                frame_rgb = cv2.resize(frame_rgb, (nuevo_w, nuevo_h), interpolation=cv2.INTER_AREA)
            
            img = Image.fromarray(frame_rgb)
            imgtk = ImageTk.PhotoImage(image=img)
            self.lbl_video.imgtk = imgtk
            self.lbl_video.configure(image=imgtk, text="")
            
        self.root.after(15, self.actualizar_camara)

    def cerrar_aplicacion(self):
        self.camara_activa = False
        self.robot.desconectar()
        if self.cap: self.cap.release()
        self.root.destroy()