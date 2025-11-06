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
   └── src/
       ├── backend/
       │   ├── nfs_manager.py
       │   └── config_parser.py
       ├── gui/
       │   └── main_window.py
       └── utils/
           └── validators.py
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
