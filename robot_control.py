import serial
import threading
import time

class ScorbotController:
    def __init__(self, callback_recepcion=None):
        self.ser = None
        self.callback = callback_recepcion
        self.conectado = False
        self.buffer_respuestas = ""
        self.puerto_lock = threading.Lock() 

    def conectar(self, puerto):
        if self.conectado:
            self.desconectar()
            time.sleep(0.5) # Pausa larga para que el OS libere la memoria

        try:
            # =========================================================
            # INSTANCIACIÓN ATÓMICA: Todo en una sola instrucción.
            # Al pasar el 'port' aquí, PySerial hace el .open() automáticamente
            # mediante una sola llamada a la API de Windows, evitando colapsos.
            # =========================================================
            self.ser = serial.Serial(
                port=puerto,
                baudrate=9600,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=0.1
            )
            
            self.conectado = True
            self.buffer_respuestas = ""
            
            # A veces limpiar el buffer muy rápido crashea el driver. Lo hacemos con cuidado.
            with self.puerto_lock:
                try:
                    self.ser.reset_input_buffer()
                    self.ser.reset_output_buffer()
                except:
                    pass
            
            # Lanzamos el hilo de escucha
            threading.Thread(target=self._hilo_escucha, daemon=True).start()
            
            # Despertar al Scorbot
            time.sleep(0.2)
            self.enviar_comando("|echo")
            
            return True
            
        except Exception as e:
            print(f"Fallo en inicio de conexión: {e}")
            self.conectado = False
            if self.ser:
                try:
                    self.ser.close()
                except:
                    pass
            return False

    def desconectar(self):
        self.conectado = False 
        time.sleep(0.2) 
        
        with self.puerto_lock:
            if self.ser and self.ser.is_open:
                try:
                    self.ser.close()
                except:
                    pass
                self.ser = None

    def enviar_comando(self, comando):
        cmd_completo = comando.strip()
        if self.conectado and self.ser and self.ser.is_open:
            with self.puerto_lock: 
                try:
                    self.ser.write(cmd_completo.encode() + b"\r")
                except Exception as e:
                    print(f"Error enviando comando: {e}")
            
    def _hilo_escucha(self):
        while self.conectado:
            with self.puerto_lock: 
                try:
                    if self.ser and self.ser.is_open and self.ser.in_waiting > 0:
                        datos_crudos = self.ser.read_all()
                        datos = datos_crudos.decode('ascii', errors='ignore')
                        
                        if datos:
                            self.buffer_respuestas += datos
                            if self.callback:
                                self.callback(datos)
                except Exception:
                    pass
            
            time.sleep(0.05)