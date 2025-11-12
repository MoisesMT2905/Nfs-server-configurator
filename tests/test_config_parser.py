"""Tests for ExportsConfigParser"""

import pytest
import os
import tempfile
from datetime import datetime
from src.backend.config_parser import ExportsConfigParser, build_export_line


class TestExportsConfigParser:
    """Test suite for ExportsConfigParser class"""
    
    def test_parsear_opciones_simple(self):
        """Test parsing simple options string"""
        opciones_str = "rw,sync,no_root_squash"
        result = ExportsConfigParser._parsear_opciones(opciones_str)
        
        assert result == {
            'rw': True,
            'sync': True,
            'no_root_squash': True
        }
    
    def test_parsear_opciones_con_valores(self):
        """Test parsing options with values"""
        opciones_str = "rw,sync,anonuid=1000,anongid=1000"
        result = ExportsConfigParser._parsear_opciones(opciones_str)
        
        assert result == {
            'rw': True,
            'sync': True,
            'anonuid': '1000',
            'anongid': '1000'
        }
    
    def test_parsear_opciones_vacio(self):
        """Test parsing empty options"""
        result = ExportsConfigParser._parsear_opciones("")
        assert result == {}
    
    def test_generar_opciones_str_basico(self):
        """Test generating basic options string"""
        opciones = {
            'rw': True,
            'sync': True,
            'no_root_squash': True
        }
        result = ExportsConfigParser._generar_opciones_str(opciones)
        assert result == "rw,sync,no_root_squash"
    
    def test_generar_opciones_str_con_anonuid(self):
        """Test generating options with anonuid/anongid"""
        opciones = {
            'ro': True,
            'all_squash': True,
            'anonuid': '65534',
            'anongid': '65534'
        }
        result = ExportsConfigParser._generar_opciones_str(opciones)
        assert 'ro' in result
        assert 'all_squash' in result
        assert 'anonuid=65534' in result
        assert 'anongid=65534' in result
    
    def test_generar_opciones_str_orden(self):
        """Test that options are in recommended order"""
        opciones = {
            'secure': True,
            'sync': True,
            'rw': True,
            'no_subtree_check': True
        }
        result = ExportsConfigParser._generar_opciones_str(opciones)
        # rw should come before sync in the recommended order
        assert result.index('rw') < result.index('sync')
    
    def test_generar_linea_export(self):
        """Test generating complete export line"""
        directorio = "/srv/nfs/share"
        cliente = "192.168.1.0/24"
        opciones = {
            'rw': True,
            'sync': True,
            'no_subtree_check': True
        }
        
        result = ExportsConfigParser.generar_linea_export(directorio, cliente, opciones)
        
        assert directorio in result
        assert cliente in result
        assert 'rw' in result
        assert 'sync' in result
        assert 'no_subtree_check' in result
        # Check format: path client(options)
        assert '(' in result and ')' in result
    
    def test_parsear_linea_export_simple(self):
        """Test parsing simple export line"""
        linea = "/srv/nfs 192.168.1.0/24(rw,sync)"
        
        directorio, clientes = ExportsConfigParser.parsear_linea_export(linea)
        
        assert directorio == "/srv/nfs"
        assert len(clientes) == 1
        assert clientes[0][0] == "192.168.1.0/24"
        assert clientes[0][1]['rw'] is True
        assert clientes[0][1]['sync'] is True
    
    def test_parsear_linea_export_multiple_clientes(self):
        """Test parsing export line with multiple clients"""
        linea = "/srv/nfs 192.168.1.0/24(rw,sync) 10.0.0.5(ro)"
        
        directorio, clientes = ExportsConfigParser.parsear_linea_export(linea)
        
        assert directorio == "/srv/nfs"
        assert len(clientes) == 2
        assert clientes[0][0] == "192.168.1.0/24"
        assert clientes[1][0] == "10.0.0.5"
    
    def test_parsear_linea_export_invalida(self):
        """Test parsing invalid export line without parentheses"""
        linea = "invalid line without proper format"

        directorio, clientes = ExportsConfigParser.parsear_linea_export(linea)

        # The parser will split on whitespace, but won't find any (options) patterns
        # So it returns the directory but empty clients list
        assert directorio == "invalid"
        assert clientes == []
    
    def test_crear_backup(self, tmp_path, monkeypatch):
        """Test backup creation"""
        # Create a temporary exports file
        exports_file = tmp_path / "exports"
        exports_file.write_text("/srv/nfs 192.168.1.0/24(rw,sync)\n")
        
        # Mock the EXPORTS_FILE constant
        monkeypatch.setattr(ExportsConfigParser, 'EXPORTS_FILE', str(exports_file))
        
        # Create backup
        backup_file = ExportsConfigParser.crear_backup()
        
        # Verify backup was created
        assert backup_file is not None
        assert os.path.exists(backup_file)
        assert backup_file.startswith(str(exports_file))
        
        # Verify backup content matches original
        with open(backup_file, 'r') as f:
            backup_content = f.read()
        with open(exports_file, 'r') as f:
            original_content = f.read()
        assert backup_content == original_content
    
    def test_restaurar_backup(self, tmp_path, monkeypatch):
        """Test backup restoration"""
        # Create temporary files
        exports_file = tmp_path / "exports"
        backup_file = tmp_path / "exports.backup"
        
        # Write different content to each
        exports_file.write_text("/srv/nfs 192.168.1.0/24(rw,sync)\n")
        backup_file.write_text("/srv/nfs 10.0.0.0/8(ro)\n")
        
        # Mock the EXPORTS_FILE constant
        monkeypatch.setattr(ExportsConfigParser, 'EXPORTS_FILE', str(exports_file))
        
        # Restore backup
        success = ExportsConfigParser.restaurar_backup(str(backup_file))
        
        # Verify restoration succeeded
        assert success is True
        
        # Verify content was restored
        with open(exports_file, 'r') as f:
            content = f.read()
        assert content == "/srv/nfs 10.0.0.0/8(ro)\n"
    
    def test_restaurar_backup_no_existe(self):
        """Test restoring non-existent backup"""
        result = ExportsConfigParser.restaurar_backup("/non/existent/file")
        assert result is False


class TestBuildExportLine:
    """Test suite for build_export_line helper function"""
    
    def test_build_export_line_single_client(self):
        """Test building export line for single client"""
        path = "/srv/nfs"
        clients = ["192.168.1.0/24"]
        options = {'rw': True, 'sync': True}
        
        result = build_export_line(path, clients, options)
        
        assert path in result
        assert clients[0] in result
        assert 'rw' in result
        assert 'sync' in result
    
    def test_build_export_line_multiple_clients(self):
        """Test building export line for multiple clients"""
        path = "/srv/nfs"
        clients = ["192.168.1.0/24", "10.0.0.5"]
        options = {'rw': True, 'sync': True}
        
        result = build_export_line(path, clients, options)
        
        # Should have separate lines for each client
        lines = result.split('\n')
        assert len(lines) == 2
        assert clients[0] in result
        assert clients[1] in result
    
    def test_build_export_line_empty_clients(self):
        """Test building export line with empty clients list"""
        path = "/srv/nfs"
        clients = []
        options = {'rw': True}
        
        result = build_export_line(path, clients, options)
        
        # Should return empty string
        assert result == ""
    
    def test_build_export_line_complex_options(self):
        """Test building export line with complex options"""
        path = "/srv/nfs"
        clients = ["*"]
        options = {
            'ro': True,
            'all_squash': True,
            'anonuid': '65534',
            'anongid': '65534',
            'secure': True,
            'no_subtree_check': True
        }
        
        result = build_export_line(path, clients, options)
        
        assert 'ro' in result
        assert 'all_squash' in result
        assert 'anonuid=65534' in result
        assert 'anongid=65534' in result
        assert 'secure' in result
        assert 'no_subtree_check' in result
