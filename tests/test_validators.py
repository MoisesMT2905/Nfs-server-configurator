"""Tests for validators module"""
import pytest
import sys
import os
import tempfile

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.validators import (
    validate_path, validate_client, validate_ip_or_cidr, 
    validate_hostname, validate_uid_gid, NFSValidator
)


class TestValidatePath:
    """Test validate_path function"""
    
    def test_validate_path_valid_directory(self):
        """Test with valid directory"""
        # Use /tmp which should exist on all systems
        assert validate_path("/tmp") is True
    
    def test_validate_path_nonexistent(self):
        """Test with nonexistent path"""
        assert validate_path("/nonexistent/path/that/does/not/exist") is False
    
    def test_validate_path_empty(self):
        """Test with empty path"""
        assert validate_path("") is False
    
    def test_validate_path_root(self):
        """Test that root directory is rejected"""
        assert validate_path("/") is False
    
    def test_validate_path_relative(self):
        """Test with relative path"""
        assert validate_path("relative/path") is False
    
    def test_validate_path_file(self):
        """Test with file instead of directory"""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_file = f.name
        try:
            assert validate_path(temp_file) is False
        finally:
            os.unlink(temp_file)


class TestValidateClient:
    """Test validate_client function"""
    
    def test_validate_client_valid_ip(self):
        """Test with valid IP address"""
        assert validate_client("192.168.1.10") is True
        assert validate_client("10.0.0.1") is True
        assert validate_client("172.16.0.1") is True
    
    def test_validate_client_invalid_ip(self):
        """Test with invalid IP address"""
        assert validate_client("256.1.1.1") is False
        assert validate_client("192.168.1.256") is False
        assert validate_client("192.168") is False
    
    def test_validate_client_valid_subnet(self):
        """Test with valid subnet"""
        assert validate_client("192.168.1.0/24") is True
        assert validate_client("10.0.0.0/8") is True
        assert validate_client("172.16.0.0/16") is True
    
    def test_validate_client_invalid_subnet(self):
        """Test with invalid subnet"""
        assert validate_client("192.168.1.0/33") is False
        assert validate_client("192.168.1.0/-1") is False
        assert validate_client("256.1.1.0/24") is False
    
    def test_validate_client_wildcard(self):
        """Test with wildcard"""
        assert validate_client("*") is True
    
    def test_validate_client_netgroup(self):
        """Test with netgroup"""
        assert validate_client("@mygroup") is True
        assert validate_client("@servers") is True
    
    def test_validate_client_valid_hostname(self):
        """Test with valid hostname"""
        assert validate_client("server.example.com") is True
        assert validate_client("host1") is True
        assert validate_client("my-server.local") is True
    
    def test_validate_client_invalid_hostname(self):
        """Test with invalid hostname"""
        assert validate_client("-invalid") is False
        assert validate_client("invalid-") is False
        assert validate_client("in valid") is False
        assert validate_client("invalid..com") is False
    
    def test_validate_client_empty(self):
        """Test with empty client"""
        assert validate_client("") is False


class TestValidateIpOrCidr:
    """Test validate_ip_or_cidr function"""
    
    def test_validate_ip_or_cidr_valid_ip(self):
        """Test with valid IP"""
        assert validate_ip_or_cidr("192.168.1.1") is True
        assert validate_ip_or_cidr("10.0.0.1") is True
    
    def test_validate_ip_or_cidr_invalid_ip(self):
        """Test with invalid IP"""
        assert validate_ip_or_cidr("256.1.1.1") is False
        assert validate_ip_or_cidr("invalid") is False
    
    def test_validate_ip_or_cidr_valid_cidr(self):
        """Test with valid CIDR"""
        assert validate_ip_or_cidr("192.168.1.0/24") is True
        assert validate_ip_or_cidr("10.0.0.0/8") is True
    
    def test_validate_ip_or_cidr_invalid_cidr(self):
        """Test with invalid CIDR"""
        assert validate_ip_or_cidr("192.168.1.0/33") is False
        assert validate_ip_or_cidr("256.1.1.0/24") is False


class TestValidateHostname:
    """Test validate_hostname function"""
    
    def test_validate_hostname_valid(self):
        """Test with valid hostnames"""
        assert validate_hostname("server") is True
        assert validate_hostname("server1") is True
        assert validate_hostname("my-server") is True
        assert validate_hostname("server.example.com") is True
        assert validate_hostname("sub.domain.example.com") is True
    
    def test_validate_hostname_invalid(self):
        """Test with invalid hostnames"""
        assert validate_hostname("-server") is False
        assert validate_hostname("server-") is False
        assert validate_hostname("ser ver") is False
        assert validate_hostname("server..com") is False
        assert validate_hostname("") is False
    
    def test_validate_hostname_special_chars(self):
        """Test hostname with special characters"""
        assert validate_hostname("server_1") is False  # Underscore not allowed
        assert validate_hostname("server!") is False


class TestValidateUidGid:
    """Test validate_uid_gid function"""
    
    def test_validate_uid_gid_valid(self):
        """Test with valid UID/GID"""
        assert validate_uid_gid("0") is True
        assert validate_uid_gid("1000") is True
        assert validate_uid_gid("65534") is True
        assert validate_uid_gid("65535") is True
    
    def test_validate_uid_gid_invalid_range(self):
        """Test with out of range values"""
        assert validate_uid_gid("-1") is False
        assert validate_uid_gid("65536") is False
        assert validate_uid_gid("100000") is False
    
    def test_validate_uid_gid_invalid_format(self):
        """Test with invalid format"""
        assert validate_uid_gid("abc") is False
        assert validate_uid_gid("12.34") is False
        assert validate_uid_gid("") is False
        assert validate_uid_gid("1000x") is False


class TestNFSValidator:
    """Test NFSValidator class"""
    
    def test_validar_opciones_valid_single_group(self):
        """Test valid options from single groups"""
        options = {"rw": True, "sync": True}
        valid, errors = NFSValidator.validar_opciones(options)
        assert valid is True
        assert len(errors) == 0
    
    def test_validar_opciones_mutually_exclusive_rw_ro(self):
        """Test mutually exclusive rw/ro"""
        options = {"rw": True, "ro": True}
        valid, errors = NFSValidator.validar_opciones(options)
        assert valid is False
        assert len(errors) > 0
        assert any("acceso" in err for err in errors)
    
    def test_validar_opciones_mutually_exclusive_sync_async(self):
        """Test mutually exclusive sync/async"""
        options = {"sync": True, "async": True}
        valid, errors = NFSValidator.validar_opciones(options)
        assert valid is False
        assert len(errors) > 0
    
    def test_validar_opciones_mutually_exclusive_root_squash(self):
        """Test mutually exclusive root_squash options"""
        options = {"no_root_squash": True, "root_squash": True}
        valid, errors = NFSValidator.validar_opciones(options)
        assert valid is False
        assert len(errors) > 0
    
    def test_validar_opciones_mutually_exclusive_subtree(self):
        """Test mutually exclusive subtree options"""
        options = {"no_subtree_check": True, "subtree_check": True}
        valid, errors = NFSValidator.validar_opciones(options)
        assert valid is False
        assert len(errors) > 0
    
    def test_validar_opciones_mutually_exclusive_secure(self):
        """Test mutually exclusive secure/insecure"""
        options = {"secure": True, "insecure": True}
        valid, errors = NFSValidator.validar_opciones(options)
        assert valid is False
        assert len(errors) > 0
    
    def test_validar_opciones_anonuid_requires_all_squash(self):
        """Test that anonuid requires all_squash"""
        options = {"rw": True, "anonuid": "65534"}
        valid, errors = NFSValidator.validar_opciones(options)
        assert valid is False
        assert any("all_squash" in err for err in errors)
    
    def test_validar_opciones_anongid_requires_all_squash(self):
        """Test that anongid requires all_squash"""
        options = {"rw": True, "anongid": "65534"}
        valid, errors = NFSValidator.validar_opciones(options)
        assert valid is False
        assert any("all_squash" in err for err in errors)
    
    def test_validar_opciones_valid_with_all_squash(self):
        """Test valid options with all_squash and anon IDs"""
        options = {
            "ro": True,
            "all_squash": True,
            "anonuid": "65534",
            "anongid": "65534"
        }
        valid, errors = NFSValidator.validar_opciones(options)
        assert valid is True
        assert len(errors) == 0
    
    def test_validar_opciones_invalid_anonuid(self):
        """Test invalid anonuid value"""
        options = {
            "ro": True,
            "all_squash": True,
            "anonuid": "invalid"
        }
        valid, errors = NFSValidator.validar_opciones(options)
        assert valid is False
        assert any("anonuid" in err for err in errors)
    
    def test_validar_opciones_invalid_anongid(self):
        """Test invalid anongid value"""
        options = {
            "ro": True,
            "all_squash": True,
            "anongid": "abc"
        }
        valid, errors = NFSValidator.validar_opciones(options)
        assert valid is False
        assert any("anongid" in err for err in errors)
    
    def test_validar_directorio_valid(self):
        """Test valid directory validation"""
        valid, msg = NFSValidator.validar_directorio("/tmp")
        assert valid is True
    
    def test_validar_directorio_root_rejected(self):
        """Test that root directory is rejected"""
        valid, msg = NFSValidator.validar_directorio("/")
        assert valid is False
    
    def test_validar_cliente_valid_ip(self):
        """Test valid client IP"""
        valid, msg = NFSValidator.validar_cliente("192.168.1.10")
        assert valid is True
    
    def test_validar_cliente_valid_subnet(self):
        """Test valid client subnet"""
        valid, msg = NFSValidator.validar_cliente("192.168.1.0/24")
        assert valid is True
    
    def test_validar_cliente_wildcard(self):
        """Test wildcard client"""
        valid, msg = NFSValidator.validar_cliente("*")
        assert valid is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
