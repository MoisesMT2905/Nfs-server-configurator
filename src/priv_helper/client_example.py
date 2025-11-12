#!/usr/bin/env python3
"""
Example client for testing the NFS Helper D-Bus service

This script demonstrates how to call the privileged D-Bus service
from a non-root user application.
"""

import sys
import dbus

SERVICE_NAME = "org.yast2.NFSHelper"
OBJECT_PATH = "/org/yast2/NFSHelper"
INTERFACE_NAME = "org.yast2.NFSHelper"


def test_apply_configuration():
    """Test applying a simple NFS configuration"""
    
    # Example export configuration
    test_config = "/srv/nfs/share 192.168.1.0/24(rw,sync,no_subtree_check)"
    
    print(f"Testing ApplyConfiguration with:")
    print(f"  {test_config}")
    print()
    
    try:
        # Connect to system bus
        bus = dbus.SystemBus()
        
        # Get the service object
        proxy = bus.get_object(SERVICE_NAME, OBJECT_PATH)
        interface = dbus.Interface(proxy, INTERFACE_NAME)
        
        # Call ApplyConfiguration
        print("Calling D-Bus method (polkit authentication may prompt)...")
        result = interface.ApplyConfiguration(test_config)
        
        # Display result
        print("\nResult:")
        print(f"  Success: {result['success']}")
        print(f"  Message: {result['message']}")
        
        return result['success']
        
    except dbus.exceptions.DBusException as e:
        print(f"\nD-Bus Error: {e}", file=sys.stderr)
        if "org.freedesktop.DBus.Error.ServiceUnknown" in str(e):
            print("\nThe D-Bus service is not running.", file=sys.stderr)
            print("Make sure the service is installed and started:", file=sys.stderr)
            print("  sudo systemctl start yast2-nfs-helper.service", file=sys.stderr)
        return False
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        return False


def test_get_exports():
    """Test reading current exports (no authentication required)"""
    
    print("Testing GetCurrentExports...")
    print()
    
    try:
        # Connect to system bus
        bus = dbus.SystemBus()
        
        # Get the service object
        proxy = bus.get_object(SERVICE_NAME, OBJECT_PATH)
        interface = dbus.Interface(proxy, INTERFACE_NAME)
        
        # Call GetCurrentExports
        exports = interface.GetCurrentExports()
        
        print("Current exports:")
        if exports:
            print(exports)
        else:
            print("  (none)")
        
        return True
        
    except dbus.exceptions.DBusException as e:
        print(f"\nD-Bus Error: {e}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        return False


def main():
    """Main entry point"""
    
    print("=" * 60)
    print("NFS Helper D-Bus Service - Test Client")
    print("=" * 60)
    print()
    
    # Test 1: Get current exports
    print("TEST 1: Get Current Exports")
    print("-" * 60)
    test_get_exports()
    print()
    
    # Test 2: Apply configuration (requires polkit authentication)
    print("TEST 2: Apply Configuration")
    print("-" * 60)
    print("NOTE: This will prompt for authentication via polkit")
    print()
    
    response = input("Continue with apply test? (y/N): ")
    if response.lower() == 'y':
        test_apply_configuration()
    else:
        print("Skipped apply test")
    
    print()
    print("=" * 60)
    print("Tests completed")
    print("=" * 60)


if __name__ == '__main__':
    main()
