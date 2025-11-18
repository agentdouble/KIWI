#!/usr/bin/env python3
"""CLI interface for PowerPoint JSON generator."""

import sys
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from loguru import logger
from src.converter import PowerPointConverter
from src.powerpoint_generator import PowerPointGenerator
from src.schema import Presentation
from config import config

# Initialize Typer app and Rich console
app = typer.Typer(
    name="powerpoint-generator",
    help="Convert text to PowerPoint JSON using Mistral AI",
    add_completion=False
)
console = Console()

# Configure logging
logger.remove()  # Remove default handler
logger.add(
    sys.stderr,
    format=config.logging.format,
    level=config.logging.level,
    colorize=True
)


@app.command()
def convert(
    input_file: Optional[Path] = typer.Option(
        None,
        "--input", "-i",
        help="Path to input text file",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True
    ),
    text: Optional[str] = typer.Option(
        None,
        "--text", "-t",
        help="Direct text input (alternative to file)"
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output", "-o",
        help="Output JSON file path"
    ),
    no_refine: bool = typer.Option(
        False,
        "--no-refine",
        help="Skip JSON refinement step"
    ),
    no_validate: bool = typer.Option(
        False,
        "--no-validate",
        help="Skip schema validation"
    ),
    show: bool = typer.Option(
        True,
        "--show/--no-show",
        help="Display generated JSON in terminal"
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        help="Enable debug logging"
    )
):
    """Convert text to PowerPoint JSON format."""
    
    # Enable debug if requested
    if debug:
        logger.remove()
        logger.add(sys.stderr, level="DEBUG")
    
    # Validate input
    if not input_file and not text:
        console.print("[red]Error:[/red] Provide either --input file or --text")
        raise typer.Exit(1)
    
    if input_file and text:
        console.print("[red]Error:[/red] Provide either --input or --text, not both")
        raise typer.Exit(1)
    
    # Check API key
    if not config.validate_api_key():
        console.print(Panel(
            "[red]Mistral API key not found![/red]\n\n"
            "Please set your API key in the .env file:\n"
            "MISTRAL_API_KEY=your_key_here",
            title="Configuration Error",
            border_style="red"
        ))
        raise typer.Exit(1)
    
    try:
        # Initialize converter
        with console.status("[bold green]Initializing converter..."):
            converter = PowerPointConverter()
        
        # Convert based on input type
        if input_file:
            with console.status(f"[bold green]Converting {input_file.name}..."):
                presentation = converter.convert_file(
                    input_file=input_file,
                    output_file=output,
                    refine=not no_refine,
                    validate=not no_validate
                )
        else:
            with console.status("[bold green]Converting text..."):
                presentation = converter.convert_text(
                    text=text,
                    output_file=output,
                    refine=not no_refine,
                    validate=not no_validate
                )
        
        # Display success message
        console.print(Panel(
            f"✅ Successfully generated presentation with [bold]{presentation.metadata.total_slides}[/bold] slides",
            title="Success",
            border_style="green"
        ))
        
        # Display presentation info
        _display_presentation_info(presentation)
        
        # Show JSON if requested
        if show:
            json_str = presentation.to_json(indent=2)
            syntax = Syntax(json_str, "json", theme="monokai", line_numbers=True)
            console.print("\n[bold]Generated JSON:[/bold]")
            console.print(syntax)
        
        # Show output file if saved
        if output:
            console.print(f"\n📁 Saved to: [cyan]{output}[/cyan]")
    
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        if debug:
            logger.exception("Detailed error:")
        raise typer.Exit(1)


@app.command()
def test():
    """Test connection to Mistral API."""
    console.print("[bold]Testing Mistral API connection...[/bold]\n")
    
    # Check API key
    if not config.validate_api_key():
        console.print("[red]✗[/red] API key not found in .env file")
        raise typer.Exit(1)
    
    console.print("[green]✓[/green] API key found")
    console.print(f"[green]✓[/green] Using model: {config.mistral.model}")
    
    try:
        # Test connection
        with console.status("[bold green]Connecting to Mistral API..."):
            converter = PowerPointConverter()
            success = converter.test_connection()
        
        if success:
            console.print("[green]✓[/green] Successfully connected to Mistral API")
            console.print("\n[bold green]Ready to generate presentations![/bold]")
        else:
            console.print("[red]✗[/red] Connection test failed")
            raise typer.Exit(1)
            
    except Exception as e:
        console.print(f"[red]✗[/red] Connection failed: {e}")
        raise typer.Exit(1)


@app.command()
def example():
    """Show example usage and sample output."""
    console.print(Panel(
        "[bold]PowerPoint JSON Generator Examples[/bold]",
        border_style="blue"
    ))
    
    # Show example commands
    console.print("\n[bold]Example Commands:[/bold]\n")
    
    examples = [
        ("Convert a text file:", "python main.py convert -i document.txt -o presentation.json"),
        ("Direct text input:", 'python main.py convert -t "Your presentation content here"'),
        ("Quick conversion without refinement:", "python main.py convert -i doc.txt --no-refine"),
        ("Test API connection:", "python main.py test"),
    ]
    
    for desc, cmd in examples:
        console.print(f"  [cyan]{desc}[/cyan]")
        console.print(f"  $ {cmd}\n")
    
    # Show sample input/output
    console.print("[bold]Sample Input Text:[/bold]\n")
    sample_input = """Introduction to Machine Learning

Machine learning is a subset of artificial intelligence that enables systems to learn from data.

Key Concepts:
- Supervised Learning: Learning from labeled data
- Unsupervised Learning: Finding patterns in unlabeled data  
- Reinforcement Learning: Learning through trial and error

Applications include image recognition, natural language processing, and predictive analytics."""
    
    console.print(Panel(sample_input, border_style="dim"))
    
    console.print("\n[bold]Sample Output Structure:[/bold]\n")
    sample_output = """{
  "title": "Introduction to Machine Learning",
  "slides": [
    {
      "id": 1,
      "title": "Introduction to Machine Learning",
      "layout_type": "title_slide",
      "content": {...}
    },
    {
      "id": 2,
      "title": "What is Machine Learning?",
      "layout_type": "text_heavy",
      "content": {
        "paragraphs": ["Machine learning is a subset..."],
        "key_points": ["AI subset", "Learn from data"]
      }
    },
    {
      "id": 3,
      "title": "Key Concepts",
      "layout_type": "bullet_points",
      "content": {
        "bullets": [
          {
            "text": "Supervised Learning",
            "sub_bullets": ["Learning from labeled data"]
          }
        ]
      }
    }
  ],
  "metadata": {
    "total_slides": 3,
    "theme_suggestion": "Professional"
  }
}"""
    
    syntax = Syntax(sample_output, "json", theme="monokai")
    console.print(syntax)


def _display_presentation_info(presentation: Presentation):
    """Display presentation information in a table."""
    table = Table(title="Presentation Overview", show_header=True)
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="white")
    
    table.add_row("Title", presentation.title)
    if presentation.subtitle:
        table.add_row("Subtitle", presentation.subtitle)
    table.add_row("Total Slides", str(presentation.metadata.total_slides))
    
    if presentation.metadata.estimated_duration_minutes:
        table.add_row("Est. Duration", f"{presentation.metadata.estimated_duration_minutes} min")
    
    if presentation.metadata.theme_suggestion:
        table.add_row("Theme", presentation.metadata.theme_suggestion)
    
    if presentation.metadata.audience_level:
        table.add_row("Audience Level", presentation.metadata.audience_level)
    
    if presentation.metadata.main_topics:
        table.add_row("Main Topics", ", ".join(presentation.metadata.main_topics))
    
    # Show slide types distribution
    layout_counts = {}
    for slide in presentation.slides:
        layout_counts[slide.layout_type] = layout_counts.get(slide.layout_type, 0) + 1
    
    layout_str = ", ".join([f"{k}: {v}" for k, v in layout_counts.items()])
    table.add_row("Layout Types", layout_str)
    
    console.print(table)


@app.command()
def to_pptx(
    json_file: Path = typer.Argument(
        ...,
        help="Path to JSON file to convert",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output", "-o",
        help="Output PowerPoint file path"
    ),
    open_file: bool = typer.Option(
        False,
        "--open",
        help="Open the PowerPoint file after generation"
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        help="Enable debug logging"
    )
):
    """Convert JSON to PowerPoint presentation."""
    
    # Enable debug if requested
    if debug:
        logger.remove()
        logger.add(sys.stderr, level="DEBUG")
    
    try:
        # Initialize generator
        with console.status("[bold green]Initializing PowerPoint generator..."):
            generator = PowerPointGenerator()
        
        # Generate default output path if not provided
        if output is None:
            output = json_file.parent / f"{json_file.stem}.pptx"
        
        # Generate PowerPoint
        with console.status(f"[bold green]Generating PowerPoint from {json_file.name}..."):
            output_path = generator.generate_from_json_file(json_file, output)
        
        # Display success message
        console.print(Panel(
            f"✅ PowerPoint successfully generated!",
            title="Success",
            border_style="green"
        ))
        
        console.print(f"\n📁 Saved to: [cyan]{output_path}[/cyan]")
        
        # Open file if requested
        if open_file:
            import platform
            import subprocess
            
            system = platform.system()
            if system == "Darwin":  # macOS
                subprocess.run(["open", str(output_path)])
            elif system == "Windows":
                subprocess.run(["start", "", str(output_path)], shell=True)
            elif system == "Linux":
                subprocess.run(["xdg-open", str(output_path)])
            
            console.print("[green]✓[/green] Opening PowerPoint file...")
    
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] Failed to generate PowerPoint: {e}")
        if debug:
            logger.exception("Detailed error:")
        raise typer.Exit(1)


@app.command()
def full_pipeline(
    input_file: Optional[Path] = typer.Option(
        None,
        "--input", "-i",
        help="Path to input text file",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True
    ),
    text: Optional[str] = typer.Option(
        None,
        "--text", "-t",
        help="Direct text input (alternative to file)"
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output", "-o",
        help="Output PowerPoint file path"
    ),
    save_json: bool = typer.Option(
        False,
        "--save-json",
        help="Save intermediate JSON file"
    ),
    open_file: bool = typer.Option(
        False,
        "--open",
        help="Open the PowerPoint file after generation"
    ),
    no_refine: bool = typer.Option(
        False,
        "--no-refine",
        help="Skip JSON refinement step"
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        help="Enable debug logging"
    )
):
    """Complete pipeline: Text → JSON → PowerPoint."""
    
    # Enable debug if requested
    if debug:
        logger.remove()
        logger.add(sys.stderr, level="DEBUG")
    
    # Validate input
    if not input_file and not text:
        console.print("[red]Error:[/red] Provide either --input file or --text")
        raise typer.Exit(1)
    
    if input_file and text:
        console.print("[red]Error:[/red] Provide either --input or --text, not both")
        raise typer.Exit(1)
    
    # Check API key
    if not config.validate_api_key():
        console.print(Panel(
            "[red]Mistral API key not found![/red]\n\n"
            "Please set your API key in the .env file:\n"
            "MISTRAL_API_KEY=your_key_here",
            title="Configuration Error",
            border_style="red"
        ))
        raise typer.Exit(1)
    
    try:
        # Step 1: Convert text to JSON
        console.print("\n[bold]Step 1: Converting text to JSON...[/bold]")
        
        with console.status("[bold green]Initializing converter..."):
            converter = PowerPointConverter()
        
        # Determine JSON output path
        if save_json:
            if input_file:
                json_path = config.output.output_dir / f"{input_file.stem}_presentation.json"
            else:
                json_path = config.output.output_dir / "presentation.json"
        else:
            json_path = None
        
        # Convert based on input type
        if input_file:
            with console.status(f"[bold green]Converting {input_file.name}..."):
                presentation = converter.convert_file(
                    input_file=input_file,
                    output_file=json_path,
                    refine=not no_refine,
                    validate=True
                )
        else:
            with console.status("[bold green]Converting text..."):
                presentation = converter.convert_text(
                    text=text,
                    output_file=json_path,
                    refine=not no_refine,
                    validate=True
                )
        
        console.print(f"[green]✓[/green] Generated {presentation.metadata.total_slides} slides")
        
        # Step 2: Convert JSON to PowerPoint
        console.print("\n[bold]Step 2: Generating PowerPoint presentation...[/bold]")
        
        with console.status("[bold green]Creating PowerPoint..."):
            generator = PowerPointGenerator()
            
            # Determine PowerPoint output path
            if output is None:
                if input_file:
                    output = config.output.output_dir / f"{input_file.stem}.pptx"
                else:
                    output = config.output.output_dir / "presentation.pptx"
            
            # Generate PowerPoint from presentation object
            pptx_path = generator.generate_from_json(presentation.model_dump(), output)
        
        # Display success
        console.print(Panel(
            f"✅ Successfully generated PowerPoint with {presentation.metadata.total_slides} slides!",
            title="Pipeline Complete",
            border_style="green"
        ))
        
        # Display presentation info
        _display_presentation_info(presentation)
        
        console.print(f"\n📁 PowerPoint saved to: [cyan]{pptx_path}[/cyan]")
        if json_path:
            console.print(f"📄 JSON saved to: [cyan]{json_path}[/cyan]")
        
        # Open file if requested
        if open_file:
            import platform
            import subprocess
            
            system = platform.system()
            if system == "Darwin":  # macOS
                subprocess.run(["open", str(pptx_path)])
            elif system == "Windows":
                subprocess.run(["start", "", str(pptx_path)], shell=True)
            elif system == "Linux":
                subprocess.run(["xdg-open", str(pptx_path)])
            
            console.print("[green]✓[/green] Opening PowerPoint file...")
    
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        if debug:
            logger.exception("Detailed error:")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()