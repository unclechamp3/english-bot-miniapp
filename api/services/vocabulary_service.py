"""
Service for managing user vocabulary with spaced repetition learning.
"""

import logging
import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from pathlib import Path

from openai import AsyncOpenAI
from config import Config

logger = logging.getLogger(__name__)


class VocabularyService:
    """Manages user vocabulary with spaced repetition system."""
    
    # Spaced repetition intervals (in days)
    INTERVALS = [1, 3, 7, 14, 30, 90]  # Progressive intervals
    
    def __init__(self):
        """Initialize vocabulary service."""
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        self.vocab_file = self.data_dir / "vocabulary.json"
        self.vocabulary_data = self._load_data()
        self.client = AsyncOpenAI(api_key=Config.OPENAI_API_KEY)
    
    def _load_data(self) -> Dict:
        """Load vocabulary data from disk."""
        if self.vocab_file.exists():
            try:
                with open(self.vocab_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                logger.info("Loaded vocabulary data from disk")
                return data
            except Exception as e:
                logger.error(f"Error loading vocabulary: {e}")
                return {}
        return {}
    
    def _save_data(self):
        """Save vocabulary data to disk."""
        try:
            with open(self.vocab_file, 'w', encoding='utf-8') as f:
                json.dump(self.vocabulary_data, f, ensure_ascii=False, indent=2)
            logger.debug("Saved vocabulary data to disk")
        except Exception as e:
            logger.error(f"Error saving vocabulary: {e}")
    
    def _ensure_user_data(self, user_id: int):
        """Ensure user vocabulary structure exists."""
        user_key = str(user_id)
        if user_key not in self.vocabulary_data:
            self.vocabulary_data[user_key] = {"words": []}
    
    async def add_word(self, user_id: int, word: str) -> Dict:
        """
        Add a new word to user's vocabulary with GPT-generated content.
        
        Args:
            user_id: Telegram user ID
            word: English word to add
            
        Returns:
            Word data (word, translation, example)
        """
        self._ensure_user_data(user_id)
        user_key = str(user_id)
        
        # Check if word already exists
        for existing_word in self.vocabulary_data[user_key]["words"]:
            if existing_word["word"].lower() == word.lower():
                logger.info(f"Word '{word}' already exists for user {user_id}")
                return existing_word
        
        # Generate translation and example using GPT
        try:
            prompt = f"""Generate vocabulary data for the English word: "{word}"

Provide:
1. Russian translation (one or two words, most common meaning)
2. Example sentence in English using this word

Format your response EXACTLY like this:
Translation: [Russian translation]
Example: [English example sentence]

Example:
Translation: фотография
Example: I enjoy photography as a hobby"""

            response = await self.client.chat.completions.create(
                model=Config.GPT_MODEL,
                messages=[
                    {"role": "system", "content": "You are a helpful English-Russian vocabulary teacher. Provide concise translations and natural example sentences."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=150
            )
            
            result = response.choices[0].message.content.strip()
            
            # Parse response
            translation = ""
            example = ""
            
            for line in result.split('\n'):
                line = line.strip()
                if line.startswith("Translation:"):
                    translation = line.replace("Translation:", "").strip()
                elif line.startswith("Example:"):
                    example = line.replace("Example:", "").strip()
            
            if not translation or not example:
                logger.error(f"Failed to parse GPT response: {result}")
                translation = "перевод"
                example = f"I use the word {word} in sentences."
            
        except Exception as e:
            logger.error(f"Error generating vocabulary data: {e}")
            translation = "перевод"
            example = f"I use the word {word} in sentences."
        
        # Create word entry
        word_data = {
            "word": word.lower(),
            "translation": translation,
            "example": example,
            "added_date": datetime.now().strftime("%Y-%m-%d"),
            "next_review": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
            "interval_days": 1,
            "status": "new",  # new, learning, mastered
            "reviews_count": 0,
            "correct_count": 0
        }
        
        # Add to vocabulary
        self.vocabulary_data[user_key]["words"].append(word_data)
        self._save_data()
        
        logger.info(f"Added word '{word}' for user {user_id}")
        return word_data
    
    def get_due_words(self, user_id: int, limit: int = 5) -> List[Dict]:
        """
        Get words that are due for review.
        
        Args:
            user_id: Telegram user ID
            limit: Maximum number of words to return
            
        Returns:
            List of words due for review
        """
        self._ensure_user_data(user_id)
        user_key = str(user_id)
        
        today = datetime.now().date()
        due_words = []
        
        for word in self.vocabulary_data[user_key]["words"]:
            next_review = datetime.strptime(word["next_review"], "%Y-%m-%d").date()
            if next_review <= today:
                due_words.append(word)
        
        # Sort by next_review date (oldest first)
        due_words.sort(key=lambda w: w["next_review"])
        
        return due_words[:limit]
    
    def mark_word_correct(self, user_id: int, word: str):
        """
        Mark word as correctly recalled, increase interval.
        
        Args:
            user_id: Telegram user ID
            word: Word that was recalled correctly
        """
        self._ensure_user_data(user_id)
        user_key = str(user_id)
        
        for word_data in self.vocabulary_data[user_key]["words"]:
            if word_data["word"].lower() == word.lower():
                word_data["reviews_count"] += 1
                word_data["correct_count"] += 1
                
                # Calculate next interval
                current_interval = word_data["interval_days"]
                next_interval = self._get_next_interval(current_interval)
                
                word_data["interval_days"] = next_interval
                word_data["next_review"] = (datetime.now() + timedelta(days=next_interval)).strftime("%Y-%m-%d")
                
                # Update status
                if next_interval >= 30:
                    word_data["status"] = "mastered"
                elif word_data["reviews_count"] >= 3:
                    word_data["status"] = "learning"
                
                self._save_data()
                logger.info(f"Word '{word}' marked correct for user {user_id}, next review in {next_interval} days")
                return
    
    def mark_word_forgot(self, user_id: int, word: str):
        """
        Mark word as forgotten, reset interval.
        
        Args:
            user_id: Telegram user ID
            word: Word that was forgotten
        """
        self._ensure_user_data(user_id)
        user_key = str(user_id)
        
        for word_data in self.vocabulary_data[user_key]["words"]:
            if word_data["word"].lower() == word.lower():
                word_data["reviews_count"] += 1
                
                # Reset to first interval
                word_data["interval_days"] = 1
                word_data["next_review"] = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
                word_data["status"] = "learning"
                
                self._save_data()
                logger.info(f"Word '{word}' marked forgot for user {user_id}, reset to 1 day")
                return
    
    def _get_next_interval(self, current_interval: int) -> int:
        """
        Get next spaced repetition interval.
        
        Args:
            current_interval: Current interval in days
            
        Returns:
            Next interval in days
        """
        for interval in self.INTERVALS:
            if interval > current_interval:
                return interval
        return self.INTERVALS[-1]  # Max interval
    
    def get_user_words(self, user_id: int, status: Optional[str] = None) -> List[Dict]:
        """
        Get all words for a user, optionally filtered by status.
        
        Args:
            user_id: Telegram user ID
            status: Optional status filter (new, learning, mastered)
            
        Returns:
            List of word data
        """
        self._ensure_user_data(user_id)
        user_key = str(user_id)
        
        words = self.vocabulary_data[user_key]["words"]
        
        if status:
            words = [w for w in words if w["status"] == status]
        
        return words
    
    def delete_word(self, user_id: int, word: str) -> bool:
        """
        Delete a word from user's vocabulary.
        
        Args:
            user_id: Telegram user ID
            word: Word to delete
            
        Returns:
            True if deleted, False if not found
        """
        self._ensure_user_data(user_id)
        user_key = str(user_id)
        
        words = self.vocabulary_data[user_key]["words"]
        for i, word_data in enumerate(words):
            if word_data["word"].lower() == word.lower():
                del words[i]
                self._save_data()
                logger.info(f"Deleted word '{word}' for user {user_id}")
                return True
        
        return False
    
    def get_stats(self, user_id: int) -> Dict:
        """
        Get vocabulary statistics for a user.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            Statistics dict
        """
        self._ensure_user_data(user_id)
        user_key = str(user_id)
        
        words = self.vocabulary_data[user_key]["words"]
        
        stats = {
            "total": len(words),
            "new": len([w for w in words if w["status"] == "new"]),
            "learning": len([w for w in words if w["status"] == "learning"]),
            "mastered": len([w for w in words if w["status"] == "mastered"]),
            "due_today": len(self.get_due_words(user_id, limit=999))
        }
        
        return stats


# Global instance
vocabulary_service = VocabularyService()

