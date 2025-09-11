#!/usr/bin/env python3
"""
Production server runner for School Upgrade System
Run with: python run_server.py
"""

import os
import sys
from app import app

def main():
    """Run the Flask application in production mode"""
    # Get host and port from environment variables or use defaults
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5010))
    
    print(f"🚀 Starting School Upgrade System")
    print(f"📍 Local access: http://127.0.0.1:{port}")
    print(f"🌐 Network access: http://192.168.1.192:{port}")
    print(f"📱 Mobile/Tablet: Same URL works on all devices")
    print(f"🛑 Press Ctrl+C to stop the server")
    print("-" * 50)
    
    try:
        app.run(
            host=host,
            port=port,
            debug=False,  # Set to False for production
            threaded=True  # Handle multiple requests simultaneously
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
