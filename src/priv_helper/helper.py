#!/usr/bin/env python3
"""
D-Bus Service for NFS Configuration with Polkit Authorization

This service provides privileged operations for NFS export configuration,
allowing non-root users to make changes after polkit authorization.

Service: org.yast2.NFSHelper
Object Path: /org/yast2/NFSHelper
Interface: org.yast2.NFSHelper
"""

import sys
import os
import subprocess
import logging
from typing import Dict, Any

import dbus
import dbus.service
import dbus.mainloop.glib
from gi.repository import GLib

# Add parent directories to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.backend.nfs_manager import NFSManager
from src.backend.config_parser import ExportsConfigParser

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
LOG = logging.getLogger("nfs-helper")

# D-Bus service configuration
SERVICE_NAME = "org.yast2.NFSHelper"
OBJECT_PATH = "/org/yast2/NFSHelper"
INTERFACE_NAME = "org.yast2.NFSHelper"
POLKIT_ACTION = "org.yast2.nfshelper.apply-configuration"


class NFSHelperService(dbus.service.Object):
    """D-Bus service for privileged NFS operations"""
    
    def __init__(self, bus, object_path):
        super().__init__(bus, object_path)
        LOG.info(f"NFSHelper service initialized at {object_path}")
    
    def _check_polkit_authorization(self, sender: str, action: str) -> bool:
        """
        Check if the sender is authorized via polkit
        
        Args:
            sender: D-Bus sender name
            action: Polkit action ID
            
        Returns:
            True if authorized, False otherwise
        """
        try:
            # Get the system bus
            system_bus = dbus.SystemBus()
            
            # Get PID of the sender
            bus_obj = system_bus.get_object('org.freedesktop.DBus', '/org/freedesktop/DBus')
            bus_iface = dbus.Interface(bus_obj, 'org.freedesktop.DBus')
            pid = bus_iface.GetConnectionUnixProcessID(sender)
            
            LOG.info(f"Checking polkit authorization for PID {pid}, action {action}")
            
            # Use pkcheck to verify authorization
            result = subprocess.run(
                ['pkcheck', '--action-id', action, '--process', str(pid)],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                LOG.info(f"Authorization granted for PID {pid}")
                return True
            else:
                LOG.warning(f"Authorization denied for PID {pid}: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            LOG.error("Polkit check timeout")
            return False
        except Exception as e:
            LOG.error(f"Error checking polkit authorization: {e}")
            return False
    
    @dbus.service.method(
        dbus_interface=INTERFACE_NAME,
        in_signature='s',
        out_signature='a{sv}',
        sender_keyword='sender'
    )
    def ApplyConfiguration(self, exports_text: str, sender=None) -> Dict[str, Any]:
        """
        Apply NFS export configuration
        
        Args:
            exports_text: The complete exports configuration text
            sender: D-Bus sender (automatically provided)
            
        Returns:
            Dictionary with 'success' (bool) and 'message' (str)
        """
        LOG.info(f"ApplyConfiguration called by {sender}")
        
        # Check polkit authorization
        if not self._check_polkit_authorization(sender, POLKIT_ACTION):
            LOG.error("Authorization check failed")
            return {
                'success': False,
                'message': 'Authorization denied. User not authorized to apply NFS configuration.'
            }
        
        # Validate exports_text is not empty
        if not exports_text or not exports_text.strip():
            LOG.error("Empty exports configuration")
            return {
                'success': False,
                'message': 'Empty configuration provided'
            }
        
        try:
            # Use NFSManager to apply the configuration
            LOG.info("Applying NFS configuration...")
            success, message = NFSManager.aplicar_exportaciones(exports_text)
            
            if success:
                LOG.info("Configuration applied successfully")
                return {
                    'success': True,
                    'message': message
                }
            else:
                LOG.error(f"Failed to apply configuration: {message}")
                return {
                    'success': False,
                    'message': message
                }
                
        except Exception as e:
            LOG.error(f"Exception in ApplyConfiguration: {e}", exc_info=True)
            return {
                'success': False,
                'message': f'Internal error: {str(e)}'
            }
    
    @dbus.service.method(
        dbus_interface=INTERFACE_NAME,
        in_signature='',
        out_signature='s'
    )
    def GetCurrentExports(self) -> str:
        """
        Get current NFS exports (read-only operation, no polkit check needed)
        
        Returns:
            String with current exports configuration
        """
        try:
            exports = ExportsConfigParser.leer_exports()
            return '\n'.join(exports)
        except Exception as e:
            LOG.error(f"Error reading exports: {e}")
            return f"Error: {str(e)}"


def main():
    """Main entry point for the D-Bus service"""
    
    # Check if running as root
    if os.geteuid() != 0:
        print("ERROR: This D-Bus service must run as root", file=sys.stderr)
        print("It should be started via systemd with appropriate permissions", file=sys.stderr)
        sys.exit(1)
    
    LOG.info("Starting NFS Helper D-Bus service...")
    
    # Initialize D-Bus main loop
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    
    try:
        # Connect to system bus
        system_bus = dbus.SystemBus()
        
        # Request the service name
        bus_name = dbus.service.BusName(SERVICE_NAME, bus=system_bus)
        
        # Create the service object
        service = NFSHelperService(system_bus, OBJECT_PATH)
        
        LOG.info(f"Service {SERVICE_NAME} is ready")
        LOG.info(f"Listening on {OBJECT_PATH}")
        
        # Run the main loop
        mainloop = GLib.MainLoop()
        mainloop.run()
        
    except KeyboardInterrupt:
        LOG.info("Service interrupted by user")
        sys.exit(0)
    except Exception as e:
        LOG.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
