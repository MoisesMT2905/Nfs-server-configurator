#!/usr/bin/env python3
"""
Cliente de ejemplo para probar el helper D-Bus.

Este script puede ser ejecutado por un usuario normal para probar
la comunicación con el helper privilegiado vía D-Bus y polkit.

Uso:
    python3 client_example.py
"""

import sys
import os

try:
    from pydbus import SystemBus
except ImportError:
    print("Error: pydbus no está instalado")
    print("Instale con: sudo apt install python3-pydbus")
    sys.exit(1)


def test_apply_configuration():
    """Prueba el método ApplyConfiguration del helper"""
    
    # Configuración de ejemplo para prueba
    test_config = """/tmp/test_share 192.168.1.0/24(rw,sync,no_subtree_check)
/tmp/test_public *(ro,all_squash,anonuid=65534,anongid=65534)
"""
    
    print("=" * 60)
    print("Cliente de prueba para yast2-nfs-helper")
    print("=" * 60)
    print()
    print("Este cliente intentará:")
    print("1. Conectar al helper D-Bus (org.yast2.NFSHelper)")
    print("2. Solicitar aplicar una configuración de prueba")
    print("3. Polkit solicitará autorización administrativa")
    print()
    print("Configuración de prueba a aplicar:")
    print("-" * 60)
    print(test_config)
    print("-" * 60)
    print()
    
    input("Presione Enter para continuar...")
    print()
    
    try:
        # Conectar al bus del sistema
        print("Conectando al bus del sistema D-Bus...")
        bus = SystemBus()
        
        # Obtener el objeto del helper
        print("Obteniendo proxy del helper...")
        helper = bus.get('org.yast2.NFSHelper')
        
        print("Helper obtenido correctamente")
        print()
        
        # Llamar al método ApplyConfiguration
        print("Invocando ApplyConfiguration...")
        print("(Polkit puede solicitar autenticación administrativa)")
        print()
        
        ok, message = helper.ApplyConfiguration(test_config)
        
        print()
        print("=" * 60)
        print("RESULTADO:")
        print("=" * 60)
        print(f"Éxito: {ok}")
        print(f"Mensaje: {message}")
        print("=" * 60)
        
        if ok:
            print()
            print("✓ Configuración aplicada exitosamente")
            print()
            print("Verificar con: sudo exportfs -v")
            return 0
        else:
            print()
            print("✗ Error al aplicar configuración")
            return 1
            
    except Exception as e:
        print()
        print("=" * 60)
        print("ERROR:")
        print("=" * 60)
        print(f"Excepción: {type(e).__name__}")
        print(f"Mensaje: {str(e)}")
        print("=" * 60)
        print()
        print("Posibles causas:")
        print("- El servicio helper no está ejecutándose")
        print("  (sudo systemctl start yast2-nfs-helper)")
        print("- La política polkit no está instalada")
        print("- El usuario no tiene permisos para autenticarse")
        return 1


def test_list_service():
    """Lista información sobre el servicio D-Bus"""
    print()
    print("=" * 60)
    print("Información del servicio D-Bus")
    print("=" * 60)
    print()
    print("Bus name: org.yast2.NFSHelper")
    print("Object path: /org/yast2/NFSHelper")
    print("Interface: org.yast2.NFSHelper")
    print()
    print("Métodos disponibles:")
    print("  - ApplyConfiguration(exports_text: str) -> (bool, str)")
    print()
    print("Para verificar que el servicio está corriendo:")
    print("  systemctl status yast2-nfs-helper")
    print()
    print("Para ver logs del servicio:")
    print("  journalctl -u yast2-nfs-helper -f")
    print()


def main():
    """Función principal"""
    print()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--info':
        test_list_service()
        return 0
    
    return test_apply_configuration()


if __name__ == '__main__':
    sys.exit(main())
