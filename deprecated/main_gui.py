import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.filedialog import asksaveasfilename
import threading
import time
from robot_control import ScorbotController

class AplicacionGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Scorbot Terminal")
        self.root.geometry("800x600")
        self.root.minsize(800, 600)
        
        try:
            self.root.iconbitmap("bot.ico")
        except:
            pass
    
        self.robot = ScorbotController(callback_recepcion=self.actualizar_texto_recibido)
        self.configurar_interfaz()

    def configurar_interfaz(self):
        # --- Estado ---
        tk.Label(self.root, text="Estado :").place(x=15, y=15)
        self.TextoEstado = tk.Text(self.root, height=1, width=17, bg="white")
        self.TextoEstado.insert("1.0", "DESCONECTADO")
        self.TextoEstado.configure(state="disabled")
        self.TextoEstado.place(x=120, y=15)

        # --- Conexión ---
        tk.Label(self.root, text="Puerto :").place(x=15, y=40)

        self.comboBox1 = ttk.Combobox(self.root, state="readonly", values=[f"COM{i}" for i in range(1, 10)])
        self.comboBox1.set("COM5") 
        self.comboBox1.place(x=120, y=40, width=140, height=22)

        self.btn_conectar = tk.Button(self.root, text="Conectar", command=self.click_conectar)
        self.btn_conectar.place(x=270, y=40)
        tk.Label(self.root, text="/").place(x=330,y=42)
        self.btn_desconectar = tk.Button(self.root, text="Desconectar", command=self.click_desconectar)
        self.btn_desconectar.place(x=340, y=40)

        # --- Temporizador ---
        tk.Label(self.root, text="Temporizador :").place(x=15, y=65)
        self.ComboBoxT = ttk.Combobox(self.root, state="readonly", values=list(range(3, 11)))
        self.ComboBoxT.set(3)
        self.ComboBoxT.place(x=120, y=65, width=140, height=22)
        tk.Label(self.root, text="(Recomendado mínimo 3 segundos)", fg="gray").place(x=265, y=67)

        # --- Botones de Acción directos ---
        tk.Label(self.root, text="Aciones directas").place(x=15, y=115)
        acciones = [
            ("Abortar", "A"), ("Open", "open"), ("Close", "close"), 
            ("Move 0", "move 0"), ("Move 1", "move 1"), ("Move 2", "move 2"), ("Move 3", "move 3"), ("Move 4", "move 4"), ("Move 5", "move 5"),
            ("C_ON", "con"), ("C_OFF", "coff"), ("Auto", "auto"), ("Homing", "home")
        ]
        y_pos = 135
        for texto_btn, comando in acciones:
            
            btn = tk.Button(self.root, text=texto_btn, width=10, 
                            command=lambda c=comando: self.robot.enviar_comando(c) if c != "A" else self.click_abortar(c))
            btn.place(x=15, y=y_pos)
            if texto_btn == "Abortar":
                btn.config(bg="red", fg="white", font=("Arial", 9 ,"bold")) # Destacamos el abortar por seguridad
            y_pos += 30

        # --- Cajas de Texto y Botones Inferiores ---
        # Caja de Enviados
        tk.Label(self.root, text="Datos Enviados").place(x=120, y=100)
        frame_enviar = tk.Frame(self.root)
        frame_enviar.place(x=120, y=120)
        Escrollbar = tk.Scrollbar(frame_enviar)
        Escrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.TextEnviar = tk.Text(frame_enviar, height=24, width=25, yscrollcommand=Escrollbar.set)
        self.TextEnviar.pack(side=tk.LEFT, fill=tk.BOTH)
        Escrollbar.config(command=self.TextEnviar.yview)

        # Caja de Recibidos
        tk.Label(self.root, text="Datos Recibidos").place(x=350, y=100)
        frame_recibidos = tk.Frame(self.root)
        frame_recibidos.place(x=350, y=120)
        Rscrollbar = tk.Scrollbar(frame_recibidos)
        Rscrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.TextRecibidos = tk.Text(frame_recibidos, height=24, width=50, yscrollcommand=Rscrollbar.set)
        self.TextRecibidos.pack(side=tk.LEFT, fill=tk.BOTH)
        self.TextRecibidos.insert("1.0", "Inicio del programa...")
        self.TextRecibidos.configure(state="disabled")
        Rscrollbar.config(command=self.TextRecibidos.yview)

        # --- Botones Inferiores ---
        self.btn_enviar = tk.Button(self.root, text="Enviar Secuencia", command=self.click_enviar)
        self.btn_enviar.place(x=120, y=520)

        self.btn_guardar = tk.Button(self.root, text="Guardar Log", command=self.click_guardar)
        self.btn_guardar.place(x=350, y=520)

        # --- Texto de Resultados ---
        tk.Label(self.root, text="Estado de envío:").place(x=15, y=560)
        self.lbl_resultado = tk.Label(self.root, text="Esperando comandos...", fg="gray")
        self.lbl_resultado.place(x=120, y=560)

    # --- Funciones de Lógica de la Interfaz ---
    def actualizar_texto_recibido(self, texto):

        # Insertamos el texto al FINAL (tk.END) en lugar de al principio ("1.0")
        self.root.after(0, lambda: self.TextRecibidos.insert(tk.END, texto))
        
        # Hacemos que la caja de texto baje automáticamente (auto-scroll)
        self.root.after(0, lambda: self.TextRecibidos.see(tk.END))
    
    def mostrar_resultado(self, mensaje, color="green"):
        # Actualiza el texto y el color del label
        self.lbl_resultado.config(text=mensaje, fg=color)
        
        # Limpiar el mensaje después de 3 segundos
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
            messagebox.showinfo(message="Puerto Conectado")
        else:
            messagebox.showerror(message="Error al conectar puerto")

    def click_desconectar(self):
        self.robot.desconectar()
        self.cambiar_estado("Desconectado", "red")
        messagebox.showinfo(message="Puerto Desconectado")

    def click_abortar(self, cmd):
        self.robot.enviar_comando(cmd)
        messagebox.showwarning("Abortado", "Se envió comando de parada de emergencia (A)")

    def click_enviar(self):
        if not self.robot.conectado:
            messagebox.showwarning(message="Debe conectar el puerto primero." ,title="Atención")
            return

        msj = self.TextEnviar.get("1.0", tk.END)
        lineas = msj.split("\n")
        tiempo_extra = int(self.ComboBoxT.get())

        # INICIAMOS UN HILO para no congelar la ventana durante las pausas
        threading.Thread(target=self.rutina_envio_secuencia, args=(lineas, tiempo_extra), daemon=True).start()

    def rutina_envio_secuencia(self, lineas, tiempo_extra, limpiar_caja=True):
        for comando in lineas:
            if comando.strip() == "":
                continue

            self.robot.buffer_respuestas = "" # Limpiamos el buffer histórico

            if "Run" in comando:
                self.robot.enviar_comando(comando)

                while "ok" not in self.robot.buffer_respuestas.lower():
                    time.sleep(0.2) 
                    if not self.robot.conectado: return

                self.root.after(0, lambda c=comando: self.mostrar_resultado(f"Programa '{c}' finalizado con éxito"))

            
            else:
                tiempo_ejecucion = 0 + tiempo_extra

                self.robot.enviar_comando(comando)
                
                # 1. ESPERA LÓGICA - Esperamos a que el robot confirme recibo de información
                while "done" not in self.robot.buffer_respuestas.lower():
                    time.sleep(0.1)
                    if not self.robot.conectado: return

                self.root.after(0, lambda c=comando: self.mostrar_resultado(f"Comando '{c}' ejecutado"))

                # 2. ESPERA FÍSICA - Le damos tiempo al robot de moverse
                if "move" in comando.lower():
                    time.sleep(tiempo_extra)
                else:
                    time.sleep(1)

        if limpiar_caja:
            self.root.after(0, lambda: self.TextEnviar.delete("1.0", tk.END))

    def click_guardar(self):
        filepath = asksaveasfilename(defaultextension="txt", filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
        if filepath:
            with open(filepath, "w") as output_file:
                text = self.TextEnviar.get("1.0", tk.END)
                output_file.write(text)

if __name__ == "__main__":
    ventana = tk.Tk()
    app = AplicacionGUI(ventana)
    ventana.mainloop()