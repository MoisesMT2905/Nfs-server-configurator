#!/usr/bin/env python3
"""
Interfaz GTK principal. Esta implementación adapta los controles para usar CheckButtons
para las 13 opciones de permisos NFS solicitadas y añade validaciones para opciones mutuamente
exclusivas y validación de UID/GID. Mantiene el resto de la lógica de la GUI.
"""
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GObject
import logging
import os

from src.backend.config_parser import build_export_line
from src.backend.nfs_manager import NFSManager
from src.utils.validators import validate_path, validate_client, validate_uid_gid

LOG = logging.getLogger("gui")

class NFSConfiguratorGUI(Gtk.Window):
    def __init__(self):
        super().__init__(title="Configurador NFS - Servidor")
        self.set_default_size(800, 600)
        self.set_border_width(6)

        # Main vertical box
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.add(vbox)

        # Export section
        frame_export = Gtk.Frame(label="Configuración de Exportación")
        vbox.pack_start(frame_export, False, False, 0)
        grid = Gtk.Grid(column_spacing=6, row_spacing=6, margin=6)
        frame_export.add(grid)

        # Path entry + browse
        self.path_entry = Gtk.Entry()
        browse_btn = Gtk.Button(label="Examinar...")
        browse_btn.connect("clicked", self.on_browse)
        grid.attach(Gtk.Label(label="Directorio a Exportar:"), 0, 0, 1, 1)
        grid.attach(self.path_entry, 1, 0, 4, 1)
        grid.attach(browse_btn, 5, 0, 1, 1)

        # Client entry + add
        self.client_entry = Gtk.Entry()
        add_client_btn = Gtk.Button(label="Agregar Cliente")
        add_client_btn.connect("clicked", self.on_add_client)
        grid.attach(Gtk.Label(label="Cliente (IP/Subnet/Hostname):"), 0, 1, 1, 1)
        grid.attach(self.client_entry, 1, 1, 3, 1)
        grid.attach(add_client_btn, 4, 1, 1, 1)

        # Clients list (simple TextView for initial)
        self.clients_store = []
        self.clients_view = Gtk.TextView()
        self.clients_view.set_editable(False)
        clients_scrolled = Gtk.ScrolledWindow()
        clients_scrolled.set_min_content_height(80)
        clients_scrolled.add(self.clients_view)
        grid.attach(Gtk.Label(label="Clientes Configurados:"), 0, 2, 1, 1)
        grid.attach(clients_scrolled, 1, 2, 5, 1)

        # Buttons Edit/Delete
        edit_btn = Gtk.Button(label="Editar Cliente")
        edit_btn.connect("clicked", self.on_edit_client)
        del_btn = Gtk.Button(label="Eliminar Cliente")
        del_btn.connect("clicked", self.on_delete_client)
        grid.attach(edit_btn, 1, 3, 1, 1)
        grid.attach(del_btn, 2, 3, 1, 1)

        # Options frame (use CheckButtons for all 13 options)
        options_frame = Gtk.Frame(label="Opciones de Permisos NFS")
        vbox.pack_start(options_frame, False, False, 0)
        opts_grid = Gtk.Grid(column_spacing=6, row_spacing=6, margin=6)
        options_frame.add(opts_grid)

        # 1) rw, 2) ro
        opts_grid.attach(Gtk.Label(label="Permisos Básicos"), 0, 0, 1, 1)
        self.rw_chk = Gtk.CheckButton(label="rw")
        self.ro_chk = Gtk.CheckButton(label="ro")
        opts_grid.attach(self.rw_chk, 0, 1, 1, 1)
        opts_grid.attach(self.ro_chk, 1, 1, 1, 1)

        # 3) sync, 4) async
        opts_grid.attach(Gtk.Label(label="Sincronización"), 0, 2, 1, 1)
        self.sync_chk = Gtk.CheckButton(label="sync")
        self.async_chk = Gtk.CheckButton(label="async")
        opts_grid.attach(self.sync_chk, 0, 3, 1, 1)
        opts_grid.attach(self.async_chk, 1, 3, 1, 1)

        # 5) no_root_squash, 6) root_squash
        opts_grid.attach(Gtk.Label(label="Seguridad Root"), 2, 0, 1, 1)
        self.no_root_chk = Gtk.CheckButton(label="no_root_squash")
        self.root_squash_chk = Gtk.CheckButton(label="root_squash")
        opts_grid.attach(self.no_root_chk, 2, 1, 1, 1)
        opts_grid.attach(self.root_squash_chk, 3, 1, 1, 1)

        # 7) all_squash
        self.all_squash_chk = Gtk.CheckButton(label="all_squash - Squash para todos")
        opts_grid.attach(self.all_squash_chk, 2, 2, 2, 1)

        # 8) no_subtree_check, 9) subtree_check
        opts_grid.attach(Gtk.Label(label="Verificación de Subárbol"), 4, 0, 1, 1)
        self.no_subtree_chk = Gtk.CheckButton(label="no_subtree_check")
        self.subtree_chk = Gtk.CheckButton(label="subtree_check")
        opts_grid.attach(self.no_subtree_chk, 4, 1, 1, 1)
        opts_grid.attach(self.subtree_chk, 5, 1, 1, 1)

        # 10) insecure, 11) secure
        opts_grid.attach(Gtk.Label(label="Seguridad de Puertos"), 4, 2, 1, 1)
        self.insecure_chk = Gtk.CheckButton(label="insecure")
        self.secure_chk = Gtk.CheckButton(label="secure")
        opts_grid.attach(self.insecure_chk, 4, 3, 1, 1)
        opts_grid.attach(self.secure_chk, 5, 3, 1, 1)

        # 12) anonuid, 13) anongid
        opts_grid.attach(Gtk.Label(label="Configuración Avanzada"), 0, 4, 1, 1)
        opts_grid.attach(Gtk.Label(label="anonuid:"), 1, 4, 1, 1)
        self.anonuid_entry = Gtk.Entry()
        opts_grid.attach(self.anonuid_entry, 2, 4, 1, 1)
        opts_grid.attach(Gtk.Label(label="anongid:"), 3, 4, 1, 1)
        self.anongid_entry = Gtk.Entry()
        opts_grid.attach(self.anongid_entry, 4, 4, 1, 1)

        # Exports current (TextView)
        frame_current = Gtk.Frame(label="Exportaciones Configuradas Actualmente")
        vbox.pack_start(frame_current, True, True, 0)
        self.exports_view = Gtk.TextView()
        self.exports_view.set_editable(False)
        sc = Gtk.ScrolledWindow()
        sc.add(self.exports_view)
        frame_current.add(sc)

        # Bottom buttons
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        apply_btn = Gtk.Button(label="Aplicar Cambios")
        apply_btn.connect("clicked", self.on_apply)
        update_btn = Gtk.Button(label="Actualizar")
        update_btn.connect("clicked", self.on_update)
        hbox.pack_end(apply_btn, False, False, 0)
        hbox.pack_end(update_btn, False, False, 0)
        vbox.pack_start(hbox, False, False, 0)

        # Inicializar vista con exportfs -v
        self.on_update(None)
        self.show_all()

    def on_browse(self, widget):
        dialog = Gtk.FileChooserDialog(title="Seleccione directorio", parent=self, action=Gtk.FileChooserAction.SELECT_FOLDER)
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
        resp = dialog.run()
        if resp == Gtk.ResponseType.OK:
            self.path_entry.set_text(dialog.get_filename())
        dialog.destroy()

    def on_add_client(self, widget):
        val = self.client_entry.get_text().strip()
        if not val:
            return
        if not validate_client(val):
            self._show_error("Cliente inválido", f"Cliente '{val}' no parece ser IP/CIDR/hostname válido")
            return
        self.clients_store.append(val)
        self._refresh_clients_view()
        self.client_entry.set_text("")

    def on_edit_client(self, widget):
        # Simplificado: mostrar diálogo para editar último cliente
        if not self.clients_store:
            return
        old = self.clients_store[-1]
        dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.QUESTION, Gtk.ButtonsType.OK_CANCEL, "Editar cliente")
        dialog.format_secondary_text(f"Editar último cliente ({old}): ingrese nuevo valor")
        entry = Gtk.Entry()
        entry.set_text(old)
        dialog.get_content_area().pack_end(entry, False, False, 0)
        entry.show()
        resp = dialog.run()
        if resp == Gtk.ResponseType.OK:
            val = entry.get_text().strip()
            if validate_client(val):
                self.clients_store[-1] = val
                self._refresh_clients_view()
            else:
                self._show_error("Cliente inválido", f"Valor '{val}' inválido")
        dialog.destroy()

    def on_delete_client(self, widget):
        if not self.clients_store:
            return
        self.clients_store.pop()
        self._refresh_clients_view()

    def _refresh_clients_view(self):
        buf = self.clients_view.get_buffer()
        buf.set_text("\n".join(self.clients_store))

    def on_update(self, widget):
        text = NFSManager.list_exports()
        buf = self.exports_view.get_buffer()
        buf.set_text(text if text else "No hay exportaciones configuradas")

    def _validate_options(self, options: dict) -> (bool, str):
        """Valida combinaciones mutuamente exclusivas y valores de anonuid/anongid."""
        # rw vs ro: exactamente one selected
        if options.get("rw") and options.get("ro"):
            return False, "No puede seleccionar 'rw' y 'ro' al mismo tiempo"
        if not options.get("rw") and not options.get("ro"):
            return False, "Debe seleccionar al menos 'rw' o 'ro'"
        # sync vs async
        if options.get("sync") and options.get("async"):
            return False, "No puede seleccionar 'sync' y 'async' simultáneamente"
        # subtree
        if options.get("no_subtree_check") and options.get("subtree_check"):
            return False, "No puede seleccionar 'no_subtree_check' y 'subtree_check' al mismo tiempo"
        # root squash
        if options.get("no_root_squash") and options.get("root_squash"):
            return False, "No puede seleccionar 'no_root_squash' y 'root_squash' al mismo tiempo"
        # secure/insecure
        if options.get("secure") and options.get("insecure"):
            return False, "No puede seleccionar 'secure' y 'insecure' al mismo tiempo"
        # anonuid/anongid validation
        anonuid = options.get("anonuid")
        anongid = options.get("anongid")
        if anonuid:
            if not validate_uid_gid(anonuid):
                return False, f"anonuid '{anonuid}' no es un UID válido"
        if anongid:
            if not validate_uid_gid(anongid):
                return False, f"anongid '{anongid}' no es un GID válido"
        return True, ""

    def on_apply(self, widget):
        path = self.path_entry.get_text().strip()
        if not path:
            self._show_error("Directorio requerido", "Debe indicar el directorio a exportar")
            return
        if not validate_path(path):
            self._show_error("Directorio inválido", f"El directorio '{path}' no existe o no es accesible")
            return
        if not self.clients_store:
            self._show_error("Clientes vacíos", "Agregue al menos un cliente")
            return

        options = {
            "rw": self.rw_chk.get_active(),
            "ro": self.ro_chk.get_active(),
            "sync": self.sync_chk.get_active(),
            "async": self.async_chk.get_active(),
            "no_subtree_check": self.no_subtree_chk.get_active(),
            "subtree_check": self.subtree_chk.get_active(),
            "no_root_squash": self.no_root_chk.get_active(),
            "root_squash": self.root_squash_chk.get_active(),
            "all_squash": self.all_squash_chk.get_active(),
            "secure": self.secure_chk.get_active(),
            "insecure": self.insecure_chk.get_active(),
            "anonuid": self.anonuid_entry.get_text().strip() or None,
            "anongid": self.anongid_entry.get_text().strip() or None,
        }

        ok, msg = self._validate_options(options)
        if not ok:
            self._show_error("Opciones inválidas", msg)
            return

        exports_text = build_export_line(path, self.clients_store, options)

        confirm = Gtk.MessageDialog(self, 0, Gtk.MessageType.QUESTION, Gtk.ButtonsType.OK_CANCEL,
                                    "Confirmar aplicación")
        confirm.format_secondary_text(f"Se aplicará la siguiente configuración:\n\n{exports_text}")
        resp = confirm.run()
        confirm.destroy()
        if resp != Gtk.ResponseType.OK:
            return

        # Check if running as root
        if os.geteuid() == 0:
            # Running as root, use NFSManager directly
            LOG.info("Running as root, using NFSManager directly")
            res = NFSManager.apply_configuration(exports_text)
            if res.get("ok"):
                self._show_info("Éxito", res.get("msg"))
                self.on_update(None)
            else:
                self._show_error("Fallo al aplicar", res.get("msg"))
        else:
            # Not running as root, use D-Bus helper with polkit
            LOG.info("Not running as root, using D-Bus helper")
            success, message = self._apply_via_helper(exports_text)
            if success:
                self._show_info("Éxito", message)
                self.on_update(None)
            else:
                self._show_error("Fallo al aplicar", message)

    def _apply_via_helper(self, exports_text):
        """
        Apply configuration via D-Bus helper service.
        Returns: (success: bool, message: str)
        """
        try:
            from pydbus import SystemBus
            
            # Connect to system bus
            bus = SystemBus()
            
            # Get helper service
            helper = bus.get("org.yast2.NFSHelper", "/org/yast2/NFSHelper")
            
            # Call ApplyConfiguration method
            LOG.info("Calling helper.ApplyConfiguration via D-Bus")
            success, message = helper.ApplyConfiguration(exports_text)
            
            return success, message
            
        except Exception as e:
            error_msg = f"Error connecting to helper service: {str(e)}\n\n"
            error_msg += "Asegúrese de que:\n"
            error_msg += "1. El servicio yast2-nfs-helper está corriendo\n"
            error_msg += "2. El usuario tiene permisos de polkit configurados\n"
            error_msg += "3. D-Bus está configurado correctamente"
            LOG.error(error_msg)
            return False, error_msg

    def _show_error(self, title, msg):
        dlg = Gtk.MessageDialog(self, 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.OK, title)
        dlg.format_secondary_text(msg)
        dlg.run()
        dlg.destroy()

    def _show_info(self, title, msg):
        dlg = Gtk.MessageDialog(self, 0, Gtk.MessageType.INFO, Gtk.ButtonsType.OK, title)
        dlg.format_secondary_text(msg)
        dlg.run()
        dlg.destroy()