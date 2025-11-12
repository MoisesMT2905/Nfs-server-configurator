import subprocess
import os
from typing import Tuple, List
from src.backend.config_parser import ExportsConfigParser
from src.utils.validators import NFSValidator

class NFSManager:
    """Gestor de configuración NFS del sistema"""
    
    EXPORTS_FILE = '/etc/exports'
    
    @staticmethod
    def verificar_permisos() -> bool:
        """Verifica si se ejecuta con permisos suficientes"""
        return os.getuid() == 0
    
    @staticmethod
    def ejecutar_comando(comando: List[str], usar_sudo: bool = False) -> Tuple[bool, str]:
        """Ejecuta comando del sistema"""
        try:
            if usar_sudo and not NFSManager.verificar_permisos():
                comando = ['sudo'] + comando
            
            resultado = subprocess.run(
                comando,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if resultado.returncode == 0:
                return True, resultado.stdout
            else:
                return False, resultado.stderr
        except subprocess.TimeoutExpired:
            return False, "Comando expiró (timeout)"
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def aplicar_exportaciones(contenido_nuevo: str) -> Tuple[bool, str]:
        """
        Aplica nuevas exportaciones de forma segura
        1. Crea backup
        2. Valida sintaxis
        3. Aplica cambios
        4. Reinicia servicio
        """
        try:
            # Crear backup
            backup_file = ExportsConfigParser.crear_backup()
            
            # Escribir nuevo contenido (requiere permisos)
            try:
                with open(ExportsConfigParser.EXPORTS_FILE, 'w') as f:
                    f.write(contenido_nuevo)
            except PermissionError:
                return False, "No hay permisos para escribir /etc/exports"
            
            # Validar sintaxis con exportfs -ra
            exito, mensaje = NFSManager.ejecutar_comando(['exportfs', '-ra'], usar_sudo=True)
            if not exito:
                # Restaurar backup si falla
                ExportsConfigParser.restaurar_backup(backup_file)
                return False, f"Error de sintaxis: {mensaje}"
            
            # Reiniciar servicio
            exito, mensaje = NFSManager.ejecutar_comando(
                ['systemctl', 'restart', 'nfs-server'],
                usar_sudo=True
            )
            
            if exito:
                return True, f"Configuración aplicada. Servicio reiniciado. Backup: {backup_file}"
            else:
                ExportsConfigParser.restaurar_backup(backup_file)
                return False, f"Error al reiniciar servicio: {mensaje}"
                
        except Exception as e:
            return False, f"Error al aplicar configuración: {str(e)}"
    
    @staticmethod
    def obtener_exportaciones_actuales() -> List[str]:
        """Obtiene exportaciones actuales del sistema"""
        try:
            exito, salida = NFSManager.ejecutar_comando(['exportfs', '-v'], usar_sudo=True)
            if exito:
                return salida.strip().split('\n') if salida.strip() else []
            return []
        except:
            return []
    
    @staticmethod
    def validar_configuracion_completa(directorio: str, cliente: str, opciones: dict) -> Tuple[bool, List[str]]:
        """Valida directorio, cliente y opciones"""
        errores = []
        
        # Validar directorio
        valido, msg = NFSValidator.validar_directorio(directorio)
        if not valido:
            errores.append(msg)
        
        # Validar cliente
        valido, msg = NFSValidator.validar_cliente(cliente)
        if not valido:
            errores.append(msg)
        
        # Validar opciones
        valido, msgs = NFSValidator.validar_opciones(opciones)
        if not valido:
            errores.extend(msgs)
        
        return len(errores) == 0, errores
    
    @staticmethod
    def apply_configuration(exports_text: str) -> dict:
        """
        Aplica configuración de exportaciones NFS.
        Este método es llamado directamente cuando se ejecuta como root
        o por el helper D-Bus cuando se ejecuta como usuario normal.
        
        Returns:
            dict: {'ok': bool, 'msg': str}
        """
        try:
            # Validar que el texto no esté vacío
            if not exports_text or not exports_text.strip():
                return {'ok': False, 'msg': 'La configuración no puede estar vacía'}
            
            # Crear backup
            backup_file = ExportsConfigParser.crear_backup()
            if not backup_file:
                backup_file = "sin_backup"
            
            # Escribir nuevo contenido (requiere permisos)
            try:
                with open(NFSManager.EXPORTS_FILE, 'w') as f:
                    f.write(exports_text)
            except PermissionError:
                return {'ok': False, 'msg': 'No hay permisos para escribir /etc/exports. Ejecute como root o use el helper D-Bus.'}
            except Exception as e:
                return {'ok': False, 'msg': f'Error al escribir /etc/exports: {str(e)}'}
            
            # Validar sintaxis con exportfs -ra
            exito, mensaje = NFSManager.ejecutar_comando(['exportfs', '-ra'], usar_sudo=False)
            if not exito:
                # Restaurar backup si falla
                if backup_file != "sin_backup":
                    ExportsConfigParser.restaurar_backup(backup_file)
                return {'ok': False, 'msg': f'Error de sintaxis al aplicar configuración: {mensaje}'}
            
            # Reiniciar servicio (intentar, pero no es crítico)
            exito_restart, mensaje_restart = NFSManager.ejecutar_comando(
                ['systemctl', 'restart', 'nfs-server'],
                usar_sudo=False
            )
            
            msg_final = f'Configuración aplicada exitosamente. Backup guardado en: {backup_file}'
            if not exito_restart:
                msg_final += f'\nAdvertencia: No se pudo reiniciar el servicio NFS: {mensaje_restart}'
            
            return {'ok': True, 'msg': msg_final}
                
        except Exception as e:
            return {'ok': False, 'msg': f'Error al aplicar configuración: {str(e)}'}
    
    @staticmethod
    def list_exports() -> str:
        """Lista las exportaciones actuales del sistema usando exportfs -v"""
        try:
            exito, salida = NFSManager.ejecutar_comando(['exportfs', '-v'], usar_sudo=False)
            if exito:
                return salida.strip() if salida.strip() else "No hay exportaciones configuradas"
            return f"Error al listar exportaciones: {salida}"
        except Exception as e:
            return f"Error: {str(e)}"
