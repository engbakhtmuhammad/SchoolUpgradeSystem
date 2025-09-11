#!/usr/bin/env python3
"""
Network-enabled Flask server for School Upgrade System
Ensures the server is accessible from mobile devices
"""

import os
import sys
import socket
from app import app

def get_local_ip():
    """Get the local IP address"""
    try:
        # Create a socket to get the local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "Unable to determine"

def main():
    """Run the Flask application with network access"""
    # Force network binding
    host = '0.0.0.0'  # This is crucial for network access
    port = 5010
    
    # Get the actual IP address
    local_ip = get_local_ip()
    
    print("=" * 60)
    print("🏫 BALOCHISTAN SCHOOL UPGRADE SYSTEM")
    print("=" * 60)
    print(f"🖥️  Server Host: {host} (All interfaces)")
    print(f"🔌 Server Port: {port}")
    print(f"📍 Local IP: {local_ip}")
    print("")
    print("📱 ACCESS URLS:")
    print(f"   Local:   http://127.0.0.1:{port}")
    print(f"   Network: http://{local_ip}:{port}")
    print("")
    print("📲 For mobile devices, use: http://{local_ip}:{port}")
    print("🌐 Make sure both devices are on the same WiFi network")
    print("")
    print("🛑 Press Ctrl+C to stop the server")
    print("=" * 60)
    
    try:
        # Start the Flask app with network access
        app.run(
            host=host,      # 0.0.0.0 allows access from any IP
            port=port,
            debug=True,
            threaded=True,
            use_reloader=False  # Disable reloader to prevent issues
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"\n❌ Port {port} is already in use!")
            print("Try running: lsof -i :5010 to see what's using it")
            print("Or use: kill -9 <PID> to stop it")
        else:
            print(f"\n❌ Error starting server: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
