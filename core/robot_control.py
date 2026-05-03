# core/robot_control.py
import serial
import threading
import time
import queue
from .protocol import ACLCommands

class ScorbotController:
    def __init__(self, callback_recepcion=None):
        self.ser = None
        self.callback = callback_recepcion
        self.conectado = False

    def conectar(self, puerto, baudrate=9600):
        if self.conectado:
            self.desconectar()
        try:
            self.ser = serial.Serial(
                port=puerto,
                baudrate=baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=0.1
            )
            self.conectado = True
            self.cola_comandos.queue.clear()
            
            # Iniciamos el hilo inteligente
            threading.Thread(target=self._hilo_gestor_serial, daemon=True).start()
            return True
        except Exception as e:
            print(f"Error de conexión: {e}")
            return False

    def desconectar(self):
        self.conectado = False 
        time.sleep(0.2) 
        if self.ser and self.ser.is_open:
            self.ser.close()
            self.ser = None

    def encolar_comando(self, comando):
        """Agrega el comando a la fila. El gestor lo enviará cuando sea seguro."""
        self.cola_comandos.put(comando)

    def abortar(self):
        """Borra la fila y envía el aborto directo al robot."""
        self.cola_comandos.queue.clear()
        if self.conectado and self.ser and self.ser.is_open:
            try:
                self.ser.write(b"a\r")
                self.ser.flush()
            except:
                pass

    def _hilo_gestor_serial(self):
        while self.conectado:
            try:
                # 1. Sacamos un comando de la fila (espera 0.05s)
                comando = self.cola_comandos.get(timeout=0.05)
                
                if self.ser and self.ser.is_open:
                    # Lo enviamos físicamente al Scorbot
                    self.ser.write((comando.strip() + '\r').encode('ascii'))
                    self.ser.flush()
                    
                    # 2. ESPERA INTELIGENTE
                    respuesta_actual = ""
                    while self.conectado:
                        if self.ser.in_waiting > 0:
                            datos = self.ser.read(self.ser.in_waiting).decode('ascii', errors='ignore')
                            if self.callback:
                                # Enviamos a la GUI limpiando los retornos de carro
                                self.callback(datos.replace('\r', ''))
                            
                            respuesta_actual += datos
                            
                            # LA MAGIA: 
                            # Al usar strip().endswith('>'), ignoramos el "> move 1" del inicio
                            # y solo nos destrabamos cuando vemos el ">" final y solitario
                            # que aparece estrictamente después del "Done."
                            if respuesta_actual.strip().endswith('>'):
                                break # ¡Terminó la transacción! Vamos por el siguiente comando
                        
                        time.sleep(0.02)
                        
            except queue.Empty:
                # Si no hay comandos en fila, solo escuchamos el puerto pasivamente
                if self.ser and self.ser.is_open and self.ser.in_waiting > 0:
                    try:
                        datos = self.ser.read(self.ser.in_waiting).decode('ascii', errors='ignore')
                        if self.callback:
                            self.callback(datos.replace('\r', ''))
                    except:
                        pass
            except Exception as e:
                print(f"Error en comunicación: {e}")
                self.conectado = False
                break
                
            time.sleep(0.01)