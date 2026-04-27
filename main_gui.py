import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledText
from ttkbootstrap.dialogs import Messagebox
from tkinter.filedialog import asksaveasfilename
import threading
import time
import cv2
import numpy as np # IMPORTANTE: Agrega numpy
from PIL import Image, ImageTk
from ultralytics import YOLO # IMPORTANTE: Importamos YOLOv11

from robot_control import ScorbotController

class AplicacionGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Scorbot Vision Terminal")
        self.root.geometry("1280x720")
        self.root.minsize(800, 600)
        
        try:
            self.root.iconbitmap("bot.ico")
        except:
            pass 

        self.root.protocol("WM_DELETE_WINDOW", self.cerrar_aplicacion)
        
        self.cam_w = 640
        self.cam_h = 480

        self.cap = None
        self.camara_activa = False

        # --- NUEVO: INICIALIZAR YOLO ---
        # Usamos el modelo 'nano' (yolo11n.pt) porque es el más rápido para video en tiempo real.
        # Si es la primera vez, se descargará automáticamente de internet.
        self.modelo_yolo = YOLO("yolo11n.pt") 
        self.objetivo_detectado_px = None # Almacenará la tupla (x, y) del centro del objeto
        
        self.robot = ScorbotController(callback_recepcion=self.actualizar_texto_recibido)
        # ... (resto del init)

        self.robot = ScorbotController(callback_recepcion=self.actualizar_texto_recibido)
        self.root.bind("<Escape>", self.abortar_emergencia)

        self.configurar_interfaz()

    def configurar_interfaz(self):
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        main_frame = ttk.Frame(self.root, padding=15)
        main_frame.grid(row=0, column=0, sticky="nsew")
        main_frame.columnconfigure(0, weight=1) 
        main_frame.rowconfigure(1, weight=1)

        # =========================================================
        # PANEL SUPERIOR (Fuera de las pestañas, siempre visible)
        # =========================================================
        top_frame = ttk.Frame(main_frame)
        top_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        
        top_frame.columnconfigure(7, weight=1)

        ttk.Label(top_frame, text="Estado:").grid(row=0, column=0, sticky="w", padx=(0, 5), pady=2)
        self.lbl_estado = ttk.Label(top_frame, text="DESCONECTADO", bootstyle="inverse-danger", width=15, anchor="center")
        self.lbl_estado.grid(row=0, column=1, sticky="w", padx=(0, 15), pady=2)

        ttk.Label(top_frame, text="Puerto:").grid(row=0, column=2, sticky="w", padx=(0, 5), pady=2)
        self.comboBox1 = ttk.Combobox(top_frame, state="readonly", values=[f"COM{i}" for i in range(1, 10)], width=10, bootstyle="primary")
        self.comboBox1.set("COM5") 
        self.comboBox1.grid(row=0, column=3, sticky="w", padx=(0, 15))
        
        self.btn_conectar = ttk.Button(top_frame, text="Conectar", command=self.click_conectar, bootstyle="primary")
        self.btn_conectar.grid(row=0, column=4, padx=(0, 5))
        
        ttk.Label(top_frame, text="/").grid(row=0, column=5, padx=2)
        
        self.btn_desconectar = ttk.Button(top_frame, text="Desconectar", command=self.click_desconectar, bootstyle="outline primary")
        self.btn_desconectar.grid(row=0, column=6, padx=(5, 0))

        # Selector de Temas
        lista_temas = ["darkly", "flatly", "superhero", "cyborg"]
        frame_tema = ttk.Frame(top_frame)
        frame_tema.grid(row=0, column=8, sticky="e") 
        
        ttk.Label(frame_tema, text="Tema Visual:").pack(side=LEFT, padx=(0, 5))
        self.combo_temas = ttk.Combobox(frame_tema, state="readonly", values=lista_temas, width=15)
        self.combo_temas.set(self.root.style.theme.name) 
        self.combo_temas.pack(side=LEFT)
        self.combo_temas.bind("<<ComboboxSelected>>", self.cambiar_tema)

        # =========================================================
        # SISTEMA DE PESTAÑAS (Notebook)
        # =========================================================
        self.notebook = ttk.Notebook(main_frame, bootstyle="dark")
        self.notebook.grid(row=1, column=0, sticky="nsew")

        self.tab_principal = ttk.Frame(self.notebook)
        self.tab_terminal = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_principal, text="Página Principal")
        self.notebook.add(self.tab_terminal, text="Terminal Hyper")

        self._construir_tab_principal()
        self._construir_tab_terminal()

    def _construir_tab_principal(self):
        self.tab_principal.columnconfigure(0, weight=3, uniform="layout_principal") 
        self.tab_principal.columnconfigure(1, weight=2, uniform="layout_principal") 
        self.tab_principal.rowconfigure(0, weight=1)

        # --- PANEL IZQUIERDO DE CÁMARA ---
        cam_frame = ttk.Frame(self.tab_principal, bootstyle="dark")
        cam_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 15), pady=10)
        
        header_camara_frame = ttk.Frame(cam_frame, bootstyle="dark")
        header_camara_frame.pack(side=TOP, fill=X, padx=10, pady=5)
        
        ttk.Label(header_camara_frame, text="Cámara:", font=("Helvetica", 10, "bold"), bootstyle="inverse-dark").pack(side=LEFT, padx=(0, 5))
        self.combo_camaras = ttk.Combobox(header_camara_frame, state="readonly", values=["Cámara 0", "Cámara 1", "Cámara 2", "Cámara 3"], width=10)
        self.combo_camaras.set("Cámara 0")
        self.combo_camaras.pack(side=LEFT)

        self.btn_apagar_cam = ttk.Button(header_camara_frame, text="Apagar", bootstyle="danger", command=self.apagar_camara)
        self.btn_apagar_cam.pack(side=RIGHT, padx=(5, 0))
        
        self.btn_encender_cam = ttk.Button(header_camara_frame, text="Encender", bootstyle="success", command=self.encender_camara)
        self.btn_encender_cam.pack(side=RIGHT)

        video_container = ttk.Frame(cam_frame, bootstyle="dark")
        video_container.pack(side=TOP, fill=BOTH, expand=True)
        video_container.bind("<Configure>", self.evento_redimensionar_camara)
        
        self.lbl_video = ttk.Label(video_container, text="Cámara Apagada", foreground="gray", font=("Helvetica", 14), anchor="center")
        self.lbl_video.place(relx=0.5, rely=0.5, anchor="center")

        # --- PANEL DERECHO DE TEXTOS ---
        textos_frame = ttk.Frame(self.tab_principal)
        textos_frame.grid(row=0, column=1, sticky="nsew", pady=10)
        textos_frame.columnconfigure(0, weight=1)
        textos_frame.rowconfigure(1, weight=1) 
        textos_frame.rowconfigure(4, weight=0) 

        ttk.Label(textos_frame, text="Datos Recibidos", font=("Helvetica", 10, "bold")).grid(row=0, column=0, sticky="w", pady=(0, 5))
        self.TextRecibidos = ScrolledText(textos_frame, padding=5, font=("Consolas", 10), bootstyle="secondary", autohide=False)
        self.TextRecibidos.grid(row=1, column=0, sticky="nsew")
        self.TextRecibidos.insert("1.0", "Inicio de terminal...\n")
        self.TextRecibidos.text.configure(state="disabled") 

        frame_botones_reci = ttk.Frame(textos_frame)
        frame_botones_reci.grid(row=2, column=0, sticky="ew", pady=(10,10))
        self.btn_guardar_log = ttk.Button(frame_botones_reci, text="Guardar Log", width=17, bootstyle="primary", command=self.click_guardar_log)
        self.btn_guardar_log.pack(side=LEFT)
        self.btn_limpiar_log = ttk.Button(frame_botones_reci, text="Limpiar Log", width=17, bootstyle="warning", command=self.click_borrar_log)
        self.btn_limpiar_log.pack(side=RIGHT)

        header_enviados = ttk.Frame(textos_frame)
        header_enviados.grid(row=3, column=0, sticky="ew", pady=(0, 5))
        ttk.Label(header_enviados, text="Datos Enviados", font=("Helvetica", 10, "bold")).pack(side=LEFT)
        self.lbl_resultado = ttk.Label(header_enviados, text="Esperando comandos...", bootstyle="secondary", font=("Helvetica", 10, "italic"))
        self.lbl_resultado.pack(side=LEFT, padx=(15, 0))

        self.TextEnviar = ttk.Text(textos_frame, height=2, font=("Consolas", 11), undo=True)
        self.TextEnviar.grid(row=4, column=0, sticky="nsew")
        self.TextEnviar.bind("<Return>", lambda e: self.enviar_desde_gui(self.TextEnviar))

        frame_botones = ttk.Frame(textos_frame)
        frame_botones.grid(row=5, column=0, sticky="ew", pady=(10, 10))
        self.btn_enviar = ttk.Button(frame_botones, text="Enviar (Enter)", width=17, bootstyle="primary", command=lambda: self.enviar_desde_gui(self.TextEnviar))
        self.btn_enviar.pack(side=LEFT)
        self.btn_abortar = ttk.Button(frame_botones, text="Abortar (Esc)", width=17, bootstyle="danger", command=self.abortar_emergencia)
        self.btn_abortar.pack(side=RIGHT)

    def _construir_tab_terminal(self):
        self.tab_terminal.columnconfigure(0, weight=1)
        self.tab_terminal.rowconfigure(0, weight=1) 

        self.TextTerminalOut = ScrolledText(self.tab_terminal, padding=10, font=("Consolas", 12), bootstyle="dark", autohide=False)
        self.TextTerminalOut.grid(row=0, column=0, sticky="nsew", pady=(10, 5))
        self.TextTerminalOut.insert("1.0", "SCORBOT ER-IX HYPERTERMINAL MODE...\n")
        self.TextTerminalOut.text.configure(state="disabled")

        input_frame = ttk.Frame(self.tab_terminal)
        input_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        input_frame.columnconfigure(1, weight=1)

        ttk.Label(input_frame, text="> ", font=("Consolas", 14, "bold")).grid(row=0, column=0, padx=(5, 2))
        
        self.EntryTerminalIn = ttk.Entry(input_frame, font=("Consolas", 12))
        self.EntryTerminalIn.grid(row=0, column=1, sticky="ew")
        self.EntryTerminalIn.bind("<Return>", lambda e: self.enviar_desde_gui(self.EntryTerminalIn))

        ttk.Button(input_frame, text="Enviar", bootstyle="primary", command=lambda: self.enviar_desde_gui(self.EntryTerminalIn)).grid(row=0, column=2, padx=(5, 0))

    # =========================================================
    # LÓGICA DE TEMAS
    # =========================================================
    def cambiar_tema(self, event=None):
        tema_seleccionado = self.combo_temas.get()
        self.root.style.theme_use(tema_seleccionado)

    # =========================================================
    # LÓGICA DE VISIÓN (Control de Cámara)
    # =========================================================
    def encender_camara(self):
        # 1. FEEDBACK VISUAL ANTES DE CONGELAR
        self.btn_encender_cam.configure(state="disabled", text="Conectando...")
        self.btn_apagar_cam.configure(state="disabled")
        
        self.lbl_video.configure(image='', text="Iniciando hardware de visión...\nPor favor espere.", foreground="white")
        self.lbl_video.image = None
        self.root.update()

        # 2. LIBERAR CÁMARA ANTERIOR
        self.camara_activa = False
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        
        # 3. ABRIR NUEVA CÁMARA
        idx_str = self.combo_camaras.get()
        idx = int(idx_str.split(" ")[-1])
        self.cap = cv2.VideoCapture(idx)
        
        if self.cap.isOpened():
            self.camara_activa = True
            self.lbl_video.configure(text="") # Borramos el texto porque ya hay señal
            self.actualizar_camara()
        else:
            Messagebox.show_error(f"No se pudo conectar a la {idx_str}. Verifique la conexión USB.", "Error de Hardware")
            self.cap = None
            self.lbl_video.configure(text="Sin señal de video.", foreground="red")

        # 4. RESTAURAR BOTONES
        self.btn_encender_cam.configure(state="normal", text="Encender")
        self.btn_apagar_cam.configure(state="normal")

    def apagar_camara(self):
        # 1. FEEDBACK VISUAL DE APAGADO
        self.btn_apagar_cam.configure(state="disabled", text="Apagando...")
        self.btn_encender_cam.configure(state="disabled")
        self.root.update()

        # 2. APAGAR HARDWARE
        self.camara_activa = False 
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        
        # 3. ACTUALIZAR PANTALLA Y BOTONES
        self.lbl_video.configure(image='', text="Cámara Apagada", foreground="gray")
        self.lbl_video.image = None

        self.btn_apagar_cam.configure(state="normal", text="Apagar")
        self.btn_encender_cam.configure(state="normal")

    def evento_redimensionar_camara(self, event):
        self.cam_w = event.width
        self.cam_h = event.height

    def actualizar_camara(self):
        if not self.camara_activa or self.cap is None:
            return

        ret, frame = self.cap.read()
        if ret and self.cam_w > 10 and self.cam_h > 10:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img_h, img_w = frame_rgb.shape[:2]
            
            escala = min(self.cam_w / img_w, self.cam_h / img_h)
            nuevo_w = int(img_w * escala)
            nuevo_h = int(img_h * escala)
            
            if nuevo_w > 0 and nuevo_h > 0:
                frame_rgb = cv2.resize(frame_rgb, (nuevo_w, nuevo_h), interpolation=cv2.INTER_AREA)
            
            img = Image.fromarray(frame_rgb)
            imgtk = ImageTk.PhotoImage(image=img)
            self.lbl_video.imgtk = imgtk
            # Al actualizar la imagen nos aseguramos de que no haya texto encima
            self.lbl_video.configure(image=imgtk, text="")
            
        self.root.after(15, self.actualizar_camara)

    def cerrar_aplicacion(self):
        self.camara_activa = False
        if self.cap is not None and self.cap.isOpened(): 
            self.cap.release()
        self.root.destroy()

    # =========================================================
    # LÓGICA DE LA INTERFAZ Y COMUNICACIÓN
    # =========================================================
    def actualizar_texto_recibido(self, texto):
        self.root.after(0, lambda: self._escribir_en_cajas_log(texto))
        
    def _escribir_en_cajas_log(self, texto, clear=False):
        self.TextRecibidos.text.configure(state="normal")
        if clear: self.TextRecibidos.delete("1.0", END)
        self.TextRecibidos.insert(END, texto)
        self.TextRecibidos.text.see(END)
        self.TextRecibidos.text.configure(state="disabled")

        self.TextTerminalOut.text.configure(state="normal")
        if clear: self.TextTerminalOut.delete("1.0", END)
        self.TextTerminalOut.insert(END, texto)
        self.TextTerminalOut.text.see(END)
        self.TextTerminalOut.text.configure(state="disabled")
    
    def mostrar_resultado(self, mensaje, estilo="success"):
        self.lbl_resultado.config(text=mensaje, bootstyle=estilo)
        self.root.after(3000, lambda: self.lbl_resultado.config(text="Esperando comandos...", bootstyle="secondary"))

    def cambiar_estado(self, texto, estilo):
        self.lbl_estado.config(text=texto, bootstyle=estilo)

    def click_conectar(self):
        puerto = self.comboBox1.get()
        if self.robot.conectar(puerto):
            self.cambiar_estado("CONECTADO", "inverse-success")
        else:
            Messagebox.show_error("Error al conectar puerto.", "Error")

    def click_desconectar(self):
        self.robot.desconectar()
        self.cambiar_estado("DESCONECTADO", "inverse-danger")

    def enviar_desde_gui(self, widget_origen):
        if not self.robot.conectado:
            Messagebox.show_info("Primero debe conectarse con el puerto COM.", "Atención")
            return "break"

        if isinstance(widget_origen, ttk.Entry):
            comando = widget_origen.get().strip()
        else:
            comando = widget_origen.get("1.0", END).strip()
        
        if not comando: return "break"

        threading.Thread(target=self.rutina_envio, args=(comando, widget_origen), daemon=True).start()
        return "break"

    def rutina_envio(self, comando, widget_origen):
        self.robot.buffer_respuestas = "" 
        self.robot.enviar_comando(comando)
        
        while ">" not in self.robot.buffer_respuestas:
            time.sleep(0.05)
            if not self.robot.conectado: return

        self.root.after(0, lambda: self.mostrar_resultado(f"Enviado: {comando}"))
        
        if isinstance(widget_origen, ttk.Entry):
            self.root.after(0, lambda: widget_origen.delete(0, END))
        else:
            self.root.after(0, lambda: widget_origen.delete("1.0", END))

    def click_guardar_log(self):
        filepath = asksaveasfilename(defaultextension="txt", filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
        if filepath:
            try:
                with open(filepath, "w") as f:
                    f.write(self.TextRecibidos.get("1.0", END))
            except Exception as e:
                Messagebox.show_error(f"No se pudo guardar el log: {e}", "Error")
    
    def click_borrar_log(self):
        self.root.after(0, lambda: self._escribir_en_cajas_log(texto="Inicio de terminal...\n", clear=True))
    
    def abortar_emergencia(self, event=None):
        if not self.robot.conectado: return
        self.robot.enviar_comando("a\r") 
        self.mostrar_resultado("¡ABORTAR OPERACIÓN ENVIADO!", "danger")

if __name__ == "__main__":
    ventana = ttk.Window(themename="darkly") 
    app = AplicacionGUI(ventana)
    ventana.mainloop()