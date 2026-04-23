import serial
import threading
import time

class ScorbotController:
    def __init__(self, callback_recepcion=None):
        self.ser = None
        self.callback = callback_recepcion
        self.conectado = False
        self.buffer_respuestas = ""
        # Eliminamos el puerto_lock, volveremos a confiar en la gestión nativa de PySerial

    def conectar(self, puerto):
        if self.conectado:
            self.desconectar()

        try:
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
            
            threading.Thread(target=self._hilo_escucha, daemon=True).start()
            
            time.sleep(0.5)
            self.enviar_comando("|echo")
            
            return True
            
        except Exception as e:
            print(f"Fallo en inicio de conexión: {e}")
            self.conectado = False
            return False

    def desconectar(self):
        self.conectado = False 
        time.sleep(0.5) 
        
        if self.ser and self.ser.is_open:
            try:
                self.ser.close()
            except Exception as e:
                print(f"Error al cerrar el puerto: {e}")
            finally:
                self.ser = None

    def enviar_comando(self, comando):
        if self.conectado and self.ser and self.ser.is_open:
            try:
                comando = comando.strip()
                self.ser.write(comando.encode('ascii') + b"\r")
            except Exception as e:
                print(f"Error de envío: {e}")
            
    def _hilo_escucha(self):
        while self.conectado:
            try:
                if self.ser and self.ser.is_open and self.ser.in_waiting > 0:
                    datos_crudos = self.ser.read(self.ser.in_waiting)
                    datos = datos_crudos.decode('ascii', errors='ignore')
                    
                    if datos:
                        self.buffer_respuestas += datos
                        if self.callback:
                            self.callback(datos)
            except serial.SerialException:
                self.conectado = False
                print("Conexión serial perdida.")
                break
            except Exception:
                pass
            
            time.sleep(0.05)