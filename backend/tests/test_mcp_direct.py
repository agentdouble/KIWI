#!/usr/bin/env python3
"""Direct test of MCP communication"""

import asyncio
import json
import sys
from pathlib import Path

# Add backend path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from app.services.mcp_client import PowerPointMCPClient

async def test_mcp_direct():
    """Test MCP client-server communication directly."""
    print("🔧 Testing direct MCP communication...")
    
    client = PowerPointMCPClient()
    
    try:
        # Connect
        print("1. Connecting to MCP server...")
        connected = await client.connect()
        print(f"   Connection: {'✅ Success' if connected else '❌ Failed'}")
        
        if not connected:
            return False
        
        # Test raw message sending
        print("2. Testing raw tools/list request...")
        
        # Send list tools request manually
        request = {
            "jsonrpc": "2.0",
            "id": 123,
            "method": "tools/list"
        }
        
        await client._send_message(request)
        response = await client._read_message()
        
        print(f"   Response: {json.dumps(response, indent=2)}")
        
        # Test with params
        print("3. Testing tools/list with empty params...")
        
        request_with_params = {
            "jsonrpc": "2.0", 
            "id": 124,
            "method": "tools/list",
            "params": {}
        }
        
        await client._send_message(request_with_params)
        response2 = await client._read_message()
        
        print(f"   Response: {json.dumps(response2, indent=2)}")
        
        # Test high-level method
        print("4. Testing high-level list_tools method...")
        tools = await client.list_tools()
        print(f"   Tools: {tools}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(test_mcp_direct())