"""Main converter logic for text to PowerPoint JSON."""

import json
from typing import Optional, Dict, Any
from pathlib import Path
from loguru import logger
from src.mistral_client import MistralClient
from src.prompt_engine import PromptEngine
from src.schema import Presentation
from config import config
import asyncio


class PowerPointConverter:
    """Converts text to PowerPoint JSON using Mistral AI or local LLM."""
    
    def __init__(self, api_key: Optional[str] = None, use_local: bool = False):
        """Initialize converter with Mistral client or local LLM."""
        self.use_local = use_local or config.mistral.mode == "local"
        self.prompt_engine = PromptEngine()
        
        if self.use_local:
            # Import only if needed
            from src.local_client import LocalPowerPointConverter, LocalLLMConfig
            local_config = LocalLLMConfig(
                base_url=getattr(config.mistral, 'local_base_url', 'http://localhost:5263/v1'),
                model_path=getattr(config.mistral, 'local_model_path', '/home/llama/models/base_models/Mistral-Small-3.1-24B-Instruct-2503'),
                max_tokens=config.mistral.max_tokens,
                timeout=config.mistral.timeout
            )
            self.local_converter = LocalPowerPointConverter(local_config)
            self.client = None
            logger.info("PowerPoint converter initialized with LOCAL LLM")
        else:
            self.client = MistralClient(api_key)
            self.local_converter = None
            logger.info("PowerPoint converter initialized with Mistral API")
        
        # Ensure output directory exists
        config.output.output_dir.mkdir(parents=True, exist_ok=True)
    
    def convert_text(
        self,
        text: str,
        output_file: Optional[Path] = None,
        refine: bool = True,
        validate: bool = True
    ) -> Presentation:
        """
        Convert text to PowerPoint JSON.
        
        Args:
            text: Input text to convert
            output_file: Optional path to save JSON output
            refine: Whether to refine the generated JSON
            validate: Whether to validate against schema
            
        Returns:
            Presentation object
        """
        logger.info(f"Converting text of length {len(text)} characters")
        
        # Step 1: Generate initial JSON
        json_data = self._generate_json(text)
        
        # Step 2: Refine if requested
        if refine:
            json_data = self._refine_json(json_data)
        
        # Step 3: Validate and create Presentation object
        presentation = self._validate_and_create(json_data, validate)
        
        # Step 4: Save if output file specified
        if output_file:
            self._save_output(presentation, output_file)
        
        logger.success(f"Successfully converted text to {presentation.metadata.total_slides} slides")
        return presentation
    
    def convert_file(
        self,
        input_file: Path,
        output_file: Optional[Path] = None,
        refine: bool = True,
        validate: bool = True
    ) -> Presentation:
        """
        Convert text file to PowerPoint JSON.
        
        Args:
            input_file: Path to input text file
            output_file: Path to save JSON output
            refine: Whether to refine the generated JSON
            validate: Whether to validate against schema
            
        Returns:
            Presentation object
        """
        if not input_file.exists():
            raise FileNotFoundError(f"Input file not found: {input_file}")
        
        logger.info(f"Reading input file: {input_file}")
        text = input_file.read_text(encoding='utf-8')
        
        # Generate default output filename if not specified
        if output_file is None:
            output_file = config.output.output_dir / f"{input_file.stem}_presentation.json"
        
        return self.convert_text(text, output_file, refine, validate)
    
    async def _generate_json_async(self, text: str) -> Dict[str, Any]:
        """Generate initial JSON from text using local LLM."""
        logger.debug("Generating initial JSON structure with local LLM")
        logger.info(f"Processing text of {len(text)} characters")
        
        # Use the same prompt structure as API mode
        system_prompt = (
            self.prompt_engine.get_system_prompt() + "\n\n" +
            self.prompt_engine.get_schema_prompt()
        )
        
        # Add analysis guidance
        user_prompt = (
            self.prompt_engine.get_analysis_prompt(len(text)) + "\n\n" +
            self.prompt_engine.create_conversion_prompt(text)
        )
        
        # Get examples for few-shot learning (same as API mode)
        examples = self.prompt_engine.get_examples()
        
        try:
            json_data = await self.local_converter.convert_text(
                text=user_prompt,
                system_prompt=system_prompt,
                temperature=config.mistral.temperature,  # Use same temperature as API
                examples=examples  # Pass the few-shot examples
            )
            return json_data
        except Exception as e:
            logger.error(f"Failed to generate JSON with local LLM: {e}")
            raise
    
    def _generate_json(self, text: str) -> Dict[str, Any]:
        """Generate initial JSON from text."""
        if self.use_local:
            # Run async function in sync context
            return asyncio.run(self._generate_json_async(text))
        
        logger.debug("Generating initial JSON structure")
        logger.info(f"Processing text of {len(text)} characters")
        
        # Combine all prompts
        system_prompt = (
            self.prompt_engine.get_system_prompt() + "\n\n" +
            self.prompt_engine.get_schema_prompt()
        )
        
        # Add analysis guidance
        user_prompt = (
            self.prompt_engine.get_analysis_prompt(len(text)) + "\n\n" +
            self.prompt_engine.create_conversion_prompt(text)
        )
        
        # Get examples for few-shot learning
        examples = self.prompt_engine.get_examples()
        
        # Generate JSON using Mistral
        try:
            json_data = self.client.generate_json(
                prompt=user_prompt,
                system_prompt=system_prompt,
                examples=examples,
                temperature=config.mistral.temperature,
                max_tokens=config.mistral.max_tokens
            )
            
            # Save intermediate if configured
            if config.output.save_intermediate:
                intermediate_path = config.output.output_dir / "intermediate_raw.json"
                intermediate_path.write_text(json.dumps(json_data, indent=2))
                logger.debug(f"Saved intermediate JSON to {intermediate_path}")
            
            return json_data
            
        except Exception as e:
            logger.error(f"Failed to generate JSON: {e}")
            raise
    
    def _refine_json(self, json_data: Dict[str, Any]) -> Dict[str, Any]:
        """Refine the generated JSON for better quality."""
        if self.use_local:
            # Skip refinement for local mode for now
            logger.debug("Skipping refinement in local mode")
            return json_data
            
        logger.debug("Refining generated JSON")
        
        # Convert to string for refinement
        json_str = json.dumps(json_data, indent=2)
        
        # Create refinement prompt
        refinement_prompt = self.prompt_engine.get_refinement_prompt(json_str)
        
        # Generate refined version
        try:
            refined_data = self.client.generate_json(
                prompt=refinement_prompt,
                system_prompt=self.prompt_engine.get_system_prompt(),
                temperature=0.2,  # Lower temperature for refinement
                max_tokens=config.mistral.max_tokens
            )
            
            # Save intermediate if configured
            if config.output.save_intermediate:
                intermediate_path = config.output.output_dir / "intermediate_refined.json"
                intermediate_path.write_text(json.dumps(refined_data, indent=2))
                logger.debug(f"Saved refined JSON to {intermediate_path}")
            
            return refined_data
            
        except Exception as e:
            logger.warning(f"Refinement failed, using original: {e}")
            return json_data
    
    def _validate_and_create(self, json_data: Dict[str, Any], validate: bool) -> Presentation:
        """Validate JSON and create Presentation object."""
        if not validate:
            logger.warning("Skipping validation as requested")
            # Create presentation without validation
            return Presentation.model_construct(**json_data)
        
        try:
            # Validate using Pydantic
            presentation = Presentation.model_validate(json_data)
            logger.debug("JSON validation successful")
            return presentation
            
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            
            # Try to fix common issues
            json_data = self._fix_common_issues(json_data)
            
            # Try validation again
            try:
                presentation = Presentation.model_validate(json_data)
                logger.info("JSON validation successful after fixes")
                return presentation
            except Exception as e2:
                logger.error(f"Validation still failed after fixes: {e2}")
                raise
    
    def _fix_common_issues(self, json_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fix common JSON structure issues."""
        logger.debug("Attempting to fix common JSON issues")
        
        # Ensure slides have sequential IDs
        if "slides" in json_data:
            for i, slide in enumerate(json_data["slides"], 1):
                slide["id"] = i
        
        # Ensure metadata exists
        if "metadata" not in json_data:
            json_data["metadata"] = {}
        
        # Update total_slides count
        if "slides" in json_data:
            json_data["metadata"]["total_slides"] = len(json_data["slides"])
        
        # Ensure each slide has required fields
        for slide in json_data.get("slides", []):
            if "title" not in slide:
                slide["title"] = f"Slide {slide.get('id', '?')}"
            if "layout_type" not in slide:
                slide["layout_type"] = "bullet_points"
            if "content" not in slide:
                slide["content"] = {"bullets": [{"text": "Content placeholder"}]}
        
        return json_data
    
    def _save_output(self, presentation: Presentation, output_file: Path) -> None:
        """Save presentation to JSON file."""
        try:
            # Create parent directories if needed
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Write JSON
            json_str = presentation.to_json(indent=config.output.indent)
            output_file.write_text(json_str, encoding='utf-8')
            
            logger.success(f"Saved presentation to {output_file}")
            
        except Exception as e:
            logger.error(f"Failed to save output: {e}")
            raise
    
    def test_connection(self) -> bool:
        """Test connection to Mistral API."""
        return self.client.test_connection()