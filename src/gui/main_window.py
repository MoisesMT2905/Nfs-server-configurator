import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import sys
from src.backend.nfs_manager import NFSManager
from src.backend.config_parser import ExportsConfigParser
from src.utils.validators import NFSValidator

class NFSConfiguratorGUI:
    """Interfaz gráfica principal del configurador NFS"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Configurador NFS - Servidor")
        self.root.geometry("900x1000")
        
        # Variables de control
        self.directorio_var = tk.StringVar()
        self.cliente_var = tk.StringVar()
        self.clientes_lista = []
        self.opciones_vars = {}
        self.exportaciones_actuales = []
        
        self._construir_interfaz()
        self._actualizar_exportaciones()
    
    def _construir_interfaz(self):
        """Construye los elementos de la interfaz"""
        # Frame principal con scroll
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Título
        titulo = ttk.Label(main_frame, text="CONFIGURADOR NFS - SERVIDOR", 
                          font=("Arial", 14, "bold"))
        titulo.pack(pady=10)
        
        # Sección: Configuración de Exportación
        self._crear_seccion_configuracion(main_frame)
        
        # Separador
        ttk.Separator(main_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        # Sección: Opciones de Permisos
        self._crear_seccion_permisos(main_frame)
        
        # Separador
        ttk.Separator(main_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        # Sección: Exportaciones Configuradas
        self._crear_seccion_exportaciones(main_frame)
        
        # Separador
        ttk.Separator(main_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        # Botones de acción
        self._crear_botones_accion(main_frame)
    
    def _crear_seccion_configuracion(self, parent):
        """Crea la sección de configuración básica"""
        frame = ttk.LabelFrame(parent, text="Configuración de Exportación", padding=10)
        frame.pack(fill=tk.X, pady=5)
        
        # Directorio
        dir_frame = ttk.Frame(frame)
        dir_frame.pack(fill=tk.X, pady=5)
        ttk.Label(dir_frame, text="Directorio a Exportar:").pack(side=tk.LEFT)
        ttk.Entry(dir_frame, textvariable=self.directorio_var, width=40).pack(side=tk.LEFT, padx=5)
        ttk.Button(dir_frame, text="Examinar...", command=self._examinar_directorio).pack(side=tk.LEFT)
        
        # Cliente
        cliente_frame = ttk.Frame(frame)
        cliente_frame.pack(fill=tk.X, pady=5)
        ttk.Label(cliente_frame, text="Cliente (IP/Subnet/Hostname):").pack(side=tk.LEFT)
        ttk.Entry(cliente_frame, textvariable=self.cliente_var, width=30).pack(side=tk.LEFT, padx=5)
        ttk.Button(cliente_frame, text="Agregar Cliente", command=self._agregar_cliente).pack(side=tk.LEFT)
        
        # Lista de clientes
        clientes_label = ttk.Label(frame, text="Clientes Configurados:")
        clientes_label.pack(anchor=tk.W, pady=(10, 2))
        
        self.clientes_listbox = tk.Listbox(frame, height=3)
        self.clientes_listbox.pack(fill=tk.BOTH, expand=True, pady=5)
        
        botones_frame = ttk.Frame(frame)
        botones_frame.pack(fill=tk.X, pady=5)
        ttk.Button(botones_frame, text="Eliminar Cliente", command=self._eliminar_cliente).pack(side=tk.LEFT, padx=2)
        ttk.Button(botones_frame, text="Editar Cliente", command=self._editar_cliente).pack(side=tk.LEFT, padx=2)
    
    def _crear_seccion_permisos(self, parent):
        """Crea la sección de opciones de permisos"""
        frame = ttk.LabelFrame(parent, text="Opciones de Permisos NFS", padding=10)
        frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Crear dos columnas
        col1 = ttk.Frame(frame)
        col1.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        col2 = ttk.Frame(frame)
        col2.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)
        
        # Columna 1: Permisos Básicos
        ttk.Label(col1, text="Permisos Básicos", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
        self._crear_radio_grupo(col1, "acceso", ["rw", "ro"])
        
        ttk.Label(col1, text="Sincronización", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(10, 5))
        self._crear_radio_grupo(col1, "sincronizacion", ["sync", "async"])
        
        ttk.Label(col1, text="Verificación de Subárbol", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(10, 5))
        self._crear_radio_grupo(col1, "subtree", ["no_subtree_check", "subtree_check"])
        
        # Columna 2: Seguridad
        ttk.Label(col2, text="Seguridad Root", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
        self._crear_radio_grupo(col2, "root_squash", ["no_root_squash", "root_squash"])
        
        ttk.Label(col2, text="Squash de Usuarios", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(10, 5))
        self._crear_checkbox(col2, "all_squash", "all_squash - Squash para todos")
        
        ttk.Label(col2, text="Seguridad de Puertos", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(10, 5))
        self._crear_radio_grupo(col2, "puertos", ["insecure", "secure"])
        
        # Configuración avanzada (abajo)
        ttk.Label(frame, text="Configuración Avanzada", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(15, 5))
        
        avanzado_frame = ttk.Frame(frame)
        avanzado_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(avanzado_frame, text="anonuid:").pack(side=tk.LEFT, padx=5)
        anonuid_var = tk.StringVar()
        self.opciones_vars['anonuid'] = anonuid_var
        ttk.Entry(avanzado_frame, textvariable=anonuid_var, width=10).pack(side=tk.LEFT, padx=2)
        
        ttk.Label(avanzado_frame, text="anongid:").pack(side=tk.LEFT, padx=5)
        anongid_var = tk.StringVar()
        self.opciones_vars['anongid'] = anongid_var
        ttk.Entry(avanzado_frame, textvariable=anongid_var, width=10).pack(side=tk.LEFT, padx=2)
    
    def _crear_radio_grupo(self, parent, grupo, opciones):
        """Crea un grupo de radio buttons"""
        var = tk.StringVar(value="")
        self.opciones_vars[grupo] = var
        
        for opcion in opciones:
            ttk.Radiobutton(parent, text=opcion, variable=var, value=opcion).pack(anchor=tk.W, padx=10)
    
    def _crear_checkbox(self, parent, clave, texto):
        """Crea un checkbox"""
        var = tk.BooleanVar(value=False)
        self.opciones_vars[clave] = var
        ttk.Checkbutton(parent, text=texto, variable=var).pack(anchor=tk.W, padx=10)
    
    def _crear_seccion_exportaciones(self, parent):
        """Crea la sección de exportaciones actuales"""
        frame = ttk.LabelFrame(parent, text="Exportaciones Configuradas Actualmente", padding=10)
        frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.exportaciones_text = scrolledtext.ScrolledText(frame, height=6, width=80)
        self.exportaciones_text.pack(fill=tk.BOTH, expand=True, pady=5)
        self.exportaciones_text.config(state=tk.DISABLED)
        
        botones_frame = ttk.Frame(frame)
        botones_frame.pack(fill=tk.X, pady=5)
        ttk.Button(botones_frame, text="Actualizar", command=self._actualizar_exportaciones).pack(side=tk.LEFT, padx=2)
    
    def _crear_botones_accion(self, parent):
        """Crea los botones de acción principal"""
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(frame, text="Validar Configuración", command=self._validar_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame, text="Aplicar Cambios", command=self._aplicar_cambios).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame, text="Limpiar Formulario", command=self._limpiar_formulario).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame, text="Salir", command=self.root.quit).pack(side=tk.RIGHT, padx=5)
    
    def _examinar_directorio(self):
        """Abre diálogo para seleccionar directorio"""
        directorio = filedialog.askdirectory(title="Seleccionar directorio a exportar")
        if directorio:
            self.directorio_var.set(directorio)
    
    def _agregar_cliente(self):
        """Agrega un cliente a la lista"""
        cliente = self.cliente_var.get().strip()
        if not cliente:
            messagebox.showwarning("Advertencia", "Ingrese un cliente")
            return
        
        valido, msg = NFSValidator.validar_cliente(cliente)
        if not valido:
            messagebox.showerror("Error de Validación", msg)
            return
        
        if cliente not in self.clientes_lista:
            self.clientes_lista.append(cliente)
            self.clientes_listbox.insert(tk.END, cliente)
            self.cliente_var.set("")
        else:
            messagebox.showinfo("Información", "Este cliente ya está en la lista")
    
    def _eliminar_cliente(self):
        """Elimina cliente seleccionado"""
        seleccion = self.clientes_listbox.curselection()
        if seleccion:
            indice = seleccion[0]
            cliente = self.clientes_lista.pop(indice)
            self.clientes_listbox.delete(indice)
    
    def _editar_cliente(self):
        """Edita cliente seleccionado"""
        seleccion = self.clientes_listbox.curselection()
        if seleccion:
            indice = seleccion[0]
            cliente_actual = self.clientes_lista[indice]
            self.cliente_var.set(cliente_actual)
            self._eliminar_cliente()
    
    def _obtener_opciones(self) -> dict:
        """Obtiene las opciones seleccionadas"""
        opciones = {}
        
        # Radio buttons
        for grupo in NFSValidator.PERMISSION_GROUPS:
            valor = self.opciones_vars[grupo].get()
            if valor:
                opciones[valor] = True
        
        # Checkboxes
        if self.opciones_vars['all_squash'].get():
            opciones['all_squash'] = True
        
        # Campos numéricos
        anonuid = self.opciones_vars['anonuid'].get()
        if anonuid:
            opciones['anonuid'] = anonuid
        
        anongid = self.opciones_vars['anongid'].get()
        if anongid:
            opciones['anongid'] = anongid
        
        return opciones
    
    def _validar_config(self):
        """Valida la configuración actual"""
        directorio = self.directorio_var.get()
        if not self.clientes_lista:
            messagebox.showerror("Error", "Agregue al menos un cliente")
            return
        
        opciones = self._obtener_opciones()
        
        # Validar cada cliente
        errores = []
        for cliente in self.clientes_lista:
            valido, msgs = NFSManager.validar_configuracion_completa(directorio, cliente, opciones)
            if not valido:
                errores.extend(msgs)
        
        if errores:
            messagebox.showerror("Errores de Validación", "\n".join(errores))
        else:
            # Generar preview
            preview = "Configuración válida:\n\n"
            for cliente in self.clientes_lista:
                linea = ExportsConfigParser.generar_linea_export(directorio, cliente, opciones)
                preview += linea + "\n"
            messagebox.showinfo("Configuración Válida", preview)
    
    def _aplicar_cambios(self):
        """Aplica los cambios de configuración"""
        if not NFSManager.verificar_permisos():
            messagebox.showerror("Error", "Este programa debe ejecutarse como root")
            return
        
        directorio = self.directorio_var.get()
        if not self.clientes_lista:
            messagebox.showerror("Error", "Agregue al menos un cliente")
            return
        
        # Generar contenido nuevo para /etc/exports
        lineas_nuevas = []
        opciones = self._obtener_opciones()
        
        for cliente in self.clientes_lista:
            linea = ExportsConfigParser.generar_linea_export(directorio, cliente, opciones)
            lineas_nuevas.append(linea)
        
        contenido_nuevo = "\n".join(lineas_nuevas) + "\n"
        
        # Confirmar cambios
        if messagebox.askyesno("Confirmación", f"¿Aplicar estos cambios a /etc/exports?\n\n{contenido_nuevo}"):
            exito, msg = NFSManager.aplicar_exportaciones(contenido_nuevo)
            if exito:
                messagebox.showinfo("Éxito", msg)
                self._actualizar_exportaciones()
                self._limpiar_formulario()
            else:
                messagebox.showerror("Error", msg)
    
    def _limpiar_formulario(self):
        """Limpia el formulario"""
        self.directorio_var.set("")
        self.cliente_var.set("")
        self.clientes_lista.clear()
        self.clientes_listbox.delete(0, tk.END)
        
        for var in self.opciones_vars.values():
            if isinstance(var, tk.StringVar):
                var.set("")
            elif isinstance(var, tk.BooleanVar):
                var.set(False)
    
    def _actualizar_exportaciones(self):
        """Actualiza la lista de exportaciones actuales"""
        try:
            lineas = ExportsConfigParser.leer_exports()
            self.exportaciones_text.config(state=tk.NORMAL)
            self.exportaciones_text.delete(1.0, tk.END)
            
            if lineas:
                for i, linea in enumerate(lineas, 1):
                    self.exportaciones_text.insert(tk.END, f"{i}. {linea}\n")
            else:
                self.exportaciones_text.insert(tk.END, "No hay exportaciones configuradas")
            
            self.exportaciones_text.config(state=tk.DISABLED)
        except Exception as e:
            self.exportaciones_text.config(state=tk.NORMAL)
            self.exportaciones_text.delete(1.0, tk.END)
            self.exportaciones_text.insert(tk.END, f"Error: {str(e)}")
            self.exportaciones_text.config(state=tk.DISABLED)
