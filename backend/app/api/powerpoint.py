"""API endpoints for PowerPoint generation."""

from fastapi import APIRouter, HTTPException, Depends, Body
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
from pathlib import Path
from loguru import logger

from ..services.powerpoint_service import powerpoint_service
from ..utils.dependencies import get_current_user
from ..models.user import User


router = APIRouter(prefix="/powerpoint", tags=["powerpoint"])


class GenerateFromTextRequest(BaseModel):
    """Request model for text to PowerPoint generation."""
    text: str
    filename: Optional[str] = None


class GenerateFromJSONRequest(BaseModel):
    """Request model for JSON to PowerPoint generation."""
    json_data: Dict[str, Any]
    filename: Optional[str] = None


@router.post("/generate-from-text")
async def generate_from_text(
    request: GenerateFromTextRequest,
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    Generate PowerPoint presentation from text.
    
    Args:
        request: Text and optional filename
        current_user: Current authenticated user (optional)
        
    Returns:
        Generation result with file metadata
    """
    try:
        user_id = current_user.id if current_user else None
        
        result = await powerpoint_service.generate_from_text(
            text=request.text,
            filename=request.filename,
            user_id=user_id
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("error", "Generation failed"))
        
        return result
        
    except Exception as e:
        logger.error(f"Error generating PowerPoint from text: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-from-json")
async def generate_from_json(
    request: GenerateFromJSONRequest,
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    Generate PowerPoint presentation from JSON structure.
    
    Args:
        request: JSON data and optional filename
        current_user: Current authenticated user (optional)
        
    Returns:
        Generation result with file metadata
    """
    try:
        user_id = current_user.id if current_user else None
        
        result = await powerpoint_service.generate_from_json(
            json_data=request.json_data,
            filename=request.filename,
            user_id=user_id
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("error", "Generation failed"))
        
        return result
        
    except Exception as e:
        logger.error(f"Error generating PowerPoint from JSON: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download/{file_path:path}")
async def download_powerpoint(
    file_path: str,
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    Download generated PowerPoint file.
    
    Args:
        file_path: Relative path to the file
        current_user: Current authenticated user (optional)
        
    Returns:
        File response with PowerPoint
    """
    try:
        # Construct full path
        base_path = Path(__file__).parent.parent.parent
        full_path = base_path / file_path
        
        # Security check - ensure file is in uploads directory
        uploads_dir = base_path / "uploads"
        if not full_path.resolve().is_relative_to(uploads_dir.resolve()):
            raise HTTPException(status_code=403, detail="Access denied")
        
        if not full_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        # If user is authenticated, check if they have access
        if current_user:
            user_id = current_user.id
            user_dir = uploads_dir / "powerpoints" / str(user_id)
            if user_dir.exists() and not full_path.resolve().is_relative_to(user_dir.resolve()):
                # File is not in user's directory, deny access
                raise HTTPException(status_code=403, detail="Access denied")
        
        return FileResponse(
            path=full_path,
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            filename=full_path.name
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading PowerPoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-from-chat-message")
async def generate_from_chat_message(
    content: str = Body(..., embed=True),
    filename: Optional[str] = Body(None, embed=True),
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    Generate PowerPoint from a chat message.
    This endpoint is designed to be called from the chat interface.
    
    Args:
        content: The chat message content to convert
        filename: Optional filename for the presentation
        current_user: Current authenticated user (optional)
        
    Returns:
        Generation result with file metadata
    """
    try:
        user_id = current_user.id if current_user else None
        
        # Extract PowerPoint content from the message
        # The user might say something like "Create a presentation about X"
        # We need to extract the actual content
        
        # Simple extraction: if the message starts with certain keywords, 
        # remove them to get the actual content
        trigger_phrases = [
            "create a presentation about",
            "generate a powerpoint about",
            "make a presentation on",
            "create powerpoint for",
            "generate presentation for",
            "faire une présentation sur",
            "créer un powerpoint sur"
        ]
        
        clean_content = content.lower()
        for phrase in trigger_phrases:
            if clean_content.startswith(phrase):
                content = content[len(phrase):].strip()
                break
        
        result = await powerpoint_service.generate_from_text(
            text=content,
            filename=filename,
            user_id=user_id
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("error", "Generation failed"))
        
        # Add download URL to result
        if result.get("relative_path"):
            result["download_url"] = f"/api/powerpoint/download/{result['relative_path']}"
        
        return result
        
    except Exception as e:
        logger.error(f"Error generating PowerPoint from chat: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))