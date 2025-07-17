import logging
import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

logger = logging.getLogger(__name__)

class TelegramNotifier:
    def __init__(self, bot_token: str = None, chat_id: str = None):
        self.bot_token = bot_token or TELEGRAM_BOT_TOKEN
        self.chat_id = chat_id or TELEGRAM_CHAT_ID
        
        if self.bot_token == "YOUR_BOT_TOKEN_HERE":
            logger.warning("Telegram bot token not configured. Please update config.py")
    
    def send_message(self, message: str) -> bool:
        """
        Send a message to Telegram chat using requests.
        
        Args:
            message: The message to send
            
        Returns:
            True if message was sent successfully, False otherwise
        """
        if self.bot_token == "YOUR_BOT_TOKEN_HERE":
            logger.error("Telegram bot token not configured. Please update config.py")
            return False
            
        if self.chat_id == "YOUR_CHAT_ID_HERE":
            logger.error("Telegram chat ID not configured. Please update config.py")
            return False
        
        try:
            print(message)
            
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": "Markdown"
            }
            
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            
            logger.info(f"Message sent successfully to chat {self.chat_id}")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending Telegram message: {e}")
            return False
    
    def send_availability_notification(self, facility_name: str, facility_id: str, 
                                     date: str, available_slots: list) -> bool:
        """
        Send a formatted notification about available padel games.
        
        Args:
            facility_name: Name of the facility
            facility_id: ID of the facility
            date: Date of availability
            available_slots: List of available time slot groups
            
        Returns:
            True if notification was sent successfully
        """
        if not available_slots:
            return False
        
        # Format date with day of week for better readability
        from datetime import datetime
        date_obj = datetime.strptime(date, "%Y-%m-%d")
        day_name = date_obj.strftime("%A")  # Full day name (e.g., "Monday")
        formatted_date = date_obj.strftime("%Y-%m-%d")
        
        message = f"🎾 *Padel Game Available!*\n\n"
        message += f"📍 *Facility:* {facility_name} (ID: `{facility_id}`)\n"
        message += f"📅 *Date:* `{formatted_date}` ({day_name})\n\n"
        
        for i, slot_group in enumerate(available_slots, 1):
            start_time = slot_group[0]["formattedHourStart"]
            end_time = slot_group[-1]["formattedHourEnd"]
            duration = len(slot_group) * 0.5
            
            message += f"⏰ *Slot {i}:* `{start_time}` - `{end_time}` ({duration} hours)\n"
        
        message += f"\n🔔 [Book now at Padel Store](https://book.padelstore.co.il)"
        
        return self.send_message(message)
    
    def send_test_message(self) -> bool:
        """Send a test message to verify bot configuration"""
        message = "🤖 *Padel Monitor Bot is working!*\n\n✅ Test message sent successfully."
        return self.send_message(message)
    
    def send_error_notification(self, error_message: str) -> bool:
        """Send an error notification"""
        message = f"❌ *Padel Monitor Error*\n\n```\n{error_message}\n```"
        return self.send_message(message) 