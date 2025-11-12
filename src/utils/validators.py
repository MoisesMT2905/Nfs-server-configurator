import os
import re
import socket
from ipaddress import IPv4Network, IPv4Address
from typing import Tuple, List

class NFSValidator:
    """Validador de configuraciones NFS"""
    
    # Opciones NFS válidas agrupadas
    PERMISSION_GROUPS = {
        'acceso': ['rw', 'ro'],
        'sincronizacion': ['sync', 'async'],
        'root_squash': ['no_root_squash', 'root_squash'],
        'subtree': ['no_subtree_check', 'subtree_check'],
        'puertos': ['insecure', 'secure']
    }
    
    INDEPENDENT_OPTIONS = ['all_squash']
    ALL_OPTIONS = sum(PERMISSION_GROUPS.values(), []) + INDEPENDENT_OPTIONS
    
    DEPENDENCIES = {
        'anonuid': 'all_squash',
        'anongid': 'all_squash'
    }
    
    @staticmethod
    def validar_directorio(ruta: str) -> Tuple[bool, str]:
        """Valida que el directorio exista y sea accesible"""
        if not ruta:
            return False, "Directorio no especificado"
        
        if ruta == '/':
            return False, "No se puede exportar el directorio raíz"
        
        if not os.path.isabs(ruta):
            return False, "La ruta debe ser absoluta"
        
        if not os.path.exists(ruta):
            return False, f"Directorio no existe: {ruta}"
        
        if not os.path.isdir(ruta):
            return False, f"No es un directorio: {ruta}"
        
        if not os.access(ruta, os.R_OK):
            return False, f"Sin permisos de lectura: {ruta}"
        
        return True, "Directorio válido"
    
    @staticmethod
    def validar_cliente(cliente: str) -> Tuple[bool, str]:
        """Valida formato de cliente (IP, subnet, hostname, wildcard)"""
        if not cliente:
            return False, "Cliente no especificado"
        
        cliente = cliente.strip()
        
        # Wildcard permitido
        if cliente == '*':
            return True, "Wildcard válido"
        
        # Netgroup (comienza con @)
        if cliente.startswith('@'):
            return True, "Netgroup válido"
        
        # Intenta validar como IP
        if '/' in cliente:
            try:
                IPv4Network(cliente, strict=False)
                return True, "Subred válida"
            except ValueError:
                return False, f"Subred inválida: {cliente}"
        
        # Intenta validar como IP simple
        try:
            IPv4Address(cliente)
            return True, "IP válida"
        except ValueError:
            pass
        
        # Intenta validar como hostname
        if re.match(r'^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$', cliente):
            return True, "Hostname válido"
        
        return False, f"Formato de cliente inválido: {cliente}"
    
    @staticmethod
    def validar_opciones(opciones: dict) -> Tuple[bool, List[str]]:
        """Valida que las opciones sean válidas y no conflictúen"""
        errores = []
        opciones_seleccionadas = [opt for opt, val in opciones.items() if val]
        
        # Validar que no haya opciones inválidas
        opciones_validas = set(NFSValidator.ALL_OPTIONS) | {'anonuid', 'anongid'}
        for opt in opciones_seleccionadas:
            if opt not in opciones_validas:
                errores.append(f"Opción desconocida: {opt}")
        
        # Validar grupos mutuamente excluyentes
        for grupo, opciones_grupo in NFSValidator.PERMISSION_GROUPS.items():
            seleccionadas = [o for o in opciones_grupo if opciones.get(o, False)]
            if len(seleccionadas) > 1:
                errores.append(f"Solo una opción permitida en {grupo}: {', '.join(seleccionadas)}")
        
        # Validar dependencias
        for opcion, depende_de in NFSValidator.DEPENDENCIES.items():
            if opciones.get(opcion) and not opciones.get(depende_de):
                errores.append(f"{opcion} requiere {depende_de} activado")
        
        # Validar anonuid y anongid son números
        if opciones.get('anonuid'):
            try:
                int(opciones.get('anonuid', 0))
            except ValueError:
                errores.append("anonuid debe ser un número (UID)")
        
        if opciones.get('anongid'):
            try:
                int(opciones.get('anongid', 0))
            except ValueError:
                errores.append("anongid debe ser un número (GID)")
        
        return len(errores) == 0, errores
    
    @staticmethod
    def validar_uid_gid(valor: str) -> bool:
        """Valida que sea un UID/GID válido"""
        try:
            uid = int(valor)
            return 0 <= uid <= 65535
        except ValueError:
            return False

# English wrappers for GUI compatibility
def validate_path(path: str) -> bool:
    """Validate path (wrapper for GUI)"""
    valid, _ = NFSValidator.validar_directorio(path)
    return valid

def validate_client(client: str) -> bool:
    """Validate client (wrapper for GUI)"""
    valid, _ = NFSValidator.validar_cliente(client)
    return valid

def validate_uid_gid(value: str) -> bool:
    """Validate UID/GID (wrapper for GUI)"""
    return NFSValidator.validar_uid_gid(value)
