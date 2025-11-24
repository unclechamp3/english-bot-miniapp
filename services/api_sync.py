"""
Service for syncing analytics data to the remote API.
"""

import logging
import aiohttp
from typing import Optional
from config import Config

logger = logging.getLogger(__name__)


async def sync_message_to_api(user_id: int, message_type: str) -> bool:
    """
    Sync a message tracking event to the remote API.
    
    Args:
        user_id: Telegram user ID
        message_type: "voice" or "text"
        
    Returns:
        True if successful, False otherwise
    """
    if not Config.API_URL:
        # API URL not configured, skip sync
        return False
    
    try:
        url = f"{Config.API_URL}/api/analytics/{user_id}/track-message"
        payload = {"message_type": message_type}
        headers = {
            "X-Bot-Token": Config.TELEGRAM_BOT_TOKEN
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as response:
                if response.status == 200:
                    logger.info(f"Synced {message_type} message to API for user {user_id}")
                    return True
                else:
                    error_text = await response.text()
                    logger.warning(f"Failed to sync message to API: {response.status} - {error_text}")
                    return False
    except Exception as e:
        logger.error(f"Error syncing message to API: {e}")
        return False


async def sync_errors_to_api(user_id: int, errors: str) -> bool:
    """
    Sync grammar errors to the remote API.
    
    Args:
        user_id: Telegram user ID
        errors: Error text from grammar checker
        
    Returns:
        True if successful, False otherwise
    """
    if not Config.API_URL:
        # API URL not configured, skip sync
        return False
    
    try:
        url = f"{Config.API_URL}/api/analytics/{user_id}/track-errors"
        payload = {"errors": errors}
        headers = {
            "X-Bot-Token": Config.TELEGRAM_BOT_TOKEN
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as response:
                if response.status == 200:
                    logger.info(f"Synced errors to API for user {user_id}")
                    return True
                else:
                    error_text = await response.text()
                    logger.warning(f"Failed to sync errors to API: {response.status} - {error_text}")
                    return False
    except Exception as e:
        logger.error(f"Error syncing errors to API: {e}")
        return False

