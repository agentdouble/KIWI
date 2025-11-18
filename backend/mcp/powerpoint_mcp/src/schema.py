"""Flexible JSON schemas for PowerPoint slides using Pydantic."""

from typing import List, Optional, Union, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, field_validator


class LayoutType(str, Enum):
    """Types of slide layouts available."""
    TITLE_SLIDE = "title_slide"
    BULLET_POINTS = "bullet_points"
    TABLE = "table"
    TEXT_HEAVY = "text_heavy"
    COMPARISON = "comparison"
    PROCESS_FLOW = "process_flow"
    MIXED = "mixed"


class SubBullet(BaseModel):
    """Sub-bullet point in a bullet list."""
    text: str
    level: int = 2


class BulletPoint(BaseModel):
    """Main bullet point with optional sub-bullets."""
    text: str
    sub_bullets: Optional[List[Union[str, SubBullet]]] = None


class BulletPointsContent(BaseModel):
    """Content for bullet points layout."""
    bullets: List[BulletPoint]
    intro_text: Optional[str] = None


class TableContent(BaseModel):
    """Content for table layout."""
    headers: List[str]
    rows: List[List[str]]
    caption: Optional[str] = None
    
    @field_validator('rows')
    def validate_rows(cls, rows, info):
        """Ensure all rows have the same number of columns as headers."""
        if 'headers' in info.data:
            headers = info.data['headers']
            for i, row in enumerate(rows):
                if len(row) != len(headers):
                    raise ValueError(f"Row {i} has {len(row)} columns, expected {len(headers)}")
        return rows


class TextHeavyContent(BaseModel):
    """Content for text-heavy slides."""
    paragraphs: List[str]
    key_points: Optional[List[str]] = None
    emphasis: Optional[str] = None


class ComparisonSide(BaseModel):
    """One side of a comparison."""
    title: str
    points: List[str]
    color: Optional[str] = None


class ComparisonContent(BaseModel):
    """Content for comparison layout."""
    left: ComparisonSide
    right: ComparisonSide
    comparison_title: Optional[str] = None


class ProcessStep(BaseModel):
    """A step in a process flow."""
    title: str
    description: Optional[str] = None
    order: int
    connected_to: Optional[int] = None


class ProcessFlowContent(BaseModel):
    """Content for process flow layout."""
    steps: List[ProcessStep]
    flow_type: str = "linear"  # linear, circular, branched
    
    @field_validator('steps')
    def validate_order(cls, steps):
        """Ensure steps have unique orders."""
        orders = [step.order for step in steps]
        if len(orders) != len(set(orders)):
            raise ValueError("Process steps must have unique order numbers")
        return steps


class MixedContent(BaseModel):
    """Mixed content that can contain multiple elements."""
    elements: List[Dict[str, Any]]
    layout_hint: Optional[str] = None


class Slide(BaseModel):
    """Individual slide with flexible content."""
    id: int
    title: str
    layout_type: LayoutType
    content: Union[
        BulletPointsContent,
        TableContent,
        TextHeavyContent,
        ComparisonContent,
        ProcessFlowContent,
        MixedContent,
        Dict[str, Any]  # Allow raw dict for maximum flexibility
    ]
    notes: Optional[str] = None
    transition: Optional[str] = None
    duration_seconds: Optional[int] = None
    
    class Config:
        use_enum_values = True


class PresentationMetadata(BaseModel):
    """Metadata about the presentation."""
    total_slides: int
    estimated_duration_minutes: Optional[float] = None
    theme_suggestion: Optional[str] = None
    audience_level: Optional[str] = None
    main_topics: Optional[List[str]] = None
    created_by: str = "Mistral AI"
    version: str = "1.0"


class Presentation(BaseModel):
    """Complete presentation structure."""
    title: str
    subtitle: Optional[str] = None
    slides: List[Slide]
    metadata: PresentationMetadata
    
    @field_validator('slides')
    def validate_slide_ids(cls, slides):
        """Ensure slide IDs are unique and sequential."""
        ids = [slide.id for slide in slides]
        expected_ids = list(range(1, len(slides) + 1))
        if ids != expected_ids:
            raise ValueError("Slide IDs must be sequential starting from 1")
        return slides
    
    def to_json(self, indent: int = 2) -> str:
        """Export presentation to JSON string."""
        return self.model_dump_json(indent=indent, exclude_none=True)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Presentation':
        """Create presentation from JSON string."""
        return cls.model_validate_json(json_str)


