"""Tests for config_parser module."""
import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.backend.config_parser import ExportsConfigParser, build_export_line


class TestExportsConfigParser:
    """Tests for ExportsConfigParser class."""
    
    def test_parsear_opciones_simple(self):
        """Test parsing simple options string."""
        result = ExportsConfigParser._parsear_opciones("rw,sync")
        assert result == {"rw": True, "sync": True}
    
    def test_parsear_opciones_con_valores(self):
        """Test parsing options with values."""
        result = ExportsConfigParser._parsear_opciones("rw,anonuid=65534,anongid=65534")
        assert result == {"rw": True, "anonuid": "65534", "anongid": "65534"}
    
    def test_parsear_opciones_vacio(self):
        """Test parsing empty options string."""
        result = ExportsConfigParser._parsear_opciones("")
        assert result == {}
    
    def test_generar_linea_export(self):
        """Test generating export line."""
        options = {"rw": True, "sync": True, "no_root_squash": True}
        result = ExportsConfigParser.generar_linea_export("/shared", "192.168.1.0/24", options)
        assert result == "/shared 192.168.1.0/24(rw,sync,no_root_squash)"
    
    def test_generar_opciones_str_complejo(self):
        """Test generating complex options string."""
        options = {
            "rw": True,
            "sync": True,
            "no_root_squash": True,
            "no_subtree_check": True,
            "anonuid": "1000",
            "anongid": "1000"
        }
        result = ExportsConfigParser._generar_opciones_str(options)
        assert "rw" in result
        assert "sync" in result
        assert "no_root_squash" in result
        assert "no_subtree_check" in result
        assert "anonuid=1000" in result
        assert "anongid=1000" in result
    
    def test_generar_linea_export_solo_lectura(self):
        """Test generating read-only export line."""
        options = {"ro": True, "sync": True}
        result = ExportsConfigParser.generar_linea_export("/backup", "10.0.0.5", options)
        assert result == "/backup 10.0.0.5(ro,sync)"
    
    def test_parsear_linea_export_simple(self):
        """Test parsing simple export line."""
        line = "/shared 192.168.1.0/24(rw,sync,no_root_squash)"
        directorio, clientes = ExportsConfigParser.parsear_linea_export(line)
        
        assert directorio == "/shared"
        assert len(clientes) == 1
        assert clientes[0][0] == "192.168.1.0/24"
        assert clientes[0][1]["rw"] is True
        assert clientes[0][1]["sync"] is True
        assert clientes[0][1]["no_root_squash"] is True


class TestBuildExportLine:
    """Tests for build_export_line function."""
    
    def test_build_export_line_single_client(self):
        """Test building export line with single client."""
        options = {"rw": True, "sync": True}
        result = build_export_line("/data", ["192.168.1.100"], options)
        assert result == "/data 192.168.1.100(rw,sync)"
    
    def test_build_export_line_multiple_clients(self):
        """Test building export line with multiple clients."""
        options = {"ro": True, "sync": True}
        result = build_export_line("/shared", ["192.168.1.0/24", "10.0.0.5"], options)
        lines = result.split('\n')
        assert len(lines) == 2
        assert "/shared 192.168.1.0/24(ro,sync)" in lines
        assert "/shared 10.0.0.5(ro,sync)" in lines
    
    def test_build_export_line_wildcard(self):
        """Test building export line with wildcard."""
        options = {"ro": True, "all_squash": True}
        result = build_export_line("/public", ["*"], options)
        assert "/public *(ro,all_squash)" in result
