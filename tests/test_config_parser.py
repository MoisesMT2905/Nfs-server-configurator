"""
Tests para el módulo config_parser.py

Verifica el correcto funcionamiento del parser de configuración de exportaciones NFS,
incluyendo las 13 opciones soportadas y sus combinaciones.
"""

import pytest
import os
import tempfile
import shutil
from datetime import datetime

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.backend.config_parser import ExportsConfigParser, build_export_line


class TestExportsConfigParser:
    """Tests para ExportsConfigParser"""
    
    def test_generar_opciones_str_basicas(self):
        """Test generación de opciones básicas rw/ro"""
        # Solo rw
        opciones = {'rw': True}
        result = ExportsConfigParser._generar_opciones_str(opciones)
        assert result == 'rw'
        
        # Solo ro
        opciones = {'ro': True}
        result = ExportsConfigParser._generar_opciones_str(opciones)
        assert result == 'ro'
    
    def test_generar_opciones_str_sync(self):
        """Test generación de opciones de sincronización"""
        # sync
        opciones = {'rw': True, 'sync': True}
        result = ExportsConfigParser._generar_opciones_str(opciones)
        assert 'rw' in result
        assert 'sync' in result
        
        # async
        opciones = {'ro': True, 'async': True}
        result = ExportsConfigParser._generar_opciones_str(opciones)
        assert 'ro' in result
        assert 'async' in result
    
    def test_generar_opciones_str_root_squash(self):
        """Test generación de opciones root_squash"""
        # no_root_squash
        opciones = {'rw': True, 'no_root_squash': True}
        result = ExportsConfigParser._generar_opciones_str(opciones)
        assert 'no_root_squash' in result
        
        # root_squash
        opciones = {'rw': True, 'root_squash': True}
        result = ExportsConfigParser._generar_opciones_str(opciones)
        assert 'root_squash' in result
    
    def test_generar_opciones_str_all_squash(self):
        """Test generación de opción all_squash"""
        opciones = {'ro': True, 'all_squash': True}
        result = ExportsConfigParser._generar_opciones_str(opciones)
        assert 'all_squash' in result
    
    def test_generar_opciones_str_subtree(self):
        """Test generación de opciones subtree_check"""
        # no_subtree_check
        opciones = {'rw': True, 'no_subtree_check': True}
        result = ExportsConfigParser._generar_opciones_str(opciones)
        assert 'no_subtree_check' in result
        
        # subtree_check
        opciones = {'rw': True, 'subtree_check': True}
        result = ExportsConfigParser._generar_opciones_str(opciones)
        assert 'subtree_check' in result
    
    def test_generar_opciones_str_secure(self):
        """Test generación de opciones de seguridad de puertos"""
        # insecure
        opciones = {'rw': True, 'insecure': True}
        result = ExportsConfigParser._generar_opciones_str(opciones)
        assert 'insecure' in result
        
        # secure
        opciones = {'rw': True, 'secure': True}
        result = ExportsConfigParser._generar_opciones_str(opciones)
        assert 'secure' in result
    
    def test_generar_opciones_str_anonuid_anongid(self):
        """Test generación de opciones anonuid/anongid"""
        opciones = {'ro': True, 'all_squash': True, 'anonuid': '65534', 'anongid': '65534'}
        result = ExportsConfigParser._generar_opciones_str(opciones)
        assert 'anonuid=65534' in result
        assert 'anongid=65534' in result
    
    def test_generar_opciones_str_combinacion_completa(self):
        """Test generación con todas las opciones combinadas"""
        opciones = {
            'rw': True,
            'sync': True,
            'no_root_squash': True,
            'no_subtree_check': True,
            'secure': True,
            'anonuid': '1000',
            'anongid': '1000'
        }
        result = ExportsConfigParser._generar_opciones_str(opciones)
        
        # Verificar que todas las opciones están presentes
        assert 'rw' in result
        assert 'sync' in result
        assert 'no_root_squash' in result
        assert 'no_subtree_check' in result
        assert 'secure' in result
        assert 'anonuid=1000' in result
        assert 'anongid=1000' in result
        
        # Verificar formato (separadas por comas, sin espacios)
        assert ', ' not in result  # No debe tener espacios después de comas
        parts = result.split(',')
        assert len(parts) == 7
    
    def test_generar_linea_export_simple(self):
        """Test generación de línea de exportación simple"""
        directorio = '/shared/data'
        cliente = '192.168.1.0/24'
        opciones = {'rw': True, 'sync': True}
        
        result = ExportsConfigParser.generar_linea_export(directorio, cliente, opciones)
        
        assert result.startswith('/shared/data ')
        assert '192.168.1.0/24' in result
        assert '(rw,sync)' in result
    
    def test_generar_linea_export_compleja(self):
        """Test generación de línea con opciones complejas"""
        directorio = '/public'
        cliente = '*'
        opciones = {
            'ro': True,
            'all_squash': True,
            'no_subtree_check': True,
            'anonuid': '65534',
            'anongid': '65534'
        }
        
        result = ExportsConfigParser.generar_linea_export(directorio, cliente, opciones)
        
        assert '/public' in result
        assert '*(' in result
        assert 'ro' in result
        assert 'all_squash' in result
        assert 'anonuid=65534' in result
    
    def test_parsear_opciones(self):
        """Test parsing de opciones desde string"""
        # Opciones simples
        result = ExportsConfigParser._parsear_opciones('rw,sync,no_root_squash')
        assert result == {'rw': True, 'sync': True, 'no_root_squash': True}
        
        # Opciones con valores
        result = ExportsConfigParser._parsear_opciones('ro,all_squash,anonuid=65534,anongid=65534')
        assert result['ro'] is True
        assert result['all_squash'] is True
        assert result['anonuid'] == '65534'
        assert result['anongid'] == '65534'
    
    def test_parsear_linea_export(self):
        """Test parsing de línea completa de exportación"""
        linea = '/shared/data 192.168.1.0/24(rw,sync,no_subtree_check)'
        
        directorio, clientes = ExportsConfigParser.parsear_linea_export(linea)
        
        assert directorio == '/shared/data'
        assert len(clientes) == 1
        assert clientes[0][0] == '192.168.1.0/24'
        assert clientes[0][1]['rw'] is True
        assert clientes[0][1]['sync'] is True
    
    def test_build_export_line_single_client(self):
        """Test construcción de línea con un solo cliente"""
        path = '/test'
        clients = ['192.168.1.100']
        options = {'rw': True, 'sync': True}
        
        result = build_export_line(path, clients, options)
        
        assert '/test' in result
        assert '192.168.1.100' in result
        assert 'rw' in result
    
    def test_build_export_line_multiple_clients(self):
        """Test construcción de líneas con múltiples clientes"""
        path = '/test'
        clients = ['192.168.1.100', '192.168.1.200', '10.0.0.0/8']
        options = {'ro': True, 'async': True}
        
        result = build_export_line(path, clients, options)
        
        # Debe haber una línea por cliente
        lines = result.split('\n')
        assert len(lines) == 3
        
        # Cada línea debe tener el path y opciones
        for line in lines:
            assert '/test' in line
            assert 'ro' in line
    
    def test_backup_and_restore(self):
        """Test crear backup y restaurar"""
        # Crear archivo temporal simulando /etc/exports
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.exports') as f:
            test_file = f.name
            f.write('# Test exports\n/test 192.168.1.0/24(rw)\n')
        
        try:
            # Temporalmente cambiar la ruta del archivo
            original_file = ExportsConfigParser.EXPORTS_FILE
            ExportsConfigParser.EXPORTS_FILE = test_file
            
            # Crear backup
            backup_file = ExportsConfigParser.crear_backup()
            assert backup_file is not None
            assert os.path.exists(backup_file)
            
            # Modificar archivo original
            with open(test_file, 'w') as f:
                f.write('# Modified\n/modified 10.0.0.0/8(ro)\n')
            
            # Restaurar backup
            success = ExportsConfigParser.restaurar_backup(backup_file)
            assert success is True
            
            # Verificar contenido restaurado
            with open(test_file, 'r') as f:
                content = f.read()
            assert '# Test exports' in content
            assert '/test 192.168.1.0/24' in content
            
            # Limpiar
            if os.path.exists(backup_file):
                os.unlink(backup_file)
            
        finally:
            # Restaurar ruta original
            ExportsConfigParser.EXPORTS_FILE = original_file
            if os.path.exists(test_file):
                os.unlink(test_file)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
