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
                    
                    # 1. Transformamos el texto a una cadena de bits ASCII 
                    # 2. Le concatenamos el bit de "Enter" que requiere el controlador SCORBOT
                    instruccion_bits = comando.encode('ascii') + b"\r"
                    
                    # 3. Escribimos la instrucción en el puerto serial
                    self.ser.write(instruccion_bits)
                    
                    # 4. CRÍTICO: Obligamos al puerto a vaciar su buffer y enviar el paquete 
                    # completo inmediatamente, evitando que el Scorbot lo reciba entrecortado.
                    self.ser.flush() 
                    
                except Exception as e:
                    print(f"Error de envío: {e}")
                
    def _hilo_escucha(self):
        buffer_linea = "" # Almacenador temporal para formar frases completas
        
        while self.conectado:
            try:
                if self.ser and self.ser.is_open and self.ser.in_waiting > 0:
                    datos_crudos = self.ser.read(self.ser.in_waiting)
                    # Decodificamos los bits de respuesta a texto
                    datos = datos_crudos.decode('ascii', errors='ignore')
                    
                    if datos:
                        # Actualizamos el historial global para la lógica interna (como tu rutina_envio)
                        self.buffer_respuestas += datos
                        
                        # Sumamos la información al buffer local para la Interfaz Gráfica
                        buffer_linea += datos
                        
                        # Si en el texto recibido viene un Enter (\r o \n) o el símbolo de espera del Scorbot (>)
                        # significa que el mensaje está completo y es hora de mostrarlo.
                        if '\r' in buffer_linea or '\n' in buffer_linea or '>' in buffer_linea:
                            if self.callback:
                                self.callback(buffer_linea)
                            # Vaciamos el acumulador para la siguiente frase
                            buffer_linea = "" 
                            
            except serial.SerialException:
                self.conectado = False
                print("Conexión serial perdida.")
                break
            except Exception:
                pass
            
            # Bajamos el tiempo de espera de 0.05 a 0.02 para que reaccione más rápido
            # pero sin saturar el procesador de tu computadora
            time.sleep(0.02)