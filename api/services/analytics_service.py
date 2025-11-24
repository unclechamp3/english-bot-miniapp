"""
Analytics service for tracking user activity and progress.
Stores data persistently in JSON files.
"""

import logging
import json
from typing import Dict, Optional
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Manages user analytics and progress tracking."""
    
    def __init__(self):
        """Initialize analytics storage."""
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        self.analytics_file = self.data_dir / "analytics.json"
        
        # Load existing data
        self.analytics_data = self._load_data()
    
    def _load_data(self) -> Dict:
        """Load analytics data from disk."""
        if self.analytics_file.exists():
            try:
                with open(self.analytics_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                logger.info("Loaded analytics data from disk")
                return data
            except Exception as e:
                logger.error(f"Error loading analytics: {e}")
                return {}
        return {}
    
    def _save_data(self):
        """Save analytics data to disk."""
        try:
            with open(self.analytics_file, 'w', encoding='utf-8') as f:
                json.dump(self.analytics_data, f, ensure_ascii=False, indent=2)
            logger.debug("Saved analytics data to disk")
        except Exception as e:
            logger.error(f"Error saving analytics: {e}")
    
    def _ensure_user_data(self, user_id: int):
        """Ensure user data structure exists."""
        user_key = str(user_id)
        if user_key not in self.analytics_data:
            self.analytics_data[user_key] = {
                "total_messages": 0,
                "voice_messages": 0,
                "text_messages": 0,
                "total_errors": 0,
                "error_types": {},
                "practice_days": [],
                "streak": 0,
                "daily_activity": {},
                "last_activity": None
            }
    
    def track_message(self, user_id: int, message_type: str):
        """
        Track a user message (voice or text).
        
        Args:
            user_id: Telegram user ID
            message_type: "voice" or "text"
        """
        self._ensure_user_data(user_id)
        user_key = str(user_id)
        user_data = self.analytics_data[user_key]
        
        # Increment counters
        user_data["total_messages"] += 1
        if message_type == "voice":
            user_data["voice_messages"] += 1
        elif message_type == "text":
            user_data["text_messages"] += 1
        
        # Track daily activity
        today = datetime.now().strftime("%Y-%m-%d")
        if today not in user_data["daily_activity"]:
            user_data["daily_activity"][today] = {"messages": 0, "errors": 0}
        user_data["daily_activity"][today]["messages"] += 1
        
        # Update practice days and streak
        if today not in user_data["practice_days"]:
            user_data["practice_days"].append(today)
            user_data["practice_days"].sort()
            self._update_streak(user_id)
        
        # Update last activity
        user_data["last_activity"] = datetime.now().isoformat()
        
        self._save_data()
        logger.info(f"Tracked {message_type} message for user {user_id}")
    
    def track_errors(self, user_id: int, errors: str):
        """
        Track grammar errors from a message.
        
        Args:
            user_id: Telegram user ID
            errors: Error text from grammar checker
        """
        self._ensure_user_data(user_id)
        user_key = str(user_id)
        user_data = self.analytics_data[user_key]
        
        # Parse errors to count by type
        if errors and errors != "No errors found.":
            # Count errors (each numbered item is one error)
            error_count = errors.count("1. Ошибка:") + errors.count("2. Ошибка:") + \
                         errors.count("3. Ошибка:") + errors.count("4. Ошибка:") + \
                         errors.count("5. Ошибка:")
            
            user_data["total_errors"] += error_count
            
            # Track daily errors
            today = datetime.now().strftime("%Y-%m-%d")
            if today in user_data["daily_activity"]:
                user_data["daily_activity"][today]["errors"] += error_count
            
            # Categorize error types (simple heuristic)
            error_lower = errors.lower()
            if "глагол" in error_lower or "verb" in error_lower or "tense" in error_lower:
                user_data["error_types"]["verb_tense"] = user_data["error_types"].get("verb_tense", 0) + 1
            if "артикл" in error_lower or "article" in error_lower:
                user_data["error_types"]["articles"] = user_data["error_types"].get("articles", 0) + 1
            if "предлог" in error_lower or "preposition" in error_lower:
                user_data["error_types"]["prepositions"] = user_data["error_types"].get("prepositions", 0) + 1
            if "порядок слов" in error_lower or "word order" in error_lower:
                user_data["error_types"]["word_order"] = user_data["error_types"].get("word_order", 0) + 1
            if "согласование" in error_lower or "agreement" in error_lower:
                user_data["error_types"]["agreement"] = user_data["error_types"].get("agreement", 0) + 1
            if "не закончено" in error_lower or "incomplete" in error_lower:
                user_data["error_types"]["incomplete"] = user_data["error_types"].get("incomplete", 0) + 1
            
            # If no specific category matched, count as "other"
            if not any(key in error_lower for key in ["глагол", "verb", "артикл", "article", 
                                                       "предлог", "preposition", "порядок", "order",
                                                       "согласование", "agreement", "закончено", "incomplete"]):
                user_data["error_types"]["other"] = user_data["error_types"].get("other", 0) + 1
            
            self._save_data()
            logger.info(f"Tracked {error_count} errors for user {user_id}")
    
    def _update_streak(self, user_id: int):
        """Calculate current practice streak."""
        user_key = str(user_id)
        user_data = self.analytics_data[user_key]
        practice_days = user_data["practice_days"]
        
        if not practice_days:
            user_data["streak"] = 0
            return
        
        # Sort days
        practice_days.sort()
        
        # Calculate streak from today backwards
        today = datetime.now().date()
        streak = 0
        
        for i in range(len(practice_days) - 1, -1, -1):
            practice_date = datetime.strptime(practice_days[i], "%Y-%m-%d").date()
            expected_date = today - timedelta(days=streak)
            
            if practice_date == expected_date:
                streak += 1
            else:
                break
        
        user_data["streak"] = streak
        logger.info(f"Updated streak for user {user_id}: {streak} days")
    
    def get_user_analytics(self, user_id: int) -> Optional[Dict]:
        """
        Get analytics data for a user.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            Dict with user analytics or None
        """
        user_key = str(user_id)
        if user_key in self.analytics_data:
            # Calculate some derived stats
            data = self.analytics_data[user_key].copy()
            
            # Error rate
            if data["total_messages"] > 0:
                data["error_rate"] = round((data["total_errors"] / data["total_messages"]) * 100, 1)
            else:
                data["error_rate"] = 0.0
            
            # Messages this week
            today = datetime.now()
            week_ago = today - timedelta(days=7)
            messages_this_week = 0
            
            for date_str, activity in data["daily_activity"].items():
                date = datetime.strptime(date_str, "%Y-%m-%d")
                if date >= week_ago:
                    messages_this_week += activity["messages"]
            
            data["messages_this_week"] = messages_this_week
            
            return data
        return None
    
    def get_chart_data(self, user_id: int, days: int = 7) -> Dict:
        """
        Get chart data for the last N days.
        
        Args:
            user_id: Telegram user ID
            days: Number of days to include
            
        Returns:
            Dict with chart data
        """
        user_key = str(user_id)
        if user_key not in self.analytics_data:
            return {"daily": [], "error_types": {}}
        
        user_data = self.analytics_data[user_key]
        
        # Get last N days of activity
        today = datetime.now()
        daily_data = []
        
        for i in range(days - 1, -1, -1):
            date = today - timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")
            
            activity = user_data["daily_activity"].get(date_str, {"messages": 0, "errors": 0})
            daily_data.append({
                "date": date_str,
                "messages": activity["messages"],
                "errors": activity["errors"]
            })
        
        return {
            "daily": daily_data,
            "error_types": user_data["error_types"]
        }


# Global instance
analytics_service = AnalyticsService()

