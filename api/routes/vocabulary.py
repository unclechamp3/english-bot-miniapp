"""
Vocabulary routes for managing user vocabulary.
"""

import logging
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, Depends, Body
from pydantic import BaseModel

from services.vocabulary_service import vocabulary_service
from api.routes.auth import get_current_user, TelegramUser

router = APIRouter()
logger = logging.getLogger(__name__)


class AddWordRequest(BaseModel):
    """Request model for adding a word."""
    word: str


class ReviewWordRequest(BaseModel):
    """Request model for reviewing a word."""
    word: str
    correct: bool  # True if user knew the word, False if forgot


@router.get("/vocabulary/{user_id}")
async def get_user_vocabulary(
    user_id: int,
    status: str = None,
    current_user: TelegramUser = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get user's vocabulary, optionally filtered by status.
    
    Args:
        user_id: Telegram user ID
        status: Optional status filter (new, learning, mastered)
        current_user: Validated Telegram user from auth
        
    Returns:
        User vocabulary data
    """
    # Verify user can only access their own data
    if user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can only access your own vocabulary"
        )
    
    # Get words
    words = vocabulary_service.get_user_words(user_id, status)
    stats = vocabulary_service.get_stats(user_id)
    
    return {
        "user_id": user_id,
        "words": words,
        "stats": stats
    }


@router.get("/vocabulary/{user_id}/due")
async def get_due_words(
    user_id: int,
    limit: int = 5,
    current_user: TelegramUser = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get words due for review.
    
    Args:
        user_id: Telegram user ID
        limit: Maximum number of words to return
        current_user: Validated Telegram user from auth
        
    Returns:
        Due words list
    """
    # Verify user can only access their own data
    if user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can only access your own vocabulary"
        )
    
    # Get due words
    due_words = vocabulary_service.get_due_words(user_id, limit)
    
    return {
        "user_id": user_id,
        "due_words": due_words,
        "count": len(due_words)
    }


@router.post("/vocabulary/{user_id}/add")
async def add_word(
    user_id: int,
    request: AddWordRequest = Body(...),
    current_user: TelegramUser = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Add a new word to user's vocabulary.
    
    Args:
        user_id: Telegram user ID
        request: Word to add
        current_user: Validated Telegram user from auth
        
    Returns:
        Added word data
    """
    # Verify user can only update their own data
    if user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can only update your own vocabulary"
        )
    
    # Add word
    try:
        word_data = await vocabulary_service.add_word(user_id, request.word)
        return {
            "status": "ok",
            "word": word_data
        }
    except Exception as e:
        logger.error(f"Error adding word: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error adding word: {str(e)}"
        )


@router.post("/vocabulary/{user_id}/review")
async def review_word(
    user_id: int,
    request: ReviewWordRequest = Body(...),
    current_user: TelegramUser = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Mark a word as reviewed (correct or forgot).
    
    Args:
        user_id: Telegram user ID
        request: Review data (word and result)
        current_user: Validated Telegram user from auth
        
    Returns:
        Success status
    """
    # Verify user can only update their own data
    if user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can only update your own vocabulary"
        )
    
    # Mark word as reviewed
    if request.correct:
        vocabulary_service.mark_word_correct(user_id, request.word)
    else:
        vocabulary_service.mark_word_forgot(user_id, request.word)
    
    return {
        "status": "ok",
        "message": f"Word '{request.word}' marked as {'correct' if request.correct else 'forgot'}"
    }


@router.delete("/vocabulary/{user_id}/{word}")
async def delete_word(
    user_id: int,
    word: str,
    current_user: TelegramUser = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Delete a word from user's vocabulary.
    
    Args:
        user_id: Telegram user ID
        word: Word to delete
        current_user: Validated Telegram user from auth
        
    Returns:
        Success status
    """
    # Verify user can only update their own data
    if user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can only update your own vocabulary"
        )
    
    # Delete word
    success = vocabulary_service.delete_word(user_id, word)
    
    if success:
        return {
            "status": "ok",
            "message": f"Word '{word}' deleted"
        }
    else:
        raise HTTPException(
            status_code=404,
            detail=f"Word '{word}' not found"
        )


@router.get("/vocabulary/{user_id}/stats")
async def get_vocabulary_stats(
    user_id: int,
    current_user: TelegramUser = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get vocabulary statistics for a user.
    
    Args:
        user_id: Telegram user ID
        current_user: Validated Telegram user from auth
        
    Returns:
        Vocabulary statistics
    """
    # Verify user can only access their own data
    if user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can only access your own vocabulary"
        )
    
    # Get stats
    stats = vocabulary_service.get_stats(user_id)
    
    return {
        "user_id": user_id,
        **stats
    }

