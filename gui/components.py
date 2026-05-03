# gui/components.py
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.widgets.scrolled import ScrolledText

class TerminalWidget(ttk.Frame):
    """Componente reutilizable de terminal de texto."""
    def __init__(self, master, title, font=("Consolas", 10), bootstyle="secondary"):
        super().__init__(master)
        
        ttk.Label(self, text=title, font=("Helvetica", 10, "bold")).pack(anchor="w", pady=(0, 5))
        
        self.text_area = ScrolledText(
            self, 
            padding=5, 
            font=font, 
            bootstyle=bootstyle, 
            autohide=False
        )
        self.text_area.pack(fill=BOTH, expand=True)
        self.text_area.text.configure(state="disabled")

    def write(self, texto, clear=False):
        """Escribe texto en la terminal de forma segura."""
        self.text_area.text.configure(state="normal")
        if clear:
            self.text_area.delete("1.0", END)
        self.text_area.insert(END, texto)
        self.text_area.text.see(END)
        self.text_area.text.configure(state="disabled")

    def get_content(self):
        """Retorna todo el texto de la terminal."""
        return self.text_area.get("1.0", END)