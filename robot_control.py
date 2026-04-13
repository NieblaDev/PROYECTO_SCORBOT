import serial
import threading
import time

class ScorbotController:
    def __init__(self, callback_recepcion=None):
        self.ser = serial.Serial()
        self.callback = callback_recepcion
        self.conectado = False
        self.buffer_respuestas = ""

    def conectar(self, puerto):
        try:
            if not self.ser.is_open:
                self.ser.baudrate = 9600
                self.ser.bytesize = 8
                self.ser.parity = "N"
                self.ser.stopbits = serial.STOPBITS_ONE
                self.ser.port = puerto
                self.ser.timeout = 0.5
                self.ser.open()
                self.conectado = True
                
                threading.Thread(target=self._hilo_escucha, daemon=True).start()
                return True
        except Exception as e:
            print(f"Error de conexión: {e}")
            return False

    def desconectar(self):
        self.conectado = False
        if self.ser.is_open:
            self.ser.close()

    def enviar_comando(self, comando):
        cmd_completo = comando.strip() + "\r"
        
        if self.ser.is_open:
            self.ser.write(cmd_completo.encode('ascii'))
            
    def _hilo_escucha(self):
        """Este hilo corre en segundo plano sin congelar la interfaz"""
        while self.conectado and self.ser.is_open:
            try:
                if self.ser.in_waiting > 0:
                    datos = self.ser.read(self.ser.in_waiting).decode('ascii', errors='ignore')
                    self.buffer_respuestas += datos # Acumulamos para la secuencia automática
                    
                    if self.callback:
                        self.callback(datos)
            except Exception as e:
                pass
            time.sleep(0.05) # Pequeña pausa para no saturar el procesador
