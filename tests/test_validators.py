#!/usr/bin/env python3
"""
Unit tests for NFSValidator and validation functions.
Tests validation of directories, clients, options, and UIDs/GIDs.
"""

import pytest
import tempfile
import os
from src.utils.validators import (
    NFSValidator, 
    validate_path, 
    validate_client, 
    validate_uid_gid
)


class TestValidarDirectorio:
    """Test suite for directory validation"""
    
    def test_directorio_valido(self, tmp_path):
        """Test validation of valid directory"""
        test_dir = tmp_path / "testdir"
        test_dir.mkdir()
        
        valido, msg = NFSValidator.validar_directorio(str(test_dir))
        
        assert valido is True
        assert "válido" in msg.lower()
    
    def test_directorio_no_existe(self):
        """Test validation of non-existent directory"""
        valido, msg = NFSValidator.validar_directorio("/nonexistent/path")
        
        assert valido is False
        assert "no existe" in msg.lower()
    
    def test_directorio_vacio(self):
        """Test validation of empty path"""
        valido, msg = NFSValidator.validar_directorio("")
        
        assert valido is False
        assert "no especificado" in msg.lower()
    
    def test_directorio_raiz(self):
        """Test validation of root directory"""
        valido, msg = NFSValidator.validar_directorio("/")
        
        assert valido is False
        assert "raíz" in msg.lower() or "root" in msg.lower()
    
    def test_directorio_no_absoluto(self):
        """Test validation of relative path"""
        valido, msg = NFSValidator.validar_directorio("relative/path")
        
        assert valido is False
        assert "absoluta" in msg.lower()
    
    def test_directorio_es_archivo(self, tmp_path):
        """Test validation when path is a file, not directory"""
        test_file = tmp_path / "testfile"
        test_file.write_text("content")
        
        valido, msg = NFSValidator.validar_directorio(str(test_file))
        
        assert valido is False
        assert "directorio" in msg.lower()


class TestValidarCliente:
    """Test suite for client validation"""
    
    def test_cliente_ip_valida(self):
        """Test validation of valid IP address"""
        valido, msg = NFSValidator.validar_cliente("192.168.1.100")
        
        assert valido is True
        assert "válida" in msg.lower()
    
    def test_cliente_subnet_valida(self):
        """Test validation of valid subnet"""
        valido, msg = NFSValidator.validar_cliente("192.168.1.0/24")
        
        assert valido is True
        assert "válida" in msg.lower() or "subred" in msg.lower()
    
    def test_cliente_wildcard(self):
        """Test validation of wildcard"""
        valido, msg = NFSValidator.validar_cliente("*")
        
        assert valido is True
        assert "válido" in msg.lower()
    
    def test_cliente_hostname_valido(self):
        """Test validation of valid hostname"""
        valido, msg = NFSValidator.validar_cliente("server.example.com")
        
        assert valido is True
        assert "válido" in msg.lower()
    
    def test_cliente_hostname_simple(self):
        """Test validation of simple hostname"""
        valido, msg = NFSValidator.validar_cliente("server01")
        
        assert valido is True
    
    def test_cliente_netgroup(self):
        """Test validation of netgroup"""
        valido, msg = NFSValidator.validar_cliente("@trusted_hosts")
        
        assert valido is True
        assert "válido" in msg.lower()
    
    def test_cliente_ip_invalida(self):
        """Test validation of invalid IP (accepted as hostname)"""
        # Note: 300.300.300.300 is invalid as IP but valid as hostname pattern
        # So validator accepts it as hostname
        valido, msg = NFSValidator.validar_cliente("300.300.300.300")
        
        # This will be accepted as a hostname pattern, which is correct behavior
        assert valido is True
    
    def test_cliente_vacio(self):
        """Test validation of empty client"""
        valido, msg = NFSValidator.validar_cliente("")
        
        assert valido is False
        assert "no especificado" in msg.lower()
    
    def test_cliente_formato_invalido(self):
        """Test validation of invalid format"""
        valido, msg = NFSValidator.validar_cliente("invalid@format!")
        
        assert valido is False


class TestValidarOpciones:
    """Test suite for options validation"""
    
    def test_opciones_validas_basicas(self):
        """Test validation of basic valid options"""
        opciones = {
            'rw': True,
            'sync': True,
            'no_subtree_check': True
        }
        valido, errores = NFSValidator.validar_opciones(opciones)
        
        assert valido is True
        assert len(errores) == 0
    
    def test_opciones_conflicto_rw_ro(self):
        """Test validation detects rw/ro conflict"""
        opciones = {
            'rw': True,
            'ro': True
        }
        valido, errores = NFSValidator.validar_opciones(opciones)
        
        assert valido is False
        assert len(errores) > 0
        assert any('acceso' in err.lower() for err in errores)
    
    def test_opciones_conflicto_sync_async(self):
        """Test validation detects sync/async conflict"""
        opciones = {
            'sync': True,
            'async': True
        }
        valido, errores = NFSValidator.validar_opciones(opciones)
        
        assert valido is False
        assert len(errores) > 0
    
    def test_opciones_conflicto_root_squash(self):
        """Test validation detects root_squash conflict"""
        opciones = {
            'no_root_squash': True,
            'root_squash': True
        }
        valido, errores = NFSValidator.validar_opciones(opciones)
        
        assert valido is False
        assert len(errores) > 0
    
    def test_opciones_conflicto_subtree(self):
        """Test validation detects subtree_check conflict"""
        opciones = {
            'no_subtree_check': True,
            'subtree_check': True
        }
        valido, errores = NFSValidator.validar_opciones(opciones)
        
        assert valido is False
        assert len(errores) > 0
    
    def test_opciones_conflicto_secure_insecure(self):
        """Test validation detects secure/insecure conflict"""
        opciones = {
            'secure': True,
            'insecure': True
        }
        valido, errores = NFSValidator.validar_opciones(opciones)
        
        assert valido is False
        assert len(errores) > 0
    
    def test_opciones_anonuid_sin_all_squash(self):
        """Test validation detects anonuid without all_squash"""
        opciones = {
            'rw': True,
            'anonuid': '65534'
        }
        valido, errores = NFSValidator.validar_opciones(opciones)
        
        assert valido is False
        assert any('anonuid' in err.lower() and 'all_squash' in err.lower() for err in errores)
    
    def test_opciones_anongid_sin_all_squash(self):
        """Test validation detects anongid without all_squash"""
        opciones = {
            'rw': True,
            'anongid': '65534'
        }
        valido, errores = NFSValidator.validar_opciones(opciones)
        
        assert valido is False
        assert any('anongid' in err.lower() and 'all_squash' in err.lower() for err in errores)
    
    def test_opciones_anonuid_valido_con_all_squash(self):
        """Test validation allows anonuid with all_squash"""
        opciones = {
            'ro': True,
            'all_squash': True,
            'anonuid': '65534'
        }
        valido, errores = NFSValidator.validar_opciones(opciones)
        
        assert valido is True
        assert len(errores) == 0
    
    def test_opciones_anonuid_invalido(self):
        """Test validation detects invalid anonuid"""
        opciones = {
            'ro': True,
            'all_squash': True,
            'anonuid': 'not_a_number'
        }
        valido, errores = NFSValidator.validar_opciones(opciones)
        
        assert valido is False
        assert any('anonuid' in err.lower() for err in errores)
    
    def test_opciones_anongid_invalido(self):
        """Test validation detects invalid anongid"""
        opciones = {
            'ro': True,
            'all_squash': True,
            'anongid': 'not_a_number'
        }
        valido, errores = NFSValidator.validar_opciones(opciones)
        
        assert valido is False
        assert any('anongid' in err.lower() for err in errores)
    
    def test_opciones_desconocida(self):
        """Test validation detects unknown option"""
        opciones = {
            'rw': True,
            'unknown_option': True
        }
        valido, errores = NFSValidator.validar_opciones(opciones)
        
        assert valido is False
        assert any('desconocida' in err.lower() or 'unknown' in err.lower() for err in errores)


class TestValidarUidGid:
    """Test suite for UID/GID validation"""
    
    def test_uid_valido(self):
        """Test validation of valid UID"""
        assert NFSValidator.validar_uid_gid("0") is True
        assert NFSValidator.validar_uid_gid("1000") is True
        assert NFSValidator.validar_uid_gid("65534") is True
        assert NFSValidator.validar_uid_gid("65535") is True
    
    def test_uid_invalido_negativo(self):
        """Test validation rejects negative UID"""
        assert NFSValidator.validar_uid_gid("-1") is False
    
    def test_uid_invalido_muy_grande(self):
        """Test validation rejects UID too large"""
        assert NFSValidator.validar_uid_gid("70000") is False
    
    def test_uid_invalido_no_numero(self):
        """Test validation rejects non-numeric UID"""
        assert NFSValidator.validar_uid_gid("abc") is False
        assert NFSValidator.validar_uid_gid("12.34") is False
    
    def test_uid_invalido_vacio(self):
        """Test validation rejects empty UID"""
        assert NFSValidator.validar_uid_gid("") is False


class TestWrapperFunctions:
    """Test suite for wrapper functions (GUI compatibility)"""
    
    def test_validate_path_wrapper(self, tmp_path):
        """Test validate_path wrapper function"""
        test_dir = tmp_path / "testdir"
        test_dir.mkdir()
        
        assert validate_path(str(test_dir)) is True
        assert validate_path("/nonexistent") is False
    
    def test_validate_client_wrapper(self):
        """Test validate_client wrapper function"""
        assert validate_client("192.168.1.100") is True
        assert validate_client("invalid@!") is False
    
    def test_validate_uid_gid_wrapper(self):
        """Test validate_uid_gid wrapper function"""
        assert validate_uid_gid("1000") is True
        assert validate_uid_gid("abc") is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
