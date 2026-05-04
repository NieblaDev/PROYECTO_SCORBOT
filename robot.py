import time
import random

try:
    import serial
except ImportError:
    serial = None

class ScorbotController:
    """Clase para manejar la comunicación real con el SCORBOT vía RS232."""
    def __init__(self):
        self.ser = None
        self.conectado = False

    def conectar(self, puerto: str, baudrate: int = 9600) -> bool:
        if serial is None:
            return False
        try:
            self.ser = serial.Serial(
                port=puerto,
                baudrate=baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=0.2
            )
            self.conectado = True
            return True
        except Exception as e:
            print("Error conectando:", e)
            self.ser = None
            self.conectado = False
            return False

    def desconectar(self):
        if self.ser and self.ser.is_open:
            self.ser.close()
        self.ser = None
        self.conectado = False

    def enviar_comando(self, cmd: str) -> str:
        if not self.conectado:
            return ""
        
        # Formato básico para comandos ACL (normalmente terminan en retorno de carro)
        cmd_str = f"{cmd.strip()}\r"
        
        try:
            self.ser.write(cmd_str.encode('ascii'))
            self.ser.flush()
            time.sleep(0.05)
            # Leer respuesta
            data = self.ser.read_all()
            return data.decode("ascii", errors="ignore") if data else ""
        except Exception as e:
            print("Error enviando:", e)
            return ""

    def abortar(self):
        """Envía el comando de abortar 'a' o Ctrl+A dependiendo del protocolo, aquí usamos 'a' como ejemplo"""
        if self.conectado:
            try:
                self.ser.write(b"a\r")
                self.ser.flush()
            except:
                pass

class MockScorbotController:
    """Clase para simular el comportamiento del SCORBOT cuando no hay hardware."""
    def __init__(self):
        self.conectado = False
        self.respuestas_mock = {
            "HOME": "Homing started...\nHoming complete.\n>",
            "SPEED": "Speed set to {}%\n>",
            "MOVE": "Moving to point...\nDone.\n>",
            "OPEN": "Gripper open.\n>",
            "CLOSE": "Gripper closed.\n>",
        }

    def conectar(self, puerto: str) -> bool:
        # Simulamos que la conexión toma un pequeño tiempo y luego tiene éxito
        time.sleep(0.5)
        self.conectado = True
        return True

    def desconectar(self):
        self.conectado = False

    def enviar_comando(self, cmd: str) -> str:
        if not self.conectado:
            return ""
        
        cmd_upper = cmd.strip().upper()
        # Generar una respuesta mock según el comando
        for key, resp in self.respuestas_mock.items():
            if cmd_upper.startswith(key):
                # Simular tiempo de procesamiento
                time.sleep(0.1)
                return f"\n{cmd}\n{resp}"
                
        # Respuesta por defecto para comandos no mapeados
        time.sleep(0.1)
        return f"\n{cmd}\nExecuted {cmd}.\n>"

    def abortar(self):
        # Simular comportamiento de abortar
        pass
