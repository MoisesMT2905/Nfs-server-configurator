import os
import re
from typing import List, Dict, Tuple
from datetime import datetime

class ExportsConfigParser:
    """Parser para leer y escribir /etc/exports"""
    
    EXPORTS_FILE = '/etc/exports'
    BACKUP_DIR = '/etc/exports.backup'
    
    @staticmethod
    def leer_exports() -> List[str]:
        """Lee las exportaciones actuales del sistema"""
        try:
            if os.path.exists(ExportsConfigParser.EXPORTS_FILE):
                with open(ExportsConfigParser.EXPORTS_FILE, 'r') as f:
                    lineas = f.readlines()
                return [l.strip() for l in lineas if l.strip() and not l.startswith('#')]
            return []
        except PermissionError:
            raise PermissionError("No hay permisos para leer /etc/exports")
    
    @staticmethod
    def parsear_linea_export(linea: str) -> Tuple[str, List[Tuple[str, dict]]]:
        """
        Parsea una línea de exportación.
        Retorna: (directorio, [(cliente, opciones)])
        """
        # Formato: /dir cliente1(opción1,opción2) cliente2(opción3)
        match = re.match(r'^(\S+)\s+(.+)$', linea)
        if not match:
            return None, []
        
        directorio = match.group(1)
        clientes_str = match.group(2)
        
        clientes = []
        # Buscar patrones cliente(opciones)
        patron = r'(\S+?)\(([^)]*)\)'
        for cliente_match in re.finditer(patron, clientes_str):
            cliente = cliente_match.group(1)
            opciones_str = cliente_match.group(2)
            opciones = ExportsConfigParser._parsear_opciones(opciones_str)
            clientes.append((cliente, opciones))
        
        return directorio, clientes
    
    @staticmethod
    def _parsear_opciones(opciones_str: str) -> dict:
        """Parsea string de opciones en diccionario"""
        opciones = {}
        if not opciones_str:
            return opciones
        
        partes = opciones_str.split(',')
        for parte in partes:
            parte = parte.strip()
            if '=' in parte:
                clave, valor = parte.split('=', 1)
                opciones[clave.strip()] = valor.strip()
            else:
                opciones[parte] = True
        
        return opciones
    
    @staticmethod
    def generar_linea_export(directorio: str, cliente: str, opciones: dict) -> str:
        """Genera una línea de exportación válida"""
        opciones_str = ExportsConfigParser._generar_opciones_str(opciones)
        return f"{directorio} {cliente}({opciones_str})"
    
    @staticmethod
    def _generar_opciones_str(opciones: dict) -> str:
        """Convierte diccionario de opciones a string"""
        partes = []
        
        # Orden recomendado para las opciones
        orden = ['rw', 'ro', 'sync', 'async', 'no_root_squash', 'root_squash',
                'all_squash', 'no_subtree_check', 'subtree_check', 'insecure', 'secure']
        
        for opt in orden:
            if opciones.get(opt):
                partes.append(opt)
        
        # Agregar anonuid y anongid
        if opciones.get('anonuid'):
            partes.append(f"anonuid={opciones['anonuid']}")
        if opciones.get('anongid'):
            partes.append(f"anongid={opciones['anongid']}")
        
        # Agregar opciones no listadas
        for opt, valor in opciones.items():
            if opt not in orden and opt not in ['anonuid', 'anongid']:
                if valor is True:
                    partes.append(opt)
        
        return ','.join(partes)
    
    @staticmethod
    def crear_backup() -> str:
        """Crea backup de /etc/exports"""
        try:
            if os.path.exists(ExportsConfigParser.EXPORTS_FILE):
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_file = f"{ExportsConfigParser.EXPORTS_FILE}.{timestamp}"
                
                with open(ExportsConfigParser.EXPORTS_FILE, 'r') as original:
                    contenido = original.read()
                
                with open(backup_file, 'w') as backup:
                    backup.write(contenido)
                
                return backup_file
        except PermissionError:
            raise PermissionError("No hay permisos para crear backup")
        return None
    
    @staticmethod
    def restaurar_backup(backup_file: str) -> bool:
        """Restaura /etc/exports desde un backup"""
        try:
            if not os.path.exists(backup_file):
                return False
            
            with open(backup_file, 'r') as bak:
                contenido = bak.read()
            
            with open(ExportsConfigParser.EXPORTS_FILE, 'w') as original:
                original.write(contenido)
            
            return True
        except PermissionError:
            raise PermissionError("No hay permisos para restaurar backup")

# English wrappers for GUI compatibility
def build_export_line(path: str, clients: List[str], options: dict) -> str:
    """Build export line(s) for multiple clients (wrapper for GUI)"""
    lines = []
    for client in clients:
        line = ExportsConfigParser.generar_linea_export(path, client, options)
        lines.append(line)
    return '\n'.join(lines)
