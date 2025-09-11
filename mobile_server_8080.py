#!/usr/bin/env python3
"""
Alternative port server for mobile access
"""

from app import app
import socket

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "192.168.1.192"

if __name__ == '__main__':
    local_ip = get_local_ip()
    port = 8080  # Different port
    
    print("=" * 50)
    print("🏫 SCHOOL UPGRADE SYSTEM (Alternative Port)")
    print("=" * 50)
    print(f"📱 Mobile URL: http://{local_ip}:{port}")
    print(f"🖥️  Desktop URL: http://127.0.0.1:{port}")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=port, debug=True)
