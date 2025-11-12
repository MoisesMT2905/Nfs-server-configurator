#!/usr/bin/env python3
"""
Unit tests for NFSManager.
Tests NFS configuration management with mocked subprocess calls.
"""

import pytest
from unittest.mock import patch, MagicMock, mock_open
import tempfile
import os
from src.backend.nfs_manager import NFSManager


class TestVerificarPermisos:
    """Test suite for permission verification"""
    
    @patch('os.getuid')
    def test_verificar_permisos_root(self, mock_getuid):
        """Test permission check when running as root"""
        mock_getuid.return_value = 0
        
        assert NFSManager.verificar_permisos() is True
    
    @patch('os.getuid')
    def test_verificar_permisos_usuario_normal(self, mock_getuid):
        """Test permission check when running as normal user"""
        mock_getuid.return_value = 1000
        
        assert NFSManager.verificar_permisos() is False


class TestEjecutarComando:
    """Test suite for command execution"""
    
    @patch('subprocess.run')
    def test_ejecutar_comando_exitoso(self, mock_run):
        """Test successful command execution"""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="success output",
            stderr=""
        )
        
        exito, mensaje = NFSManager.ejecutar_comando(['echo', 'test'])
        
        assert exito is True
        assert mensaje == "success output"
        mock_run.assert_called_once()
    
    @patch('subprocess.run')
    def test_ejecutar_comando_fallo(self, mock_run):
        """Test failed command execution"""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="error message"
        )
        
        exito, mensaje = NFSManager.ejecutar_comando(['false'])
        
        assert exito is False
        assert mensaje == "error message"
    
    @patch('subprocess.run')
    @patch('os.getuid')
    def test_ejecutar_comando_con_sudo(self, mock_getuid, mock_run):
        """Test command execution with sudo when not root"""
        mock_getuid.return_value = 1000  # Not root
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="output",
            stderr=""
        )
        
        NFSManager.ejecutar_comando(['exportfs', '-v'], usar_sudo=True)
        
        # Should prepend 'sudo' to command
        args = mock_run.call_args[0][0]
        assert args[0] == 'sudo'
        assert 'exportfs' in args
    
    @patch('subprocess.run')
    def test_ejecutar_comando_timeout(self, mock_run):
        """Test command execution timeout"""
        from subprocess import TimeoutExpired
        mock_run.side_effect = TimeoutExpired('cmd', 30)
        
        exito, mensaje = NFSManager.ejecutar_comando(['sleep', '100'])
        
        assert exito is False
        assert "timeout" in mensaje.lower() or "expiró" in mensaje.lower()
    
    @patch('subprocess.run')
    def test_ejecutar_comando_excepcion(self, mock_run):
        """Test command execution with exception"""
        mock_run.side_effect = Exception("Unexpected error")
        
        exito, mensaje = NFSManager.ejecutar_comando(['bad-command'])
        
        assert exito is False
        assert "Unexpected error" in mensaje


class TestObtenerExportacionesActuales:
    """Test suite for getting current exports"""
    
    @patch('src.backend.nfs_manager.NFSManager.ejecutar_comando')
    def test_obtener_exportaciones_exitoso(self, mock_ejecutar):
        """Test successfully getting current exports"""
        mock_ejecutar.return_value = (True, "/data 192.168.1.0/24(rw,sync)\n/backup 10.0.0.5(ro)")
        
        result = NFSManager.obtener_exportaciones_actuales()
        
        assert len(result) == 2
        assert "/data" in result[0]
        assert "/backup" in result[1]
    
    @patch('src.backend.nfs_manager.NFSManager.ejecutar_comando')
    def test_obtener_exportaciones_vacio(self, mock_ejecutar):
        """Test getting exports when none exist"""
        mock_ejecutar.return_value = (True, "")
        
        result = NFSManager.obtener_exportaciones_actuales()
        
        assert result == []
    
    @patch('src.backend.nfs_manager.NFSManager.ejecutar_comando')
    def test_obtener_exportaciones_error(self, mock_ejecutar):
        """Test getting exports when command fails"""
        mock_ejecutar.return_value = (False, "error")
        
        result = NFSManager.obtener_exportaciones_actuales()
        
        assert result == []
    
    @patch('src.backend.nfs_manager.NFSManager.ejecutar_comando')
    def test_obtener_exportaciones_excepcion(self, mock_ejecutar):
        """Test getting exports with exception"""
        mock_ejecutar.side_effect = Exception("Error")
        
        result = NFSManager.obtener_exportaciones_actuales()
        
        assert result == []


class TestAplicarExportaciones:
    """Test suite for applying exports"""
    
    @patch('src.backend.nfs_manager.NFSManager.ejecutar_comando')
    @patch('src.backend.config_parser.ExportsConfigParser.crear_backup')
    @patch('src.backend.config_parser.ExportsConfigParser.restaurar_backup')
    @patch('builtins.open', new_callable=mock_open)
    def test_aplicar_exportaciones_exitoso(self, mock_file, mock_restaurar, mock_backup, mock_ejecutar):
        """Test successfully applying exports"""
        mock_backup.return_value = "/etc/exports.20241112_120000"
        # Mock exportfs and systemctl to succeed
        mock_ejecutar.side_effect = [
            (True, "exportfs success"),  # exportfs -ra
            (True, "systemctl success")  # systemctl restart
        ]
        
        contenido = "/data 192.168.1.0/24(rw,sync)"
        exito, mensaje = NFSManager.aplicar_exportaciones(contenido)
        
        assert exito is True
        assert "aplicada" in mensaje.lower() or "success" in mensaje.lower()
        mock_file.assert_called()
    
    @patch('src.backend.nfs_manager.NFSManager.ejecutar_comando')
    @patch('src.backend.config_parser.ExportsConfigParser.crear_backup')
    @patch('src.backend.config_parser.ExportsConfigParser.restaurar_backup')
    @patch('builtins.open', new_callable=mock_open)
    def test_aplicar_exportaciones_error_exportfs(self, mock_file, mock_restaurar, mock_backup, mock_ejecutar):
        """Test applying exports when exportfs fails"""
        mock_backup.return_value = "/etc/exports.backup"
        mock_ejecutar.return_value = (False, "syntax error")
        
        contenido = "/data invalid(syntax)"
        exito, mensaje = NFSManager.aplicar_exportaciones(contenido)
        
        assert exito is False
        assert "sintaxis" in mensaje.lower() or "syntax" in mensaje.lower()
        # Should restore backup on failure
        mock_restaurar.assert_called_once()
    
    @patch('src.backend.nfs_manager.NFSManager.ejecutar_comando')
    @patch('src.backend.config_parser.ExportsConfigParser.crear_backup')
    @patch('src.backend.config_parser.ExportsConfigParser.restaurar_backup')
    @patch('builtins.open', new_callable=mock_open)
    def test_aplicar_exportaciones_error_systemctl(self, mock_file, mock_restaurar, mock_backup, mock_ejecutar):
        """Test applying exports when systemctl fails"""
        mock_backup.return_value = "/etc/exports.backup"
        mock_ejecutar.side_effect = [
            (True, "exportfs ok"),  # exportfs succeeds
            (False, "service error")  # systemctl fails
        ]
        
        contenido = "/data 192.168.1.0/24(rw,sync)"
        exito, mensaje = NFSManager.aplicar_exportaciones(contenido)
        
        assert exito is False
        assert "servicio" in mensaje.lower() or "service" in mensaje.lower()
        # Should restore backup on failure
        mock_restaurar.assert_called_once()
    
    @patch('src.backend.config_parser.ExportsConfigParser.crear_backup')
    @patch('builtins.open', new_callable=mock_open)
    def test_aplicar_exportaciones_sin_permisos(self, mock_file, mock_backup):
        """Test applying exports without permissions"""
        mock_backup.return_value = "/etc/exports.backup"
        mock_file.side_effect = PermissionError("No write permission")
        
        contenido = "/data 192.168.1.0/24(rw,sync)"
        exito, mensaje = NFSManager.aplicar_exportaciones(contenido)
        
        assert exito is False
        assert "permisos" in mensaje.lower() or "permission" in mensaje.lower()


class TestValidarConfiguracionCompleta:
    """Test suite for complete configuration validation"""
    
    @patch('src.utils.validators.NFSValidator.validar_directorio')
    @patch('src.utils.validators.NFSValidator.validar_cliente')
    @patch('src.utils.validators.NFSValidator.validar_opciones')
    def test_validacion_completa_exitosa(self, mock_validar_opciones, mock_validar_cliente, mock_validar_directorio):
        """Test successful complete validation"""
        mock_validar_directorio.return_value = (True, "OK")
        mock_validar_cliente.return_value = (True, "OK")
        mock_validar_opciones.return_value = (True, [])
        
        valido, errores = NFSManager.validar_configuracion_completa(
            "/data",
            "192.168.1.0/24",
            {'rw': True, 'sync': True}
        )
        
        assert valido is True
        assert len(errores) == 0
    
    @patch('src.utils.validators.NFSValidator.validar_directorio')
    @patch('src.utils.validators.NFSValidator.validar_cliente')
    @patch('src.utils.validators.NFSValidator.validar_opciones')
    def test_validacion_completa_directorio_invalido(self, mock_validar_opciones, mock_validar_cliente, mock_validar_directorio):
        """Test validation with invalid directory"""
        mock_validar_directorio.return_value = (False, "Directorio no existe")
        mock_validar_cliente.return_value = (True, "OK")
        mock_validar_opciones.return_value = (True, [])
        
        valido, errores = NFSManager.validar_configuracion_completa(
            "/nonexistent",
            "192.168.1.0/24",
            {'rw': True}
        )
        
        assert valido is False
        assert len(errores) > 0
        assert any("no existe" in err.lower() for err in errores)
    
    @patch('src.utils.validators.NFSValidator.validar_directorio')
    @patch('src.utils.validators.NFSValidator.validar_cliente')
    @patch('src.utils.validators.NFSValidator.validar_opciones')
    def test_validacion_completa_cliente_invalido(self, mock_validar_opciones, mock_validar_cliente, mock_validar_directorio):
        """Test validation with invalid client"""
        mock_validar_directorio.return_value = (True, "OK")
        mock_validar_cliente.return_value = (False, "Cliente inválido")
        mock_validar_opciones.return_value = (True, [])
        
        valido, errores = NFSManager.validar_configuracion_completa(
            "/data",
            "invalid@!",
            {'rw': True}
        )
        
        assert valido is False
        assert len(errores) > 0
    
    @patch('src.utils.validators.NFSValidator.validar_directorio')
    @patch('src.utils.validators.NFSValidator.validar_cliente')
    @patch('src.utils.validators.NFSValidator.validar_opciones')
    def test_validacion_completa_opciones_invalidas(self, mock_validar_opciones, mock_validar_cliente, mock_validar_directorio):
        """Test validation with invalid options"""
        mock_validar_directorio.return_value = (True, "OK")
        mock_validar_cliente.return_value = (True, "OK")
        mock_validar_opciones.return_value = (False, ["rw y ro no pueden estar juntas"])
        
        valido, errores = NFSManager.validar_configuracion_completa(
            "/data",
            "192.168.1.0/24",
            {'rw': True, 'ro': True}
        )
        
        assert valido is False
        assert len(errores) > 0


class TestWrapperMethods:
    """Test suite for wrapper methods (GUI compatibility)"""
    
    @patch('src.backend.nfs_manager.NFSManager.aplicar_exportaciones')
    def test_apply_configuration_exitoso(self, mock_aplicar):
        """Test apply_configuration wrapper with success"""
        mock_aplicar.return_value = (True, "Configuration applied")
        
        result = NFSManager.apply_configuration("/data 192.168.1.0/24(rw)")
        
        assert result["ok"] is True
        assert result["msg"] == "Configuration applied"
    
    @patch('src.backend.nfs_manager.NFSManager.aplicar_exportaciones')
    def test_apply_configuration_fallo(self, mock_aplicar):
        """Test apply_configuration wrapper with failure"""
        mock_aplicar.return_value = (False, "Error applying")
        
        result = NFSManager.apply_configuration("/data 192.168.1.0/24(rw)")
        
        assert result["ok"] is False
        assert result["msg"] == "Error applying"
    
    @patch('src.backend.nfs_manager.NFSManager.obtener_exportaciones_actuales')
    def test_list_exports_con_datos(self, mock_obtener):
        """Test list_exports with data"""
        mock_obtener.return_value = [
            "/data 192.168.1.0/24(rw,sync)",
            "/backup 10.0.0.5(ro)"
        ]
        
        result = NFSManager.list_exports()
        
        assert "/data" in result
        assert "/backup" in result
        assert "\n" in result
    
    @patch('src.backend.nfs_manager.NFSManager.obtener_exportaciones_actuales')
    def test_list_exports_vacio(self, mock_obtener):
        """Test list_exports with no data"""
        mock_obtener.return_value = []
        
        result = NFSManager.list_exports()
        
        assert result == ""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
