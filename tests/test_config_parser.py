"""Tests for config_parser module - testing all 13 NFS options"""
import pytest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.backend.config_parser import ExportsConfigParser, build_export_line


class TestExportsConfigParser:
    """Test ExportsConfigParser class"""
    
    def test_generar_opciones_str_rw(self):
        """Test rw option"""
        options = {"rw": True}
        result = ExportsConfigParser._generar_opciones_str(options)
        assert "rw" in result
    
    def test_generar_opciones_str_ro(self):
        """Test ro option"""
        options = {"ro": True}
        result = ExportsConfigParser._generar_opciones_str(options)
        assert "ro" in result
    
    def test_generar_opciones_str_sync(self):
        """Test sync option"""
        options = {"sync": True}
        result = ExportsConfigParser._generar_opciones_str(options)
        assert "sync" in result
    
    def test_generar_opciones_str_async(self):
        """Test async option"""
        options = {"async": True}
        result = ExportsConfigParser._generar_opciones_str(options)
        assert "async" in result
    
    def test_generar_opciones_str_no_root_squash(self):
        """Test no_root_squash option"""
        options = {"no_root_squash": True}
        result = ExportsConfigParser._generar_opciones_str(options)
        assert "no_root_squash" in result
    
    def test_generar_opciones_str_root_squash(self):
        """Test root_squash option"""
        options = {"root_squash": True}
        result = ExportsConfigParser._generar_opciones_str(options)
        assert "root_squash" in result
    
    def test_generar_opciones_str_all_squash(self):
        """Test all_squash option"""
        options = {"all_squash": True}
        result = ExportsConfigParser._generar_opciones_str(options)
        assert "all_squash" in result
    
    def test_generar_opciones_str_no_subtree_check(self):
        """Test no_subtree_check option"""
        options = {"no_subtree_check": True}
        result = ExportsConfigParser._generar_opciones_str(options)
        assert "no_subtree_check" in result
    
    def test_generar_opciones_str_subtree_check(self):
        """Test subtree_check option"""
        options = {"subtree_check": True}
        result = ExportsConfigParser._generar_opciones_str(options)
        assert "subtree_check" in result
    
    def test_generar_opciones_str_insecure(self):
        """Test insecure option"""
        options = {"insecure": True}
        result = ExportsConfigParser._generar_opciones_str(options)
        assert "insecure" in result
    
    def test_generar_opciones_str_secure(self):
        """Test secure option"""
        options = {"secure": True}
        result = ExportsConfigParser._generar_opciones_str(options)
        assert "secure" in result
    
    def test_generar_opciones_str_anonuid(self):
        """Test anonuid option"""
        options = {"anonuid": "65534"}
        result = ExportsConfigParser._generar_opciones_str(options)
        assert "anonuid=65534" in result
    
    def test_generar_opciones_str_anongid(self):
        """Test anongid option"""
        options = {"anongid": "65534"}
        result = ExportsConfigParser._generar_opciones_str(options)
        assert "anongid=65534" in result
    
    def test_generar_opciones_str_multiple_basic(self):
        """Test combination of basic options"""
        options = {
            "rw": True,
            "sync": True,
            "no_root_squash": True
        }
        result = ExportsConfigParser._generar_opciones_str(options)
        assert "rw" in result
        assert "sync" in result
        assert "no_root_squash" in result
        # Check they're comma separated
        parts = result.split(',')
        assert len(parts) == 3
    
    def test_generar_opciones_str_all_options(self):
        """Test all options together (though some are mutually exclusive in practice)"""
        options = {
            "rw": True,
            "sync": True,
            "no_root_squash": True,
            "all_squash": True,
            "no_subtree_check": True,
            "secure": True,
            "anonuid": "65534",
            "anongid": "65534"
        }
        result = ExportsConfigParser._generar_opciones_str(options)
        assert "rw" in result
        assert "sync" in result
        assert "no_root_squash" in result
        assert "all_squash" in result
        assert "no_subtree_check" in result
        assert "secure" in result
        assert "anonuid=65534" in result
        assert "anongid=65534" in result
    
    def test_generar_opciones_str_with_anon_ids(self):
        """Test anonymous UID/GID"""
        options = {
            "ro": True,
            "all_squash": True,
            "anonuid": "1000",
            "anongid": "1000"
        }
        result = ExportsConfigParser._generar_opciones_str(options)
        assert "ro" in result
        assert "all_squash" in result
        assert "anonuid=1000" in result
        assert "anongid=1000" in result
    
    def test_generar_linea_export_simple(self):
        """Test generating simple export line"""
        options = {"rw": True, "sync": True}
        result = ExportsConfigParser.generar_linea_export("/shared", "192.168.1.0/24", options)
        assert result == "/shared 192.168.1.0/24(rw,sync)"
    
    def test_generar_linea_export_complex(self):
        """Test generating complex export line"""
        options = {
            "ro": True,
            "async": True,
            "all_squash": True,
            "no_subtree_check": True,
            "anonuid": "65534",
            "anongid": "65534"
        }
        result = ExportsConfigParser.generar_linea_export("/public", "*", options)
        expected_parts = ["ro", "async", "all_squash", "no_subtree_check", "anonuid=65534", "anongid=65534"]
        assert result.startswith("/public *(")
        assert result.endswith(")")
        for part in expected_parts:
            assert part in result
    
    def test_generar_linea_export_hostname(self):
        """Test export line with hostname"""
        options = {"rw": True, "no_root_squash": True}
        result = ExportsConfigParser.generar_linea_export("/data", "server.local", options)
        assert result == "/data server.local(rw,no_root_squash)"
    
    def test_parsear_opciones(self):
        """Test parsing options string"""
        options_str = "rw,sync,no_root_squash"
        result = ExportsConfigParser._parsear_opciones(options_str)
        assert result == {"rw": True, "sync": True, "no_root_squash": True}
    
    def test_parsear_opciones_with_values(self):
        """Test parsing options with values"""
        options_str = "ro,all_squash,anonuid=65534,anongid=65534"
        result = ExportsConfigParser._parsear_opciones(options_str)
        assert result["ro"] is True
        assert result["all_squash"] is True
        assert result["anonuid"] == "65534"
        assert result["anongid"] == "65534"


class TestBuildExportLine:
    """Test build_export_line function"""
    
    def test_build_export_line_single_client(self):
        """Test building export line with single client"""
        options = {"rw": True, "sync": True}
        result = build_export_line("/shared", ["192.168.1.10"], options)
        assert result == "/shared 192.168.1.10(rw,sync)"
    
    def test_build_export_line_multiple_clients(self):
        """Test building export line with multiple clients"""
        options = {"rw": True, "sync": True}
        clients = ["192.168.1.10", "192.168.1.11", "192.168.1.12"]
        result = build_export_line("/shared", clients, options)
        lines = result.split('\n')
        assert len(lines) == 3
        assert lines[0] == "/shared 192.168.1.10(rw,sync)"
        assert lines[1] == "/shared 192.168.1.11(rw,sync)"
        assert lines[2] == "/shared 192.168.1.12(rw,sync)"
    
    def test_build_export_line_subnet(self):
        """Test building export line with subnet"""
        options = {"ro": True, "async": True}
        result = build_export_line("/backups", ["10.0.0.0/24"], options)
        assert result == "/backups 10.0.0.0/24(ro,async)"
    
    def test_build_export_line_wildcard(self):
        """Test building export line with wildcard"""
        options = {"ro": True, "all_squash": True}
        result = build_export_line("/public", ["*"], options)
        assert result == "/public *(ro,all_squash)"
    
    def test_build_export_line_all_13_options(self):
        """Test export line with representation of all 13 options"""
        # Using compatible options (not mutually exclusive)
        options = {
            "rw": True,
            "sync": True,
            "no_root_squash": True,
            "all_squash": True,
            "no_subtree_check": True,
            "insecure": True,
            "anonuid": "1000",
            "anongid": "1000"
        }
        result = build_export_line("/test", ["192.168.1.0/24"], options)
        # Verify all specified options are present
        assert "rw" in result
        assert "sync" in result
        assert "no_root_squash" in result
        assert "all_squash" in result
        assert "no_subtree_check" in result
        assert "insecure" in result
        assert "anonuid=1000" in result
        assert "anongid=1000" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
