"""
Analytics routes for retrieving user statistics and chart data.
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Body
from pydantic import BaseModel

import os
from fastapi import Header

from services.analytics_service import analytics_service
from api.routes.auth import get_current_user, TelegramUser

router = APIRouter()
logger = logging.getLogger(__name__)


def verify_bot_token(x_bot_token: str = Header(None, alias="X-Bot-Token")) -> bool:
    """
    Verify bot token for internal API calls.
    
    Args:
        x_bot_token: Bot token from header
        
    Returns:
        True if valid, False otherwise
    """
    expected_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not expected_token:
        return False
    return x_bot_token == expected_token


class TrackMessageRequest(BaseModel):
    """Request model for tracking a message."""
    message_type: str  # "voice" or "text"


class TrackErrorsRequest(BaseModel):
    """Request model for tracking errors."""
    errors: str


@router.get("/analytics/{user_id}")
async def get_user_analytics(
    user_id: int,
    current_user: TelegramUser = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get analytics data for a specific user.
    
    Args:
        user_id: Telegram user ID
        current_user: Validated Telegram user from auth
        
    Returns:
        User analytics data
        
    Raises:
        HTTPException: If user_id doesn't match authenticated user or no data found
    """
    # Verify user can only access their own data
    if user_id != current_user.id:
        logger.warning(f"User {current_user.id} tried to access data for user {user_id}")
        raise HTTPException(
            status_code=403,
            detail="You can only access your own analytics data"
        )
    
    # Get analytics data
    analytics_data = analytics_service.get_user_analytics(user_id)
    
    if not analytics_data:
        logger.info(f"No analytics data found for user {user_id}")
        # Return empty data structure instead of error
        return {
            "user_id": user_id,
            "total_messages": 0,
            "voice_messages": 0,
            "text_messages": 0,
            "total_errors": 0,
            "error_types": {},
            "practice_days": [],
            "streak": 0,
            "daily_activity": {},
            "error_rate": 0.0,
            "messages_this_week": 0
        }
    
    logger.info(f"Returning analytics for user {user_id}")
    return {
        "user_id": user_id,
        **analytics_data
    }


@router.get("/charts/{user_id}")
async def get_chart_data(
    user_id: int,
    days: int = 7,
    current_user: TelegramUser = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get chart data for a specific user.
    
    Args:
        user_id: Telegram user ID
        days: Number of days to include (default: 7)
        current_user: Validated Telegram user from auth
        
    Returns:
        Chart data (daily activity, error types)
        
    Raises:
        HTTPException: If user_id doesn't match authenticated user
    """
    # Verify user can only access their own data
    if user_id != current_user.id:
        logger.warning(f"User {current_user.id} tried to access chart data for user {user_id}")
        raise HTTPException(
            status_code=403,
            detail="You can only access your own chart data"
        )
    
    # Validate days parameter
    if days < 1 or days > 30:
        raise HTTPException(
            status_code=400,
            detail="Days parameter must be between 1 and 30"
        )
    
    # Get chart data
    chart_data = analytics_service.get_chart_data(user_id, days)
    
    logger.info(f"Returning chart data for user {user_id} ({days} days)")
    return {
        "user_id": user_id,
        "days": days,
        **chart_data
    }


@router.get("/stats/summary")
async def get_summary_stats(
    current_user: TelegramUser = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get summary statistics for the authenticated user.
    Convenience endpoint that combines analytics and recent chart data.
    
    Args:
        current_user: Validated Telegram user from auth
        
    Returns:
        Summary statistics
    """
    user_id = current_user.id
    
    # Get both analytics and chart data
    analytics_data = analytics_service.get_user_analytics(user_id)
    chart_data = analytics_service.get_chart_data(user_id, days=7)
    
    if not analytics_data:
        analytics_data = {
            "total_messages": 0,
            "voice_messages": 0,
            "text_messages": 0,
            "total_errors": 0,
            "error_types": {},
            "streak": 0,
            "error_rate": 0.0,
            "messages_this_week": 0
        }
    
    return {
        "user_id": user_id,
        "summary": {
            "total_messages": analytics_data.get("total_messages", 0),
            "messages_this_week": analytics_data.get("messages_this_week", 0),
            "total_errors": analytics_data.get("total_errors", 0),
            "error_rate": analytics_data.get("error_rate", 0.0),
            "streak": analytics_data.get("streak", 0)
        },
        "recent_activity": chart_data.get("daily", []),
        "error_breakdown": chart_data.get("error_types", {})
    }


@router.post("/analytics/{user_id}/track-message")
async def track_message(
    user_id: int,
    request: TrackMessageRequest = Body(...),
    x_bot_token: str = Header(None, alias="X-Bot-Token")
) -> Dict[str, Any]:
    """
    Track a message for analytics.
    Called by bot with X-Bot-Token header.
    
    Args:
        user_id: Telegram user ID
        request: Message tracking request
        x_bot_token: Bot token for authentication
        
    Returns:
        Success status
    """
    # Verify bot token (required for this endpoint)
    if not x_bot_token or not verify_bot_token(x_bot_token):
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing bot token"
        )
    
    # Track the message
    analytics_service.track_message(user_id, request.message_type)
    
    logger.info(f"Tracked {request.message_type} message for user {user_id}")
    return {
        "status": "ok",
        "message": f"Tracked {request.message_type} message"
    }


@router.post("/analytics/{user_id}/track-errors")
async def track_errors(
    user_id: int,
    request: TrackErrorsRequest = Body(...),
    x_bot_token: str = Header(None, alias="X-Bot-Token")
) -> Dict[str, Any]:
    """
    Track grammar errors for analytics.
    Called by bot with X-Bot-Token header.
    
    Args:
        user_id: Telegram user ID
        request: Error tracking request
        x_bot_token: Bot token for authentication
        
    Returns:
        Success status
    """
    # Verify bot token (required for this endpoint)
    if not x_bot_token or not verify_bot_token(x_bot_token):
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing bot token"
        )
    
    # Track the errors
    analytics_service.track_errors(user_id, request.errors)
    
    logger.info(f"Tracked errors for user {user_id}")
    return {
        "status": "ok",
        "message": "Tracked errors"
    }

