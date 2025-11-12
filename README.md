# Configurador NFS - Servidor Gráfico

Sistema gráfico para configurar exportaciones NFS en Linux, inspirado en YaST2 con funcionalidades avanzadas de permisos.

## Requisitos Previos

- **Sistema Operativo**: Linux (Ubuntu 18.04+, Debian 10+, CentOS 7+)
- **Python**: 3.8 o superior
- **Paquetes del Sistema**:
  \`\`\`bash
  sudo apt-get install nfs-common nfs-kernel-server
  \`\`\`

## Instalación

1. **Clonar o descargar el proyecto**:
   \`\`\`bash
   git clone <repo>
   cd nfs-configurator
   \`\`\`

2. **Verificar estructura**:
   \`\`\`
   ├── main.py
   ├── README.md
   ├── requirements.txt
   ├── packaging/
   │   ├── yast2-nfs-server.spec
   │   ├── yast2-nfs-helper.service
   │   └── org.yast2.nfshelper.policy
   ├── src/
   │   ├── backend/
   │   │   ├── nfs_manager.py
   │   │   └── config_parser.py
   │   ├── gui/
   │   │   └── main_window.py
   │   ├── priv_helper/
   │   │   ├── helper.py
   │   │   └── client_example.py
   │   └── utils/
   │       └── validators.py
   └── tests/
       ├── test_config_parser.py
       ├── test_validators.py
       └── test_nfs_manager.py
   \`\`\`

3. **Instalar dependencias del sistema**:
   \`\`\`bash
   # Para Debian/Ubuntu
   sudo apt-get install nfs-common nfs-kernel-server python3-gi python3-dbus polkit
   
   # Instalar dependencias de Python para desarrollo
   pip install -r requirements.txt
   \`\`\`

## Instalación del Helper Privilegiado (D-Bus + Polkit)

El configurador NFS incluye un helper privilegiado que permite a usuarios no-root configurar exportaciones NFS de forma segura mediante D-Bus y polkit.

### Instalación Manual del Helper

1. **Instalar el helper D-Bus**:
   \`\`\`bash
   sudo cp src/priv_helper/helper.py /usr/libexec/yast2-nfs-helper
   sudo chmod 755 /usr/libexec/yast2-nfs-helper
   \`\`\`

2. **Instalar la política de polkit**:
   \`\`\`bash
   sudo cp packaging/org.yast2.nfshelper.policy /usr/share/polkit-1/actions/
   sudo chmod 644 /usr/share/polkit-1/actions/org.yast2.nfshelper.policy
   \`\`\`

3. **Instalar el servicio systemd**:
   \`\`\`bash
   sudo cp packaging/yast2-nfs-helper.service /etc/systemd/system/
   sudo chmod 644 /etc/systemd/system/yast2-nfs-helper.service
   \`\`\`

4. **Configurar D-Bus**:
   \`\`\`bash
   # Crear archivo de configuración D-Bus
   sudo tee /etc/dbus-1/system.d/org.yast2.NFSHelper.conf > /dev/null << 'EOF'
   <!DOCTYPE busconfig PUBLIC
    "-//freedesktop//DTD D-BUS Bus Configuration 1.0//EN"
    "http://www.freedesktop.org/standards/dbus/1.0/busconfig.dtd">
   <busconfig>
     <policy user="root">
       <allow own="org.yast2.NFSHelper"/>
       <allow send_destination="org.yast2.NFSHelper"/>
     </policy>
     
     <policy context="default">
       <allow send_destination="org.yast2.NFSHelper"
              send_interface="org.yast2.NFSHelper"/>
     </policy>
   </busconfig>
   EOF
   
   # Crear archivo de servicio D-Bus
   sudo tee /usr/share/dbus-1/system-services/org.yast2.NFSHelper.service > /dev/null << 'EOF'
   [D-BUS Service]
   Name=org.yast2.NFSHelper
   Exec=/usr/libexec/yast2-nfs-helper
   User=root
   SystemdService=yast2-nfs-helper.service
   EOF
   \`\`\`

5. **Habilitar y iniciar el servicio**:
   \`\`\`bash
   # Recargar configuración de D-Bus
   sudo systemctl reload dbus
   
   # Habilitar e iniciar el servicio del helper
   sudo systemctl daemon-reload
   sudo systemctl enable yast2-nfs-helper.service
   sudo systemctl start yast2-nfs-helper.service
   
   # Verificar estado
   sudo systemctl status yast2-nfs-helper.service
   \`\`\`

6. **Verificar la instalación**:
   \`\`\`bash
   # Probar el helper con el cliente de ejemplo
   python3 src/priv_helper/client_example.py '/shared 192.168.1.0/24(rw,sync)'
   \`\`\`

### Instalación mediante RPM (openSUSE/SUSE)

Para sistemas basados en RPM, use el archivo spec proporcionado:

\`\`\`bash
rpmbuild -ba packaging/yast2-nfs-server.spec
sudo rpm -i rpmbuild/RPMS/noarch/yast2-nfs-server-*.rpm
\`\`\`

## Uso

### Ejecución Normal (lectura)
\`\`\`bash
python3 main.py
\`\`\`

### Ejecución con Permisos Completos (recomendado)
\`\`\`bash
sudo python3 main.py
\`\`\`

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

### Problema: "No hay permisos"
**Solución**: Ejecutar con `sudo python3 main.py`

### Problema: "Servicio NFS no inicia"
**Solución**: 
\`\`\`bash
sudo systemctl status nfs-server
sudo systemctl restart nfs-server
\`\`\`

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

### Consideraciones Importantes

1. **Nunca exportar directorios sensibles** (/etc, /root, /boot)
2. **no_root_squash** solo en redes confiables
3. **all_squash** para acceso público
4. Usar **secure** en producción, no **insecure**
5. Revisar permisos del directorio base

### Seguridad del Helper D-Bus y Polkit

El sistema utiliza polkit para autorización segura de operaciones privilegiadas:

- **Autenticación requerida**: Los usuarios no-root deben autenticarse para aplicar cambios
- **Política de seguridad**: Definida en `/usr/share/polkit-1/actions/org.yast2.nfshelper.policy`
- **Niveles de autorización**:
  - `auth_admin`: Requiere contraseña de administrador
  - `auth_admin_keep`: Mantiene credenciales por un período corto
- **Aislamiento del servicio**: El helper se ejecuta con permisos limitados (systemd hardening)
- **Validación de entrada**: Todas las operaciones validan la sintaxis antes de aplicar cambios
- **Backup automático**: Se crea backup de `/etc/exports` antes de cada cambio
- **Logs de auditoría**: Todas las operaciones se registran en el journal de systemd

### Verificar Seguridad del Helper

\`\`\`bash
# Verificar permisos del helper
ls -l /usr/libexec/yast2-nfs-helper

# Verificar configuración de polkit
cat /usr/share/polkit-1/actions/org.yast2.nfshelper.policy

# Revisar logs del helper
journalctl -u yast2-nfs-helper.service -f

# Verificar hardening del servicio
systemd-analyze security yast2-nfs-helper.service
\`\`\`

### Configuración Recomendada por Caso

**Uso Interno (Red de Confianza)**:
\`\`\`
rw, sync, no_root_squash, secure, subtree_check
\`\`\`

**Uso Público**:
\`\`\`
ro, all_squash, secure, no_subtree_check, anonuid=65534, anongid=65534
\`\`\`

**Backups**:
\`\`\`
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

\`\`\`bash
exportfs -ra          # Recargar exportaciones
exportfs -v          # Ver exportaciones activas
systemctl restart nfs-server  # Reiniciar servicio
systemctl status nfs-server   # Estado del servicio
showmount -e         # Ver exportaciones (cliente)
\`\`\`

## Licencia

MIT License - Use libremente

## Autor

Sistema desarrollado como herramienta de administración de servidores NFS

## Versión

v1.0 - 2025

## Desarrollo y Testing

### Ejecutar Tests

\`\`\`bash
# Instalar dependencias de testing
pip install pytest pytest-cov pytest-mock flake8

# Ejecutar todos los tests
pytest tests/ -v

# Ejecutar tests con cobertura
pytest tests/ --cov=src --cov-report=html

# Ver reporte de cobertura
open htmlcov/index.html
\`\`\`

### Linting

\`\`\`bash
# Verificar sintaxis y estilo
flake8 src/ tests/

# Verificar solo errores críticos
flake8 src/ tests/ --select=E9,F63,F7,F82
\`\`\`

### CI/CD

El proyecto incluye integración continua con GitHub Actions:

- **Linting**: Verifica código con flake8
- **Tests**: Ejecuta suite de tests con pytest
- **Cobertura**: Genera reporte de cobertura de código
- **Integración**: Verifica que todos los módulos se importen correctamente

Ver `.github/workflows/ci.yaml` para más detalles.

### Pruebas Manuales

Para probar el helper D-Bus manualmente:

\`\`\`bash
# 1. Iniciar el servicio helper (si no está corriendo)
sudo systemctl start yast2-nfs-helper.service

# 2. Ejecutar cliente de ejemplo
python3 src/priv_helper/client_example.py '/test/path 192.168.1.0/24(rw,sync)'

# 3. Verificar logs
journalctl -u yast2-nfs-helper.service -n 50

# 4. Probar GUI como usuario no-root
python3 main.py
\`\`\`
