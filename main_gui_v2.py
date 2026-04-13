import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.filedialog import asksaveasfilename, askopenfilename
import threading
import time
from robot_control import ScorbotController

class AplicacionGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Scorbot Terminal")
        self.root.geometry("1280x720")
        self.root.minsize(800, 600)
        
        try:
            self.root.iconbitmap("bot.ico")
        except:
            pass 

        self.robot = ScorbotController(callback_recepcion=self.actualizar_texto_recibido)
        self.configurar_interfaz()

    def configurar_interfaz(self):
        # Configuramos el grid principal de la ventana para que se expanda
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # --- CONTENEDOR PRINCIPAL ---
        main_frame = tk.Frame(self.root, padx=10, pady=10)
        main_frame.grid(row=0, column=0, sticky="nsew")
        
        # Grid del main_frame
        main_frame.columnconfigure(1, weight=1) # La columna central (cajas de texto) se expandirá
        main_frame.rowconfigure(1, weight=1)    # La fila central (cajas de texto) se expandirá

        # =========================================================
        # 1. PANEL SUPERIOR (Estado, Conexión, Temporizador)
        # =========================================================
        top_frame = tk.Frame(main_frame)
        top_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 15))

        # Estado
        tk.Label(top_frame, text="Estado :").grid(row=0, column=0, sticky="w", padx=(0, 5), pady=2)
        self.TextoEstado = tk.Text(top_frame, height=1, width=17, bg="white")
        self.TextoEstado.insert("1.0", "DESCONECTADO")
        self.TextoEstado.configure(state="disabled")
        self.TextoEstado.grid(row=0, column=1, sticky="w", padx=(0, 15), pady=2)

        # Conexión
        tk.Label(top_frame, text="Puerto :").grid(row=1, column=0, sticky="w", padx=(0, 5), pady=2)
        
        conn_frame = tk.Frame(top_frame)
        conn_frame.grid(row=1, column=1, sticky="w", pady=2)
        self.comboBox1 = ttk.Combobox(conn_frame, state="readonly", values=[f"COM{i}" for i in range(1, 10)], width=10)
        self.comboBox1.set("COM5") 
        self.comboBox1.pack(side=tk.LEFT, padx=(0, 10))
        
        self.btn_conectar = tk.Button(conn_frame, text="Conectar", command=self.click_conectar)
        self.btn_conectar.pack(side=tk.LEFT, padx=(0, 5))
        tk.Label(conn_frame, text="/").pack(side=tk.LEFT, padx=2)
        self.btn_desconectar = tk.Button(conn_frame, text="Desconectar", command=self.click_desconectar)
        self.btn_desconectar.pack(side=tk.LEFT, padx=(5, 0))

        # Temporizador
        tk.Label(top_frame, text="Temporizador :").grid(row=2, column=0, sticky="w", padx=(0, 5), pady=2)
        temp_frame = tk.Frame(top_frame)
        temp_frame.grid(row=2, column=1, sticky="w", pady=2)
        
        self.ComboBoxT = ttk.Combobox(temp_frame, state="readonly", values=list(range(1, 11)), width=10)
        self.ComboBoxT.set(3)
        self.ComboBoxT.pack(side=tk.LEFT, padx=(0, 10))
        tk.Label(temp_frame, text="(Recomendado 3 segundos)", fg="gray").pack(side=tk.LEFT)

        # =========================================================
        # 2. PANEL IZQUIERDO (Botones de acción directa)
        # =========================================================
        left_frame = tk.Frame(main_frame, width=120)
        left_frame.grid(row=1, column=0, sticky="ns", padx=(0, 15))
        
        tk.Label(left_frame, text="Acciones Directas").pack(pady=(0, 5), fill=tk.X)
        
        acciones = [
            ("Abortar", "A"), ("Open", "open"), ("Close", "close"), 
            ("Move 0", "move 0"), ("Move 1", "move 1"), ("Move 2", "move 2"), 
            ("Move 3", "move 3"), ("Move 4", "move 4"), ("Move 5", "move 5"),
            ("C_ON", "con"), ("C_OFF", "coff"), ("Auto", "auto"), ("Homing", "home")
        ]
        
        for texto_btn, comando in acciones:
            btn = tk.Button(left_frame, text=texto_btn, width=12,
                            command=lambda c=comando: self.robot.enviar_comando(c) if c != "A" else self.click_abortar(c))
            btn.pack(pady=2, fill=tk.X)
            if texto_btn == "Abortar":
                btn.config(bg="red", fg="white", font=("Arial", 9 ,"bold"))

        # =========================================================
        # 3. PANEL CENTRAL (Cajas de texto y Botones)
        # =========================================================
        center_frame = tk.Frame(main_frame)
        center_frame.grid(row=1, column=1, sticky="nsew")
        
        # Configuramos el center_frame para que ambas columnas crezcan igual
        center_frame.columnconfigure(0, weight=1)
        center_frame.columnconfigure(1, weight=1) 
        center_frame.rowconfigure(1, weight=1)

# --- Columna 0: Datos Enviados ---
        tk.Label(center_frame, text="Datos Enviados").grid(row=0, column=0, sticky="w")
        
        frame_enviar = tk.Frame(center_frame)
        frame_enviar.grid(row=1, column=0, sticky="nsew", padx=(0, 5), pady=(5, 0))
        
        Escrollbar = tk.Scrollbar(frame_enviar)
        Escrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.TextEnviar = tk.Text(frame_enviar, height=10, width=20, yscrollcommand=Escrollbar.set)
        self.TextEnviar.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        Escrollbar.config(command=self.TextEnviar.yview)

        # Sub-contenedor para agrupar los 3 botones de secuencias
        btn_frame_enviados = tk.Frame(center_frame)
        btn_frame_enviados.grid(row=2, column=0, sticky="w", padx=(0, 5), pady=(5, 0))

        self.btn_enviar = tk.Button(btn_frame_enviados, text="Enviar", width=10, command=self.click_enviar)
        self.btn_enviar.pack(side=tk.LEFT, padx=(0, 5))

        self.btn_cargar = tk.Button(btn_frame_enviados, text="Cargar", width=10, command=self.click_cargar_secuencia)
        self.btn_cargar.pack(side=tk.LEFT, padx=(0, 5))

        self.btn_guardar_sec = tk.Button(btn_frame_enviados, text="Guardar", width=10, command=self.click_guardar_secuencia)
        self.btn_guardar_sec.pack(side=tk.LEFT)


# --- Columna 1: Datos Recibidos ---
        tk.Label(center_frame, text="Datos Recibidos").grid(row=0, column=1, sticky="w")
        
        frame_recibidos = tk.Frame(center_frame)
        frame_recibidos.grid(row=1, column=1, sticky="nsew", padx=(5, 0), pady=(5, 0))
        
        Rscrollbar = tk.Scrollbar(frame_recibidos)
        Rscrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.TextRecibidos = tk.Text(frame_recibidos, height=10, width=30, yscrollcommand=Rscrollbar.set)
        self.TextRecibidos.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.TextRecibidos.insert("1.0", "Inicio del programa...\n")
        self.TextRecibidos.configure(state="disabled") 
        Rscrollbar.config(command=self.TextRecibidos.yview)

        # Botón debajo de Recibidos (Guardar Log de ejecución)
        self.btn_guardar_log = tk.Button(center_frame, text="Guardar Log", width=10, command=self.click_guardar_log)
        self.btn_guardar_log.grid(row=2, column=1, sticky="w", padx=(5, 0), pady=(5, 0))
        
        # =========================================================
        # 4. PANEL INFERIOR (Solo Resultados)
        # =========================================================
        bottom_frame = tk.Frame(main_frame)
        bottom_frame.grid(row=2, column=1, sticky="ew", pady=(15, 0))

        tk.Label(bottom_frame, text="Estado de envío:").pack(side=tk.LEFT, padx=(0, 5))
        self.lbl_resultado = tk.Label(bottom_frame, text="Esperando comandos...", fg="gray")
        self.lbl_resultado.pack(side=tk.LEFT)

    # =========================================================
    # LÓGICA DE LA INTERFAZ (Mantenida idéntica)
    # =========================================================
    def actualizar_texto_recibido(self, texto):
        self.TextRecibidos.configure(state="normal")
        self.TextRecibidos.insert(tk.END, texto)
        self.TextRecibidos.see(tk.END)
        self.TextRecibidos.configure(state="disabled")
    
    def mostrar_resultado(self, mensaje, color="green"):
        self.lbl_resultado.config(text=mensaje, fg=color)
        self.root.after(3000, lambda: self.lbl_resultado.config(text="Esperando comandos...", fg="gray"))

    def cambiar_estado(self, texto, color):
        self.TextoEstado.configure(state="normal")
        self.TextoEstado.delete("1.0", tk.END)
        self.TextoEstado.insert("1.0", texto)
        self.TextoEstado.configure(background=color, state="disabled")

    def click_conectar(self):
        puerto = self.comboBox1.get()
        if self.robot.conectar(puerto):
            self.cambiar_estado("Conectado", "LIME")
            messagebox.showinfo("Atención", "Puerto Conectado")
        else:
            messagebox.showerror("Error", "Error al conectar puerto")

    def click_desconectar(self):
        self.robot.desconectar()
        self.cambiar_estado("Desconectado", "red")
        messagebox.showinfo("Atención", "Puerto Desconectado")

    def click_abortar(self, cmd):
        self.robot.enviar_comando(cmd)
        messagebox.showwarning("Abortado", "Se envió comando de parada de emergencia")

    def click_enviar(self):
        if not self.robot.conectado:
            messagebox.showinfo("Atención", "Primero debe conectarse con el puerto COM seleccionado")
            return

        msj = self.TextEnviar.get("1.0", tk.END)
        lineas = msj.split("\n")
        tiempo_instruccion = int(self.ComboBoxT.get())

        threading.Thread(target=self.rutina_envio_secuencia, args=(lineas, tiempo_instruccion), daemon=True).start()

    def rutina_envio_secuencia(self, lineas, tiempo_instruccion, limpiar_caja=True):
        for comando in lineas:
            if comando.strip() == "":
                continue

            self.robot.buffer_respuestas = ""

            if "Run" in comando:
                self.robot.enviar_comando(comando)

                while "ok" not in self.robot.buffer_respuestas.lower():
                    time.sleep(0.2) 
                    if not self.robot.conectado: return

                self.root.after(0, lambda c=comando: self.mostrar_resultado(f"Programa '{c}' finalizado con éxito"))
            
            else:
                self.robot.enviar_comando(comando)
                
                # 1. ESPERA LÓGICA
                while "done" not in self.robot.buffer_respuestas.lower():
                    time.sleep(0.1)
                    if not self.robot.conectado: return

                self.root.after(0, lambda c=comando: self.mostrar_resultado(f"Comando '{c}' ejecutado"))

                # 2. ESPERA FÍSICA
                if "move" in comando.lower():
                    time.sleep(tiempo_instruccion)
                else:
                    time.sleep(0.5)

        if limpiar_caja:
            self.root.after(0, lambda: self.TextEnviar.delete("1.0", tk.END))

    def click_cargar_secuencia(self):
            filepath = askopenfilename(defaultextension="txt", filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
            if filepath:
                try:
                    with open(filepath, "r") as input_file:
                        text = input_file.read()
                        self.TextEnviar.delete("1.0", tk.END)
                        self.TextEnviar.insert("1.0", text)
                except Exception as e:
                    messagebox.showerror("Error", f"No se pudo cargar el archivo: {e}")

    def click_guardar_secuencia(self):
        filepath = asksaveasfilename(defaultextension="txt", filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
        if filepath:
            try:
                with open(filepath, "w") as output_file:
                    text = self.TextEnviar.get("1.0", tk.END)
                    output_file.write(text)
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo guardar la secuencia: {e}")

    def click_guardar_log(self):
        filepath = asksaveasfilename(defaultextension="txt", filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
        if filepath:
            try:
                with open(filepath, "w") as output_file:
                    text = self.TextRecibidos.get("1.0", tk.END) # Ahora guarda el Log real del robot
                    output_file.write(text)
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo guardar el log: {e}")

if __name__ == "__main__":
    ventana = tk.Tk()
    app = AplicacionGUI(ventana)
    ventana.mainloop()