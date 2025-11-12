#!/usr/bin/env python3
"""
D-Bus service for privileged NFS configuration operations.
Uses polkit for authorization checking.
"""
import sys
import os
import subprocess
import logging
from gi.repository import GLib
from pydbus import SystemBus
from pydbus.generic import signal

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.backend.nfs_manager import NFSManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
LOG = logging.getLogger("nfs-helper")

class NFSHelperService:
    """
    D-Bus service that exposes privileged NFS operations.
    Interface: org.yast2.NFSHelper
    Object Path: /org/yast2/NFSHelper
    """
    
    dbus = """
    <node>
        <interface name='org.yast2.NFSHelper'>
            <method name='ApplyConfiguration'>
                <arg type='s' name='exports_text' direction='in'/>
                <arg type='b' name='success' direction='out'/>
                <arg type='s' name='message' direction='out'/>
            </method>
            <method name='ListExports'>
                <arg type='s' name='exports' direction='out'/>
            </method>
            <method name='BackupExports'>
                <arg type='s' name='backup_file' direction='out'/>
            </method>
        </interface>
    </node>
    """
    
    def ApplyConfiguration(self, exports_text):
        """
        Apply NFS exports configuration.
        Requires polkit authorization: org.yast2.nfshelper.apply
        
        Args:
            exports_text: Content to write to /etc/exports
            
        Returns:
            (success: bool, message: str)
        """
        # Get caller's PID and UID for polkit check
        caller_pid = self._get_caller_pid()
        
        # Check authorization via pkcheck
        if not self._check_authorization(caller_pid):
            LOG.warning(f"Authorization denied for PID {caller_pid}")
            return False, "Authorization denied. User not authenticated."
        
        LOG.info(f"Authorization granted for PID {caller_pid}, applying configuration")
        
        # Call NFSManager to apply configuration
        try:
            result = NFSManager.apply_configuration(exports_text)
            LOG.info(f"Configuration applied: {result}")
            return result["ok"], result["msg"]
        except Exception as e:
            error_msg = f"Error applying configuration: {str(e)}"
            LOG.error(error_msg)
            return False, error_msg
    
    def ListExports(self):
        """
        List current NFS exports.
        
        Returns:
            exports: String with current exports
        """
        try:
            exports = NFSManager.list_exports()
            return exports if exports else "No exports configured"
        except Exception as e:
            LOG.error(f"Error listing exports: {str(e)}")
            return f"Error: {str(e)}"
    
    def BackupExports(self):
        """
        Create backup of /etc/exports.
        
        Returns:
            backup_file: Path to backup file
        """
        try:
            backup_file = NFSManager.backup_exports()
            return backup_file if backup_file else "No backup created"
        except Exception as e:
            LOG.error(f"Error creating backup: {str(e)}")
            return f"Error: {str(e)}"
    
    def _get_caller_pid(self):
        """Get the PID of the D-Bus caller"""
        # In a real implementation, this would use D-Bus GetConnectionUnixProcessID
        # For now, we'll use a placeholder that works with pkcheck
        try:
            # Get sender from D-Bus context
            sender = self._connection.get_unique_name()
            # Query D-Bus for the PID
            bus = SystemBus()
            dbus_obj = bus.get("org.freedesktop.DBus", "/org/freedesktop/DBus")
            pid = dbus_obj.GetConnectionUnixProcessID(sender)
            return pid
        except Exception as e:
            LOG.warning(f"Could not get caller PID: {e}")
            # Fallback: return a value that will require authentication
            return 0
    
    def _check_authorization(self, caller_pid):
        """
        Check if caller is authorized using polkit (pkcheck).
        
        Args:
            caller_pid: Process ID of the caller
            
        Returns:
            bool: True if authorized, False otherwise
        """
        try:
            # Use pkcheck to verify authorization
            # Action ID: org.yast2.nfshelper.apply
            result = subprocess.run(
                [
                    'pkcheck',
                    '--action-id', 'org.yast2.nfshelper.apply',
                    '--process', str(caller_pid),
                    '--allow-user-interaction'
                ],
                capture_output=True,
                text=True,
                timeout=60  # Allow time for user interaction
            )
            
            # pkcheck returns 0 if authorized
            authorized = result.returncode == 0
            
            if authorized:
                LOG.info(f"Polkit authorization granted for PID {caller_pid}")
            else:
                LOG.warning(f"Polkit authorization denied for PID {caller_pid}: {result.stderr}")
            
            return authorized
            
        except subprocess.TimeoutExpired:
            LOG.error("Polkit check timed out")
            return False
        except FileNotFoundError:
            LOG.error("pkcheck not found. Install polkit-tools package.")
            return False
        except Exception as e:
            LOG.error(f"Error checking authorization: {str(e)}")
            return False


def main():
    """Main entry point for the D-Bus service"""
    LOG.info("Starting NFS Helper D-Bus service...")
    
    # Check if running as root
    if os.geteuid() != 0:
        LOG.error("Helper must run as root")
        sys.exit(1)
    
    try:
        # Connect to system bus
        bus = SystemBus()
        
        # Create service instance
        service = NFSHelperService()
        
        # Store bus connection for PID lookup
        service._connection = bus.con
        
        # Publish service on the bus
        bus.publish("org.yast2.NFSHelper", service)
        
        LOG.info("Service published on D-Bus as org.yast2.NFSHelper")
        LOG.info("Waiting for requests...")
        
        # Run main loop
        loop = GLib.MainLoop()
        loop.run()
        
    except KeyboardInterrupt:
        LOG.info("Service interrupted by user")
    except Exception as e:
        LOG.error(f"Fatal error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
