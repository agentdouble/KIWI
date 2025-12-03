#!/usr/bin/env python3
"""Test OpenAI with MCP tools."""

import asyncio
import os
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

# Set API key from environment
if not os.environ.get("OPENAI_API_KEY"):
    print("❌ Please set OPENAI_API_KEY environment variable")
    sys.exit(1)

async def test_openai_with_tools():
    """Test OpenAI API with PowerPoint tools."""
    from app.services.openai_service import OpenAIService
    from app.services.mcp_service import get_mcp_service
    
    print("=" * 60)
    print("Testing OpenAI with MCP Tools")
    print("=" * 60)
    
    # Initialize services
    service = OpenAIService()
    mcp = get_mcp_service()
    
    # Get available tools
    tools = mcp.get_available_tools()
    print(f"\n✅ MCP Service provides {len(tools)} tool(s)")
    print(f"Tool: {tools[0]['function']['name']}")
    
    # Test messages
    test_cases = [
        "Bonjour, comment vas-tu?",
        "Génère un PowerPoint sur les chats",
        "Peux-tu créer une présentation sur l'intelligence artificielle?",
        "Fais moi des slides sur Python"
    ]
    
    for i, user_message in enumerate(test_cases, 1):
        print(f"\n--- Test {i} ---")
        print(f"User: {user_message}")
        
        messages = [
            {
                "role": "system", 
                "content": "Tu es un assistant utile. Tu as accès à des outils pour générer des présentations PowerPoint. Si l'utilisateur demande de créer une présentation, utilise l'outil generate_powerpoint_from_text."
            },
            {
                "role": "user",
                "content": user_message
            }
        ]
        
        try:
            # Call OpenAI with tools
            response, metadata = await service.generate_response_with_metadata(messages, tools)
            
            print(f"OpenAI used tools: {metadata.get('tools_used', False)}")
            if metadata.get('tool_calls'):
                print(f"Tool calls: {metadata['tool_calls']}")
            
            print(f"Response preview: {response[:200]}...")
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("Test completed!")

if __name__ == "__main__":
    asyncio.run(test_openai_with_tools())
