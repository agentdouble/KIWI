"""Test script for vLLM tool calls integration."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.vllm_service import VLLMService
from app.services.mcp_service import get_mcp_service
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_vllm_with_tools():
    """Test vLLM with PowerPoint generation tool."""
    
    # Initialize services
    vllm_service = VLLMService()
    mcp_service = get_mcp_service()
    
    # Get available tools
    tools = await mcp_service.get_available_tools()
    logger.info(f"Available tools: {[t['function']['name'] for t in tools]}")
    
    # Test message requesting PowerPoint
    messages = [
        {
            "role": "system",
            "content": "Tu es un assistant capable de générer des présentations PowerPoint."
        },
        {
            "role": "user",
            "content": "Génère moi un PowerPoint sur les coquelicots"
        }
    ]
    
    try:
        # Test non-streaming response
        logger.info("Testing non-streaming response with tools...")
        response = await vllm_service.generate_response(messages, tools)
        logger.info(f"Response: {response}")
        
        # Test with metadata
        logger.info("\nTesting response with metadata...")
        response_meta, metadata = await vllm_service.generate_response_with_metadata(messages, tools)
        logger.info(f"Response: {response_meta}")
        logger.info(f"Metadata: {metadata}")
        
        # Test streaming
        logger.info("\nTesting streaming response...")
        async for chunk in vllm_service.generate_stream_response(messages, tools):
            if chunk.startswith("[["):
                logger.info(f"Signal: {chunk}")
            else:
                print(chunk, end="", flush=True)
        print()  # New line after streaming
        
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        return False
    
    return True


async def test_direct_tool_execution():
    """Test direct MCP tool execution."""
    
    mcp_service = get_mcp_service()
    
    parameters = {
        "text": "Les coquelicots sont des fleurs sauvages magnifiques",
        "title": "Les Coquelicots",
        "theme_suggestion": "Nature et Botanique"
    }
    
    try:
        logger.info("Testing direct PowerPoint generation...")
        result = await mcp_service.execute_tool("generate_powerpoint_from_text", parameters)
        logger.info(f"Result: {result}")
        
        if result.get("success"):
            logger.info("✅ PowerPoint generated successfully!")
            logger.info(f"Details: {result.get('mcp_details', {})}")
        else:
            logger.error(f"❌ Generation failed: {result.get('message')}")
            
    except Exception as e:
        logger.error(f"Direct tool test failed: {e}", exc_info=True)
        return False
    
    return True


if __name__ == "__main__":
    # Run tests
    asyncio.run(test_vllm_with_tools())
    # asyncio.run(test_direct_tool_execution())