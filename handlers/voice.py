"""
Handler for voice messages.
Complete pipeline: STT -> Grammar Check -> Generate Response -> TTS
"""

import logging
import os
import tempfile
from pathlib import Path

from aiogram import Router, F, Bot
from aiogram.types import Message, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.enums import ChatAction

from services.openai_service import openai_service
from services.grammar_checker import grammar_checker
from services.context_manager import context_manager
from services.analytics_service import analytics_service

router = Router()
logger = logging.getLogger(__name__)

# Store bot's responses for transcription button
bot_responses = {}


@router.message(F.voice)
async def handle_voice_message(message: Message, bot: Bot):
    """
    Handle voice messages from users.
    
    Pipeline:
    1. Download voice message
    2. Transcribe using Whisper (STT)
    3. Check grammar
    4. Generate response using GPT
    5. Convert response to speech (TTS)
    6. Send voice reply
    """
    
    user_id = message.from_user.id
    
    try:
        # Show typing indicator
        await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
        
        # Create temp directory if it doesn't exist
        temp_dir = Path("temp")
        temp_dir.mkdir(exist_ok=True)
        
        # Step 1: Download voice message
        logger.info(f"Downloading voice message from user {user_id}")
        
        voice_file = await bot.get_file(message.voice.file_id)
        voice_file_path = temp_dir / f"voice_{user_id}_{message.message_id}.ogg"
        
        await bot.download_file(voice_file.file_path, destination=voice_file_path)
        
        # Step 2: Transcribe audio to text with context
        logger.info(f"Transcribing audio for user {user_id}")
        await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
        
        # Get conversation context for better transcription
        profile = context_manager.get_user_profile(user_id) if context_manager.has_profile(user_id) else None
        context = None
        if profile:
            # Build context from profile and recent conversation
            context = f"The speaker is interested in {profile.get('interests', 'various topics')}."
            recent_messages = context_manager.get_conversation_history(user_id)
            if recent_messages and len(recent_messages) > 0:
                # Get last few messages for context
                last_messages = recent_messages[-3:]  # Last 3 messages
                context += " Recent conversation: "
                context += " ".join([msg.get('content', '')[:50] for msg in last_messages])
        
        transcribed_text = await openai_service.transcribe_audio(str(voice_file_path), context=context)
        
        # Delete the downloaded voice file
        voice_file_path.unlink(missing_ok=True)
        
        if not transcribed_text:
            await message.answer("Извините, не удалось распознать речь. Попробуйте еще раз.")
            return
        
        logger.info(f"Transcribed text: {transcribed_text}")
        
        # Check if user has a profile (do this early)
        if not context_manager.has_profile(user_id):
            await message.answer(
                "Please start with /start to create your profile first! 😊"
            )
            return
        
        # Step 3: Add to conversation context and prepare data
        context_manager.add_user_message(user_id, transcribed_text)
        profile = context_manager.get_user_profile(user_id)
        conversation_history = context_manager.get_conversation_history(user_id)
        
        # Track voice message in analytics (local + sync to API)
        analytics_service.track_message(user_id, "voice")
        # Sync to remote API if configured
        from services.api_sync import sync_message_to_api
        await sync_message_to_api(user_id, "voice")
        
        # Step 4 & 5: Check grammar AND generate response IN PARALLEL! 🚀
        logger.info(f"Processing grammar check and response generation in parallel for user {user_id}")
        await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
        
        import asyncio
        
        # Launch BOTH tasks simultaneously
        grammar_task = grammar_checker.check_grammar(transcribed_text)
        response_task = openai_service.generate_chat_response(
            user_message=transcribed_text,
            conversation_history=conversation_history,
            user_profile=profile
        )
        
        # Wait for BOTH to complete (running in parallel)
        grammar_errors, response_text = await asyncio.gather(grammar_task, response_task)
        
        # If there are grammar errors, send them to the user
        if grammar_errors:
            error_message = f"📝 <b>Распознанный текст:</b>\n{transcribed_text}\n\n"
            error_message += f"❌ <b>Найдены ошибки:</b>\n{grammar_errors}\n\n"
            error_message += "Продолжаю диалог..."
            
            await message.answer(error_message)
            
            # Track errors in analytics (local + sync to API)
            analytics_service.track_errors(user_id, grammar_errors)
            # Sync to remote API if configured
            from services.api_sync import sync_errors_to_api
            await sync_errors_to_api(user_id, grammar_errors)
        
        # Add assistant response to context
        context_manager.add_assistant_message(user_id, response_text)
        
        # Step 6: Convert response to speech
        logger.info(f"Converting response to speech for user {user_id}")
        await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.RECORD_VOICE)
        
        tts_file_path = temp_dir / f"response_{user_id}_{message.message_id}.mp3"
        await openai_service.text_to_speech(response_text, str(tts_file_path))
        
        # Step 7: Send voice message with transcription button
        logger.info(f"Sending voice reply to user {user_id}")
        
        # Create inline keyboard with transcription button
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📝 Show text / Показать текст", callback_data=f"transcribe_{user_id}_{message.message_id}")]
        ])
        
        voice_file = FSInputFile(tts_file_path)
        sent_message = await message.answer_voice(voice=voice_file, reply_markup=keyboard)
        
        # Store response text for later transcription
        bot_responses[f"{user_id}_{message.message_id}"] = response_text
        
        # Clean up the generated audio file
        tts_file_path.unlink(missing_ok=True)
        
        logger.info(f"Successfully processed voice message for user {user_id}")
        
    except Exception as e:
        logger.error(f"Error processing voice message: {e}", exc_info=True)
        await message.answer(
            "😔 Извините, произошла ошибка при обработке голосового сообщения. "
            "Пожалуйста, попробуйте еще раз."
        )
        
        # Clean up any remaining temp files
        try:
            if 'voice_file_path' in locals() and voice_file_path.exists():
                voice_file_path.unlink(missing_ok=True)
            if 'tts_file_path' in locals() and tts_file_path.exists():
                tts_file_path.unlink(missing_ok=True)
        except:
            pass


@router.callback_query(F.data.startswith("transcribe_"))
async def show_transcription(callback: CallbackQuery):
    """Show text transcription of bot's voice message."""
    try:
        # Extract user_id and message_id from callback data
        parts = callback.data.split("_")
        user_id = int(parts[1])
        message_id = int(parts[2])
        
        # Get stored response text
        key = f"{user_id}_{message_id}"
        response_text = bot_responses.get(key)
        
        if response_text:
            # Send transcription as a new message
            await callback.message.answer(
                f"📝 <b>Text transcription:</b>\n\n"
                f"{response_text}"
            )
            await callback.answer("✅ Text shown!")
        else:
            await callback.answer("❌ Transcription not available", show_alert=True)
    
    except Exception as e:
        logger.error(f"Error showing transcription: {e}")
        await callback.answer("❌ Error", show_alert=True)

