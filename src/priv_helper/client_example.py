#!/usr/bin/env python3
"""
Example client for testing the NFS Helper D-Bus service.
Usage: python3 client_example.py [command] [args...]
"""
import sys
from pydbus import SystemBus


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: client_example.py <command> [args...]")
        print("\nCommands:")
        print("  list                     - List current exports")
        print("  backup                   - Create backup of /etc/exports")
        print("  apply <exports_text>     - Apply new configuration")
        print("\nExample:")
        print("  python3 client_example.py list")
        print("  python3 client_example.py apply '/shared 192.168.1.0/24(rw,sync)'")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    try:
        # Connect to system bus
        bus = SystemBus()
        
        # Get the NFS Helper service
        helper = bus.get("org.yast2.NFSHelper", "/org/yast2/NFSHelper")
        
        if command == "list":
            print("Current NFS Exports:")
            print("-" * 50)
            exports = helper.ListExports()
            print(exports)
            
        elif command == "backup":
            print("Creating backup...")
            backup_file = helper.BackupExports()
            print(f"Backup created: {backup_file}")
            
        elif command == "apply":
            if len(sys.argv) < 3:
                print("Error: 'apply' requires exports text as argument")
                sys.exit(1)
            
            exports_text = sys.argv[2]
            print(f"Applying configuration:")
            print(exports_text)
            print("-" * 50)
            
            success, message = helper.ApplyConfiguration(exports_text)
            
            if success:
                print(f"✓ Success: {message}")
                sys.exit(0)
            else:
                print(f"✗ Failed: {message}")
                sys.exit(1)
        else:
            print(f"Unknown command: {command}")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error: {str(e)}")
        print("\nMake sure:")
        print("  1. The helper service is running")
        print("  2. D-Bus is configured properly")
        print("  3. You have proper permissions")
        sys.exit(1)


if __name__ == "__main__":
    main()
