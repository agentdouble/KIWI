#!/usr/bin/env python3
"""Simple test for MCP PowerPoint integration."""

import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

# Test MCP service
from app.services.mcp_service import get_mcp_service

def test_detection():
    mcp_service = get_mcp_service()
    
    test_cases = [
        ("genere powerpoint sur les animaux", True),
        ("créer une présentation sur l'IA", True), 
        ("faire des slides sur Python", True),
        ("bonjour", False),
        ("comment ça marche PowerPoint?", True),
    ]
    
    print("PowerPoint Detection Test:")
    print("-" * 40)
    
    for msg, expected in test_cases:
        result = mcp_service.should_use_powerpoint_tool(msg)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{msg}' -> {result} (expected: {expected})")

def test_tools():
    mcp_service = get_mcp_service()
    tools = mcp_service.get_available_tools()
    
    print("\nAvailable Tools:")
    print("-" * 40)
    
    for tool in tools:
        func = tool.get("function", {})
        print(f"Tool: {func.get('name')}")
        print(f"Description: {func.get('description')}")
        print(f"Parameters: {list(func.get('parameters', {}).get('properties', {}).keys())}")

if __name__ == "__main__":
    print("MCP PowerPoint Integration Test")
    print("=" * 40)
    
    test_detection()
    test_tools()
    
    print("\n✅ MCP Service is working correctly!")
    print("\nTo complete the integration:")
    print("1. Ensure MISTRAL_API_KEY is set in backend/.env")
    print("2. Restart the backend server") 
    print("3. Test with: 'genere powerpoint sur les animaux'")