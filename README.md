# Configurador NFS - Servidor Gráfico

Sistema gráfico para configurar exportaciones NFS en Linux, inspirado en YaST2 con funcionalidades avanzadas de permisos y autenticación mediante polkit.

## 🎯 Características Principales

- **Interfaz Gráfica GTK3**: Interfaz intuitiva para configurar exportaciones NFS
- **D-Bus + Polkit**: Usuarios no-root pueden aplicar cambios con autenticación
- **13 Opciones NFS**: Configuración completa de permisos y opciones de exportación
- **Validación en Tiempo Real**: Verifica directorios, clientes y opciones antes de aplicar
- **Gestión Segura**: Backups automáticos y recuperación ante errores
- **Tests Completos**: Suite de pruebas con pytest (cobertura de código)
- **CI/CD**: Integración continua con GitHub Actions

## 📋 Requisitos Previos

### Sistema Operativo
- Linux (Ubuntu 18.04+, Debian 10+, CentOS 7+, openSUSE)
- Python 3.8 o superior

### Paquetes del Sistema

**Debian/Ubuntu:**
```bash
sudo apt-get update
sudo apt-get install -y \
    nfs-common \
    nfs-kernel-server \
    python3 \
    python3-gi \
    python3-dbus \
    gir1.2-gtk-3.0 \
    policykit-1
```

**RHEL/CentOS/Fedora:**
```bash
sudo dnf install -y \
    nfs-utils \
    python3 \
    python3-gobject \
    python3-dbus \
    gtk3 \
    polkit
```

**openSUSE:**
```bash
sudo zypper install -y \
    nfs-kernel-server \
    python3 \
    python3-gobject \
    python3-dbus \
    gtk3 \
    polkit
```

## 🚀 Instalación

### Método 1: Instalación desde Fuente

1. **Clonar el repositorio**:
   ```bash
   git clone https://github.com/MoisesMT2905/Nfs-server-configurator.git
   cd Nfs-server-configurator
   ```

2. **Instalar dependencias Python**:
   ```bash
   pip3 install -r requirements.txt
   ```

3. **Instalar el Helper Privilegiado D-Bus** (necesario para usuarios no-root):
   ```bash
   # Copiar archivos del helper
   sudo cp src/priv_helper/helper.py /usr/libexec/yast2-nfs-helper
   sudo chmod +x /usr/libexec/yast2-nfs-helper
   
   # Instalar polkit policy
   sudo cp packaging/org.yast2.nfshelper.policy /usr/share/polkit-1/actions/
   
   # Instalar D-Bus configuration
   sudo cp packaging/org.yast2.NFSHelper.conf /etc/dbus-1/system.d/
   
   # Instalar systemd unit
   sudo cp packaging/yast2-nfs-helper.service /etc/systemd/system/
   
   # Recargar configuración
   sudo systemctl daemon-reload
   sudo dbus-send --system --type=method_call --dest=org.freedesktop.DBus / org.freedesktop.DBus.ReloadConfig
   
   # Iniciar el servicio
   sudo systemctl enable yast2-nfs-helper.service
   sudo systemctl start yast2-nfs-helper.service
   ```

4. **Verificar instalación del helper**:
   ```bash
   systemctl status yast2-nfs-helper.service
   ```

### Método 2: Instalación RPM (RHEL/CentOS/Fedora/openSUSE)

```bash
# Construir RPM (requiere rpmbuild)
rpmbuild -ba packaging/yast2-nfs-server.spec

# Instalar RPM generado
sudo rpm -ivh ~/rpmbuild/RPMS/noarch/yast2-nfs-server-1.0.0-1.noarch.rpm
```

## 📖 Estructura del Proyecto

```
Nfs-server-configurator/
├── main.py                          # Punto de entrada de la aplicación
├── README.md                        # Este archivo
├── requirements.txt                 # Dependencias Python
├── pytest.ini                       # Configuración de pytest
├── .github/
│   └── workflows/
│       └── ci.yaml                  # GitHub Actions CI/CD
├── src/
│   ├── backend/
│   │   ├── nfs_manager.py          # Lógica de gestión NFS
│   │   └── config_parser.py        # Parser de /etc/exports
│   ├── gui/
│   │   └── main_window.py          # Interfaz gráfica GTK3
│   ├── priv_helper/
│   │   ├── helper.py               # Servicio D-Bus privilegiado
│   │   └── client_example.py       # Cliente de prueba
│   └── utils/
│       └── validators.py           # Validadores de entrada
├── packaging/
│   ├── yast2-nfs-server.spec       # Especificación RPM
│   ├── org.yast2.nfshelper.policy  # Política Polkit
│   ├── org.yast2.NFSHelper.conf    # Configuración D-Bus
│   └── yast2-nfs-helper.service    # Unit systemd
└── tests/
    ├── test_config_parser.py       # Tests del parser
    ├── test_validators.py          # Tests de validadores
    └── test_nfs_manager.py         # Tests del gestor NFS
```

## 💻 Uso

### Ejecución de la Aplicación

**Como usuario normal (recomendado con D-Bus helper):**
```bash
python3 main.py
```
- La aplicación usará el helper D-Bus con autenticación polkit
- Se solicitará autenticación al aplicar cambios

**Como root (modo directo):**
```bash
sudo python3 main.py
```
- Aplica cambios directamente sin D-Bus
- No requiere el helper instalado

## 🎨 Características

### 1. Configuración Básica
- **Selección de Directorio**: Explorador visual de directorios
- **Gestión de Clientes**: Agregar, editar, eliminar clientes
- **Validación en Tiempo Real**: Verifica rutas y direcciones IP

### 2. Opciones de Permisos NFS (13 opciones)

#### Permisos Básicos
- `rw` - Lectura/Escritura
- `ro` - Solo Lectura

#### Sincronización
- `sync` - Escrituras síncronas (recomendado)
- `async` - Escrituras asíncronas (mejor rendimiento)

#### Seguridad Root
- `no_root_squash` - Permite acceso root completo
- `root_squash` - Mapea root a usuario anónimo (más seguro)

#### Squash de Usuarios
- `all_squash` - Mapea todos los usuarios a anónimo

#### Verificación de Subárbol
- `no_subtree_check` - Sin verificación (más rápido)
- `subtree_check` - Con verificación (más seguro)

#### Seguridad de Puertos
- `insecure` - Permite puertos > 1024
- `secure` - Solo puertos privilegiados < 1024 (recomendado)

#### Configuración Avanzada
- `anonuid=N` - UID para usuarios anónimos (ej: 65534)
- `anongid=N` - GID para usuarios anónimos (ej: 65534)

### 3. Validaciones Automáticas

El sistema valida:
- ✓ Existencia y permisos de directorios
- ✓ Formato de direcciones IP y subredes (CIDR)
- ✓ Hostnames válidos (DNS)
- ✓ Opciones mutuamente excluyentes (rw/ro, sync/async, etc.)
- ✓ Dependencias entre opciones (anonuid requiere all_squash)
- ✓ UIDs/GIDs válidos (0-65535)

### 4. Gestión de Configuración

- **Backup Automático**: Crea `/etc/exports.YYYYMMDD_HHMMSS` antes de cambios
- **Validación de Sintaxis**: Usa `exportfs -ra` para verificar
- **Recuperación Automática**: Restaura backup si falla la aplicación
- **Logs del Sistema**: Registros en journalctl/syslog

### 5. Seguridad con D-Bus + Polkit

- **Separación de Privilegios**: GUI corre como usuario normal
- **Autenticación Explícita**: Polkit solicita contraseña para cambios
- **Auditoría**: Todas las operaciones privilegiadas se registran
- **Autorización Granular**: Control fino mediante políticas polkit

## 🔄 Flujo de Trabajo

1. **Iniciar Aplicación**: `python3 main.py`
2. **Seleccionar Directorio**: Click en "Examinar..." o ingrese ruta absoluta
3. **Agregar Clientes**: Ingrese IP/subnet/hostname y "Agregar Cliente"
4. **Configurar Permisos**: Seleccione checkboxes de opciones NFS
5. **Aplicar Cambios**: Click "Aplicar Cambios"
6. **Autenticar**: Polkit solicitará contraseña (si no es root)
7. **Verificar**: Check "Actualizar" para ver exportaciones activas

## 📝 Ejemplos de Uso

### Ejemplo 1: Compartir Directorio en Lectura/Escritura (Red Confiable)
```
Directorio: /srv/nfs/shared
Cliente: 192.168.1.0/24
Opciones: rw, sync, no_root_squash, secure, no_subtree_check
Resultado: /srv/nfs/shared 192.168.1.0/24(rw,sync,no_root_squash,secure,no_subtree_check)
```

### Ejemplo 2: Compartir en Solo Lectura (Backups)
```
Directorio: /srv/nfs/backups
Cliente: 10.0.0.5
Opciones: ro, sync, root_squash, secure, no_subtree_check
Resultado: /srv/nfs/backups 10.0.0.5(ro,sync,root_squash,secure,no_subtree_check)
```

### Ejemplo 3: Acceso Público Anónimo
```
Directorio: /srv/nfs/public
Cliente: * (wildcard)
Opciones: ro, all_squash, anonuid=65534, anongid=65534, secure, no_subtree_check
Resultado: /srv/nfs/public *(ro,all_squash,secure,no_subtree_check,anonuid=65534,anongid=65534)
```

### Ejemplo 4: Múltiples Clientes
```
Directorio: /srv/nfs/data
Clientes: 
  - 192.168.1.0/24
  - 10.0.0.10
  - server1.example.com
Opciones: rw, sync, no_subtree_check
Resultado:
  /srv/nfs/data 192.168.1.0/24(rw,sync,no_subtree_check)
  /srv/nfs/data 10.0.0.10(rw,sync,no_subtree_check)
  /srv/nfs/data server1.example.com(rw,sync,no_subtree_check)
```

## 🧪 Pruebas

### Ejecutar Tests

```bash
# Instalar dependencias de testing
pip3 install pytest pytest-cov pytest-mock

# Ejecutar todos los tests
pytest tests/ -v

# Ejecutar con cobertura
pytest tests/ -v --cov=src --cov-report=html

# Ver reporte de cobertura
firefox htmlcov/index.html  # O tu navegador preferido
```

### Tests Incluidos

- **test_config_parser.py**: Parsing de /etc/exports, generación de líneas
- **test_validators.py**: Validación de directorios, clientes, opciones
- **test_nfs_manager.py**: Gestión de exportaciones con subprocess mock

### Probar Helper D-Bus Manualmente

```bash
# Verificar servicio está corriendo
systemctl status yast2-nfs-helper.service

# Ejecutar cliente de prueba
python3 src/priv_helper/client_example.py

# Verificar con dbus-send
dbus-send --system --print-reply \
  --dest=org.yast2.NFSHelper \
  /org/yast2/NFSHelper \
  org.yast2.NFSHelper.GetCurrentExports
```

## 🛠️ Desarrollo

### Ejecutar Linters

```bash
# flake8
pip3 install flake8
flake8 src tests --max-line-length=127

# Linting de seguridad
pip3 install bandit
bandit -r src/
```

### GitHub Actions CI

El proyecto incluye CI/CD automático que ejecuta:
- ✅ Linting con flake8
- ✅ Tests en Python 3.8, 3.9, 3.10, 3.11
- ✅ Security checks con bandit y safety
- ✅ Coverage report con codecov

## 🔒 Seguridad

### ⚠️ Advertencias Importantes

1. **Nunca exportar directorios sensibles**: `/etc`, `/root`, `/boot`, `/var`, `/usr`
2. **`no_root_squash` solo en redes confiables**: Permite acceso root completo al cliente
3. **Usar `all_squash` para acceso público**: Previene escalación de privilegios
4. **Preferir `secure` sobre `insecure`**: Restringe a puertos privilegiados
5. **Validar configuración antes de producción**: Usar "Validar Configuración"

### 🔐 Configuraciones Recomendadas por Escenario

#### Red Interna Confiable
```
Opciones: rw, sync, no_root_squash, secure, no_subtree_check
Riesgo: Bajo (red privada)
Uso: Desarrollo, compartir archivos equipo
```

#### Acceso Público/Internet
```
Opciones: ro, all_squash, secure, no_subtree_check, anonuid=65534, anongid=65534
Riesgo: Bajo (solo lectura, anónimo)
Uso: Repositorios públicos, mirrors
```

#### Backups/Almacenamiento
```
Opciones: ro, sync, root_squash, secure, no_subtree_check
Riesgo: Bajo (solo lectura para clientes)
Uso: Backups, almacenamiento histórico
```

#### Desarrollo/Testing
```
Opciones: rw, async, root_squash, insecure, no_subtree_check
Riesgo: Medio (escritura permitida)
Uso: Entornos de desarrollo no críticos
```

### Auditoría del Helper D-Bus

```bash
# Ver logs del helper
journalctl -u yast2-nfs-helper.service -f

# Ver intentos de autorización polkit
journalctl -t pkcheck | grep nfshelper

# Verificar política polkit
pkaction --verbose --action-id org.yast2.nfshelper.apply-configuration
```
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


## 🐛 Troubleshooting

### Problema: "El servicio D-Bus no está disponible"

**Síntomas**: Error al aplicar cambios como usuario no-root

**Solución**:
```bash
# Verificar si el servicio está corriendo
systemctl status yast2-nfs-helper.service

# Si no está instalado, seguir pasos de instalación
sudo systemctl start yast2-nfs-helper.service
sudo systemctl enable yast2-nfs-helper.service

# Recargar configuración D-Bus
sudo dbus-send --system --type=method_call \
  --dest=org.freedesktop.DBus / \
  org.freedesktop.DBus.ReloadConfig
```

### Problema: "Autorización denegada" (Polkit)

**Síntomas**: Polkit rechaza la autenticación

**Solución**:
```bash
# Verificar política instalada
ls -la /usr/share/polkit-1/actions/org.yast2.nfshelper.policy

# Verificar permisos de usuario
pkaction --verbose --action-id org.yast2.nfshelper.apply-configuration

# Probar autenticación manualmente
pkcheck --action-id org.yast2.nfshelper.apply-configuration --process $$
```

### Problema: "No hay permisos" (modo root)

**Síntomas**: Error de permisos al ejecutar como root

**Solución**: 
```bash
# Verificar que /etc/exports es escribible
ls -la /etc/exports

# Ejecutar con sudo
sudo python3 main.py
```

### Problema: "Servicio NFS no inicia"

**Solución**:
```bash
# Verificar estado
sudo systemctl status nfs-server

# Ver logs
sudo journalctl -u nfs-server -n 50

# Reiniciar servicio
sudo systemctl restart nfs-server

# Verificar exportaciones
sudo exportfs -v
```

### Problema: "Error de sintaxis en /etc/exports"

**Solución**:
- Usar "Validar Configuración" antes de aplicar
- Verificar backup: `ls -la /etc/exports.*`
- Restaurar backup manualmente si es necesario:
  ```bash
  sudo cp /etc/exports.20250101_120000 /etc/exports
  sudo exportfs -ra
  ```

### Problema: Cliente no puede montar NFS

**Solución**:
```bash
# En el servidor: verificar exportaciones
sudo exportfs -v
sudo showmount -e localhost

# En el servidor: verificar firewall
sudo firewall-cmd --list-services  # (Fedora/RHEL)
sudo ufw status                     # (Ubuntu)

# En el servidor: abrir puertos NFS
sudo firewall-cmd --permanent --add-service=nfs
sudo firewall-cmd --reload

# En el cliente: verificar conectividad
showmount -e servidor.ejemplo.com
ping servidor.ejemplo.com

# En el cliente: montar manualmente
sudo mkdir -p /mnt/nfs
sudo mount -t nfs servidor.ejemplo.com:/srv/nfs/shared /mnt/nfs
```

### Problema: Tests fallan con módulos no encontrados

**Solución**:
```bash
# Instalar dependencias de desarrollo
pip3 install -r requirements.txt

# Verificar estructura de paquetes
python3 -c "import sys; sys.path.insert(0, '.'); from src.backend import nfs_manager"

# Ejecutar tests con PYTHONPATH
PYTHONPATH=. pytest tests/ -v
```

## 📚 Comandos Útiles del Sistema

### Gestión de Exportaciones NFS

```bash
# Recargar exportaciones sin reiniciar
sudo exportfs -ra

# Ver exportaciones activas
sudo exportfs -v

# Limpiar todas las exportaciones
sudo exportfs -ua

# Ver exportaciones desde cliente
showmount -e servidor.ejemplo.com
```

### Gestión de Servicios

```bash
# Estado del servicio NFS
sudo systemctl status nfs-server

# Reiniciar NFS
sudo systemctl restart nfs-server

# Estado del helper D-Bus
sudo systemctl status yast2-nfs-helper.service

# Ver logs del helper
sudo journalctl -u yast2-nfs-helper.service -f
```

### Diagnóstico

```bash
# Ver configuración actual
cat /etc/exports

# Ver backups disponibles
ls -lah /etc/exports.*

# Ver conexiones NFS activas
sudo nfsstat -c  # Cliente
sudo nfsstat -s  # Servidor

# Ver estadísticas RPC
sudo rpcinfo -p
```

## 🤝 Contribuir

Las contribuciones son bienvenidas. Por favor:

1. Fork el repositorio
2. Crea una rama feature (`git checkout -b feature/amazing-feature`)
3. Commit tus cambios (`git commit -m 'Add amazing feature'`)
4. Push a la rama (`git push origin feature/amazing-feature`)
5. Abre un Pull Request

### Guidelines

- Seguir PEP 8 para código Python
- Añadir tests para nuevas funcionalidades
- Actualizar documentación según sea necesario
- Ejecutar linters y tests antes de PR

## 📄 Licencia

MIT License - Ver archivo [LICENSE](LICENSE) para detalles

## 👥 Autores

- **Sistema NFS Configurator Team** - Desarrollo inicial

## 🙏 Agradecimientos

- Inspirado en YaST2 de openSUSE
- Comunidad de NFS-Utils
- Proyecto Polkit/D-Bus

## 📊 Estado del Proyecto

![CI Status](https://github.com/MoisesMT2905/Nfs-server-configurator/workflows/CI/badge.svg)
[![Coverage](https://codecov.io/gh/MoisesMT2905/Nfs-server-configurator/branch/main/graph/badge.svg)](https://codecov.io/gh/MoisesMT2905/Nfs-server-configurator)

## 📝 Changelog

### v1.0.0 (2025-11-12)
- ✨ Implementación inicial con GUI GTK3
- ✨ Helper privilegiado D-Bus con polkit
- ✨ 13 opciones de permisos NFS
- ✨ Validación completa de configuraciones
- ✨ Suite de tests con pytest
- ✨ CI/CD con GitHub Actions
- ✨ Soporte para múltiples distribuciones Linux
- ✨ Documentación completa

## 🔗 Enlaces

- [Documentación NFS](https://linux.die.net/man/5/exports)
- [D-Bus Specification](https://dbus.freedesktop.org/doc/dbus-specification.html)
- [Polkit Reference](https://www.freedesktop.org/software/polkit/docs/latest/)
- [GTK3 Documentation](https://docs.gtk.org/gtk3/)

---

**⚠️ Nota de Seguridad**: Este software modifica configuraciones críticas del sistema. Úselo con precaución y siempre en entornos de prueba antes de producción.
