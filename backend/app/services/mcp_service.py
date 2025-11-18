"""Service for MCP (Model Context Protocol) integration."""

import json
import asyncio
from typing import Dict, List, Any, Optional
from pathlib import Path
import sys
import os
from urllib.parse import urlparse, urlunparse
from loguru import logger
import tempfile
from datetime import datetime

# Add MCP PowerPoint module to path
mcp_path = Path(__file__).parent.parent.parent / "mcp" / "powerpoint_mcp"
sys.path.insert(0, str(mcp_path))

try:
    from src.converter import PowerPointConverter
    from src.powerpoint_generator import PowerPointGenerator
    from src.schema import Presentation
    from config import config as mcp_config
except ImportError as e:
    logger.error(f"Failed to import PowerPoint modules: {e}")
    PowerPointConverter = None
    PowerPointGenerator = None
    Presentation = None
    mcp_config = None


class MCPService:
    """Service for handling MCP tool integrations."""
    
    def __init__(self):
        """Initialize MCP service."""
        self.converter = None
        self.generator = None
        self.output_dir = Path(__file__).parent.parent.parent / "uploads" / "powerpoints"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info("MCP Service initialized for PowerPoint tools")
        
    def should_use_powerpoint_tool(self, message: str) -> bool:
        """
        Check if the message indicates a PowerPoint generation request.
        
        Args:
            message: User message to analyze
            
        Returns:
            True if PowerPoint generation is needed
        """
        message_lower = message.lower()
        
        # Remove accents for better matching
        import unicodedata
        message_normalized = unicodedata.normalize('NFD', message_lower)
        message_normalized = ''.join(char for char in message_normalized if unicodedata.category(char) != 'Mn')
        
        # PowerPoint keywords
        powerpoint_words = ['powerpoint', 'ppt', 'presentation', 'slides', 'diapositives', 'diapo']
        
        # Action words  
        action_words = ['genere', 'creer', 'faire', 'create', 'make', 'generate', 'peux', 'peut']
        
        # Check if message contains PowerPoint-related words
        has_powerpoint = any(word in message_normalized for word in powerpoint_words)
        
        # Check if message contains action words
        has_action = any(word in message_normalized for word in action_words)
        
        # If both action and PowerPoint words are present, it's likely a generation request
        if has_powerpoint and (has_action or '?' in message):
            logger.info(f"MCP: PowerPoint detected - has_action={has_action}, has_powerpoint={has_powerpoint}")
            return True
        
        # Also check for direct phrases
        direct_phrases = [
            'powerpoint sur',
            'presentation sur',
            'slides sur',
            'powerpoint about',
            'presentation about'
        ]
        
        for phrase in direct_phrases:
            if phrase in message_normalized:
                logger.info(f"MCP: PowerPoint detected via phrase: '{phrase}'")
                return True
        
        logger.debug(f"MCP: No PowerPoint trigger in: '{message_lower[:100]}'")
        return False
    
    async def get_available_tools(self) -> List[Dict[str, Any]]:
        """
        Get list of available MCP tools.
        
        Returns:
            List of tool definitions for Mistral function calling
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "generate_powerpoint_from_text",
                    "description": "Génère une présentation PowerPoint professionnelle à partir d'un texte ou d'un sujet",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "text": {
                                "type": "string",
                                "description": "Le texte ou sujet pour générer la présentation"
                            },
                            "title": {
                                "type": "string", 
                                "description": "Le titre de la présentation (optionnel)"
                            },
                            "theme_suggestion": {
                                "type": "string",
                                "description": "Suggestion de thème pour la présentation"
                            }
                        },
                        "required": ["text"]
                    }
                }
            }
        ]
    
    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute an MCP tool with given parameters.
        
        Args:
            tool_name: Name of the tool to execute
            parameters: Tool parameters
            
        Returns:
            Tool execution result
        """
        try:
            if tool_name == "generate_powerpoint_from_text":
                return await self.generate_powerpoint(parameters)
            else:
                return {
                    "success": False,
                    "message": f"Outil inconnu: {tool_name}"
                }
                
        except Exception as e:
            logger.error(f"MCP tool execution failed: {e}")
            return {
                "success": False,
                "message": f"Erreur lors de l'exécution MCP: {str(e)}"
            }
    
    async def generate_powerpoint(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a PowerPoint presentation using MCP.
        
        Args:
            parameters: Generation parameters
            
        Returns:
            Generation result with file info
        """
        try:
            if not PowerPointConverter or not PowerPointGenerator:
                return {
                    "success": False,
                    "message": "Les modules PowerPoint ne sont pas disponibles"
                }
            
            text = parameters.get("text", "")
            title = parameters.get("title")
            theme_suggestion = parameters.get("theme_suggestion")
            
            if not text:
                return {
                    "success": False,
                    "message": "Le texte est requis pour générer une présentation"
                }
            
            # Initialize converter if needed
            if not self.converter:
                from app.config import settings

                use_local = settings.is_local_mode

                if use_local:
                    try:
                        parsed = urlparse(settings.vllm_api_url)
                        base_path = parsed.path
                        if base_path.endswith("/chat/completions"):
                            base_path = base_path[: -len("/chat/completions")]
                        if not base_path:
                            base_path = "/"
                        base_url = urlunparse(parsed._replace(path=base_path))
                    except Exception:
                        base_url = "http://localhost:5263/v1"

                    os.environ.setdefault("MISTRAL_MODE", "local")
                    os.environ.setdefault("LOCAL_BASE_URL", base_url)
                    os.environ.setdefault("LOCAL_MODEL_PATH", settings.vllm_model_name)

                    if mcp_config:
                        mcp_config.mistral.mode = "local"
                        mcp_config.mistral.local_base_url = base_url
                        mcp_config.mistral.local_model_path = settings.vllm_model_name
                else:
                    # API mode requires a valid key
                    if not mcp_config or not mcp_config.validate_api_key():
                        if not settings.mistral_api_key:
                            return {
                                "success": False,
                                "message": "Clé API Mistral non configurée"
                            }
                        os.environ.setdefault("MISTRAL_API_KEY", settings.mistral_api_key)
                        if mcp_config:
                            mcp_config.mistral.api_key = settings.mistral_api_key

                self.converter = PowerPointConverter(
                    api_key=settings.mistral_api_key if not use_local else None,
                    use_local=use_local
                )
            
            # Convert text to presentation
            logger.info(f"Converting {len(text)} characters to presentation")
            presentation = await asyncio.to_thread(
                self.converter.convert_text,
                text=text,
                output_file=None,
                refine=True,
                validate=True
            )
            
            # Override title if provided
            if title:
                presentation.title = title
            
            # Apply theme suggestion if provided
            if theme_suggestion:
                presentation.metadata.theme_suggestion = theme_suggestion
            
            # Initialize generator if needed
            if not self.generator:
                self.generator = PowerPointGenerator()
            
            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"presentation_{timestamp}.pptx"
            output_path = self.output_dir / filename
            
            # Generate PowerPoint
            final_path = await asyncio.to_thread(
                self.generator.generate_from_json,
                presentation.model_dump(),
                output_path
            )
            
            # Build result
            result = {
                "success": True,
                "message": f"PowerPoint généré avec succès: {presentation.metadata.total_slides} slides",
                "result": f"Présentation '{presentation.title}' créée avec {presentation.metadata.total_slides} slides",
                "mcp_details": {
                    "filename": filename,
                    "path": str(final_path),
                    "relative_path": str(final_path.relative_to(self.output_dir.parent.parent)),
                    "size": final_path.stat().st_size,
                    "download_url": f"/api/powerpoint/download/{final_path.relative_to(self.output_dir.parent.parent)}",
                    "title": presentation.title,
                    "subtitle": presentation.subtitle,
                    "total_slides": presentation.metadata.total_slides,
                    "theme": presentation.metadata.theme_suggestion
                }
            }
            
            logger.info(f"PowerPoint generated successfully: {filename}")
            return result
            
        except Exception as e:
            logger.error(f"MCP PowerPoint generation failed: {e}")
            return {
                "success": False,
                "message": f"Erreur lors de la génération: {str(e)}"
            }
    
    async def cleanup(self):
        """Cleanup MCP connections."""
        pass


# Singleton instance
_mcp_service = None

def get_mcp_service() -> MCPService:
    """Get or create MCP service singleton."""
    global _mcp_service
    if _mcp_service is None:
        _mcp_service = MCPService()
    return _mcp_service


async def cleanup_mcp_service():
    """Cleanup MCP service and connections."""
    global _mcp_service
    if _mcp_service:
        await _mcp_service.cleanup()
        _mcp_service = None
