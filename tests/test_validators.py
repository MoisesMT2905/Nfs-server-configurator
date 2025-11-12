"""
Tests para el módulo validators.py

Verifica la validación de direcciones IP, CIDR, hostnames y paths.
"""

import pytest
import os
import tempfile
import shutil

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.utils.validators import NFSValidator, validate_path, validate_client, validate_uid_gid


class TestNFSValidator:
    """Tests para NFSValidator"""
    
    # Tests de validación de directorios
    
    def test_validar_directorio_valido(self):
        """Test validación de directorio válido"""
        # Usar un directorio que existe: /tmp
        valido, msg = NFSValidator.validar_directorio('/tmp')
        assert valido is True
        assert 'válido' in msg.lower()
    
    def test_validar_directorio_no_existe(self):
        """Test validación de directorio que no existe"""
        valido, msg = NFSValidator.validar_directorio('/path/que/no/existe/xyz123')
        assert valido is False
        assert 'no existe' in msg.lower()
    
    def test_validar_directorio_vacio(self):
        """Test validación de directorio vacío"""
        valido, msg = NFSValidator.validar_directorio('')
        assert valido is False
        assert 'no especificado' in msg.lower()
    
    def test_validar_directorio_root(self):
        """Test validación de directorio raíz (no permitido)"""
        valido, msg = NFSValidator.validar_directorio('/')
        assert valido is False
        assert 'raíz' in msg.lower()
    
    def test_validar_directorio_relativo(self):
        """Test validación de ruta relativa (no permitida)"""
        valido, msg = NFSValidator.validar_directorio('relative/path')
        assert valido is False
        assert 'absoluta' in msg.lower()
    
    def test_validar_directorio_temporal(self):
        """Test validación con directorio temporal creado"""
        # Crear directorio temporal
        temp_dir = tempfile.mkdtemp()
        
        try:
            valido, msg = NFSValidator.validar_directorio(temp_dir)
            assert valido is True
        finally:
            # Limpiar
            os.rmdir(temp_dir)
    
    def test_validar_directorio_es_archivo(self):
        """Test validación cuando la ruta es un archivo, no directorio"""
        # Crear archivo temporal
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_file = f.name
        
        try:
            valido, msg = NFSValidator.validar_directorio(temp_file)
            assert valido is False
            assert 'no es un directorio' in msg.lower()
        finally:
            os.unlink(temp_file)
    
    # Tests de validación de clientes
    
    def test_validar_cliente_ip_valida(self):
        """Test validación de dirección IP válida"""
        valido, msg = NFSValidator.validar_cliente('192.168.1.100')
        assert valido is True
        assert 'ip válida' in msg.lower()
    
    def test_validar_cliente_ip_invalida(self):
        """Test validación de dirección IP inválida"""
        # Usar una entrada claramente inválida (espacios no permitidos)
        valido, msg = NFSValidator.validar_cliente('192.168.1. 1')
        assert valido is False
    
    def test_validar_cliente_cidr_valido(self):
        """Test validación de CIDR válido"""
        test_cases = [
            '192.168.1.0/24',
            '10.0.0.0/8',
            '172.16.0.0/16',
            '192.168.1.0/32'
        ]
        
        for cidr in test_cases:
            valido, msg = NFSValidator.validar_cliente(cidr)
            assert valido is True, f"CIDR {cidr} debería ser válido"
            assert 'subred válida' in msg.lower()
    
    def test_validar_cliente_cidr_invalido(self):
        """Test validación de CIDR inválido"""
        test_cases = [
            '192.168.1.0/33',  # Máscara inválida
            '999.999.999.0/24',  # IP inválida
            '192.168.1.0/abc',  # Máscara no numérica
        ]
        
        for cidr in test_cases:
            valido, msg = NFSValidator.validar_cliente(cidr)
            assert valido is False, f"CIDR {cidr} no debería ser válido"
    
    def test_validar_cliente_hostname_valido(self):
        """Test validación de hostname válido"""
        test_cases = [
            'server.example.com',
            'host-name',
            'server01',
            'my-server.local',
            'host.subdomain.example.com'
        ]
        
        for hostname in test_cases:
            valido, msg = NFSValidator.validar_cliente(hostname)
            assert valido is True, f"Hostname {hostname} debería ser válido"
    
    def test_validar_cliente_hostname_invalido(self):
        """Test validación de hostname inválido"""
        test_cases = [
            '-invalid',  # No puede empezar con guión
            'invalid-',  # No puede terminar con guión
            'in valid',  # No puede tener espacios
            'invalid@host',  # Caracteres no permitidos
        ]
        
        for hostname in test_cases:
            valido, msg = NFSValidator.validar_cliente(hostname)
            assert valido is False, f"Hostname {hostname} no debería ser válido"
    
    def test_validar_cliente_wildcard(self):
        """Test validación de wildcard"""
        valido, msg = NFSValidator.validar_cliente('*')
        assert valido is True
        assert 'wildcard' in msg.lower()
    
    def test_validar_cliente_netgroup(self):
        """Test validación de netgroup"""
        valido, msg = NFSValidator.validar_cliente('@netgroup')
        assert valido is True
        assert 'netgroup' in msg.lower()
    
    def test_validar_cliente_vacio(self):
        """Test validación de cliente vacío"""
        valido, msg = NFSValidator.validar_cliente('')
        assert valido is False
        assert 'no especificado' in msg.lower()
    
    # Tests de validación de opciones
    
    def test_validar_opciones_basicas_validas(self):
        """Test validación de opciones básicas válidas"""
        opciones = {'rw': True, 'sync': True}
        valido, errores = NFSValidator.validar_opciones(opciones)
        assert valido is True
        assert len(errores) == 0
    
    def test_validar_opciones_rw_ro_mutuamente_excluyentes(self):
        """Test que rw y ro son mutuamente excluyentes"""
        opciones = {'rw': True, 'ro': True}
        valido, errores = NFSValidator.validar_opciones(opciones)
        assert valido is False
        assert len(errores) > 0
        assert any('acceso' in err.lower() for err in errores)
    
    def test_validar_opciones_sync_async_mutuamente_excluyentes(self):
        """Test que sync y async son mutuamente excluyentes"""
        opciones = {'rw': True, 'sync': True, 'async': True}
        valido, errores = NFSValidator.validar_opciones(opciones)
        assert valido is False
        assert any('sincronizacion' in err.lower() for err in errores)
    
    def test_validar_opciones_root_squash_mutuamente_excluyentes(self):
        """Test que root_squash opciones son mutuamente excluyentes"""
        opciones = {'rw': True, 'root_squash': True, 'no_root_squash': True}
        valido, errores = NFSValidator.validar_opciones(opciones)
        assert valido is False
        assert any('root_squash' in err.lower() for err in errores)
    
    def test_validar_opciones_subtree_mutuamente_excluyentes(self):
        """Test que subtree opciones son mutuamente excluyentes"""
        opciones = {'rw': True, 'subtree_check': True, 'no_subtree_check': True}
        valido, errores = NFSValidator.validar_opciones(opciones)
        assert valido is False
        assert any('subtree' in err.lower() for err in errores)
    
    def test_validar_opciones_secure_mutuamente_excluyentes(self):
        """Test que secure e insecure son mutuamente excluyentes"""
        opciones = {'rw': True, 'secure': True, 'insecure': True}
        valido, errores = NFSValidator.validar_opciones(opciones)
        assert valido is False
        assert any('puertos' in err.lower() for err in errores)
    
    def test_validar_opciones_anonuid_requiere_all_squash(self):
        """Test que anonuid requiere all_squash"""
        opciones = {'ro': True, 'anonuid': '65534'}
        valido, errores = NFSValidator.validar_opciones(opciones)
        assert valido is False
        assert any('all_squash' in err for err in errores)
    
    def test_validar_opciones_anongid_requiere_all_squash(self):
        """Test que anongid requiere all_squash"""
        opciones = {'ro': True, 'anongid': '65534'}
        valido, errores = NFSValidator.validar_opciones(opciones)
        assert valido is False
        assert any('all_squash' in err for err in errores)
    
    def test_validar_opciones_anonuid_anongid_con_all_squash(self):
        """Test que anonuid/anongid funcionan correctamente con all_squash"""
        opciones = {
            'ro': True,
            'all_squash': True,
            'anonuid': '65534',
            'anongid': '65534'
        }
        valido, errores = NFSValidator.validar_opciones(opciones)
        assert valido is True
        assert len(errores) == 0
    
    def test_validar_opciones_anonuid_no_numerico(self):
        """Test que anonuid debe ser numérico"""
        opciones = {
            'ro': True,
            'all_squash': True,
            'anonuid': 'abc'
        }
        valido, errores = NFSValidator.validar_opciones(opciones)
        assert valido is False
        assert any('anonuid' in err.lower() and 'número' in err.lower() for err in errores)
    
    def test_validar_opciones_anongid_no_numerico(self):
        """Test que anongid debe ser numérico"""
        opciones = {
            'ro': True,
            'all_squash': True,
            'anongid': 'xyz'
        }
        valido, errores = NFSValidator.validar_opciones(opciones)
        assert valido is False
        assert any('anongid' in err.lower() and 'número' in err.lower() for err in errores)
    
    def test_validar_opciones_desconocida(self):
        """Test que opciones desconocidas son rechazadas"""
        opciones = {'rw': True, 'opcion_invalida': True}
        valido, errores = NFSValidator.validar_opciones(opciones)
        assert valido is False
        assert any('desconocida' in err.lower() for err in errores)
    
    # Tests de validación de UID/GID
    
    def test_validar_uid_gid_valido(self):
        """Test validación de UID/GID válidos"""
        test_cases = ['0', '1000', '65534', '65535']
        
        for uid in test_cases:
            assert NFSValidator.validar_uid_gid(uid) is True, f"UID {uid} debería ser válido"
    
    def test_validar_uid_gid_invalido(self):
        """Test validación de UID/GID inválidos"""
        test_cases = [
            '-1',  # Negativo
            '65536',  # Fuera de rango
            'abc',  # No numérico
            '1000.5',  # Decimal
            '',  # Vacío
        ]
        
        for uid in test_cases:
            assert NFSValidator.validar_uid_gid(uid) is False, f"UID {uid} no debería ser válido"
    
    # Tests de funciones alias para compatibilidad
    
    def test_validate_path_alias(self):
        """Test función alias validate_path"""
        assert validate_path('/tmp') is True
        assert validate_path('/nonexistent/path') is False
    
    def test_validate_client_alias(self):
        """Test función alias validate_client"""
        assert validate_client('192.168.1.100') is True
        assert validate_client('invalid client') is False
    
    def test_validate_uid_gid_alias(self):
        """Test función alias validate_uid_gid"""
        assert validate_uid_gid('1000') is True
        assert validate_uid_gid('abc') is False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
