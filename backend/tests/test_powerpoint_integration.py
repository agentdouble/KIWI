#!/usr/bin/env python3
"""Test script for PowerPoint MCP integration."""

import asyncio
import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

# Set up environment
os.environ["OPENAI_API_KEY"] = os.environ.get("OPENAI_API_KEY", "")

async def test_mcp_detection():
    """Test MCP service detection of PowerPoint requests."""
    from app.services.mcp_service import get_mcp_service
    
    mcp_service = get_mcp_service()
    
    test_messages = [
        "genere powerpoint sur les animaux",
        "peux-tu créer une présentation sur l'IA?",
        "fais moi des slides sur Python",
        "bonjour comment vas-tu",  # Should not trigger
        "qu'est-ce qu'un PowerPoint?",  # Should trigger
    ]
    
    print("Testing PowerPoint detection:")
    print("-" * 40)
    
    for msg in test_messages:
        should_use = mcp_service.should_use_powerpoint_tool(msg)
        print(f"Message: '{msg}'")
        print(f"Should use PowerPoint tool: {should_use}")
        print()

async def test_tool_definition():
    """Test MCP tool definition."""
    from app.services.mcp_service import get_mcp_service
    
    mcp_service = get_mcp_service()
    tools = mcp_service.get_available_tools()
    
    print("Available MCP Tools:")
    print("-" * 40)
    
    import json
    print(json.dumps(tools, indent=2, ensure_ascii=False))

async def test_openai_with_tools():
    """Test OpenAI service with tools."""
    from app.services.openai_service import OpenAIService
    from app.services.mcp_service import get_mcp_service
    
    if not os.environ.get("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY not set. Skipping OpenAI test.")
        return
    
    service = OpenAIService()
    mcp_service = get_mcp_service()
    
    messages = [
        {"role": "user", "content": "génère un powerpoint sur les chats"}
    ]
    
    tools = mcp_service.get_available_tools()
    
    print("Testing OpenAI with PowerPoint tool:")
    print("-" * 40)
    print(f"User message: {messages[0]['content']}")
    print("Calling OpenAI with tools...")
    
    try:
        response = await service.generate_response(messages, tools)
        print(f"Response: {response}")
    except Exception as e:
        print(f"Error: {e}")

async def test_message_service():
    """Test message service with PowerPoint detection."""
    # Set up test database
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    
    # Create in-memory database for testing
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    AsyncSessionLocal = sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with AsyncSessionLocal() as session:
        from app.services.message_service import MessageService
        
        service = MessageService(session)
        
        messages = [
            {"role": "user", "content": "génère une présentation sur l'intelligence artificielle"}
        ]
        
        print("Testing Message Service with PowerPoint request:")
        print("-" * 40)
        print(f"User message: {messages[0]['content']}")
        
        try:
            # This would normally query the database, but we'll test the logic
            from app.services.mcp_service import get_mcp_service
            mcp_service = get_mcp_service()
            
            user_message = messages[-1].get("content", "")
            
            if mcp_service.should_use_powerpoint_tool(user_message):
                tools = mcp_service.get_available_tools()
                print(f"✅ PowerPoint tool detected and will be provided to Mistral")
                print(f"Tools: {len(tools)} tool(s) available")
            else:
                print("❌ PowerPoint tool not detected")
                
        except Exception as e:
            print(f"Error: {e}")

async def main():
    """Run all tests."""
    print("=" * 50)
    print("PowerPoint MCP Integration Test Suite")
    print("=" * 50)
    print()
    
    await test_mcp_detection()
    print()
    
    await test_tool_definition()
    print()
    
    await test_openai_with_tools()
    print()
    
    await test_message_service()
    
    print()
    print("=" * 50)
    print("Tests completed!")

if __name__ == "__main__":
    asyncio.run(main())
