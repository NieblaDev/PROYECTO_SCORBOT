import time
import threading

class ScorbotController:
    def __init__(self, callback_recepcion=None):
        """
        Inicializa el controlador simulado del Scorbot.
        """
        self.callback_recepcion = callback_recepcion
        self.conectado = False
        self.buffer_respuestas = ""

    def conectar(self, puerto):
        """
        Simula una conexión exitosa al puerto COM.
        """
        # Simulamos que siempre logra conectarse
        self.conectado = True
        
        # Mensaje clásico de inicio del controlador ACL
        mensaje_bienvenida = f"\nConectado a {puerto} (MODO SIMULACIÓN)\nScorbot-ER IX - Advanced Control Language V 1.0\n>"
        
        self.buffer_respuestas = mensaje_bienvenida
        if self.callback_recepcion:
            self.callback_recepcion(mensaje_bienvenida)
            
        return True

    def desconectar(self):
        """
        Simula la desconexión del puerto.
        """
        self.conectado = False
        if self.callback_recepcion:
            self.callback_recepcion("\nDesconectado del puerto serial.\n")

    def enviar_comando(self, comando):
        """
        Simula el envío de un comando y gestiona tiempos de espera falsos
        para que la interfaz sienta que está controlando hardware real.
        """
        if not self.conectado:
            return

        # 1. Eco: Mostrar lo que enviamos en la consola de recepción
        eco = f"{comando}\n"
        if self.callback_recepcion:
            self.callback_recepcion(eco)

        # 2. Iniciar un hilo simulado para no congelar la GUI
        # Esto emula el tiempo que tardaría el brazo físico en moverse
        threading.Thread(target=self._simular_accion_robot, args=(comando,), daemon=True).start()

    def _simular_accion_robot(self, comando):
        """
        Rutina interna que finge el tiempo de movimiento mecánico.
        """
        comando_lower = comando.lower().strip()
        
        # Asignamos tiempos de espera simulados según la acción
        if "home" in comando_lower:
            tiempo_simulado = 4.0  # Homing es un proceso largo
        elif "moved" in comando_lower or "move" in comando_lower:
            tiempo_simulado = 2.0  # Moverse toma un par de segundos
        elif "open" in comando_lower or "close" in comando_lower:
            tiempo_simulado = 1.0  # Abrir/cerrar pinza es rápido
        else:
            tiempo_simulado = 0.5  # Lectura de variables o comandos simples
            
        # Fingimos que los motores están trabajando
        time.sleep(tiempo_simulado)
        
        # 3. Construimos la respuesta del controlador (Done. y el prompt >)
        respuesta = "Done.\n>"
        
        # 4. Inyectamos al buffer (vital para destrabar el while en main_gui.py)
        self.buffer_respuestas += respuesta
        
        # 5. Enviamos la respuesta a la caja de texto de la GUI
        if self.callback_recepcion:
            self.callback_recepcion(respuesta)