#!/usr/bin/env python3
"""MCP server for PowerPoint generation using Mistral AI."""

import asyncio
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional
import tempfile
import os

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    GetPromptRequest,
    GetPromptResult,
    ListPromptsRequest,
    ListPromptsResult,
    ListToolsRequest,
    ListToolsResult,
    Prompt,
    PromptArgument,
    Tool,
    TextContent,
    JSONRPCError,
    ErrorCode
)
from src.converter import PowerPointConverter
from src.powerpoint_generator import PowerPointGenerator
from src.schema import Presentation
from config import config
from loguru import logger

# Create server instance
server = Server("powerpoint-mcp")

@server.list_tools()
async def list_tools() -> ListToolsResult:
    """List available PowerPoint tools."""
    return ListToolsResult(
        tools=[
            Tool(
                name="generate_powerpoint_from_text",
                description="Generate a PowerPoint presentation from text input. This tool will create a structured presentation with multiple slides based on the provided content.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "The text content to convert into a PowerPoint presentation"
                        },
                        "title": {
                            "type": "string",
                            "description": "Optional title for the presentation (will be auto-generated if not provided)"
                        },
                        "output_format": {
                            "type": "string",
                            "enum": ["json", "pptx", "both"],
                            "default": "both",
                            "description": "Output format: 'json' for structured data only, 'pptx' for PowerPoint file only, or 'both' for complete pipeline"
                        },
                        "refine": {
                            "type": "boolean",
                            "default": True,
                            "description": "Whether to refine the generated JSON for better quality"
                        },
                        "theme_suggestion": {
                            "type": "string",
                            "description": "Optional theme suggestion for the presentation (e.g., 'professional', 'creative', 'minimal')"
                        }
                    },
                    "required": ["text"]
                }
            ),
            Tool(
                name="convert_json_to_powerpoint",
                description="Convert an existing JSON presentation structure to PowerPoint file.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "presentation_json": {
                            "type": "string",
                            "description": "The JSON string representing the presentation structure"
                        },
                        "output_path": {
                            "type": "string",
                            "description": "Optional output path for the PowerPoint file (defaults to temp file)"
                        }
                    },
                    "required": ["presentation_json"]
                }
            )
        ]
    )

@server.list_prompts()
async def list_prompts() -> ListPromptsResult:
    """List available prompts for PowerPoint generation."""
    return ListPromptsResult(
        prompts=[
            Prompt(
                name="powerpoint_content_analysis",
                description="Analyze text content for PowerPoint generation potential",
                arguments=[
                    PromptArgument(
                        name="content",
                        description="Text content to analyze",
                        required=True
                    )
                ]
            ),
            Prompt(
                name="presentation_structure_optimization",
                description="Optimize presentation structure for better flow and engagement",
                arguments=[
                    PromptArgument(
                        name="current_structure",
                        description="Current presentation structure as JSON",
                        required=True
                    ),
                    PromptArgument(
                        name="target_audience",
                        description="Target audience description",
                        required=False
                    )
                ]
            )
        ]
    )

@server.get_prompt()
async def get_prompt(request: GetPromptRequest) -> GetPromptResult:
    """Get specific prompt for PowerPoint operations."""
    if request.name == "powerpoint_content_analysis":
        content = request.arguments.get("content", "")
        return GetPromptResult(
            description="Analyze this content for PowerPoint presentation potential",
            messages=[
                {
                    "role": "user",
                    "content": {
                        "type": "text",
                        "text": f"""Analyze the following content for PowerPoint presentation creation:

Content: {content}

Please provide:
1. Suggested slide structure
2. Main topics that could become slides
3. Recommended presentation flow
4. Estimated slide count
5. Audience level assessment
6. Theme suggestions

Focus on creating an engaging, well-structured presentation."""
                    }
                }
            ]
        )
    elif request.name == "presentation_structure_optimization":
        current_structure = request.arguments.get("current_structure", "{}")
        target_audience = request.arguments.get("target_audience", "general audience")
        return GetPromptResult(
            description="Optimize presentation structure",
            messages=[
                {
                    "role": "user",
                    "content": {
                        "type": "text",
                        "text": f"""Optimize this PowerPoint presentation structure for better engagement:

Current Structure: {current_structure}
Target Audience: {target_audience}

Please suggest improvements for:
1. Slide order and flow
2. Content distribution
3. Visual layout recommendations  
4. Audience engagement strategies
5. Timing and pacing suggestions"""
                    }
                }
            ]
        )
    else:
        raise JSONRPCError(
            code=ErrorCode.METHOD_NOT_FOUND,
            message=f"Unknown prompt: {request.name}"
        )

@server.call_tool()
async def call_tool(request: CallToolRequest) -> CallToolResult:
    """Handle tool calls for PowerPoint generation."""
    try:
        if request.name == "generate_powerpoint_from_text":
            return await _generate_powerpoint_from_text(request.arguments)
        elif request.name == "convert_json_to_powerpoint":
            return await _convert_json_to_powerpoint(request.arguments)
        else:
            raise JSONRPCError(
                code=ErrorCode.METHOD_NOT_FOUND,
                message=f"Unknown tool: {request.name}"
            )
    except Exception as e:
        logger.error(f"Tool call error: {e}")
        raise JSONRPCError(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"Tool execution failed: {str(e)}"
        )

async def _generate_powerpoint_from_text(args: Dict[str, Any]) -> CallToolResult:
    """Generate PowerPoint from text input."""
    text = args.get("text")
    title = args.get("title")
    output_format = args.get("output_format", "both")
    refine = args.get("refine", True)
    theme_suggestion = args.get("theme_suggestion")
    
    if not text:
        raise ValueError("Text content is required")
    
    # Validate API key
    if not config.validate_api_key():
        raise ValueError("Mistral API key not configured. Please set MISTRAL_API_KEY environment variable.")
    
    # Initialize converter
    converter = PowerPointConverter()
    
    # Generate presentation
    logger.info(f"Generating presentation from {len(text)} characters of text")
    presentation = await asyncio.to_thread(
        converter.convert_text,
        text=text,
        output_file=None,
        refine=refine,
        validate=True
    )
    
    # Override title if provided
    if title:
        presentation.title = title
    
    # Apply theme suggestion if provided
    if theme_suggestion:
        presentation.metadata.theme_suggestion = theme_suggestion
    
    results = []
    file_paths = []
    
    # Generate JSON output
    if output_format in ["json", "both"]:
        json_output = presentation.to_json(indent=2)
        results.append({
            "type": "json",
            "title": presentation.title,
            "subtitle": presentation.subtitle,
            "total_slides": presentation.metadata.total_slides,
            "content": json_output
        })
    
    # Generate PowerPoint file
    if output_format in ["pptx", "both"]:
        generator = PowerPointGenerator()
        
        # Create temp file for PowerPoint output
        with tempfile.NamedTemporaryFile(suffix=".pptx", delete=False) as tmp_file:
            output_path = Path(tmp_file.name)
        
        # Generate PowerPoint
        final_path = await asyncio.to_thread(
            generator.generate_from_json,
            presentation.model_dump(),
            output_path
        )
        
        file_paths.append(str(final_path))
        results.append({
            "type": "pptx",
            "file_path": str(final_path),
            "file_size_mb": round(final_path.stat().st_size / (1024 * 1024), 2)
        })
    
    return CallToolResult(
        content=[
            TextContent(
                type="text",
                text=f"""PowerPoint generation completed successfully!

**Presentation Details:**
- Title: {presentation.title}
- Subtitle: {presentation.subtitle or 'None'}
- Total Slides: {presentation.metadata.total_slides}
- Theme: {presentation.metadata.theme_suggestion or 'Auto-selected'}
- Estimated Duration: {presentation.metadata.estimated_duration_minutes or 'Not estimated'} minutes

**Generated Content:**
{json.dumps(results, indent=2)}

**Main Topics Covered:**
{', '.join(presentation.metadata.main_topics or ['Various topics'])}

The presentation has been successfully generated and is ready to use!
"""
            )
        ]
    )

async def _convert_json_to_powerpoint(args: Dict[str, Any]) -> CallToolResult:
    """Convert JSON to PowerPoint file."""
    presentation_json = args.get("presentation_json")
    output_path = args.get("output_path")
    
    if not presentation_json:
        raise ValueError("Presentation JSON is required")
    
    try:
        # Parse and validate JSON
        presentation_data = json.loads(presentation_json)
        presentation = Presentation.model_validate(presentation_data)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format: {e}")
    except Exception as e:
        raise ValueError(f"JSON validation failed: {e}")
    
    # Initialize PowerPoint generator
    generator = PowerPointGenerator()
    
    # Determine output path
    if not output_path:
        with tempfile.NamedTemporaryFile(suffix=".pptx", delete=False) as tmp_file:
            output_path = Path(tmp_file.name)
    else:
        output_path = Path(output_path)
    
    # Generate PowerPoint
    final_path = await asyncio.to_thread(
        generator.generate_from_json,
        presentation_data,
        output_path
    )
    
    file_size_mb = round(final_path.stat().st_size / (1024 * 1024), 2)
    
    return CallToolResult(
        content=[
            TextContent(
                type="text",
                text=f"""PowerPoint file generated successfully!

**File Details:**
- Output Path: {final_path}
- File Size: {file_size_mb} MB
- Total Slides: {presentation.metadata.total_slides}
- Title: {presentation.title}

The PowerPoint file has been created and is ready to use.
"""
            )
        ]
    )

async def main():
    """Run the MCP server."""
    # Configure logging
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    
    # Check configuration
    if not config.validate_api_key():
        logger.warning("Mistral API key not configured. Some tools may not work.")
    
    # Run server
    async with server.run_server(
        NotificationOptions()
    ) as (read_stream, write_stream):
        logger.info("PowerPoint MCP server started")
        await server.handle_messages(read_stream, write_stream)

if __name__ == "__main__":
    asyncio.run(main())