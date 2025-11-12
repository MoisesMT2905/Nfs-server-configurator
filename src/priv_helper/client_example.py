#!/usr/bin/env python3
"""
Example client for testing the yast2-nfs-helper D-Bus service.
This demonstrates how to call the helper from a non-root user.
"""

import sys
from pydbus import SystemBus
from gi.repository import GLib

DBUS_NAME = "org.yast2.NFSHelper"
DBUS_PATH = "/org/yast2/NFSHelper"


def test_apply_configuration():
    """Test applying NFS configuration via D-Bus helper"""
    
    # Sample export configuration
    test_config = """/tmp/test_export 192.168.1.0/24(rw,sync,no_subtree_check)
/tmp/another 10.0.0.5(ro,root_squash)"""
    
    print("Testing yast2-nfs-helper D-Bus service")
    print("=" * 60)
    print(f"Configuration to apply:\n{test_config}")
    print("=" * 60)
    
    try:
        # Connect to system bus
        bus = SystemBus()
        
        # Get the helper service
        print(f"Connecting to {DBUS_NAME}...")
        helper = bus.get(DBUS_NAME, DBUS_PATH)
        
        # Call ApplyConfiguration method
        print("Calling ApplyConfiguration (polkit may prompt for password)...")
        success, message = helper.ApplyConfiguration(test_config)
        
        # Display results
        print("\nResult:")
        print(f"  Success: {success}")
        print(f"  Message: {message}")
        
        if success:
            print("\n✓ Configuration applied successfully!")
            return 0
        else:
            print("\n✗ Failed to apply configuration")
            return 1
            
    except GLib.Error as e:
        print(f"\n✗ D-Bus error: {e}")
        print("\nPossible causes:")
        print("  - yast2-nfs-helper service not running")
        print("  - Service not enabled: sudo systemctl enable --now yast2-nfs-helper")
        return 2
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        return 3


def check_service_status():
    """Check if the helper service is available"""
    try:
        bus = SystemBus()
        helper = bus.get(DBUS_NAME, DBUS_PATH)
        print(f"✓ Service {DBUS_NAME} is available")
        return True
    except Exception as e:
        print(f"✗ Service {DBUS_NAME} is not available: {e}")
        print("\nTo start the service:")
        print(f"  sudo systemctl start yast2-nfs-helper")
        return False


if __name__ == "__main__":
    print("YaST2 NFS Helper - Client Example")
    print()
    
    # First check if service is available
    if not check_service_status():
        print("\nPlease start the service first.")
        sys.exit(1)
    
    print()
    
    # Test the configuration
    sys.exit(test_apply_configuration())
