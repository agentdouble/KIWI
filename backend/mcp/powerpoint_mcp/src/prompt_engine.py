"""Prompt engineering system for optimal JSON generation."""

from typing import List, Dict, Any, Optional
import json
from src.schema import LayoutType


class PromptEngine:
    """Manages prompts for Mistral to generate PowerPoint JSON."""
    
    @staticmethod
    def get_system_prompt() -> str:
        """Get the main system prompt."""
        return """You are an expert PowerPoint presentation designer and content structurer. 
Your task is to convert text content into a well-structured JSON format for PowerPoint presentations.

You must:
1. Analyze the input text and determine the best slide structure
2. Choose appropriate layout types for each slide based on content
3. Create a logical flow of information
4. Output valid JSON that follows the provided schema
5. Make intelligent decisions about content formatting (bullets, tables, comparisons, etc.)
6. IMPORTANT: Generate ALL content (title, slides, text) in the SAME LANGUAGE as the input text

Available layout types:
- title_slide: For presentation title and introduction
- bullet_points: For lists, key points, features
- table: For structured data, comparisons, specifications  
- text_heavy: For detailed explanations, quotes, definitions
- comparison: For pros/cons, before/after, alternatives
- process_flow: For steps, workflows, timelines
- mixed: For complex slides with multiple elements

Remember: 
- Each slide MUST have a title
- Content structure should match the layout type
- ALL text must be in the same language as the input
- Output ONLY valid JSON, no additional text or explanations"""
    
    @staticmethod
    def get_schema_prompt() -> str:
        """Get prompt explaining the JSON schema."""
        return """The JSON structure must follow this format:

{
  "title": "Presentation Title",
  "subtitle": "Optional Subtitle",
  "slides": [
    {
      "id": 1,
      "title": "Slide Title (REQUIRED)",
      "layout_type": "layout_type_here",
      "content": {
        // Content structure depends on layout_type
      },
      "notes": "Optional speaker notes",
      "transition": "Optional transition type"
    }
  ],
  "metadata": {
    "total_slides": number,
    "estimated_duration_minutes": number,
    "theme_suggestion": "Professional/Creative/Minimal/etc",
    "audience_level": "Beginner/Intermediate/Advanced",
    "main_topics": ["topic1", "topic2"]
  }
}

Content structures by layout type:

For bullet_points:
"content": {
  "bullets": [
    {
      "text": "Main point",
      "sub_bullets": ["Sub point 1", "Sub point 2"]
    }
  ],
  "intro_text": "Optional introduction"
}

For table:
"content": {
  "headers": ["Column 1", "Column 2"],
  "rows": [
    ["Row 1 Col 1", "Row 1 Col 2"],
    ["Row 2 Col 1", "Row 2 Col 2"]
  ],
  "caption": "Optional caption"
}

For comparison:
"content": {
  "left": {
    "title": "Option A",
    "points": ["Point 1", "Point 2"]
  },
  "right": {
    "title": "Option B", 
    "points": ["Point 1", "Point 2"]
  },
  "comparison_title": "Optional comparison title"
}

For process_flow:
"content": {
  "steps": [
    {
      "title": "Step 1",
      "description": "Description",
      "order": 1
    }
  ],
  "flow_type": "linear"
}

For text_heavy:
"content": {
  "paragraphs": ["Paragraph 1", "Paragraph 2"],
  "key_points": ["Key point 1", "Key point 2"],
  "emphasis": "Important point to emphasize"
}"""
    
    @staticmethod
    def get_analysis_prompt(text_length: int) -> str:
        """Get prompt for content analysis."""
        estimated_slides = min(max(3, text_length // 500), 20)
        
        return f"""Analyze this content and create a presentation with approximately {estimated_slides} slides.

Consider:
1. Break content into logical sections
2. Identify key points, data, and relationships
3. Determine which content needs tables, comparisons, or process flows
4. Create a compelling narrative flow
5. Add a title slide and conclusion slide
6. Ensure each slide has a clear purpose and isn't overloaded

Guidelines:
- Bullet points: Maximum 5-7 bullets per slide, 2-3 sub-bullets each
- Tables: Maximum 5-6 rows for readability
- Process flows: Maximum 6-8 steps
- Text heavy: Use sparingly, only for crucial context
- Comparisons: Use for clear either/or scenarios
- Mixed: Use when content doesn't fit other layouts

Make the presentation engaging and professional."""
    
    @staticmethod
    def get_examples() -> List[Dict[str, str]]:
        """Get few-shot examples for better generation."""
        return [
            {
                "user": "Create a presentation about project management basics",
                "assistant": json.dumps({
                    "title": "Project Management Fundamentals",
                    "subtitle": "Essential Concepts and Best Practices",
                    "slides": [
                        {
                            "id": 1,
                            "title": "Project Management Fundamentals",
                            "layout_type": "title_slide",
                            "content": {
                                "subtitle": "Essential Concepts and Best Practices",
                                "presenter": "Your Organization"
                            }
                        },
                        {
                            "id": 2,
                            "title": "What is Project Management?",
                            "layout_type": "bullet_points",
                            "content": {
                                "bullets": [
                                    {
                                        "text": "Planning, organizing, and managing resources",
                                        "sub_bullets": ["Time", "Budget", "People"]
                                    },
                                    {
                                        "text": "Achieving specific goals and objectives",
                                        "sub_bullets": ["Deliverables", "Milestones"]
                                    }
                                ]
                            }
                        },
                        {
                            "id": 3,
                            "title": "Project Lifecycle Phases",
                            "layout_type": "process_flow",
                            "content": {
                                "steps": [
                                    {"title": "Initiation", "description": "Define project goals", "order": 1},
                                    {"title": "Planning", "description": "Create project plan", "order": 2},
                                    {"title": "Execution", "description": "Implement the plan", "order": 3},
                                    {"title": "Monitoring", "description": "Track progress", "order": 4},
                                    {"title": "Closure", "description": "Complete and review", "order": 5}
                                ],
                                "flow_type": "linear"
                            }
                        }
                    ],
                    "metadata": {
                        "total_slides": 3,
                        "estimated_duration_minutes": 5,
                        "theme_suggestion": "Professional",
                        "audience_level": "Beginner",
                        "main_topics": ["project management", "lifecycle", "fundamentals"]
                    }
                }, indent=2)
            }
        ]
    
    @staticmethod
    def create_conversion_prompt(text: str) -> str:
        """Create the main conversion prompt."""
        return f"""Convert the following text into a PowerPoint presentation JSON:

TEXT TO CONVERT:
{text}

Remember to:
1. Create a compelling title slide
2. Break content into digestible slides
3. Choose the most appropriate layout for each slide's content
4. Maintain logical flow
5. Add a conclusion or summary slide if appropriate
6. GENERATE ALL CONTENT IN THE SAME LANGUAGE AS THE INPUT TEXT
7. Output ONLY valid JSON"""
    
    @staticmethod
    def get_refinement_prompt(json_str: str) -> str:
        """Get prompt to refine generated JSON."""
        return f"""Review and improve this PowerPoint JSON if needed:

{json_str}

Check for:
1. All slides have titles
2. Content matches layout types
3. No slides are too dense (max 7 bullet points, 6 table rows)
4. Logical flow between slides
5. Valid JSON structure

Output the refined JSON only."""
    
    @staticmethod
    def suggest_layout_type(content: str) -> LayoutType:
        """Suggest best layout type for given content."""
        content_lower = content.lower()
        
        # Check for specific patterns
        if any(word in content_lower for word in ["step", "process", "phase", "stage", "workflow"]):
            return LayoutType.PROCESS_FLOW
        elif any(word in content_lower for word in ["vs", "versus", "comparison", "pros and cons", "advantages"]):
            return LayoutType.COMPARISON
        elif any(word in content_lower for word in ["table", "data", "statistics", "metrics", "numbers"]):
            return LayoutType.TABLE
        elif content_lower.count('\n') > 5 or any(word in content_lower for word in ["list", "points", "features"]):
            return LayoutType.BULLET_POINTS
        elif len(content) > 500:
            return LayoutType.TEXT_HEAVY
        else:
            return LayoutType.BULLET_POINTS