"""Tests for NFSManager"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import subprocess
from src.backend.nfs_manager import NFSManager, apply_configuration, list_exports


class TestNFSManager:
    """Test suite for NFSManager class"""
    
    def test_verificar_permisos_root(self):
        """Test permission check when running as root"""
        with patch('os.getuid', return_value=0):
            assert NFSManager.verificar_permisos() is True
    
    def test_verificar_permisos_no_root(self):
        """Test permission check when not running as root"""
        with patch('os.getuid', return_value=1000):
            assert NFSManager.verificar_permisos() is False
    
    @patch('subprocess.run')
    def test_ejecutar_comando_exitoso(self, mock_run):
        """Test successful command execution"""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="Success output",
            stderr=""
        )
        
        success, output = NFSManager.ejecutar_comando(['ls', '-la'])
        
        assert success is True
        assert output == "Success output"
        mock_run.assert_called_once()
    
    @patch('subprocess.run')
    def test_ejecutar_comando_falla(self, mock_run):
        """Test failed command execution"""
        mock_run.return_value = Mock(
            returncode=1,
            stdout="",
            stderr="Error message"
        )
        
        success, output = NFSManager.ejecutar_comando(['invalid-command'])
        
        assert success is False
        assert output == "Error message"
    
    @patch('subprocess.run')
    def test_ejecutar_comando_timeout(self, mock_run):
        """Test command timeout"""
        mock_run.side_effect = subprocess.TimeoutExpired('cmd', 30)
        
        success, output = NFSManager.ejecutar_comando(['long-running-command'])
        
        assert success is False
        assert "timeout" in output.lower()
    
    @patch('subprocess.run')
    def test_ejecutar_comando_exception(self, mock_run):
        """Test command execution exception"""
        mock_run.side_effect = Exception("Unexpected error")
        
        success, output = NFSManager.ejecutar_comando(['test-command'])
        
        assert success is False
        assert "Unexpected error" in output
    
    @patch('os.getuid', return_value=1000)
    @patch('subprocess.run')
    def test_ejecutar_comando_con_sudo(self, mock_run, mock_getuid):
        """Test command execution with sudo when not root"""
        mock_run.return_value = Mock(returncode=0, stdout="OK", stderr="")
        
        NFSManager.ejecutar_comando(['exportfs', '-v'], usar_sudo=True)
        
        # Should prepend 'sudo' to command
        call_args = mock_run.call_args[0][0]
        assert call_args[0] == 'sudo'
        assert 'exportfs' in call_args
    
    @patch('os.getuid', return_value=0)
    @patch('subprocess.run')
    def test_ejecutar_comando_sin_sudo_cuando_es_root(self, mock_run, mock_getuid):
        """Test command execution without sudo when already root"""
        mock_run.return_value = Mock(returncode=0, stdout="OK", stderr="")
        
        NFSManager.ejecutar_comando(['exportfs', '-v'], usar_sudo=True)
        
        # Should NOT prepend 'sudo' when already root
        call_args = mock_run.call_args[0][0]
        assert call_args[0] != 'sudo'
        assert call_args[0] == 'exportfs'
    
    @patch('subprocess.run')
    @patch('src.backend.config_parser.ExportsConfigParser.crear_backup')
    @patch('src.backend.config_parser.ExportsConfigParser.restaurar_backup')
    @patch('builtins.open', create=True)
    def test_aplicar_exportaciones_exitoso(self, mock_open, mock_restore, mock_backup, mock_run):
        """Test successful export application"""
        # Mock backup creation
        mock_backup.return_value = "/etc/exports.20250101_120000"
        
        # Mock file write
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        # Mock successful exportfs and systemctl commands
        mock_run.return_value = Mock(returncode=0, stdout="OK", stderr="")
        
        config = "/srv/nfs 192.168.1.0/24(rw,sync)"
        success, message = NFSManager.aplicar_exportaciones(config)
        
        assert success is True
        assert "aplicada" in message.lower() or "servicio" in message.lower()
        mock_backup.assert_called_once()
    
    @patch('subprocess.run')
    @patch('src.backend.config_parser.ExportsConfigParser.crear_backup')
    @patch('src.backend.config_parser.ExportsConfigParser.restaurar_backup')
    @patch('builtins.open', create=True)
    def test_aplicar_exportaciones_exportfs_falla(self, mock_open, mock_restore, mock_backup, mock_run):
        """Test export application when exportfs fails"""
        # Mock backup creation
        mock_backup.return_value = "/etc/exports.20250101_120000"
        
        # Mock file write
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        # Mock failed exportfs command
        def run_side_effect(cmd, **kwargs):
            if 'exportfs' in cmd:
                return Mock(returncode=1, stdout="", stderr="Syntax error")
            return Mock(returncode=0, stdout="OK", stderr="")
        
        mock_run.side_effect = run_side_effect
        
        config = "/srv/nfs 192.168.1.0/24(invalid)"
        success, message = NFSManager.aplicar_exportaciones(config)
        
        assert success is False
        assert "sintaxis" in message.lower()
        # Should restore backup when exportfs fails
        mock_restore.assert_called_once()
    
    @patch('subprocess.run')
    @patch('src.backend.config_parser.ExportsConfigParser.crear_backup')
    @patch('src.backend.config_parser.ExportsConfigParser.restaurar_backup')
    @patch('builtins.open', create=True)
    def test_aplicar_exportaciones_systemctl_falla(self, mock_open, mock_restore, mock_backup, mock_run):
        """Test export application when systemctl fails"""
        # Mock backup creation
        mock_backup.return_value = "/etc/exports.20250101_120000"
        
        # Mock file write
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        # Mock exportfs success but systemctl failure
        def run_side_effect(cmd, **kwargs):
            if 'systemctl' in cmd:
                return Mock(returncode=1, stdout="", stderr="Failed to restart")
            return Mock(returncode=0, stdout="OK", stderr="")
        
        mock_run.side_effect = run_side_effect
        
        config = "/srv/nfs 192.168.1.0/24(rw,sync)"
        success, message = NFSManager.aplicar_exportaciones(config)
        
        assert success is False
        assert "servicio" in message.lower() or "reiniciar" in message.lower()
        # Should restore backup when systemctl fails
        mock_restore.assert_called_once()
    
    @patch('src.backend.config_parser.ExportsConfigParser.crear_backup')
    @patch('builtins.open', create=True)
    def test_aplicar_exportaciones_sin_permisos(self, mock_open, mock_backup):
        """Test export application without permissions"""
        mock_backup.return_value = "/etc/exports.20250101_120000"
        
        # Mock permission error on file write
        mock_open.side_effect = PermissionError("Permission denied")
        
        config = "/srv/nfs 192.168.1.0/24(rw,sync)"
        success, message = NFSManager.aplicar_exportaciones(config)
        
        assert success is False
        assert "permisos" in message.lower()
    
    @patch('subprocess.run')
    def test_obtener_exportaciones_actuales_exitoso(self, mock_run):
        """Test getting current exports successfully"""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="/srv/nfs\n\t192.168.1.0/24(rw,sync)\n",
            stderr=""
        )
        
        exports = NFSManager.obtener_exportaciones_actuales()
        
        assert isinstance(exports, list)
        assert len(exports) > 0
    
    @patch('subprocess.run')
    def test_obtener_exportaciones_actuales_vacio(self, mock_run):
        """Test getting current exports when none exist"""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="",
            stderr=""
        )
        
        exports = NFSManager.obtener_exportaciones_actuales()
        
        assert isinstance(exports, list)
        assert len(exports) == 0
    
    @patch('subprocess.run')
    def test_obtener_exportaciones_actuales_falla(self, mock_run):
        """Test getting current exports when command fails"""
        mock_run.return_value = Mock(
            returncode=1,
            stdout="",
            stderr="Error"
        )
        
        exports = NFSManager.obtener_exportaciones_actuales()
        
        assert isinstance(exports, list)
        assert len(exports) == 0
    
    def test_validar_configuracion_completa_todo_valido(self, tmp_path):
        """Test complete configuration validation with all valid inputs"""
        test_dir = tmp_path / "share"
        test_dir.mkdir()
        
        valid, errors = NFSManager.validar_configuracion_completa(
            str(test_dir),
            "192.168.1.0/24",
            {'rw': True, 'sync': True}
        )
        
        assert valid is True
        assert len(errors) == 0
    
    def test_validar_configuracion_completa_directorio_invalido(self):
        """Test complete validation with invalid directory"""
        valid, errors = NFSManager.validar_configuracion_completa(
            "/non/existent/path",
            "192.168.1.0/24",
            {'rw': True}
        )
        
        assert valid is False
        assert len(errors) > 0
        assert any('directorio' in error.lower() for error in errors)
    
    def test_validar_configuracion_completa_cliente_invalido(self, tmp_path):
        """Test complete validation with invalid client"""
        test_dir = tmp_path / "share"
        test_dir.mkdir()
        
        valid, errors = NFSManager.validar_configuracion_completa(
            str(test_dir),
            "invalid@#$client",
            {'rw': True}
        )
        
        assert valid is False
        assert len(errors) > 0
    
    def test_validar_configuracion_completa_opciones_conflictivas(self, tmp_path):
        """Test complete validation with conflicting options"""
        test_dir = tmp_path / "share"
        test_dir.mkdir()
        
        valid, errors = NFSManager.validar_configuracion_completa(
            str(test_dir),
            "192.168.1.0/24",
            {'rw': True, 'ro': True}  # Conflicting options
        )
        
        assert valid is False
        assert len(errors) > 0


class TestHelperFunctions:
    """Test suite for helper functions"""
    
    @patch('src.backend.nfs_manager.NFSManager.aplicar_exportaciones')
    def test_apply_configuration(self, mock_aplicar):
        """Test apply_configuration helper"""
        mock_aplicar.return_value = (True, "Configuration applied")
        
        result = apply_configuration("/srv/nfs 192.168.1.0/24(rw,sync)")
        
        assert result['ok'] is True
        assert result['msg'] == "Configuration applied"
    
    @patch('src.backend.nfs_manager.NFSManager.aplicar_exportaciones')
    def test_apply_configuration_falla(self, mock_aplicar):
        """Test apply_configuration helper on failure"""
        mock_aplicar.return_value = (False, "Error applying configuration")
        
        result = apply_configuration("/srv/nfs 192.168.1.0/24(rw,sync)")
        
        assert result['ok'] is False
        assert "Error" in result['msg']
    
    @patch('src.backend.nfs_manager.NFSManager.obtener_exportaciones_actuales')
    def test_list_exports(self, mock_obtener):
        """Test list_exports helper"""
        mock_obtener.return_value = [
            "/srv/nfs 192.168.1.0/24(rw,sync)",
            "/srv/backup 10.0.0.5(ro)"
        ]
        
        result = list_exports()
        
        assert isinstance(result, str)
        assert "/srv/nfs" in result
        assert "/srv/backup" in result
    
    @patch('src.backend.nfs_manager.NFSManager.obtener_exportaciones_actuales')
    def test_list_exports_vacio(self, mock_obtener):
        """Test list_exports helper when no exports"""
        mock_obtener.return_value = []
        
        result = list_exports()
        
        assert result == ""
