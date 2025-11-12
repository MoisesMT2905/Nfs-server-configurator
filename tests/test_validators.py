"""Tests for NFSValidator"""

import pytest
import os
import tempfile
from src.utils.validators import NFSValidator, validate_path, validate_client, validate_uid_gid


class TestNFSValidator:
    """Test suite for NFSValidator class"""
    
    def test_validar_directorio_existente(self, tmp_path):
        """Test validating existing directory"""
        test_dir = tmp_path / "test_share"
        test_dir.mkdir()
        
        valid, message = NFSValidator.validar_directorio(str(test_dir))
        
        assert valid is True
        assert "válido" in message.lower()
    
    def test_validar_directorio_no_existe(self):
        """Test validating non-existent directory"""
        valid, message = NFSValidator.validar_directorio("/non/existent/path")
        
        assert valid is False
        assert "no existe" in message.lower()
    
    def test_validar_directorio_raiz(self):
        """Test that root directory cannot be exported"""
        valid, message = NFSValidator.validar_directorio("/")
        
        assert valid is False
        assert "raíz" in message.lower()
    
    def test_validar_directorio_relativo(self):
        """Test that relative paths are rejected"""
        valid, message = NFSValidator.validar_directorio("relative/path")
        
        assert valid is False
        assert "absoluta" in message.lower()
    
    def test_validar_directorio_vacio(self):
        """Test empty directory path"""
        valid, message = NFSValidator.validar_directorio("")
        
        assert valid is False
        assert "no especificado" in message.lower()
    
    def test_validar_directorio_es_archivo(self, tmp_path):
        """Test that files are rejected"""
        test_file = tmp_path / "test_file"
        test_file.write_text("test")
        
        valid, message = NFSValidator.validar_directorio(str(test_file))
        
        assert valid is False
        assert "no es un directorio" in message.lower()
    
    def test_validar_cliente_ip_valida(self):
        """Test validating valid IP address"""
        valid, message = NFSValidator.validar_cliente("192.168.1.10")
        
        assert valid is True
        assert "válida" in message.lower()
    
    def test_validar_cliente_subred_valida(self):
        """Test validating valid subnet"""
        valid, message = NFSValidator.validar_cliente("192.168.1.0/24")
        
        assert valid is True
        assert "válida" in message.lower() or "subred" in message.lower()
    
    def test_validar_cliente_hostname_valido(self):
        """Test validating valid hostname"""
        valid, message = NFSValidator.validar_cliente("server.example.com")
        
        assert valid is True
        assert "válido" in message.lower()
    
    def test_validar_cliente_wildcard(self):
        """Test wildcard client"""
        valid, message = NFSValidator.validar_cliente("*")
        
        assert valid is True
        assert "wildcard" in message.lower()
    
    def test_validar_cliente_netgroup(self):
        """Test netgroup client"""
        valid, message = NFSValidator.validar_cliente("@trusted")
        
        assert valid is True
        assert "netgroup" in message.lower()
    
    def test_validar_cliente_invalido(self):
        """Test invalid client format"""
        valid, message = NFSValidator.validar_cliente("invalid@#$format")
        
        assert valid is False
        assert "inválido" in message.lower()
    
    def test_validar_cliente_vacio(self):
        """Test empty client"""
        valid, message = NFSValidator.validar_cliente("")
        
        assert valid is False
        assert "no especificado" in message.lower()
    
    def test_validar_cliente_ip_invalida(self):
        """Test invalid IP address"""
        valid, message = NFSValidator.validar_cliente("999.999.999.999")
        
        assert valid is False
    
    def test_validar_cliente_subred_invalida(self):
        """Test invalid subnet"""
        valid, message = NFSValidator.validar_cliente("192.168.1.0/99")
        
        assert valid is False
        assert "subred inválida" in message.lower()
    
    def test_validar_opciones_validas(self):
        """Test validating valid options"""
        opciones = {
            'rw': True,
            'sync': True,
            'no_root_squash': True
        }
        
        valid, errores = NFSValidator.validar_opciones(opciones)
        
        assert valid is True
        assert len(errores) == 0
    
    def test_validar_opciones_conflicto_rw_ro(self):
        """Test that rw and ro cannot be selected together"""
        opciones = {
            'rw': True,
            'ro': True
        }
        
        valid, errores = NFSValidator.validar_opciones(opciones)
        
        assert valid is False
        assert any('acceso' in error.lower() for error in errores)
    
    def test_validar_opciones_conflicto_sync_async(self):
        """Test that sync and async cannot be selected together"""
        opciones = {
            'sync': True,
            'async': True
        }
        
        valid, errores = NFSValidator.validar_opciones(opciones)
        
        assert valid is False
        assert any('sincronizacion' in error.lower() for error in errores)
    
    def test_validar_opciones_conflicto_root_squash(self):
        """Test that no_root_squash and root_squash cannot be selected together"""
        opciones = {
            'no_root_squash': True,
            'root_squash': True
        }
        
        valid, errores = NFSValidator.validar_opciones(opciones)
        
        assert valid is False
        assert any('root_squash' in error.lower() for error in errores)
    
    def test_validar_opciones_conflicto_subtree(self):
        """Test subtree check conflict"""
        opciones = {
            'no_subtree_check': True,
            'subtree_check': True
        }
        
        valid, errores = NFSValidator.validar_opciones(opciones)
        
        assert valid is False
        assert any('subtree' in error.lower() for error in errores)
    
    def test_validar_opciones_conflicto_puertos(self):
        """Test secure/insecure conflict"""
        opciones = {
            'secure': True,
            'insecure': True
        }
        
        valid, errores = NFSValidator.validar_opciones(opciones)
        
        assert valid is False
        assert any('puertos' in error.lower() for error in errores)
    
    def test_validar_opciones_anonuid_sin_all_squash(self):
        """Test that anonuid requires all_squash"""
        opciones = {
            'rw': True,
            'anonuid': '1000'
        }
        
        valid, errores = NFSValidator.validar_opciones(opciones)
        
        assert valid is False
        assert any('anonuid' in error and 'all_squash' in error for error in errores)
    
    def test_validar_opciones_anongid_sin_all_squash(self):
        """Test that anongid requires all_squash"""
        opciones = {
            'rw': True,
            'anongid': '1000'
        }
        
        valid, errores = NFSValidator.validar_opciones(opciones)
        
        assert valid is False
        assert any('anongid' in error and 'all_squash' in error for error in errores)
    
    def test_validar_opciones_anonuid_valido(self):
        """Test valid anonuid with all_squash"""
        opciones = {
            'ro': True,
            'all_squash': True,
            'anonuid': '65534'
        }
        
        valid, errores = NFSValidator.validar_opciones(opciones)
        
        assert valid is True
        assert len(errores) == 0
    
    def test_validar_opciones_anonuid_invalido(self):
        """Test invalid anonuid format"""
        opciones = {
            'ro': True,
            'all_squash': True,
            'anonuid': 'not_a_number'
        }
        
        valid, errores = NFSValidator.validar_opciones(opciones)
        
        assert valid is False
        assert any('anonuid' in error and 'número' in error for error in errores)
    
    def test_validar_opciones_anongid_invalido(self):
        """Test invalid anongid format"""
        opciones = {
            'ro': True,
            'all_squash': True,
            'anongid': 'invalid'
        }
        
        valid, errores = NFSValidator.validar_opciones(opciones)
        
        assert valid is False
        assert any('anongid' in error and 'número' in error for error in errores)
    
    def test_validar_opciones_desconocidas(self):
        """Test unknown options are rejected"""
        opciones = {
            'rw': True,
            'unknown_option': True
        }
        
        valid, errores = NFSValidator.validar_opciones(opciones)
        
        assert valid is False
        assert any('desconocida' in error.lower() for error in errores)
    
    def test_validar_uid_gid_valido(self):
        """Test valid UID/GID"""
        assert NFSValidator.validar_uid_gid("0") is True
        assert NFSValidator.validar_uid_gid("1000") is True
        assert NFSValidator.validar_uid_gid("65535") is True
    
    def test_validar_uid_gid_invalido(self):
        """Test invalid UID/GID"""
        assert NFSValidator.validar_uid_gid("-1") is False
        assert NFSValidator.validar_uid_gid("65536") is False
        assert NFSValidator.validar_uid_gid("abc") is False
        assert NFSValidator.validar_uid_gid("") is False


class TestValidatorHelpers:
    """Test suite for validator helper functions"""
    
    def test_validate_path(self, tmp_path):
        """Test validate_path helper"""
        test_dir = tmp_path / "test"
        test_dir.mkdir()
        
        assert validate_path(str(test_dir)) is True
        assert validate_path("/non/existent") is False
    
    def test_validate_client(self):
        """Test validate_client helper"""
        assert validate_client("192.168.1.0/24") is True
        assert validate_client("server.example.com") is True
        assert validate_client("*") is True
        assert validate_client("invalid@#$") is False
    
    def test_validate_uid_gid(self):
        """Test validate_uid_gid helper"""
        assert validate_uid_gid("1000") is True
        assert validate_uid_gid("0") is True
        assert validate_uid_gid("65535") is True
        assert validate_uid_gid("-1") is False
        assert validate_uid_gid("invalid") is False
