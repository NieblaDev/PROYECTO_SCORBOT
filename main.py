# main.py
import ttkbootstrap as ttk
from gui.main_window import AplicacionGUI
import utils.config as config

def main():
    # Inicialización del estilo y la ventana raíz
    app_root = ttk.Window(themename=config.DEFAULT_THEME)
    
    # Instancia de la aplicación modularizada
    app = AplicacionGUI(app_root)
    
    # Inicio del loop principal
    app_root.mainloop()

if __name__ == "__main__":
    main()