"""
Tests para el módulo nfs_manager.py

Verifica el funcionamiento de NFSManager con mocks para filesystem y subprocess.
"""

import pytest
import os
import tempfile
import subprocess
from unittest.mock import Mock, patch, mock_open, MagicMock

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.backend.nfs_manager import NFSManager


class TestNFSManager:
    """Tests para NFSManager"""
    
    def test_verificar_permisos_root(self):
        """Test verificación de permisos cuando es root"""
        with patch('os.getuid', return_value=0):
            assert NFSManager.verificar_permisos() is True
    
    def test_verificar_permisos_no_root(self):
        """Test verificación de permisos cuando no es root"""
        with patch('os.getuid', return_value=1000):
            assert NFSManager.verificar_permisos() is False
    
    def test_ejecutar_comando_exitoso(self):
        """Test ejecución exitosa de comando"""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Comando ejecutado exitosamente"
        mock_result.stderr = ""
        
        with patch('subprocess.run', return_value=mock_result):
            exito, salida = NFSManager.ejecutar_comando(['echo', 'test'])
            
            assert exito is True
            assert "exitosamente" in salida
    
    def test_ejecutar_comando_fallo(self):
        """Test ejecución fallida de comando"""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Error en el comando"
        
        with patch('subprocess.run', return_value=mock_result):
            exito, salida = NFSManager.ejecutar_comando(['false'])
            
            assert exito is False
            assert "Error" in salida
    
    def test_ejecutar_comando_timeout(self):
        """Test comando que expira (timeout)"""
        with patch('subprocess.run', side_effect=subprocess.TimeoutExpired('cmd', 30)):
            exito, salida = NFSManager.ejecutar_comando(['sleep', '60'])
            
            assert exito is False
            assert 'timeout' in salida.lower()
    
    def test_ejecutar_comando_excepcion(self):
        """Test comando que lanza excepción"""
        with patch('subprocess.run', side_effect=Exception('Error genérico')):
            exito, salida = NFSManager.ejecutar_comando(['invalid'])
            
            assert exito is False
            assert 'Error genérico' in salida
    
    def test_list_exports_exitoso(self):
        """Test listar exportaciones exitosamente"""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "/shared/data 192.168.1.0/24(rw,sync)\n/public *(ro)"
        mock_result.stderr = ""
        
        with patch('subprocess.run', return_value=mock_result):
            resultado = NFSManager.list_exports()
            
            assert '/shared/data' in resultado
            assert '192.168.1.0/24' in resultado
    
    def test_list_exports_vacio(self):
        """Test listar exportaciones cuando no hay ninguna"""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""
        
        with patch('subprocess.run', return_value=mock_result):
            resultado = NFSManager.list_exports()
            
            assert 'No hay exportaciones' in resultado
    
    def test_list_exports_error(self):
        """Test error al listar exportaciones"""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "exportfs: error"
        
        with patch('subprocess.run', return_value=mock_result):
            resultado = NFSManager.list_exports()
            
            assert 'Error' in resultado
    
    @patch('src.backend.nfs_manager.ExportsConfigParser.crear_backup')
    @patch('builtins.open', new_callable=mock_open)
    @patch('subprocess.run')
    def test_apply_configuration_exitoso(self, mock_run, mock_file, mock_backup):
        """Test aplicar configuración exitosamente"""
        # Configurar mocks
        mock_backup.return_value = '/etc/exports.20241112_120000'
        
        # Mock exportfs -ra exitoso
        mock_exportfs = Mock()
        mock_exportfs.returncode = 0
        mock_exportfs.stdout = ""
        mock_exportfs.stderr = ""
        
        # Mock systemctl restart exitoso
        mock_systemctl = Mock()
        mock_systemctl.returncode = 0
        mock_systemctl.stdout = ""
        mock_systemctl.stderr = ""
        
        mock_run.side_effect = [mock_exportfs, mock_systemctl]
        
        # Ejecutar
        exports_text = "/test 192.168.1.0/24(rw,sync)"
        result = NFSManager.apply_configuration(exports_text)
        
        # Verificar
        assert result['ok'] is True
        assert 'exitosamente' in result['msg'].lower()
        assert 'backup' in result['msg'].lower()
        
        # Verificar que se escribió el archivo
        mock_file.assert_called_once_with('/etc/exports', 'w')
        handle = mock_file()
        handle.write.assert_called_once_with(exports_text)
    
    @patch('src.backend.nfs_manager.ExportsConfigParser.crear_backup')
    @patch('builtins.open', new_callable=mock_open)
    def test_apply_configuration_texto_vacio(self, mock_file, mock_backup):
        """Test aplicar configuración con texto vacío"""
        result = NFSManager.apply_configuration('')
        
        assert result['ok'] is False
        assert 'vacía' in result['msg'].lower()
    
    @patch('src.backend.nfs_manager.ExportsConfigParser.crear_backup')
    @patch('builtins.open', side_effect=PermissionError('Sin permisos'))
    def test_apply_configuration_sin_permisos(self, mock_file, mock_backup):
        """Test aplicar configuración sin permisos de escritura"""
        mock_backup.return_value = '/etc/exports.backup'
        
        exports_text = "/test 192.168.1.0/24(rw)"
        result = NFSManager.apply_configuration(exports_text)
        
        assert result['ok'] is False
        assert 'permisos' in result['msg'].lower()
    
    @patch('src.backend.nfs_manager.ExportsConfigParser.crear_backup')
    @patch('src.backend.nfs_manager.ExportsConfigParser.restaurar_backup')
    @patch('builtins.open', new_callable=mock_open)
    @patch('subprocess.run')
    def test_apply_configuration_error_sintaxis_restaura_backup(
        self, mock_run, mock_file, mock_restore, mock_backup
    ):
        """Test que se restaura backup cuando hay error de sintaxis"""
        # Configurar mocks
        backup_file = '/etc/exports.20241112_120000'
        mock_backup.return_value = backup_file
        
        # Mock exportfs -ra con error (sintaxis inválida)
        mock_exportfs = Mock()
        mock_exportfs.returncode = 1
        mock_exportfs.stdout = ""
        mock_exportfs.stderr = "exportfs: syntax error"
        
        mock_run.return_value = mock_exportfs
        
        # Ejecutar
        exports_text = "/test invalid syntax here"
        result = NFSManager.apply_configuration(exports_text)
        
        # Verificar que falló
        assert result['ok'] is False
        assert 'sintaxis' in result['msg'].lower()
        
        # Verificar que se intentó restaurar el backup
        mock_restore.assert_called_once_with(backup_file)
    
    @patch('src.backend.nfs_manager.ExportsConfigParser.crear_backup')
    @patch('builtins.open', new_callable=mock_open)
    @patch('subprocess.run')
    def test_apply_configuration_exportfs_ok_systemctl_falla(
        self, mock_run, mock_file, mock_backup
    ):
        """Test cuando exportfs funciona pero systemctl falla"""
        mock_backup.return_value = '/etc/exports.backup'
        
        # Mock exportfs exitoso
        mock_exportfs = Mock()
        mock_exportfs.returncode = 0
        mock_exportfs.stdout = ""
        
        # Mock systemctl con fallo
        mock_systemctl = Mock()
        mock_systemctl.returncode = 1
        mock_systemctl.stderr = "Failed to restart service"
        
        mock_run.side_effect = [mock_exportfs, mock_systemctl]
        
        # Ejecutar
        exports_text = "/test 192.168.1.0/24(rw)"
        result = NFSManager.apply_configuration(exports_text)
        
        # Aún debe ser exitoso (el servicio no es crítico)
        assert result['ok'] is True
        assert 'advertencia' in result['msg'].lower()
        assert 'no se pudo reiniciar' in result['msg'].lower()
    
    @patch('src.backend.nfs_manager.NFSValidator.validar_directorio')
    @patch('src.backend.nfs_manager.NFSValidator.validar_cliente')
    @patch('src.backend.nfs_manager.NFSValidator.validar_opciones')
    def test_validar_configuracion_completa_todo_valido(
        self, mock_opciones, mock_cliente, mock_dir
    ):
        """Test validación completa con todos los elementos válidos"""
        # Configurar mocks
        mock_dir.return_value = (True, "Directorio válido")
        mock_cliente.return_value = (True, "Cliente válido")
        mock_opciones.return_value = (True, [])
        
        # Ejecutar
        directorio = '/test'
        cliente = '192.168.1.0/24'
        opciones = {'rw': True, 'sync': True}
        
        valido, errores = NFSManager.validar_configuracion_completa(
            directorio, cliente, opciones
        )
        
        # Verificar
        assert valido is True
        assert len(errores) == 0
    
    @patch('src.backend.nfs_manager.NFSValidator.validar_directorio')
    @patch('src.backend.nfs_manager.NFSValidator.validar_cliente')
    @patch('src.backend.nfs_manager.NFSValidator.validar_opciones')
    def test_validar_configuracion_completa_con_errores(
        self, mock_opciones, mock_cliente, mock_dir
    ):
        """Test validación completa con errores en múltiples elementos"""
        # Configurar mocks con errores
        mock_dir.return_value = (False, "Directorio no existe")
        mock_cliente.return_value = (False, "Cliente inválido")
        mock_opciones.return_value = (False, ["rw y ro son mutuamente excluyentes"])
        
        # Ejecutar
        directorio = '/invalid'
        cliente = 'invalid_client'
        opciones = {'rw': True, 'ro': True}
        
        valido, errores = NFSManager.validar_configuracion_completa(
            directorio, cliente, opciones
        )
        
        # Verificar
        assert valido is False
        assert len(errores) == 3
        assert any('Directorio' in err for err in errores)
        assert any('Cliente' in err for err in errores)
        assert any('mutuamente excluyentes' in err for err in errores)
    
    @patch('subprocess.run')
    def test_obtener_exportaciones_actuales_exitoso(self, mock_run):
        """Test obtener exportaciones actuales del sistema"""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "/share1 192.168.1.0/24\n/share2 10.0.0.0/8"
        
        mock_run.return_value = mock_result
        
        result = NFSManager.obtener_exportaciones_actuales()
        
        assert len(result) == 2
        assert '/share1' in result[0]
        assert '/share2' in result[1]
    
    @patch('subprocess.run')
    def test_obtener_exportaciones_actuales_vacio(self, mock_run):
        """Test obtener exportaciones cuando no hay ninguna"""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        
        mock_run.return_value = mock_result
        
        result = NFSManager.obtener_exportaciones_actuales()
        
        assert result == []
    
    @patch('subprocess.run')
    def test_obtener_exportaciones_actuales_error(self, mock_run):
        """Test error al obtener exportaciones"""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stderr = "Error"
        
        mock_run.return_value = mock_result
        
        result = NFSManager.obtener_exportaciones_actuales()
        
        assert result == []


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
