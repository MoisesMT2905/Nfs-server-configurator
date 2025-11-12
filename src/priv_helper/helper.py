#!/usr/bin/env python3
"""
D-Bus service for privileged NFS configuration operations.
This helper runs on the system bus and uses polkit for authorization.
"""

import sys
import os
import subprocess
import logging
from typing import Tuple

import dbus
import dbus.service
import dbus.mainloop.glib
from gi.repository import GLib

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.backend.nfs_manager import NFSManager

# Configure logging
logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger("nfs-helper")

BUS_NAME = "org.yast2.NFSHelper"
OBJECT_PATH = "/org/yast2/NFSHelper"
INTERFACE_NAME = "org.yast2.NFSHelper"


class NFSHelperService(dbus.service.Object):
    """D-Bus service for NFS configuration operations."""
    
    def __init__(self, bus, object_path):
        super().__init__(bus, object_path)
        LOG.info(f"NFSHelperService initialized at {object_path}")
    
    def _check_authorization(self, sender):
        """Check if the sender is authorized using polkit."""
        try:
            # Use pkcheck to verify authorization
            result = subprocess.run(
                [
                    'pkcheck',
                    '--action-id', 'org.yast2.nfshelper.configure',
                    '--process', str(os.getpid()),
                    '--allow-user-interaction'
                ],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                LOG.info(f"Authorization granted for sender: {sender}")
                return True
            else:
                LOG.warning(f"Authorization denied for sender: {sender}")
                return False
        except subprocess.TimeoutExpired:
            LOG.error("pkcheck timeout")
            return False
        except Exception as e:
            LOG.error(f"Authorization check failed: {e}")
            return False
    
    @dbus.service.method(
        dbus_interface=INTERFACE_NAME,
        in_signature='s',
        out_signature='bs',
        sender_keyword='sender'
    )
    def ApplyConfiguration(self, exports_text, sender=None):
        """
        Apply NFS configuration.
        
        Args:
            exports_text: The exports configuration text
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        LOG.info(f"ApplyConfiguration called by {sender}")
        
        # Check authorization
        if not self._check_authorization(sender):
            msg = "Authorization failed. User denied or lacks permissions."
            LOG.error(msg)
            return (False, msg)
        
        try:
            # Call NFSManager to apply configuration
            success, message = NFSManager.aplicar_exportaciones(exports_text)
            
            if success:
                LOG.info(f"Configuration applied successfully: {message}")
            else:
                LOG.error(f"Configuration failed: {message}")
            
            return (success, message)
        except Exception as e:
            error_msg = f"Error applying configuration: {str(e)}"
            LOG.error(error_msg)
            return (False, error_msg)


def main():
    """Main entry point for the D-Bus service."""
    # Initialize D-Bus main loop
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    
    try:
        # Connect to system bus
        bus = dbus.SystemBus()
        
        # Request bus name
        name = dbus.service.BusName(BUS_NAME, bus)
        
        # Create service object
        service = NFSHelperService(bus, OBJECT_PATH)
        
        LOG.info(f"NFSHelper service started on {BUS_NAME}")
        LOG.info(f"Object path: {OBJECT_PATH}")
        
        # Run main loop
        loop = GLib.MainLoop()
        loop.run()
        
    except dbus.exceptions.NameExistsException:
        LOG.error(f"Service name {BUS_NAME} already exists on the bus")
        sys.exit(1)
    except Exception as e:
        LOG.error(f"Failed to start service: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
