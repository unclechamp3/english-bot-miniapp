"""
Authentication routes for validating Telegram WebApp requests.
"""

import hashlib
import hmac
import logging
from urllib.parse import parse_qs, unquote
from typing import Optional

from fastapi import APIRouter, Header, HTTPException, Depends
from pydantic import BaseModel

import os

router = APIRouter()
logger = logging.getLogger(__name__)


class TelegramUser(BaseModel):
    """Validated Telegram user data."""
    id: int
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    language_code: Optional[str] = None


def validate_telegram_webapp_data(init_data: str) -> Optional[TelegramUser]:
    """
    Validate Telegram WebApp initData.
    
    Args:
        init_data: Raw initData string from Telegram WebApp
        
    Returns:
        TelegramUser if valid, None otherwise
    """
    try:
        if not init_data or not init_data.strip():
            logger.warning("Empty initData received")
            return None
            
        logger.info(f"Validating initData (length: {len(init_data)})")
        
        # Parse init_data
        parsed_data = parse_qs(init_data)
        logger.debug(f"Parsed data keys: {list(parsed_data.keys())}")
        
        # Extract hash
        received_hash = parsed_data.get('hash', [None])[0]
        if not received_hash:
            logger.warning("No hash in initData")
            return None
        
        # Remove hash from data for validation
        data_check_string_parts = []
        for key in sorted(parsed_data.keys()):
            if key == 'hash':
                continue
            value = parsed_data[key][0]
            data_check_string_parts.append(f"{key}={value}")
        
        data_check_string = '\n'.join(data_check_string_parts)
        logger.debug(f"Data check string: {data_check_string[:100]}...")
        
        # Calculate expected hash
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not bot_token:
            logger.error("TELEGRAM_BOT_TOKEN not set in environment")
            return None
        
        logger.debug(f"Bot token found (length: {len(bot_token)})")
        
        secret_key = hmac.new(
            key=b"WebAppData",
            msg=bot_token.encode(),
            digestmod=hashlib.sha256
        ).digest()
        
        expected_hash = hmac.new(
            key=secret_key,
            msg=data_check_string.encode(),
            digestmod=hashlib.sha256
        ).hexdigest()
        
        logger.debug(f"Hash comparison: received={received_hash[:20]}..., expected={expected_hash[:20]}...")
        
        # Validate hash
        if received_hash != expected_hash:
            logger.warning(f"Invalid hash in initData. Received: {received_hash[:20]}..., Expected: {expected_hash[:20]}...")
            return None
        
        # Extract user data
        user_json = parsed_data.get('user', [None])[0]
        if not user_json:
            logger.warning("No user data in initData")
            return None
        
        # Parse user JSON
        import json
        user_data = json.loads(unquote(user_json))
        logger.info(f"Successfully validated user: {user_data.get('id')}")
        
        return TelegramUser(**user_data)
        
    except Exception as e:
        logger.error(f"Error validating initData: {e}", exc_info=True)
        return None


async def get_current_user(
    x_telegram_init_data: str = Header(None, alias="X-Telegram-Init-Data")
) -> TelegramUser:
    """
    Dependency to get and validate current Telegram user.
    
    Args:
        x_telegram_init_data: Telegram initData from request header
        
    Returns:
        Validated TelegramUser
        
    Raises:
        HTTPException: If validation fails
    """
    if not x_telegram_init_data:
        logger.warning("Missing X-Telegram-Init-Data header")
        raise HTTPException(
            status_code=401,
            detail="Missing Telegram authentication data"
        )
    
    logger.info(f"Received initData header (length: {len(x_telegram_init_data)})")
    user = validate_telegram_webapp_data(x_telegram_init_data)
    if not user:
        logger.warning("Validation failed for initData")
        raise HTTPException(
            status_code=401,
            detail="Invalid Telegram authentication data. Please check logs for details."
        )
    
    return user


@router.post("/validate")
async def validate_auth(user: TelegramUser = Depends(get_current_user)):
    """
    Validate Telegram WebApp authentication.
    
    Returns:
        User data if authentication is valid
    """
    logger.info(f"Validated user: {user.id} ({user.first_name})")
    return {
        "status": "ok",
        "user": user.dict()
    }

