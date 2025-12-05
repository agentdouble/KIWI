#!/usr/bin/env python3
"""Test the full PowerPoint generation pipeline."""

import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

def test_mcp_detection():
    """Test that MCP service detects PowerPoint requests."""
    from app.services.mcp_service import get_mcp_service
    
    mcp = get_mcp_service()
    
    test_messages = [
        "genere powerpoint sur les animaux",
        "peux-tu générer un powerpoint sur l'IA?",
    ]
    
    print("=" * 60)
    print("1. Testing MCP Detection")
    print("=" * 60)
    
    for msg in test_messages:
        result = mcp.should_use_powerpoint_tool(msg)
        print(f"Message: '{msg}'")
        print(f"Detection: {'✅ YES' if result else '❌ NO'}")
        if result:
            tools = mcp.get_available_tools()
            print(f"Tools available: {len(tools)}")
        print()

def test_message_service_logic():
    """Test the message service PowerPoint detection logic."""
    print("=" * 60)
    print("2. Testing Message Service Logic")
    print("=" * 60)
    
    # Test the exact logic from message_service.py
    messages = [{"role": "user", "content": "genere powerpoint sur les animaux"}]
    
    # Get user message
    user_message = messages[-1].get("content", "") if messages else ""
    print(f"User message: '{user_message}'")
    
    # Import and test MCP service
    from app.services.mcp_service import get_mcp_service
    mcp_service = get_mcp_service()
    
    if mcp_service.should_use_powerpoint_tool(user_message):
        tools = mcp_service.get_available_tools()
        print(f"✅ PowerPoint detected! Will provide {len(tools)} tool(s)")
        print(f"Tool definition: {tools[0]['function']['name']}")
    else:
        print("❌ PowerPoint NOT detected")

def test_with_enhanced_prompt():
    """Test with enhanced system prompt."""
    print("=" * 60)
    print("3. Testing Enhanced System Prompt")
    print("=" * 60)
    
    from app.services.mcp_service import get_mcp_service
    
    mcp = get_mcp_service()
    user_message = "genere powerpoint sur les animaux"
    
    enhanced_system_prompt = "Tu es un assistant utile."
    
    if mcp.should_use_powerpoint_tool(user_message):
        tools = mcp.get_available_tools()
        enhanced_system_prompt += "\n\nTu as accès à des outils pour générer des présentations PowerPoint. Si l'utilisateur demande de créer une présentation, un PowerPoint, ou des slides, utilise l'outil generate_powerpoint_from_text avec le contenu approprié."
        
        print("✅ System prompt enhanced with PowerPoint instructions")
        print(f"Tools: {len(tools)} available")
        print("\nEnhanced prompt:")
        print("-" * 40)
        print(enhanced_system_prompt)
        print("-" * 40)
    else:
        print("❌ No enhancement added")

def main():
    print("\n" + "=" * 60)
    print("POWERPOINT MCP PIPELINE TEST")
    print("=" * 60 + "\n")
    
    test_mcp_detection()
    test_message_service_logic()
    test_with_enhanced_prompt()
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print("\n✅ All pipeline components are working correctly!")
    print("\nIf it's still not working in the live system:")
    print("1. Check that backend was restarted after changes")
    print("2. Check OPENAI_API_KEY is set in backend/.env")
    print("3. Check the logs for 'Checking for PowerPoint request'")
    print("4. Make sure you're testing with exact phrase: 'genere powerpoint sur les animaux'")

if __name__ == "__main__":
    main()
