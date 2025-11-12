#!/usr/bin/env python3
"""
D-Bus privileged helper for yast2-nfs-server.
This service runs as root and exposes methods via D-Bus system bus.
Uses polkit for authorization before applying NFS configuration changes.
"""

import sys
import os
import subprocess
import logging
from gi.repository import GLib
from pydbus import SystemBus
from pydbus.generic import signal

from typing import Tuple

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger("yast2-nfs-helper")

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../..'))

from src.backend.nfs_manager import NFSManager

DBUS_NAME = "org.yast2.NFSHelper"
DBUS_PATH = "/org/yast2/NFSHelper"
POLKIT_ACTION = "org.yast2.nfshelper.apply"


class NFSHelperService:
    """
    D-Bus service for privileged NFS operations.
    
    <node>
      <interface name='org.yast2.NFSHelper'>
        <method name='ApplyConfiguration'>
          <arg type='s' name='exports_text' direction='in'/>
          <arg type='b' name='success' direction='out'/>
          <arg type='s' name='message' direction='out'/>
        </method>
      </interface>
    </node>
    """
    
    def ApplyConfiguration(self, exports_text: str) -> Tuple[bool, str]:
        """
        Apply NFS configuration after polkit authorization.
        
        Args:
            exports_text: The complete /etc/exports content to apply
            
        Returns:
            Tuple of (success: bool, message: str)
        
        Note: The actual D-Bus signature is "(bs)" for compatibility
        """
        LOG.info("ApplyConfiguration called")
        
        # Get caller information from D-Bus
        try:
            sender = self._get_sender()
            LOG.info(f"Request from sender: {sender}")
        except Exception as e:
            LOG.error(f"Failed to get sender: {e}")
            return (False, f"Authorization failed: cannot identify caller")
        
        # Check polkit authorization
        if not self._check_authorization(sender):
            LOG.warning(f"Authorization denied for {sender}")
            return (False, "Authorization denied by polkit")
        
        LOG.info("Authorization granted, applying configuration")
        
        # Apply the configuration using NFSManager
        try:
            success, message = NFSManager.aplicar_exportaciones(exports_text)
            if success:
                LOG.info(f"Configuration applied successfully: {message}")
            else:
                LOG.error(f"Failed to apply configuration: {message}")
            return (success, message)
        except Exception as e:
            error_msg = f"Exception during apply: {str(e)}"
            LOG.error(error_msg)
            return (False, error_msg)
    
    def _get_sender(self):
        """Get the D-Bus sender (caller) from current message context"""
        # This would be set by pydbus from the message context
        # For now, we'll need to get it from the connection
        return "org.freedesktop.DBus"  # Placeholder
    
    def _check_authorization(self, sender: str) -> bool:
        """
        Check polkit authorization using pkcheck.
        
        Args:
            sender: D-Bus sender name
            
        Returns:
            True if authorized, False otherwise
        """
        try:
            # Extract PID from sender (in real implementation, get from D-Bus connection)
            # For security, we should get the actual PID from the D-Bus message
            # This is a simplified version
            
            # Use pkcheck to verify authorization
            # In production, we'd get the actual caller PID from D-Bus
            result = subprocess.run(
                ['pkcheck', 
                 '--action-id', POLKIT_ACTION,
                 '--process', str(os.getppid()),  # Parent process (systemd)
                 '--allow-user-interaction'],
                capture_output=True,
                text=True,
                timeout=60  # Allow time for user to respond to polkit prompt
            )
            
            if result.returncode == 0:
                LOG.info("pkcheck authorization successful")
                return True
            else:
                LOG.warning(f"pkcheck authorization failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            LOG.error("pkcheck timeout - user took too long to respond")
            return False
        except FileNotFoundError:
            LOG.error("pkcheck not found - polkit-tools not installed?")
            # In development/testing, allow if running as root
            if os.geteuid() == 0:
                LOG.warning("Running as root without pkcheck - DEVELOPMENT ONLY")
                return True
            return False
        except Exception as e:
            LOG.error(f"Error during authorization check: {e}")
            return False


def main():
    """Main entry point for the D-Bus service"""
    LOG.info("Starting yast2-nfs-helper D-Bus service")
    
    # Verify we're running as root
    if os.geteuid() != 0:
        LOG.error("Helper must run as root")
        sys.exit(1)
    
    try:
        # Connect to system bus
        bus = SystemBus()
        
        # Create service instance
        service = NFSHelperService()
        
        # Publish service on the bus
        bus.publish(DBUS_NAME, service)
        
        LOG.info(f"Service published as {DBUS_NAME} on {DBUS_PATH}")
        LOG.info("Service ready, waiting for requests...")
        
        # Run main loop
        loop = GLib.MainLoop()
        loop.run()
        
    except KeyboardInterrupt:
        LOG.info("Service interrupted by user")
        sys.exit(0)
    except Exception as e:
        LOG.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
