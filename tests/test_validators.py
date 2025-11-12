"""Tests for validators module."""
import pytest
import sys
import os
import tempfile

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.validators import NFSValidator, validate_path, validate_client, validate_uid_gid


class TestNFSValidator:
    """Tests for NFSValidator class."""
    
    def test_validar_directorio_valido(self):
        """Test validating a valid directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            valido, msg = NFSValidator.validar_directorio(tmpdir)
            assert valido is True
            assert "válido" in msg
    
    def test_validar_directorio_no_existe(self):
        """Test validating non-existent directory."""
        valido, msg = NFSValidator.validar_directorio("/path/does/not/exist")
        assert valido is False
        assert "no existe" in msg
    
    def test_validar_directorio_raiz(self):
        """Test validating root directory (should fail)."""
        valido, msg = NFSValidator.validar_directorio("/")
        assert valido is False
        assert "raíz" in msg
    
    def test_validar_directorio_vacio(self):
        """Test validating empty directory path."""
        valido, msg = NFSValidator.validar_directorio("")
        assert valido is False
        assert "no especificado" in msg
    
    def test_validar_directorio_relativo(self):
        """Test validating relative path (should fail)."""
        valido, msg = NFSValidator.validar_directorio("relative/path")
        assert valido is False
        assert "absoluta" in msg
    
    def test_validar_cliente_ip_valida(self):
        """Test validating valid IP address."""
        valido, msg = NFSValidator.validar_cliente("192.168.1.100")
        assert valido is True
        assert "válida" in msg or "válido" in msg
    
    def test_validar_cliente_subred_valida(self):
        """Test validating valid subnet."""
        valido, msg = NFSValidator.validar_cliente("192.168.1.0/24")
        assert valido is True
        assert "válida" in msg or "válido" in msg
    
    def test_validar_cliente_wildcard(self):
        """Test validating wildcard."""
        valido, msg = NFSValidator.validar_cliente("*")
        assert valido is True
        assert "válido" in msg
    
    def test_validar_cliente_hostname(self):
        """Test validating hostname."""
        valido, msg = NFSValidator.validar_cliente("server.example.com")
        assert valido is True
        assert "válido" in msg
    
    def test_validar_cliente_netgroup(self):
        """Test validating netgroup."""
        valido, msg = NFSValidator.validar_cliente("@trusted")
        assert valido is True
        assert "válido" in msg
    
    def test_validar_cliente_invalido(self):
        """Test validating invalid client."""
        valido, msg = NFSValidator.validar_cliente("not@valid!")
        assert valido is False
    
    def test_validar_cliente_vacio(self):
        """Test validating empty client."""
        valido, msg = NFSValidator.validar_cliente("")
        assert valido is False
        assert "no especificado" in msg
    
    def test_validar_opciones_validas(self):
        """Test validating valid options."""
        options = {"rw": True, "sync": True, "no_root_squash": True}
        valido, errores = NFSValidator.validar_opciones(options)
        assert valido is True
        assert len(errores) == 0
    
    def test_validar_opciones_mutuamente_excluyentes_rw_ro(self):
        """Test validating mutually exclusive rw/ro options."""
        options = {"rw": True, "ro": True}
        valido, errores = NFSValidator.validar_opciones(options)
        assert valido is False
        assert len(errores) > 0
        assert any("acceso" in err for err in errores)
    
    def test_validar_opciones_mutuamente_excluyentes_sync_async(self):
        """Test validating mutually exclusive sync/async options."""
        options = {"sync": True, "async": True}
        valido, errores = NFSValidator.validar_opciones(options)
        assert valido is False
        assert any("sincronizacion" in err for err in errores)
    
    def test_validar_opciones_anonuid_sin_all_squash(self):
        """Test validating anonuid without all_squash."""
        options = {"rw": True, "anonuid": "1000"}
        valido, errores = NFSValidator.validar_opciones(options)
        assert valido is False
        assert any("all_squash" in err for err in errores)
    
    def test_validar_opciones_anonuid_con_all_squash(self):
        """Test validating anonuid with all_squash."""
        options = {"rw": True, "all_squash": True, "anonuid": "1000"}
        valido, errores = NFSValidator.validar_opciones(options)
        assert valido is True
    
    def test_validar_opciones_anonuid_invalido(self):
        """Test validating invalid anonuid."""
        options = {"rw": True, "all_squash": True, "anonuid": "not_a_number"}
        valido, errores = NFSValidator.validar_opciones(options)
        assert valido is False
        assert any("número" in err for err in errores)
    
    def test_validar_uid_gid_valido(self):
        """Test validating valid UID/GID."""
        assert NFSValidator.validar_uid_gid("0") is True
        assert NFSValidator.validar_uid_gid("1000") is True
        assert NFSValidator.validar_uid_gid("65535") is True
    
    def test_validar_uid_gid_invalido(self):
        """Test validating invalid UID/GID."""
        assert NFSValidator.validar_uid_gid("not_a_number") is False
        assert NFSValidator.validar_uid_gid("70000") is False
        assert NFSValidator.validar_uid_gid("-1") is False


class TestWrapperFunctions:
    """Tests for wrapper functions."""
    
    def test_validate_path_wrapper(self):
        """Test validate_path wrapper function."""
        with tempfile.TemporaryDirectory() as tmpdir:
            assert validate_path(tmpdir) is True
        assert validate_path("/nonexistent") is False
    
    def test_validate_client_wrapper(self):
        """Test validate_client wrapper function."""
        assert validate_client("192.168.1.100") is True
        assert validate_client("192.168.1.0/24") is True
        assert validate_client("*") is True
        assert validate_client("invalid!@#") is False
    
    def test_validate_uid_gid_wrapper(self):
        """Test validate_uid_gid wrapper function."""
        assert validate_uid_gid("1000") is True
        assert validate_uid_gid("65535") is True
        assert validate_uid_gid("not_a_number") is False
        assert validate_uid_gid("70000") is False
