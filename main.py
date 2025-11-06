#!/usr/bin/env python3
"""
Configurador Gráfico de Servidores NFS
Sistema de configuración intuitivo inspirado en YaST2
"""

import tkinter as tk
import sys
import os

# Agregar directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.gui.main_window import NFSConfiguratorGUI
from src.backend.nfs_manager import NFSManager

def main():
    """Función principal"""
    
    # Verificar si se ejecuta en Linux
    if sys.platform != 'linux':
        print("Este programa solo funciona en Linux")
        sys.exit(1)
    
    # Advertencia sobre permisos
    if not NFSManager.verificar_permisos():
        print("⚠️  Advertencia: Este programa requiere permisos de root para aplicar cambios.")
        print("Puede ejecutarse sin permisos en modo lectura.")
        print("Para funcionalidad completa, ejecute con: sudo python3 main.py\n")
    
    # Crear ventana principal
    root = tk.Tk()
    
    # Crear aplicación
    app = NFSConfiguratorGUI(root)
    
    # Iniciar loop de eventos
    root.mainloop()

if __name__ == "__main__":
    main()
