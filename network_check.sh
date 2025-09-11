#!/bin/bash

echo "🔍 NETWORK DIAGNOSTICS FOR MOBILE ACCESS"
echo "========================================"

# Get IP address
IP=$(ifconfig en0 | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}')
echo "📍 Mac IP Address: $IP"

# Check if server is running
echo ""
echo "🔌 Checking if server is running on port 5010..."
PROCESS=$(lsof -i :5010 2>/dev/null)
if [ -n "$PROCESS" ]; then
    echo "✅ Server is running:"
    echo "$PROCESS"
else
    echo "❌ No server found on port 5010"
fi

# Check firewall
echo ""
echo "🔥 Checking firewall status..."
FIREWALL=$(/usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate)
echo "$FIREWALL"

# Test self-connectivity
echo ""
echo "🧪 Testing self-connectivity..."
curl -s -w "%{http_code}" "http://$IP:5010/health" -o /dev/null
if [ $? -eq 0 ]; then
    echo "✅ Can connect to own server"
else
    echo "❌ Cannot connect to own server"
fi

echo ""
echo "📱 MOBILE ACCESS INSTRUCTIONS:"
echo "   1. Ensure mobile is on same WiFi network"
echo "   2. Use URL: http://$IP:5010"
echo "   3. Try health check: http://$IP:5010/health"
echo ""
echo "🔧 If still not working:"
echo "   - Try port 8080: python mobile_server_8080.py"
echo "   - Check router settings for device isolation"
echo "   - Try disabling any VPN on mobile device"
