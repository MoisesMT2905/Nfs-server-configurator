# Configurador NFS - Servidor Gráfico

Sistema gráfico para configurar exportaciones NFS en Linux, inspirado en YaST2 con funcionalidades avanzadas de permisos, helper privilegiado con D-Bus y autenticación polkit.

## Requisitos Previos

- **Sistema Operativo**: Linux (Ubuntu 18.04+, Debian 10+, CentOS 7+, openSUSE)
- **Python**: 3.8 o superior
- **Paquetes del Sistema**:
  ```bash
  # Debian/Ubuntu
  sudo apt-get install nfs-common nfs-kernel-server python3-pydbus python3-gobject polkit-tools gtk3
  
  # openSUSE/SUSE
  sudo zypper install nfs-client nfs-kernel-server python3-pydbus python3-gobject typelib-1_0-Gtk-3_0 polkit
  
  # Fedora/RHEL/CentOS
  sudo dnf install nfs-utils python3-pydbus python3-gobject gtk3 polkit
  ```

## Arquitectura

Este proyecto implementa un sistema de configuración NFS con arquitectura de seguridad basada en D-Bus y polkit:

- **GUI (src/gui/)**: Interfaz gráfica GTK3 que puede ejecutarse sin privilegios
- **Backend (src/backend/)**: Lógica de negocio y validaciones
- **Helper Privilegiado (src/priv_helper/)**: Servicio D-Bus que ejecuta como root
- **Polkit**: Gestiona autenticación y autorización para operaciones privilegiadas

## Instalación

### Instalación desde Código Fuente

1. **Clonar el proyecto**:
   ```bash
   git clone https://github.com/MoisesMT2905/Nfs-server-configurator.git
   cd Nfs-server-configurator
   ```

2. **Instalar dependencias de Python**:
   ```bash
   pip3 install -r requirements.txt
   ```

3. **Instalar el helper privilegiado**:
   ```bash
   # Copiar el helper a /usr/libexec
   sudo cp src/priv_helper/helper.py /usr/libexec/yast2-nfs-server-helper
   sudo chmod +x /usr/libexec/yast2-nfs-server-helper
   
   # Instalar la policy de polkit
   sudo cp packaging/org.yast2.nfshelper.policy /usr/share/polkit-1/actions/
   
   # Instalar el servicio systemd
   sudo cp packaging/yast2-nfs-helper.service /usr/lib/systemd/system/
   
   # Recargar systemd y habilitar el servicio
   sudo systemctl daemon-reload
   sudo systemctl enable --now yast2-nfs-helper.service
   ```

4. **Verificar que el servicio está corriendo**:
   ```bash
   sudo systemctl status yast2-nfs-helper.service
   ```

### Instalación vía RPM (openSUSE/SUSE/Fedora/RHEL)

```bash
# Construir el RPM
rpmbuild -ba packaging/yast2-nfs-server.spec

# Instalar el RPM
sudo rpm -ivh ~/rpmbuild/RPMS/noarch/yast2-nfs-server-*.rpm
```

El paquete RPM automáticamente:
- Instala todos los archivos en las ubicaciones correctas
- Habilita y arranca el servicio D-Bus helper
- Configura polkit

## Uso

### Ejecución Normal (Modo Seguro - Recomendado)

**NO ejecutar la GUI como root en producción.** En su lugar, ejecutar como usuario normal y el helper se encargará de las operaciones privilegiadas:

```bash
python3 main.py
```

Cuando presione "Aplicar Cambios", el sistema:
1. Detecta que no es root
2. Se conecta al helper D-Bus
3. Polkit solicita autenticación al usuario
4. El helper aplica los cambios con privilegios

### Prueba del Helper Manualmente

Puede probar el helper con el cliente de ejemplo:

```bash
# Listar exportaciones actuales
python3 src/priv_helper/client_example.py list

# Crear backup
python3 src/priv_helper/client_example.py backup

# Aplicar configuración (solicitará autenticación polkit)
python3 src/priv_helper/client_example.py apply '/shared 192.168.1.0/24(rw,sync)'
```

### Modo de Desarrollo (Solo para Testing)

Si necesita ejecutar como root para desarrollo:
```bash
sudo python3 main.py
```

⚠️ **ADVERTENCIA**: No usar en producción. Ejecutar GUI como root es un riesgo de seguridad.

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

### Problema: "Error connecting to helper service"
**Solución**: 
```bash
# Verificar que el servicio está corriendo
sudo systemctl status yast2-nfs-helper.service

# Si no está corriendo, iniciarlo
sudo systemctl start yast2-nfs-helper.service

# Ver logs del servicio
sudo journalctl -u yast2-nfs-helper.service -f
```

### Problema: "Authorization denied"
**Solución**:
- Verificar que polkit-tools está instalado: `which pkcheck`
- Verificar que la policy está instalada: `ls /usr/share/polkit-1/actions/org.yast2.nfshelper.policy`
- El usuario debe tener permisos de administración en polkit
- Intentar ejecutar: `pkcheck --action-id org.yast2.nfshelper.apply --process $$`

### Problema: "Servicio NFS no inicia"
**Solución**: 
```bash
sudo systemctl status nfs-server
sudo systemctl restart nfs-server
```

### Problema: "Error de sintaxis en /etc/exports"
**Solución**: 
- Verificar formato de opciones
- El sistema crea backup automático: `ls -la /etc/exports.*`
- Restaurar desde backup si es necesario

### Problema: Cliente no puede montar
**Solución**:
```bash
# En servidor
sudo exportfs -v

# En cliente
showmount -e servidor.local
sudo mount -t nfs servidor.local:/shared /mnt/compartido
\`\`\`

## Seguridad

### Arquitectura de Seguridad

El sistema implementa una arquitectura de seguridad robusta:

1. **Separación de Privilegios**: La GUI se ejecuta como usuario normal, solo el helper tiene privilegios
2. **D-Bus System Bus**: Comunicación IPC segura entre GUI y helper
3. **Polkit**: Autenticación y autorización granular para operaciones privilegiadas
4. **Validación de Entrada**: Todos los datos se validan antes de procesarse
5. **Backup Automático**: Se crea backup antes de cada cambio

### Consideraciones Importantes de Seguridad NFS

1. **Nunca exportar directorios sensibles** (/etc, /root, /boot, /var)
2. **no_root_squash** solo usar en redes confiables - permite acceso root desde clientes
3. **all_squash** para acceso público - mapea todos los usuarios a anónimo
4. Usar **secure** en producción, no **insecure** - requiere puertos privilegiados (<1024)
5. Revisar permisos del directorio base antes de exportar
6. **NO ejecutar la GUI como root en producción** - usar el helper D-Bus en su lugar

### Advertencias de Seguridad del Helper

- El helper se ejecuta como root por systemd
- Polkit controla qué usuarios pueden usarlo
- Todas las operaciones se registran en syslog/journald
- El helper usa `NFSManager.apply_configuration()` para evitar inyección de comandos
- Validación de entrada en múltiples capas

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
\`\`\`

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

# Comandos del helper D-Bus
systemctl status yast2-nfs-helper.service  # Estado del helper
journalctl -u yast2-nfs-helper.service -f  # Logs del helper
pkcheck --action-id org.yast2.nfshelper.apply --process $$  # Verificar autorización
```

## Desarrollo y Testing

### Ejecutar Tests

El proyecto incluye tests completos con pytest:

```bash
# Instalar dependencias de testing
pip3 install pytest pytest-cov

# Ejecutar todos los tests
pytest tests/ -v

# Ejecutar con coverage
pytest tests/ -v --cov=src --cov-report=term-missing

# Ejecutar tests específicos
pytest tests/test_config_parser.py -v
pytest tests/test_validators.py -v
pytest tests/test_nfs_manager.py -v
```

### Linting

```bash
# Instalar flake8
pip3 install flake8

# Ejecutar linter
flake8 src/ tests/

# Ejecutar con configuración más estricta
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
```

### CI/CD

El proyecto incluye GitHub Actions workflow que:
- Ejecuta flake8 para verificar código
- Ejecuta pytest con todos los tests
- Genera reportes de coverage

El workflow se ejecuta automáticamente en:
- Push a branches: main, restructure/*, copilot/*
- Pull requests a main y restructure/*

### Estructura de Tests

```
tests/
├── __init__.py
├── test_config_parser.py   # Tests de las 13 opciones NFS
├── test_validators.py       # Tests de validaciones
└── test_nfs_manager.py     # Tests con mocks de subprocess
```

### Pasos de Prueba Manual

1. **Instalar el helper manualmente** (ver sección Instalación)
2. **Verificar el servicio**: `sudo systemctl status yast2-nfs-helper.service`
3. **Ejecutar la GUI como usuario normal**: `python3 main.py`
4. **Configurar una exportación**:
   - Seleccionar directorio: `/tmp/test-export` (crear si no existe)
   - Agregar cliente: `192.168.1.0/24`
   - Seleccionar opciones: rw, sync
5. **Aplicar cambios** - Polkit solicitará autenticación
6. **Verificar**: `cat /etc/exports` y `sudo exportfs -v`

## Licencia

MIT License - Use libremente

## Autor

Sistema desarrollado como herramienta de administración de servidores NFS

## Versión

v1.0 - 2025
