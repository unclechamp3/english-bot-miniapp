"""
Configuration module for the English Practice Bot.
Loads and validates environment variables.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Bot configuration class."""
    
    # Telegram Bot Token
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    
    # OpenAI API Key
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # OpenAI models
    WHISPER_MODEL = "whisper-1"
    GPT_MODEL = "gpt-4o-mini"  # Using gpt-4o-mini for cost efficiency
    TTS_MODEL = "tts-1"
    TTS_VOICE = "nova"  # Options: alloy, echo, fable, onyx, nova, shimmer
    
    # Context settings
    MAX_CONTEXT_MESSAGES = 10  # Keep last 10 messages in conversation history
    
    # API URL for analytics (optional - if not set, analytics won't sync to API)
    API_URL = os.getenv("API_URL", "").rstrip("/")  # Remove trailing slash if present
    
    @classmethod
    def validate(cls):
        """Validate that all required configuration variables are set."""
        if not cls.TELEGRAM_BOT_TOKEN:
            raise ValueError(
                "TELEGRAM_BOT_TOKEN is not set. "
                "Please add it to your .env file."
            )
        
        if not cls.OPENAI_API_KEY:
            raise ValueError(
                "OPENAI_API_KEY is not set. "
                "Please add it to your .env file."
            )
        
        return True


# Validate configuration on import
Config.validate()

