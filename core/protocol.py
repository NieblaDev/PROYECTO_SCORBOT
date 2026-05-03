# core/protocol.py

class ACLCommands:
    """Definición de comandos estándar para el controlador ACL."""
    ABORT = "a"
    HOME = "home"
    OPEN_GRIPPER = "open"
    CLOSE_GRIPPER = "close"
    ECHO_OFF = "|echo"
    
    @staticmethod
    def format_command(cmd: str) -> bytes:
        """Añade el terminador de carro requerido por el Scorbot."""
        return (cmd.strip() + "\r").encode('ascii')

class ResponseParser:
    """Utilidades para interpretar las respuestas del controlador."""
    PROMPT = ">"
    DONE = "Done."
    
    @staticmethod
    def is_ready(buffer: str) -> bool:
        """Verifica si el controlador está listo para un nuevo comando."""
        return ResponseParser.PROMPT in buffer