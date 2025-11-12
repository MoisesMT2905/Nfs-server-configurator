"""Tests for nfs_manager module with mocked subprocess calls"""
import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
import tempfile

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.backend.nfs_manager import NFSManager
from src.backend.config_parser import ExportsConfigParser


class TestNFSManager:
    """Test NFSManager class"""
    
    def test_verificar_permisos_root(self):
        """Test permission check as root"""
        with patch('os.getuid', return_value=0):
            assert NFSManager.verificar_permisos() is True
    
    def test_verificar_permisos_non_root(self):
        """Test permission check as non-root"""
        with patch('os.getuid', return_value=1000):
            assert NFSManager.verificar_permisos() is False
    
    @patch('subprocess.run')
    def test_ejecutar_comando_success(self, mock_run):
        """Test successful command execution"""
        mock_run.return_value = Mock(returncode=0, stdout="success output", stderr="")
        
        success, output = NFSManager.ejecutar_comando(['echo', 'test'])
        
        assert success is True
        assert output == "success output"
        mock_run.assert_called_once()
    
    @patch('subprocess.run')
    def test_ejecutar_comando_failure(self, mock_run):
        """Test failed command execution"""
        mock_run.return_value = Mock(returncode=1, stdout="", stderr="error message")
        
        success, output = NFSManager.ejecutar_comando(['false'])
        
        assert success is False
        assert output == "error message"
    
    @patch('subprocess.run')
    def test_ejecutar_comando_timeout(self, mock_run):
        """Test command timeout"""
        from subprocess import TimeoutExpired
        mock_run.side_effect = TimeoutExpired('cmd', 30)
        
        success, output = NFSManager.ejecutar_comando(['sleep', '100'])
        
        assert success is False
        assert "timeout" in output.lower()
    
    @patch('subprocess.run')
    def test_ejecutar_comando_with_sudo(self, mock_run):
        """Test command execution with sudo"""
        mock_run.return_value = Mock(returncode=0, stdout="output", stderr="")
        
        with patch.object(NFSManager, 'verificar_permisos', return_value=False):
            NFSManager.ejecutar_comando(['test'], usar_sudo=True)
        
        # Check that sudo was prepended
        call_args = mock_run.call_args[0][0]
        assert call_args[0] == 'sudo'
        assert 'test' in call_args
    
    @patch('subprocess.run')
    def test_obtener_exportaciones_actuales_success(self, mock_run):
        """Test getting current exports successfully"""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="/shared 192.168.1.0/24(rw,sync)\n/data 10.0.0.1(ro)",
            stderr=""
        )
        
        exports = NFSManager.obtener_exportaciones_actuales()
        
        assert len(exports) == 2
        assert "/shared 192.168.1.0/24(rw,sync)" in exports
        assert "/data 10.0.0.1(ro)" in exports
    
    @patch('subprocess.run')
    def test_obtener_exportaciones_actuales_empty(self, mock_run):
        """Test getting exports when none exist"""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
        
        exports = NFSManager.obtener_exportaciones_actuales()
        
        assert exports == []
    
    @patch('subprocess.run')
    def test_obtener_exportaciones_actuales_failure(self, mock_run):
        """Test handling failure when getting exports"""
        mock_run.return_value = Mock(returncode=1, stdout="", stderr="error")
        
        exports = NFSManager.obtener_exportaciones_actuales()
        
        assert exports == []
    
    def test_list_exports_with_data(self):
        """Test list_exports returns formatted string"""
        with patch.object(NFSManager, 'obtener_exportaciones_actuales', 
                         return_value=["/shared 192.168.1.0/24(rw)", "/data 10.0.0.1(ro)"]):
            result = NFSManager.list_exports()
            assert "/shared 192.168.1.0/24(rw)" in result
            assert "/data 10.0.0.1(ro)" in result
    
    def test_list_exports_empty(self):
        """Test list_exports with no exports"""
        with patch.object(NFSManager, 'obtener_exportaciones_actuales', return_value=[]):
            result = NFSManager.list_exports()
            assert result == ""
    
    def test_apply_configuration_returns_dict(self):
        """Test that apply_configuration returns a dict"""
        with patch.object(NFSManager, 'aplicar_exportaciones', 
                         return_value=(True, "Success")):
            result = NFSManager.apply_configuration("test config")
            assert isinstance(result, dict)
            assert "ok" in result
            assert "msg" in result
            assert result["ok"] is True
    
    @patch('builtins.open', new_callable=MagicMock)
    @patch.object(ExportsConfigParser, 'crear_backup')
    @patch.object(NFSManager, 'ejecutar_comando')
    def test_aplicar_exportaciones_success(self, mock_cmd, mock_backup, mock_open):
        """Test successful configuration application"""
        mock_backup.return_value = "/etc/exports.20251112_120000"
        mock_cmd.side_effect = [
            (True, ""),  # exportfs -ra
            (True, "")   # systemctl restart
        ]
        
        success, msg = NFSManager.aplicar_exportaciones("test content")
        
        assert success is True
        assert "aplicada" in msg.lower() or "success" in msg.lower()
        mock_backup.assert_called_once()
    
    @patch('builtins.open', side_effect=PermissionError())
    @patch.object(ExportsConfigParser, 'crear_backup')
    def test_aplicar_exportaciones_permission_denied(self, mock_backup, mock_open):
        """Test configuration application without permissions"""
        mock_backup.return_value = "/etc/exports.backup"
        
        success, msg = NFSManager.aplicar_exportaciones("test content")
        
        assert success is False
        assert "permisos" in msg.lower() or "permission" in msg.lower()
    
    @patch('builtins.open', new_callable=MagicMock)
    @patch.object(ExportsConfigParser, 'crear_backup')
    @patch.object(ExportsConfigParser, 'restaurar_backup')
    @patch.object(NFSManager, 'ejecutar_comando')
    def test_aplicar_exportaciones_syntax_error_rollback(self, mock_cmd, mock_restore, 
                                                         mock_backup, mock_open):
        """Test rollback on syntax error"""
        mock_backup.return_value = "/etc/exports.backup"
        # exportfs -ra fails
        mock_cmd.return_value = (False, "syntax error")
        
        success, msg = NFSManager.aplicar_exportaciones("bad content")
        
        assert success is False
        assert "sintaxis" in msg.lower() or "syntax" in msg.lower()
        mock_restore.assert_called_once_with("/etc/exports.backup")
    
    @patch('builtins.open', new_callable=MagicMock)
    @patch.object(ExportsConfigParser, 'crear_backup')
    @patch.object(ExportsConfigParser, 'restaurar_backup')
    @patch.object(NFSManager, 'ejecutar_comando')
    def test_aplicar_exportaciones_service_restart_failure(self, mock_cmd, mock_restore,
                                                           mock_backup, mock_open):
        """Test rollback when service restart fails"""
        mock_backup.return_value = "/etc/exports.backup"
        mock_cmd.side_effect = [
            (True, ""),     # exportfs -ra succeeds
            (False, "service error")  # systemctl restart fails
        ]
        
        success, msg = NFSManager.aplicar_exportaciones("test content")
        
        assert success is False
        assert "servicio" in msg.lower() or "service" in msg.lower()
        mock_restore.assert_called_once()
    
    @patch.object(ExportsConfigParser, 'crear_backup')
    def test_backup_exports(self, mock_backup):
        """Test backup_exports wrapper function"""
        mock_backup.return_value = "/etc/exports.backup"
        
        result = NFSManager.backup_exports()
        
        assert result == "/etc/exports.backup"
        mock_backup.assert_called_once()
    
    def test_validar_configuracion_completa_all_valid(self):
        """Test complete configuration validation - all valid"""
        with tempfile.TemporaryDirectory() as tmpdir:
            options = {"rw": True, "sync": True}
            valid, errors = NFSManager.validar_configuracion_completa(
                tmpdir, "192.168.1.0/24", options
            )
            assert valid is True
            assert len(errors) == 0
    
    def test_validar_configuracion_completa_invalid_directory(self):
        """Test validation with invalid directory"""
        options = {"rw": True}
        valid, errors = NFSManager.validar_configuracion_completa(
            "/nonexistent", "192.168.1.0/24", options
        )
        assert valid is False
        assert len(errors) > 0
    
    def test_validar_configuracion_completa_invalid_client(self):
        """Test validation with invalid client"""
        with tempfile.TemporaryDirectory() as tmpdir:
            options = {"rw": True}
            valid, errors = NFSManager.validar_configuracion_completa(
                tmpdir, "invalid client", options
            )
            assert valid is False
            assert len(errors) > 0
    
    def test_validar_configuracion_completa_invalid_options(self):
        """Test validation with invalid options"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Mutually exclusive options
            options = {"rw": True, "ro": True}
            valid, errors = NFSManager.validar_configuracion_completa(
                tmpdir, "192.168.1.0/24", options
            )
            assert valid is False
            assert len(errors) > 0
    
    def test_validar_configuracion_completa_multiple_errors(self):
        """Test validation with multiple errors"""
        options = {"rw": True, "ro": True}  # Invalid options
        valid, errors = NFSManager.validar_configuracion_completa(
            "/nonexistent",  # Invalid directory
            "invalid",       # Invalid client
            options
        )
        assert valid is False
        assert len(errors) >= 2  # At least directory and client errors


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
