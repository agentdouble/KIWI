"""Service for PowerPoint generation using MCP PowerPoint module."""

import os
import sys
import json
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional
from loguru import logger
from datetime import datetime
from mistralai import Mistral

# Add MCP PowerPoint module to path
mcp_path = Path(__file__).parent.parent.parent / "mcp" / "powerpoint_mcp"
sys.path.insert(0, str(mcp_path))

from src.powerpoint_generator import PowerPointGenerator
from src.schema import Presentation
from src.prompt_engine import PromptEngine


class PowerPointService:
    """Service for generating PowerPoint presentations."""
    
    def __init__(self):
        """Initialize PowerPoint service."""
        self.generator = PowerPointGenerator()
        self.prompt_engine = PromptEngine()
        self.output_dir = Path(__file__).parent.parent.parent / "uploads" / "powerpoints"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize Mistral client using config settings
        from app.config import settings
        api_key = settings.mistral_api_key
        if not api_key:
            logger.warning("MISTRAL_API_KEY not found in settings")
        self.mistral_client = Mistral(api_key=api_key) if api_key else None
        
    async def generate_from_text(
        self, 
        text: str,
        filename: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate PowerPoint from text input.
        
        Args:
            text: Text content to convert to PowerPoint
            filename: Optional filename for the output
            user_id: Optional user ID for file organization
            
        Returns:
            Dict containing file path and metadata
        """
        try:
            # Generate unique filename if not provided
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"presentation_{timestamp}.pptx"
            elif not filename.endswith('.pptx'):
                filename = f"{filename}.pptx"
            
            # Create user directory if user_id provided
            if user_id:
                output_path = self.output_dir / str(user_id) / filename
                output_path.parent.mkdir(parents=True, exist_ok=True)
            else:
                output_path = self.output_dir / filename
            
            # Convert text to JSON structure using Mistral
            logger.info(f"Converting text to PowerPoint JSON structure...")
            json_data = await self._convert_text_to_json(text)
            
            if not json_data:
                raise ValueError("Failed to convert text to JSON structure")
            
            # Validate and parse JSON
            presentation = Presentation.model_validate(json_data)
            
            # Generate PowerPoint
            logger.info(f"Generating PowerPoint file...")
            pptx_path = self.generator.generate_from_json(
                json_data, 
                output_path
            )
            
            # Return result
            result = {
                "success": True,
                "filename": filename,
                "path": str(pptx_path),
                "relative_path": str(pptx_path.relative_to(self.output_dir.parent.parent)),
                "size": pptx_path.stat().st_size,
                "slides_count": len(presentation.slides),
                "title": presentation.title,
                "created_at": datetime.now().isoformat()
            }
            
            logger.success(f"PowerPoint generated successfully: {filename}")
            return result
            
        except Exception as e:
            logger.error(f"Error generating PowerPoint: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def generate_from_json(
        self,
        json_data: Dict[str, Any],
        filename: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate PowerPoint from JSON structure.
        
        Args:
            json_data: JSON structure for PowerPoint
            filename: Optional filename for the output
            user_id: Optional user ID for file organization
            
        Returns:
            Dict containing file path and metadata
        """
        try:
            # Generate unique filename if not provided
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"presentation_{timestamp}.pptx"
            elif not filename.endswith('.pptx'):
                filename = f"{filename}.pptx"
            
            # Create user directory if user_id provided
            if user_id:
                output_path = self.output_dir / str(user_id) / filename
                output_path.parent.mkdir(parents=True, exist_ok=True)
            else:
                output_path = self.output_dir / filename
            
            # Validate JSON structure
            presentation = Presentation.model_validate(json_data)
            
            # Generate PowerPoint
            logger.info(f"Generating PowerPoint file from JSON...")
            pptx_path = self.generator.generate_from_json(
                json_data,
                output_path
            )
            
            # Return result
            result = {
                "success": True,
                "filename": filename,
                "path": str(pptx_path),
                "relative_path": str(pptx_path.relative_to(self.output_dir.parent.parent)),
                "size": pptx_path.stat().st_size,
                "slides_count": len(presentation.slides),
                "title": presentation.title,
                "created_at": datetime.now().isoformat()
            }
            
            logger.success(f"PowerPoint generated successfully: {filename}")
            return result
            
        except Exception as e:
            logger.error(f"Error generating PowerPoint from JSON: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_download_url(self, relative_path: str) -> str:
        """
        Get download URL for a generated PowerPoint.
        
        Args:
            relative_path: Relative path to the file
            
        Returns:
            Download URL
        """
        # Return the API endpoint for downloading
        return f"/api/powerpoint/download/{relative_path}"
    
    async def _convert_text_to_json(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Convert text to PowerPoint JSON structure using Mistral.
        
        Args:
            text: Input text to convert
            
        Returns:
            JSON structure for PowerPoint or None
        """
        if not self.mistral_client:
            raise ValueError("Mistral client not initialized. Please set MISTRAL_API_KEY")
        
        try:
            # Build prompts
            system_prompt = (
                self.prompt_engine.system_prompt + "\n\n" +
                self.prompt_engine.instruction_prompt + "\n\n" +
                self.prompt_engine.structure_prompt + "\n\n" +
                self.prompt_engine.get_example_prompt()
            )
            
            user_prompt = self.prompt_engine.format_user_prompt(text)
            
            # Generate with Mistral
            response = await asyncio.to_thread(
                self.mistral_client.chat.complete,
                model="mistral-large-latest",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=8000
            )
            
            if not response.choices:
                logger.error("No response from Mistral")
                return None
            
            content = response.choices[0].message.content
            
            # Extract JSON from response
            json_str = self._extract_json(content)
            if not json_str:
                logger.error("No valid JSON found in response")
                return None
            
            # Parse JSON
            json_data = json.loads(json_str)
            
            # Refine JSON if needed
            json_data = await self._refine_json(json_data)
            
            return json_data
            
        except Exception as e:
            logger.error(f"Error converting text to JSON: {str(e)}")
            return None
    
    def _extract_json(self, content: str) -> Optional[str]:
        """Extract JSON from Mistral response."""
        import re
        
        # Try to find JSON between ```json and ``` markers
        json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
        if json_match:
            return json_match.group(1)
        
        # Try to find JSON between { and }
        brace_match = re.search(r'\{.*\}', content, re.DOTALL)
        if brace_match:
            return brace_match.group(0)
        
        return None
    
    async def _refine_json(self, json_data: Dict[str, Any]) -> Dict[str, Any]:
        """Refine the generated JSON structure."""
        if not self.mistral_client:
            return json_data
        
        try:
            refinement_prompt = self.prompt_engine.refinement_prompt
            
            response = await asyncio.to_thread(
                self.mistral_client.chat.complete,
                model="mistral-large-latest",
                messages=[
                    {"role": "system", "content": refinement_prompt},
                    {"role": "user", "content": f"Please refine this presentation JSON:\n\n{json.dumps(json_data, indent=2)}"}
                ],
                temperature=0.3,
                max_tokens=8000
            )
            
            if response.choices:
                content = response.choices[0].message.content
                refined_json_str = self._extract_json(content)
                if refined_json_str:
                    return json.loads(refined_json_str)
            
        except Exception as e:
            logger.warning(f"Error refining JSON: {str(e)}")
        
        return json_data


# Singleton instance
powerpoint_service = PowerPointService()