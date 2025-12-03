#!/usr/bin/env python3
"""
Test script for MCP PowerPoint integration.
This script tests the complete pipeline without requiring the full web server.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the backend path to import our services
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

async def test_mcp_service():
    """Test the MCP service directly."""
    print("🧪 Testing MCP Service...")
    
    try:
        from app.services.mcp_service import get_mcp_service
        
        mcp_service = get_mcp_service()
        
        # Test keyword detection
        test_messages = [
            "peux-tu générer un powerpoint sur l'intelligence artificielle?",
            "hello world",
            "crée une présentation sur les meilleures pratiques",
            "what is machine learning?"
        ]
        
        print("\n📝 Testing keyword detection:")
        for msg in test_messages:
            should_use = mcp_service.should_use_powerpoint_tool(msg)
            print(f"  '{msg[:50]}...' -> {'✅ PowerPoint' if should_use else '❌ Regular'}")
        
        # Test tool availability
        tools = await mcp_service.get_available_tools()
        print(f"\n🛠️ Available tools: {len(tools)}")
        for tool in tools:
            print(f"  - {tool['function']['name']}: {tool['function']['description'][:60]}...")
        
        print("\n✅ MCP Service tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ MCP Service test failed: {e}")
        return False

async def test_powerpoint_generation():
    """Test PowerPoint generation directly."""
    print("\n🎨 Testing PowerPoint Generation...")
    
    # Check if OPENAI_API_KEY is available
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️ OPENAI_API_KEY not set, skipping generation test")
        return False
    
    try:
        from app.services.mcp_service import get_mcp_service
        
        mcp_service = get_mcp_service()
        
        # Test with simple content
        test_content = """
        Introduction à l'Intelligence Artificielle
        
        L'intelligence artificielle (IA) transforme notre monde. Cette présentation couvre :
        
        1. Définition et histoire de l'IA
        2. Types d'apprentissage automatique
        3. Applications pratiques actuelles
        4. Défis éthiques et sociétaux
        5. Perspectives d'avenir
        
        L'IA comprend l'apprentissage automatique, le deep learning, et le traitement du langage naturel.
        Les applications incluent les voitures autonomes, la médecine personnalisée, et les assistants virtuels.
        """
        
        print("🔄 Generating PowerPoint...")
        result = await mcp_service.execute_powerpoint_generation(
            text=test_content,
            title="Test IA Presentation",
            theme_suggestion="professional"
        )
        
        if result.get("success"):
            presentation = result.get("presentation", {})
            print(f"✅ Generation successful!")
            print(f"   Title: {presentation.get('title')}")
            print(f"   Slides: {presentation.get('total_slides')}")
            print(f"   Theme: {presentation.get('theme')}")
            
            # Check if files were created
            if "pptx_file" in result:
                pptx_info = result["pptx_file"]
                pptx_path = Path(pptx_info["path"])
                if pptx_path.exists():
                    print(f"   PPTX File: {pptx_path} ({pptx_info['size_mb']} MB)")
                else:
                    print(f"   ❌ PPTX File not found at {pptx_path}")
            
            return True
        else:
            print(f"❌ Generation failed: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ PowerPoint generation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_openai_integration():
    """Test OpenAI service with tools."""
    print("\n🤖 Testing OpenAI Service Integration...")
    
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️ OPENAI_API_KEY not set, skipping OpenAI test")
        return False
    
    try:
        from app.services.openai_service import OpenAIService
        from app.services.mcp_service import get_mcp_service
        
        openai_service = OpenAIService()
        mcp_service = get_mcp_service()
        
        messages = [
            {"role": "user", "content": "peux-tu générer un powerpoint sur les énergies renouvelables?"}
        ]
        
        tools = await mcp_service.get_available_tools()
        
        print("🔄 Testing OpenAI with tools...")
        response = await openai_service.generate_response(messages, tools)
        
        print(f"✅ OpenAI response received ({len(response)} chars)")
        print(f"   Response preview: {response[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ OpenAI integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests."""
    print("🚀 Starting MCP PowerPoint Integration Tests")
    print("=" * 60)
    
    # Check prerequisites
    print("🔍 Checking prerequisites...")
    
    # Check if MCP dependencies are available
    try:
        import openai  # noqa: F401
        print("  ✅ OpenAI library available")
    except ImportError:
        print("  ❌ OpenAI library not found")
        return 1
    
    # Check OPENAI_API_KEY
    if os.getenv("OPENAI_API_KEY"):
        print("  ✅ OPENAI_API_KEY configured")
    else:
        print("  ⚠️ OPENAI_API_KEY not set (some tests will be skipped)")
    
    # Run tests
    results = []
    
    # Test 1: MCP Service
    results.append(await test_mcp_service())
    
    # Test 2: PowerPoint Generation (only if API key is available)
    if os.getenv("OPENAI_API_KEY"):
        results.append(await test_powerpoint_generation())
    
    # Test 3: OpenAI Integration (only if API key is available)  
    if os.getenv("OPENAI_API_KEY"):
        results.append(await test_openai_integration())
    
    # Summary
    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"🎉 All tests passed! ({passed}/{total})")
        print("\n✅ MCP PowerPoint integration is ready!")
        print("\n📋 Next steps:")
        print("  1. Start the backend server")
        print("  2. Try asking: 'peux-tu générer un powerpoint sur l'IA?'")
        print("  3. Check the generated PowerPoint files")
        return 0
    else:
        print(f"⚠️ Some tests failed ({passed}/{total})")
        print("\n🔧 Check the error messages above and:")
        print("  1. Ensure OPENAI_API_KEY is set")
        print("  2. Run ./install_mcp_dependencies.sh")
        print("  3. Check the MCP configuration")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
