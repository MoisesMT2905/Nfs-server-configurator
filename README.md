# Configurador NFS - Servidor Gráfico (YaST2 NFS Server Module)

Sistema gráfico para configurar exportaciones NFS en Linux, inspirado en YaST2 con funcionalidades avanzadas de permisos.

**Nuevo en v2.0**: Incluye helper privilegiado D-Bus con autenticación polkit para operación segura sin root.

## Requisitos Previos

- **Sistema Operativo**: Linux (openSUSE/SLE, Ubuntu 18.04+, Debian 10+, CentOS 7+)
- **Python**: 3.8 o superior
- **Paquetes del Sistema**:
  ```bash
  # En openSUSE/SLE:
  sudo zypper install nfs-kernel-server python3-gobject python3-pydbus polkit
  
  # En Ubuntu/Debian:
  sudo apt-get install nfs-common nfs-kernel-server python3-gi python3-pydbus policykit-1
  ```

## Instalación

### Opción 1: Instalación desde RPM (openSUSE/SLE)

```bash
# Construir el RPM
rpmbuild -ba packaging/yast2-nfs-server.spec

# Instalar
sudo zypper install ./rpmbuild/RPMS/noarch/yast2-nfs-server-*.rpm

# Habilitar el servicio helper
sudo systemctl enable --now yast2-nfs-helper.service
```

### Opción 2: Instalación manual

1. **Clonar o descargar el proyecto**:
   ```bash
   git clone https://github.com/MoisesMT2905/Nfs-server-configurator
   cd Nfs-server-configurator
   ```

2. **Instalar el helper privilegiado**:
   ```bash
   # Instalar helper
   sudo install -Dm755 src/priv_helper/helper.py /usr/libexec/yast2-nfs-server-helper
   
   # Instalar polkit policy
   sudo install -Dm644 packaging/org.yast2.nfshelper.policy /usr/share/polkit-1/actions/
   
   # Instalar systemd unit
   sudo install -Dm644 packaging/yast2-nfs-helper.service /usr/lib/systemd/system/
   
   # Crear D-Bus service file
   sudo tee /usr/share/dbus-1/system-services/org.yast2.NFSHelper.service << EOF
   [D-BUS Service]
   Name=org.yast2.NFSHelper
   Exec=/usr/libexec/yast2-nfs-server-helper
   User=root
   SystemdService=yast2-nfs-helper.service
   EOF
   
   # Recargar systemd y D-Bus
   sudo systemctl daemon-reload
   sudo systemctl reload dbus.service
   
   # Habilitar e iniciar el servicio
   sudo systemctl enable --now yast2-nfs-helper.service
   ```

3. **Verificar estructura**:
   ```
   ├── main.py
   ├── README.md
   ├── requirements.txt
   ├── src/
   │   ├── backend/
   │   │   ├── nfs_manager.py
   │   │   └── config_parser.py
   │   ├── gui/
   │   │   └── main_window.py
   │   ├── utils/
   │   │   └── validators.py
   │   └── priv_helper/
   │       ├── helper.py
   │       └── client_example.py
   ├── packaging/
   │   ├── yast2-nfs-helper.service
   │   ├── org.yast2.nfshelper.policy
   │   └── yast2-nfs-server.spec
   └── tests/
       ├── test_config_parser.py
       ├── test_validators.py
       └── test_nfs_manager.py
   ```

## Uso

### Modo Recomendado: Usuario Normal con Helper D-Bus (polkit)

**⚠️ IMPORTANTE**: Esta es la forma segura y recomendada para producción.

```bash
python3 main.py
```

Cuando intente aplicar cambios, polkit solicitará su contraseña de administrador. El helper privilegiado ejecutándose como servicio D-Bus aplicará los cambios de forma segura.

### Modo Alternativo: Ejecución Directa como Root

**⚠️ ADVERTENCIA**: Solo para desarrollo/testing. No recomendado en producción.

```bash
sudo python3 main.py
```

En este modo, la aplicación usa `NFSManager` directamente sin pasar por el helper D-Bus.

### Verificar Estado del Helper

```bash
# Verificar que el servicio está ejecutándose
sudo systemctl status yast2-nfs-helper.service

# Ver logs del helper
sudo journalctl -u yast2-nfs-helper.service -f

# Probar el helper manualmente
python3 src/priv_helper/client_example.py
```

## Características

### 1. Configuración Básica
- **Selección de Directorio**: Explorador visual de directorios
- **Gestión de Clientes**: Agregar, editar, eliminar clientes
- **Validación**: Validación en tiempo real de rutas y direcciones IP

### 2. Opciones de Permisos NFS (13 opciones)

#### Permisos Básicos
- `rw` - Lectura/Escritura
- `ro` - Solo Lectura

#### Sincronización
- `sync` - Escrituras síncronas
- `async` - Escrituras asíncronas

#### Seguridad Root
- `no_root_squash` - Permite acceso root
- `root_squash` - Squash para root

#### Squash de Usuarios
- `all_squash` - Squash para todos los usuarios

#### Verificación de Subárbol
- `no_subtree_check` - Sin verificación
- `subtree_check` - Con verificación

#### Seguridad de Puertos
- `insecure` - Permite puertos > 1024
- `secure` - Solo puertos privilegiados

#### Configuración Avanzada
- `anonuid` - UID para usuarios anónimos
- `anongid` - GID para usuarios anónimos

### 3. Validaciones

El sistema valida:
- ✓ Existencia y permisos de directorios
- ✓ Formato de direcciones IP y subredes
- ✓ Hostnames válidos
- ✓ Opciones mutuamente excluyentes
- ✓ Dependencias entre opciones
- ✓ UIDs/GIDs válidos

### 4. Gestión de Configuración

- **Backup Automático**: Crea copias de seguridad antes de cambios
- **Validación de Sintaxis**: Verifica formato antes de aplicar
- **Recuperación**: Restaura configuración anterior si falla
- **Logs**: Registro de cambios realizados

## Flujo de Trabajo

1. **Seleccionar Directorio**: Click en "Examinar..." o ingrese la ruta
2. **Agregar Clientes**: Ingrese IP/subnet/hostname y click "Agregar Cliente"
3. **Configurar Permisos**: Seleccione opciones necesarias
4. **Validar**: Click "Validar Configuración" para verificar
5. **Aplicar**: Click "Aplicar Cambios" para guardar en /etc/exports
6. **Confirmar**: Confirme los cambios en el diálogo

## Ejemplos de Uso

### Ejemplo 1: Compartir Directorio en Lectura/Escritura
\`\`\`
Directorio: /shared/data
Cliente: 192.168.1.0/24
Opciones: rw, sync, no_root_squash
Resultado: /shared/data 192.168.1.0/24(rw,sync,no_root_squash)
\`\`\`

### Ejemplo 2: Compartir en Solo Lectura
\`\`\`
Directorio: /backups
Cliente: 10.0.0.5
Opciones: ro, async, root_squash
Resultado: /backups 10.0.0.5(ro,async,root_squash)
\`\`\`

### Ejemplo 3: Acceso Público Anónimo
\`\`\`
Directorio: /public
Cliente: * (wildcard)
Opciones: ro, all_squash, anonuid=65534, anongid=65534
Resultado: /public *(ro,all_squash,anonuid=65534,anongid=65534)
\`\`\`

## Troubleshooting

### Problema: "No se pudo conectar con el servicio D-Bus"
**Solución**: 
```bash
# Verificar que el servicio está ejecutándose
sudo systemctl status yast2-nfs-helper.service

# Si no está ejecutándose, iniciarlo
sudo systemctl start yast2-nfs-helper.service

# Habilitar para inicio automático
sudo systemctl enable yast2-nfs-helper.service

# Verificar logs para errores
sudo journalctl -u yast2-nfs-helper.service -n 50
```

### Problema: "Falta la biblioteca pydbus"
**Solución**:
```bash
# En openSUSE/SLE:
sudo zypper install python3-pydbus

# En Ubuntu/Debian:
sudo apt install python3-pydbus

# Verificar instalación
python3 -c "import pydbus; print('pydbus OK')"
```

### Problema: Polkit no solicita contraseña
**Solución**:
```bash
# Verificar que polkit está instalado
which pkcheck

# Verificar que la policy está instalada
ls -l /usr/share/polkit-1/actions/org.yast2.nfshelper.policy

# Recargar polkit
sudo systemctl restart polkit
```

### Problema: "No hay permisos" (modo legacy)
**Solución**: Si está ejecutando directamente sin el helper, usar `sudo python3 main.py`

### Problema: "Servicio NFS no inicia"
**Solución**: 
```bash
sudo systemctl status nfs-server
sudo systemctl restart nfs-server
```

### Problema: "Error de sintaxis en /etc/exports"
**Solución**: 
- Verificar formato de opciones
- Usar "Validar Configuración" antes de aplicar
- Check backup: `ls -la /etc/exports.*`

### Problema: Cliente no puede montar
**Solución**:
\`\`\`bash
# En servidor
sudo exportfs -v

# En cliente
showmount -e servidor.local
sudo mount -t nfs servidor.local:/shared /mnt/compartido
\`\`\`

## Seguridad

### Arquitectura de Seguridad (D-Bus + Polkit)

La aplicación implementa un modelo de seguridad por capas:

1. **Separación de Privilegios**: La GUI se ejecuta como usuario normal
2. **Helper Privilegiado**: Servicio D-Bus separado ejecutándose como root
3. **Autorización Polkit**: Verifica permisos antes de aplicar cambios
4. **Validación de Entrada**: Sanitización y validación de toda la entrada del usuario
5. **Backup Automático**: Respaldo antes de cada cambio con rollback automático en caso de fallo

### Políticas de Polkit

La policy `org.yast2.nfshelper.apply` requiere:
- **allow_any**: `auth_admin` - Requiere contraseña de administrador
- **allow_inactive**: `auth_admin` - Requiere contraseña incluso en sesión inactiva
- **allow_active**: `auth_admin_keep` - Solicita contraseña una vez por sesión activa

### Consideraciones de Seguridad NFS

1. **Nunca exportar directorios sensibles** (/etc, /root, /boot, /var, /usr)
2. **no_root_squash** solo en redes 100% confiables (permite acceso root remoto)
3. **all_squash** para acceso público (mapea todos los usuarios a anónimo)
4. Usar **secure** en producción, no **insecure** (puertos < 1024)
5. Revisar permisos Unix del directorio exportado
6. Limitar acceso por IP/subnet, evitar wildcards (*) en producción

### Configuración Recomendada por Caso

**Uso Interno (Red de Confianza)**:
```
rw, sync, no_root_squash, secure, subtree_check
```

**Uso Público**:
```
ro, all_squash, secure, no_subtree_check, anonuid=65534, anongid=65534
```

**Backups**:
```
ro, sync, root_squash, secure, no_subtree_check
```

### Advertencias de Seguridad

⚠️ **NO ejecutar la GUI como root en producción**: Usar el modo con helper D-Bus + polkit.

⚠️ **Revisar permisos de archivos**: El helper tiene acceso limitado solo a `/etc/exports`.

⚠️ **Logs de auditoría**: Todos los cambios se registran en el journal de systemd:
```bash
sudo journalctl -u yast2-nfs-helper.service
```

## Archivo /etc/exports

Ubicación: `/etc/exports`

Ejemplo de contenido generado:
\`\`\`
/shared/data 192.168.1.0/24(rw,sync,no_root_squash)
/backups 10.0.0.5(ro,async,root_squash)
/public *(ro,all_squash,anonuid=65534,anongid=65534)
\`\`\`

Después de cambios se ejecuta:
\`\`\`bash
sudo exportfs -ra
sudo systemctl restart nfs-server
\`\`\`

## Comandos del Sistema Utilizados

```bash
exportfs -ra          # Recargar exportaciones
exportfs -v          # Ver exportaciones activas
systemctl restart nfs-server  # Reiniciar servicio
systemctl status nfs-server   # Estado del servicio
showmount -e         # Ver exportaciones (cliente)
systemctl status yast2-nfs-helper  # Estado del helper D-Bus
journalctl -u yast2-nfs-helper -f  # Ver logs del helper
pkcheck --action-id org.yast2.nfshelper.apply --process $$  # Verificar autorización polkit
```

## Desarrollo y Testing

### Ejecutar Tests Automáticos

```bash
# Instalar dependencias de testing
pip install pytest pytest-cov

# Ejecutar todos los tests
pytest tests/ -v

# Ejecutar tests con cobertura
pytest tests/ -v --cov=src --cov-report=html

# Ejecutar tests específicos
pytest tests/test_validators.py -v
pytest tests/test_config_parser.py -v
pytest tests/test_nfs_manager.py -v
```

### Linting del Código

```bash
# Instalar flake8
pip install flake8

# Ejecutar linter
flake8 src/ tests/ --max-line-length=120 --exclude=__pycache__

# Errores críticos solamente
flake8 src/ tests/ --select=E9,F63,F7,F82
```

### CI/CD

El proyecto incluye GitHub Actions CI que ejecuta automáticamente:
- Linting con flake8
- Tests con pytest
- Verificación de imports
- Validación de archivos de packaging

Ver `.github/workflows/ci.yaml` para detalles.

### Probar el Helper Manualmente

```bash
# 1. Asegurar que el servicio está ejecutándose
sudo systemctl start yast2-nfs-helper.service

# 2. Ver logs en tiempo real (en terminal separada)
sudo journalctl -u yast2-nfs-helper.service -f

# 3. Ejecutar el cliente de ejemplo
python3 src/priv_helper/client_example.py
```

### Estructura de Tests

- `tests/test_config_parser.py`: Tests de parsing y generación de exports
- `tests/test_validators.py`: Tests de validación (directorios, clientes, opciones)
- `tests/test_nfs_manager.py`: Tests de NFSManager con mocks de subprocess

## Licencia

MIT License - Use libremente

## Autor

Sistema desarrollado como herramienta de administración de servidores NFS

## Versión

v2.0 - 2024 (con helper D-Bus + polkit)
