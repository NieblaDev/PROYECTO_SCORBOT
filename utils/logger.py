# utils/logger.py
import os

class SessionLogger:
    @staticmethod
    def save_log(filepath, content):
        """Guarda el contenido de la terminal en un archivo de texto."""
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"Error al guardar log: {e}")
            return False

    @staticmethod
    def format_status_message(message):
        """Añade formato a los mensajes de estado del sistema."""
        return f"--- {message} ---"