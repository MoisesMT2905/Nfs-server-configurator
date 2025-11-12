# YaST2 NFS Server Configurator

Sistema gráfico modular para configurar exportaciones NFS en Linux con arquitectura YaST2, soporte para usuarios no privilegiados mediante D-Bus y PolicyKit, y tests automatizados.

## 🎯 Características Principales

- **Interfaz GTK3** moderna e intuitiva inspirada en YaST2
- **Soporte para usuarios no root** mediante helper D-Bus privilegiado y PolicyKit
- **13 opciones de permisos NFS** con validaciones en tiempo real
- **Backup automático** antes de aplicar cambios
- **Validación completa** de rutas, clientes (IP/CIDR/hostname) y opciones
- **Tests automatizados** con pytest
- **CI/CD** con GitHub Actions

## 📋 Requisitos Previos

### Sistema Operativo
- Linux (openSUSE, SUSE Linux Enterprise, Ubuntu 18.04+, Debian 10+)

### Dependencias del Sistema
```bash
# openSUSE/SLE
sudo zypper install python3 python3-gobject python3-pydbus gtk3 polkit nfs-kernel-server

# Ubuntu/Debian
sudo apt-get install python3 python3-gi python3-pydbus gir1.2-gtk-3.0 policykit-1 nfs-kernel-server
```

### Python
- Python 3.8 o superior

## 🚀 Instalación

### Instalación desde Código Fuente

1. **Clonar el repositorio**:
   ```bash
   git clone https://github.com/MoisesMT2905/Nfs-server-configurator.git
   cd Nfs-server-configurator
   ```

2. **Instalar dependencias Python**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Instalar el helper D-Bus privilegiado** (requerido para usuarios no root):
   ```bash
   # Copiar helper a /usr/libexec
   sudo install -m 755 src/priv_helper/helper.py /usr/libexec/yast2-nfs-server-helper
   
   # Instalar unit systemd
   sudo install -m 644 packaging/yast2-nfs-helper.service /usr/lib/systemd/system/
   
   # Instalar política polkit
   sudo install -m 644 packaging/org.yast2.nfshelper.policy /usr/share/polkit-1/actions/
   
   # Habilitar y arrancar el servicio
   sudo systemctl daemon-reload
   sudo systemctl enable --now yast2-nfs-helper.service
   ```

4. **Verificar la instalación del helper**:
   ```bash
   systemctl status yast2-nfs-helper
   ```

### Instalación desde RPM (openSUSE/SLE)

```bash
sudo rpm -ivh yast2-nfs-server-1.0.0-1.noarch.rpm
```

El paquete RPM instala y habilita automáticamente el servicio helper.

## 📖 Uso

### Ejecución como Usuario Normal (Recomendado)

**⚠️ IMPORTANTE: NO ejecute la GUI como root. Use su usuario normal.**

```bash
python3 main.py
```

Cuando intente aplicar cambios, PolicyKit solicitará autenticación administrativa mediante un diálogo gráfico. El helper D-Bus privilegiado se encargará de aplicar los cambios de forma segura.

### Ejecución como Root (No Recomendado)

Si por alguna razón necesita ejecutar como root directamente:

```bash
sudo python3 main.py
```

En este modo, la aplicación saltará el helper D-Bus y aplicará cambios directamente (menos seguro).

## 🔧 Arquitectura del Sistema

### Componentes

1. **GUI (src/gui/main_window.py)**: Interfaz gráfica GTK3
2. **Backend (src/backend/)**: 
   - `nfs_manager.py`: Gestión de configuración NFS
   - `config_parser.py`: Parser de /etc/exports
3. **Validadores (src/utils/validators.py)**: Validación de entradas
4. **Helper D-Bus (src/priv_helper/helper.py)**: Servicio privilegiado para usuarios no root

### Flujo de Autorización

```
Usuario Normal → GUI → D-Bus → PolicyKit → Helper Privilegiado → NFSManager → /etc/exports
```

### Flujo como Root

```
Root → GUI → NFSManager → /etc/exports
```

## 🛡️ Seguridad

### PolicyKit

El helper D-Bus utiliza PolicyKit para solicitar autorización administrativa. La política se encuentra en:

```
/usr/share/polkit-1/actions/org.yast2.nfshelper.policy
```

**Acción**: `org.yast2.nfshelper.apply`
- **allow_any**: `auth_admin` - Requiere autenticación administrativa
- **allow_inactive**: `auth_admin` - Requiere autenticación administrativa
- **allow_active**: `auth_admin_keep` - Reutiliza autenticación reciente

### Consideraciones de Seguridad

1. **NO ejecute la GUI como root** - use el helper D-Bus
2. **El helper valida todas las entradas** antes de aplicar cambios
3. **Se crean backups automáticos** de /etc/exports antes de modificarlo
4. **El helper NO permite ejecución arbitraria de comandos**
5. **Solo se permiten operaciones específicas** sobre /etc/exports

### Recomendaciones

- ❌ **NO exportar directorios sensibles**: `/etc`, `/root`, `/boot`, `/sys`, `/proc`
- ⚠️ **`no_root_squash`**: Solo en redes completamente confiables
- ✅ **`all_squash`**: Recomendado para acceso público
- ✅ **`secure`**: Usar en producción (no `insecure`)
- ✅ **Revisar permisos** del directorio antes de exportar

## 📝 Opciones de Permisos NFS (13 Opciones Soportadas)

### Permisos Básicos (mutuamente excluyentes)
- **`rw`**: Lectura y escritura
- **`ro`**: Solo lectura

### Sincronización (mutuamente excluyentes)
- **`sync`**: Escrituras síncronas (más seguro, más lento)
- **`async`**: Escrituras asíncronas (más rápido, menos seguro)

### Seguridad Root (mutuamente excluyentes)
- **`no_root_squash`**: Permite acceso root completo (⚠️ peligroso)
- **`root_squash`**: Mapea root remoto a usuario anónimo (recomendado)

### Squash de Usuarios
- **`all_squash`**: Mapea todos los usuarios a anónimo

### Verificación de Subárbol (mutuamente excluyentes)
- **`no_subtree_check`**: Sin verificación (recomendado para exportaciones completas)
- **`subtree_check`**: Con verificación (más seguro para subdirectorios)

### Seguridad de Puertos (mutuamente excluyentes)
- **`insecure`**: Permite puertos > 1024
- **`secure`**: Solo puertos privilegiados < 1024 (recomendado)

### Configuración Avanzada
- **`anonuid=<UID>`**: UID para usuarios anónimos (requiere `all_squash`)
- **`anongid=<GID>`**: GID para usuarios anónimos (requiere `all_squash`)

### Ejemplos de Configuración

#### Uso Interno (Red de Confianza)
```
/shared/data 192.168.1.0/24(rw,sync,no_root_squash,secure,subtree_check)
```

#### Uso Público (Solo Lectura)
```
/public *(ro,all_squash,secure,no_subtree_check,anonuid=65534,anongid=65534)
```

#### Backups
```
/backups 10.0.0.5(ro,sync,root_squash,secure,no_subtree_check)
```

## 🧪 Desarrollo y Testing

### Ejecutar Tests

```bash
# Instalar dependencias de testing
pip install pytest pytest-cov

# Ejecutar todos los tests
pytest tests/ -v

# Ejecutar tests con cobertura
pytest tests/ --cov=src --cov-report=html

# Ver reporte de cobertura
open htmlcov/index.html
```

### Tests Incluidos

- **test_config_parser.py**: Tests del parser de configuración
  - Generación de opciones (13 opciones)
  - Parsing de líneas de exportación
  - Backup y restauración
  - Combinaciones de opciones

- **test_validators.py**: Tests de validación
  - Validación de directorios y paths
  - Validación de IPs, CIDR, hostnames
  - Validación de opciones mutuamente excluyentes
  - Validación de UID/GID

- **test_nfs_manager.py**: Tests del gestor NFS
  - Aplicación de configuración (con mocks)
  - Manejo de errores y permisos
  - Backup y rollback
  - Ejecución de comandos del sistema

### Linting

```bash
# Instalar linters
pip install flake8 pylint

# Ejecutar flake8
flake8 src/ --max-line-length=127

# Ejecutar pylint
pylint src/
```

## 🧪 Prueba del Helper D-Bus

### Cliente de Ejemplo

Se incluye un cliente de ejemplo para probar el helper D-Bus:

```bash
# Ejecutar cliente de ejemplo
python3 src/priv_helper/client_example.py

# Ver información del servicio
python3 src/priv_helper/client_example.py --info
```

### Verificar el Servicio

```bash
# Estado del servicio
systemctl status yast2-nfs-helper

# Ver logs en tiempo real
journalctl -u yast2-nfs-helper -f

# Probar con dbus-send (manual)
dbus-send --system --print-reply \
  --dest=org.yast2.NFSHelper \
  /org/yast2/NFSHelper \
  org.yast2.NFSHelper.ApplyConfiguration \
  string:'/test 192.168.1.0/24(rw,sync)'
```

## 🐛 Troubleshooting

### Problema: "Helper D-Bus no disponible"

**Síntomas**: Error al intentar aplicar cambios como usuario normal

**Solución**:
```bash
# Verificar que el servicio está corriendo
systemctl status yast2-nfs-helper

# Si no está corriendo, iniciarlo
sudo systemctl start yast2-nfs-helper

# Verificar logs
journalctl -u yast2-nfs-helper -n 50
```

### Problema: "No hay permisos para escribir /etc/exports"

**Síntomas**: Error de permisos al aplicar cambios

**Solución**:
- Si ejecuta como usuario normal: Asegúrese de que el helper D-Bus está instalado y corriendo
- Si ejecuta como root: Verifique permisos del archivo `/etc/exports`

### Problema: "Error de sintaxis en /etc/exports"

**Síntomas**: Falla al aplicar configuración

**Solución**:
- La aplicación debería restaurar automáticamente el backup
- Verificar manualmente: `ls -la /etc/exports.*`
- Revisar formato de opciones en la interfaz
- Usar "Validar Configuración" antes de aplicar

### Problema: "PolicyKit no solicita autenticación"

**Síntomas**: No aparece diálogo de autenticación

**Solución**:
```bash
# Verificar que polkit está instalado
which pkcheck

# Verificar política instalada
ls -la /usr/share/polkit-1/actions/org.yast2.nfshelper.policy

# Reinstalar política
sudo install -m 644 packaging/org.yast2.nfshelper.policy \
  /usr/share/polkit-1/actions/
```

### Problema: Cliente no puede montar exportación

**Síntomas**: Cliente recibe error al intentar montar

**Solución**:
```bash
# En servidor: verificar exportaciones activas
sudo exportfs -v

# En servidor: reiniciar servicio NFS
sudo systemctl restart nfs-server

# En cliente: verificar exportaciones disponibles
showmount -e <servidor>

# En cliente: montar manualmente
sudo mount -t nfs <servidor>:/ruta /mnt/punto
```

## 📚 Estructura del Proyecto

```
.
├── main.py                          # Punto de entrada de la aplicación
├── README.md                        # Este archivo
├── requirements.txt                 # Dependencias Python
├── pytest.ini                       # Configuración de pytest
├── .gitignore                       # Archivos ignorados por git
├── .github/
│   └── workflows/
│       └── ci.yaml                  # CI/CD con GitHub Actions
├── packaging/
│   ├── yast2-nfs-server.spec       # Spec file RPM
│   ├── yast2-nfs-helper.service    # Unit file systemd
│   └── org.yast2.nfshelper.policy  # Política polkit
├── src/
│   ├── backend/
│   │   ├── nfs_manager.py          # Gestor de configuración NFS
│   │   └── config_parser.py        # Parser de /etc/exports
│   ├── gui/
│   │   └── main_window.py          # Interfaz GTK3
│   ├── priv_helper/
│   │   ├── helper.py               # Helper D-Bus privilegiado
│   │   └── client_example.py       # Cliente de ejemplo
│   └── utils/
│       └── validators.py           # Validadores
└── tests/
    ├── test_config_parser.py       # Tests del parser
    ├── test_validators.py          # Tests de validadores
    └── test_nfs_manager.py         # Tests del gestor NFS
```

## 🔄 Flujo de Trabajo

1. **Usuario inicia la GUI** (`main.py`)
2. **Configura exportación**:
   - Selecciona directorio
   - Añade clientes (IP/CIDR/hostname)
   - Selecciona opciones (13 disponibles)
3. **Valida configuración** (opcional pero recomendado)
4. **Aplica cambios**:
   - Si es root: NFSManager aplica directamente
   - Si es usuario normal: GUI → D-Bus → PolicyKit → Helper → NFSManager
5. **Helper realiza**:
   - Crea backup de `/etc/exports`
   - Escribe nueva configuración
   - Ejecuta `exportfs -ra` para validar
   - Recarga servicio NFS
   - Si falla: restaura backup automáticamente
6. **GUI muestra resultado** al usuario

## 📦 Empaquetado RPM

### Crear RPM

```bash
# Preparar directorio de build
mkdir -p ~/rpmbuild/{BUILD,RPMS,SOURCES,SPECS,SRPMS}

# Copiar spec
cp packaging/yast2-nfs-server.spec ~/rpmbuild/SPECS/

# Crear tarball
tar czf ~/rpmbuild/SOURCES/yast2-nfs-server-1.0.0.tar.gz \
  --transform 's,^,yast2-nfs-server-1.0.0/,' \
  --exclude='.git*' --exclude='__pycache__' .

# Build RPM
rpmbuild -ba ~/rpmbuild/SPECS/yast2-nfs-server.spec

# RPM generado en:
# ~/rpmbuild/RPMS/noarch/yast2-nfs-server-1.0.0-1.noarch.rpm
```

## 🤝 Contribuir

Las contribuciones son bienvenidas. Por favor:

1. Fork el repositorio
2. Cree una rama para su feature (`git checkout -b feature/AmazingFeature`)
3. Commit sus cambios (`git commit -m 'Add AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abra un Pull Request

### Antes de enviar PR

- Ejecute los tests: `pytest tests/ -v`
- Verifique el linting: `flake8 src/`
- Actualice documentación si es necesario

## 📄 Licencia

MIT License - Use libremente

## 👤 Autor

Sistema desarrollado como módulo YaST2 para configuración de servidores NFS en openSUSE/SLE

## 🙏 Agradecimientos

- Proyecto YaST2 por la inspiración del diseño
- Comunidad openSUSE/SLE por el feedback

## 📞 Soporte

- **Issues**: https://github.com/MoisesMT2905/Nfs-server-configurator/issues
- **Documentación**: Este README
- **Wiki**: (próximamente)

## 🗺️ Roadmap

- [ ] Soporte para NFSv4 con Kerberos
- [ ] Importar/exportar configuraciones
- [ ] Editor avanzado de permisos por cliente
- [ ] Integración con firewall
- [ ] Modo CLI para automatización
- [ ] Soporte i18n/l10n (traducciones)

---

**Versión**: 1.0.0  
**Última actualización**: Noviembre 2024
