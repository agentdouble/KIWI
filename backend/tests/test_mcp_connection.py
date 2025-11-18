#!/usr/bin/env python3
"""Test MCP connection."""

import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

async def test_mcp_connection():
    """Test MCP client connection."""
    print("Testing MCP connection...")
    
    try:
        from app.services.mcp_client import get_powerpoint_mcp_client
        
        client = await get_powerpoint_mcp_client()
        print("✅ MCP client connected successfully")
        
        tools = await client.list_tools()
        print(f"✅ Retrieved {len(tools)} tools")
        
        for tool in tools:
            print(f"  - {tool['function']['name']}: {tool['function']['description']}")
            
        return True
        
    except Exception as e:
        print(f"❌ MCP connection failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_message_service():
    """Test message service with MCP tools."""
    print("\nTesting message service MCP integration...")
    
    try:
        from app.services.mcp_service import get_mcp_service
        
        mcp_service = get_mcp_service()
        tools = await mcp_service.get_available_tools()
        
        print(f"✅ Message service can access {len(tools)} MCP tools")
        return True
        
    except Exception as e:
        print(f"❌ Message service MCP failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    async def main():
        print("=" * 50)
        print("MCP Connection Test")
        print("=" * 50)
        
        connection_ok = await test_mcp_connection()
        service_ok = await test_message_service()
        
        if connection_ok and service_ok:
            print("\n✅ All MCP tests passed!")
            print("The backend should now be able to use MCP tools.")
        else:
            print("\n❌ Some MCP tests failed.")
            print("Check the errors above and fix the MCP setup.")
    
    asyncio.run(main())