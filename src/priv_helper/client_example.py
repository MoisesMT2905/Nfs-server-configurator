#!/usr/bin/env python3
"""
Example client for testing the NFS D-Bus helper service.
This demonstrates how to call the privileged helper from user space.
"""

import sys
import dbus

BUS_NAME = "org.yast2.NFSHelper"
OBJECT_PATH = "/org/yast2/NFSHelper"
INTERFACE_NAME = "org.yast2.NFSHelper"


def apply_configuration(exports_text):
    """
    Call the D-Bus helper to apply NFS configuration.
    
    Args:
        exports_text: The exports configuration text
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        # Connect to system bus
        bus = dbus.SystemBus()
        
        # Get the service object
        obj = bus.get_object(BUS_NAME, OBJECT_PATH)
        
        # Get the interface
        interface = dbus.Interface(obj, INTERFACE_NAME)
        
        # Call the method
        success, message = interface.ApplyConfiguration(exports_text)
        
        return bool(success), str(message)
        
    except dbus.exceptions.DBusException as e:
        return False, f"D-Bus error: {e}"
    except Exception as e:
        return False, f"Error: {e}"


def main():
    """Main entry point for testing."""
    if len(sys.argv) < 2:
        print("Usage: python3 client_example.py '<exports_text>'")
        print("\nExample:")
        print("  python3 client_example.py '/shared/data 192.168.1.0/24(rw,sync,no_root_squash)'")
        sys.exit(1)
    
    exports_text = sys.argv[1]
    
    print(f"Attempting to apply configuration:")
    print(f"  {exports_text}")
    print()
    
    success, message = apply_configuration(exports_text)
    
    if success:
        print("✓ Success!")
        print(f"  {message}")
        sys.exit(0)
    else:
        print("✗ Failed!")
        print(f"  {message}")
        sys.exit(1)


if __name__ == "__main__":
    main()
