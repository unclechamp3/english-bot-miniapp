"""
Handler for text messages.
Process text messages similar to voice, but without STT/TTS.
"""

import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.enums import ChatAction

from services.openai_service import openai_service
from services.grammar_checker import grammar_checker
from services.context_manager import context_manager
from services.analytics_service import analytics_service

router = Router()
logger = logging.getLogger(__name__)


@router.message(F.text & ~F.text.startswith('/'))
async def handle_text_message(message: Message):
    """
    Handle text messages from users.
    
    Pipeline:
    1. Get text from message
    2. Check grammar
    3. Generate response using GPT
    4. Send text reply
    """
    
    user_id = message.from_user.id
    user_text = message.text
    
    # Check if user has a profile
    if not context_manager.has_profile(user_id):
        await message.answer(
            "Please start with /start to create your profile first! 😊"
        )
        return
    
    try:
        # Show typing indicator
        await message.bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
        
        logger.info(f"Processing text message from user {user_id}: {user_text}")
        
        # Step 1: Track message in analytics (local + sync to API)
        analytics_service.track_message(user_id, "text")
        # Sync to remote API if configured
        from services.api_sync import sync_message_to_api
        await sync_message_to_api(user_id, "text")
        
        # Step 2: Check grammar
        grammar_errors = await grammar_checker.check_grammar(user_text)
        
        # If there are grammar errors, send them to the user
        if grammar_errors:
            error_message = f"📝 <b>Your message:</b>\n{user_text}\n\n"
            error_message += f"❌ <b>Grammar check:</b>\n{grammar_errors}\n\n"
            error_message += "I'll respond anyway... 😊"
            
            await message.answer(error_message)
            
            # Track errors in analytics (local + sync to API)
            analytics_service.track_errors(user_id, grammar_errors)
            # Sync to remote API if configured
            from services.api_sync import sync_errors_to_api
            await sync_errors_to_api(user_id, grammar_errors)
        
        # Step 3: Add to conversation context
        context_manager.add_user_message(user_id, user_text)
        
        # Step 4: Generate response
        await message.bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
        
        # Get user profile for personalization
        profile = context_manager.get_user_profile(user_id)
        
        # Get conversation history
        conversation_history = context_manager.get_conversation_history(user_id)
        
        response_text = await openai_service.generate_chat_response(
            user_message=user_text,
            conversation_history=conversation_history,
            user_profile=profile
        )
        
        # Add assistant response to context
        context_manager.add_assistant_message(user_id, response_text)
        
        # Step 5: Send text reply
        await message.answer(response_text)
        
        logger.info(f"Successfully processed text message for user {user_id}")
        
    except Exception as e:
        logger.error(f"Error processing text message: {e}", exc_info=True)
        await message.answer(
            "😔 Sorry, an error occurred while processing your message. "
            "Please try again!"
        )

