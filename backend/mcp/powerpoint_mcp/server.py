#!/usr/bin/env python3
"""Proper MCP server for PowerPoint generation following the official MCP protocol."""

import asyncio
import json
import sys
from pathlib import Path
from typing import Any, Dict
import tempfile

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    Tool,
    TextContent,
)
from src.converter import PowerPointConverter
from src.powerpoint_generator import PowerPointGenerator
from src.schema import Presentation
from config import config
from loguru import logger

# Create server instance
server = Server("powerpoint-mcp")


@server.list_tools()
async def list_tools(request: ListToolsRequest) -> ListToolsResult:
    """List available PowerPoint tools."""
    logger.info(f"MCP server: list_tools called with request: {request}")
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


@server.call_tool()
async def call_tool(request: CallToolRequest) -> CallToolResult:
    """Handle tool calls for PowerPoint generation."""
    try:
        if request.name == "generate_powerpoint_from_text":
            return await _generate_powerpoint_from_text(request.arguments)
        elif request.name == "convert_json_to_powerpoint":
            return await _convert_json_to_powerpoint(request.arguments)
        else:
            logger.error(f"Unknown tool requested: {request.name}")
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"Error: Unknown tool '{request.name}'"
                    )
                ],
                isError=True
            )
    except Exception as e:
        logger.error(f"Tool call error: {e}")
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f"Tool execution failed: {str(e)}"
                )
            ],
            isError=True
        )


async def _generate_powerpoint_from_text(args: Dict[str, Any]) -> CallToolResult:
    """Generate PowerPoint from text input."""
    text = args.get("text")
    title = args.get("title")
    output_format = args.get("output_format", "both")
    refine = args.get("refine", True)
    theme_suggestion = args.get("theme_suggestion")
    
    if not text:
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text="Error: Text content is required"
                )
            ],
            isError=True
        )
    
    # Validate API key
    if not config.validate_api_key():
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text="Error: LLM API key not configured. Please set API_KEY environment variable."
                )
            ],
            isError=True
        )
    
    try:
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
    
    except Exception as e:
        logger.error(f"PowerPoint generation failed: {e}")
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f"PowerPoint generation failed: {str(e)}"
                )
            ],
            isError=True
        )


async def _convert_json_to_powerpoint(args: Dict[str, Any]) -> CallToolResult:
    """Convert JSON to PowerPoint file."""
    presentation_json = args.get("presentation_json")
    output_path = args.get("output_path")
    
    if not presentation_json:
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text="Error: Presentation JSON is required"
                )
            ],
            isError=True
        )
    
    try:
        # Parse and validate JSON
        presentation_data = json.loads(presentation_json)
        presentation = Presentation.model_validate(presentation_data)
        
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
    
    except json.JSONDecodeError as e:
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f"Invalid JSON format: {e}"
                )
            ],
            isError=True
        )
    except Exception as e:
        logger.error(f"JSON to PowerPoint conversion failed: {e}")
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f"JSON to PowerPoint conversion failed: {e}"
                )
            ],
            isError=True
        )


async def main():
    """Run the MCP server using stdio transport."""
    # Configure logging to stderr to avoid interference with stdio
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    
    # Check configuration
    if not config.validate_api_key():
        logger.warning("Mistral API key not configured. Some tools may not work.")
    
    logger.info("PowerPoint MCP server starting...")
    
    # Run server with stdio transport following the official MCP pattern
    async with stdio_server() as streams:
        await server.run(
            streams[0],
            streams[1],
            InitializationOptions(
                server_name="powerpoint-mcp",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={}
                )
            )
        )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)
