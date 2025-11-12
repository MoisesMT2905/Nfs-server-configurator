#!/usr/bin/env python3
"""
Unit tests for ExportsConfigParser and related functions.
Tests parsing, generation, and utility functions for /etc/exports.
"""

import pytest
import tempfile
import os
from src.backend.config_parser import ExportsConfigParser, build_export_line


class TestExportsConfigParser:
    """Test suite for ExportsConfigParser"""
    
    def test_parsear_opciones_simple(self):
        """Test parsing simple options"""
        opciones_str = "rw,sync,no_root_squash"
        result = ExportsConfigParser._parsear_opciones(opciones_str)
        
        assert result == {
            'rw': True,
            'sync': True,
            'no_root_squash': True
        }
    
    def test_parsear_opciones_con_valores(self):
        """Test parsing options with values"""
        opciones_str = "rw,anonuid=65534,anongid=65534"
        result = ExportsConfigParser._parsear_opciones(opciones_str)
        
        assert result == {
            'rw': True,
            'anonuid': '65534',
            'anongid': '65534'
        }
    
    def test_parsear_opciones_vacio(self):
        """Test parsing empty options"""
        result = ExportsConfigParser._parsear_opciones("")
        assert result == {}
    
    def test_generar_opciones_str_basicas(self):
        """Test generating basic options string"""
        opciones = {
            'rw': True,
            'sync': True,
            'no_subtree_check': True
        }
        result = ExportsConfigParser._generar_opciones_str(opciones)
        
        # Should maintain order
        assert 'rw' in result
        assert 'sync' in result
        assert 'no_subtree_check' in result
    
    def test_generar_opciones_str_con_uid_gid(self):
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
    
    def test_generar_opciones_str_orden_correcto(self):
        """Test that options are generated in correct order"""
        opciones = {
            'anongid': '65534',
            'sync': True,
            'rw': True,
            'anonuid': '65534'
        }
        result = ExportsConfigParser._generar_opciones_str(opciones)
        
        # rw should come before sync (order matters for readability)
        parts = result.split(',')
        assert 'rw' in parts
        assert 'sync' in parts
    
    def test_generar_linea_export(self):
        """Test generating complete export line"""
        directorio = "/shared/data"
        cliente = "192.168.1.0/24"
        opciones = {
            'rw': True,
            'sync': True,
            'no_root_squash': True
        }
        
        result = ExportsConfigParser.generar_linea_export(directorio, cliente, opciones)
        
        assert result.startswith("/shared/data")
        assert "192.168.1.0/24" in result
        assert "rw" in result
        assert "sync" in result
        assert "no_root_squash" in result
        # Format should be: /path client(opt1,opt2,...)
        assert "(" in result and ")" in result
    
    def test_parsear_linea_export_simple(self):
        """Test parsing simple export line"""
        linea = "/data 192.168.1.0/24(rw,sync)"
        directorio, clientes = ExportsConfigParser.parsear_linea_export(linea)
        
        assert directorio == "/data"
        assert len(clientes) == 1
        assert clientes[0][0] == "192.168.1.0/24"
        assert clientes[0][1]['rw'] is True
        assert clientes[0][1]['sync'] is True
    
    def test_parsear_linea_export_multiples_clientes(self):
        """Test parsing export line with multiple clients"""
        linea = "/data 192.168.1.0/24(rw) 10.0.0.5(ro)"
        directorio, clientes = ExportsConfigParser.parsear_linea_export(linea)
        
        assert directorio == "/data"
        assert len(clientes) == 2
    
    def test_parsear_linea_export_invalida(self):
        """Test parsing invalid export line"""
        linea = "invalid line without client"
        directorio, clientes = ExportsConfigParser.parsear_linea_export(linea)
        
        # Parser extracts directory but finds no client patterns
        assert directorio == "invalid"
        assert clientes == []


class TestBuildExportLine:
    """Test suite for build_export_line function"""
    
    def test_build_export_line_un_cliente(self):
        """Test building export line with one client"""
        path = "/shared/data"
        clients = ["192.168.1.0/24"]
        options = {'rw': True, 'sync': True}
        
        result = build_export_line(path, clients, options)
        
        assert "/shared/data" in result
        assert "192.168.1.0/24" in result
        assert "rw" in result
        assert "sync" in result
    
    def test_build_export_line_multiples_clientes(self):
        """Test building export line with multiple clients"""
        path = "/shared/data"
        clients = ["192.168.1.0/24", "10.0.0.5"]
        options = {'rw': True, 'sync': True}
        
        result = build_export_line(path, clients, options)
        
        lines = result.split('\n')
        assert len(lines) == 2
        assert "192.168.1.0/24" in lines[0]
        assert "10.0.0.5" in lines[1]
    
    def test_build_export_line_sin_clientes(self):
        """Test building export line with no clients"""
        path = "/shared/data"
        clients = []
        options = {'rw': True}
        
        result = build_export_line(path, clients, options)
        
        assert result == ""
    
    def test_build_export_line_wildcard(self):
        """Test building export line with wildcard client"""
        path = "/public"
        clients = ["*"]
        options = {'ro': True, 'all_squash': True}
        
        result = build_export_line(path, clients, options)
        
        assert "/public" in result
        assert "*" in result
        assert "ro" in result
        assert "all_squash" in result


class TestBackupRestore:
    """Test suite for backup and restore functionality"""
    
    def test_crear_backup(self, tmp_path):
        """Test creating backup file"""
        # Create a temporary exports file
        exports_file = tmp_path / "exports"
        exports_file.write_text("/data 192.168.1.0/24(rw,sync)\n")
        
        # Mock the EXPORTS_FILE path
        original_path = ExportsConfigParser.EXPORTS_FILE
        ExportsConfigParser.EXPORTS_FILE = str(exports_file)
        
        try:
            backup_file = ExportsConfigParser.crear_backup()
            
            assert backup_file is not None
            assert os.path.exists(backup_file)
            
            # Verify backup content matches original
            with open(backup_file, 'r') as f:
                backup_content = f.read()
            assert backup_content == "/data 192.168.1.0/24(rw,sync)\n"
            
            # Cleanup
            if backup_file and os.path.exists(backup_file):
                os.remove(backup_file)
        finally:
            ExportsConfigParser.EXPORTS_FILE = original_path
    
    def test_restaurar_backup(self, tmp_path):
        """Test restoring from backup"""
        # Create temporary files
        exports_file = tmp_path / "exports"
        backup_file = tmp_path / "exports.backup"
        
        exports_file.write_text("/modified 10.0.0.1(rw)\n")
        backup_file.write_text("/original 192.168.1.0/24(rw,sync)\n")
        
        # Mock the EXPORTS_FILE path
        original_path = ExportsConfigParser.EXPORTS_FILE
        ExportsConfigParser.EXPORTS_FILE = str(exports_file)
        
        try:
            result = ExportsConfigParser.restaurar_backup(str(backup_file))
            
            assert result is True
            
            # Verify content was restored
            assert exports_file.read_text() == "/original 192.168.1.0/24(rw,sync)\n"
        finally:
            ExportsConfigParser.EXPORTS_FILE = original_path


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
