"""Test to ensure local and API modes produce similar results."""

import asyncio
import json
from pathlib import Path
from loguru import logger
from src.converter import PowerPointConverter
from config import config


async def test_both_modes():
    """Test both local and API modes with the same input."""
    
    # Test input
    test_text = """
    Introduction to Artificial Intelligence
    
    Slide 1: What is AI?
    - Machine learning and deep learning
    - Natural language processing
    - Computer vision
    
    Slide 2: Applications
    - Healthcare diagnostics
    - Autonomous vehicles
    - Virtual assistants
    
    Slide 3: Future of AI
    - AGI development
    - Ethical considerations
    - Impact on society
    """
    
    results = {}
    
    # Test API mode (if API key available)
    try:
        logger.info("Testing API mode...")
        converter_api = PowerPointConverter(use_local=False)
        presentation_api = converter_api.convert_text(test_text, refine=False)
        results["api"] = {
            "slides": len(presentation_api.slides),
            "first_title": presentation_api.slides[0].title if presentation_api.slides else None,
            "layout_types": [s.layout_type for s in presentation_api.slides]
        }
        logger.success(f"API mode: {results['api']['slides']} slides generated")
    except Exception as e:
        logger.error(f"API mode failed: {e}")
        results["api"] = {"error": str(e)}
    
    # Test Local mode
    try:
        logger.info("Testing Local mode...")
        converter_local = PowerPointConverter(use_local=True)
        presentation_local = converter_local.convert_text(test_text, refine=False)
        results["local"] = {
            "slides": len(presentation_local.slides),
            "first_title": presentation_local.slides[0].title if presentation_local.slides else None,
            "layout_types": [s.layout_type for s in presentation_local.slides]
        }
        logger.success(f"Local mode: {results['local']['slides']} slides generated")
    except Exception as e:
        logger.error(f"Local mode failed: {e}")
        results["local"] = {"error": str(e)}
    
    # Compare results
    logger.info("\n=== COMPARISON RESULTS ===")
    logger.info(f"API Mode: {json.dumps(results.get('api', {}), indent=2)}")
    logger.info(f"Local Mode: {json.dumps(results.get('local', {}), indent=2)}")
    
    # Check similarity
    if "error" not in results.get("api", {}) and "error" not in results.get("local", {}):
        api_slides = results["api"]["slides"]
        local_slides = results["local"]["slides"]
        
        if abs(api_slides - local_slides) <= 1:  # Allow 1 slide difference
            logger.success("✅ Both modes produce similar number of slides")
        else:
            logger.warning(f"⚠️ Slide count difference: API={api_slides}, Local={local_slides}")
        
        # Check if layout types are similar
        api_layouts = set(results["api"]["layout_types"])
        local_layouts = set(results["local"]["layout_types"])
        common_layouts = api_layouts & local_layouts
        
        if len(common_layouts) > 0:
            logger.success(f"✅ Common layout types: {common_layouts}")
        else:
            logger.warning(f"⚠️ No common layout types: API={api_layouts}, Local={local_layouts}")
    
    return results


if __name__ == "__main__":
    asyncio.run(test_both_modes())