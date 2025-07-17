import logging
import time
from datetime import datetime, timedelta
from typing import Set, Dict, List
import json

from clients.padel_israel_client import PadelIsraelClient
from clients.lazuz_client import LazuzClient
from telegram_bot import TelegramNotifier
from config import (
    PADEL_ISRAEL_FACILITIES, 
    LAZUZ_CLUBS,
    MIN_CONSECUTIVE_SPOTS,
    ALTERNATIVE_MIN_SPOTS,
    MONITOR_START_TIME,
    MONITOR_END_TIME,
    CHECK_INTERVAL_MINUTES,
    DAYS_AHEAD_TO_CHECK
)

logger = logging.getLogger(__name__)

class PadelMonitor:
    def __init__(self):
        self.padel_client = PadelIsraelClient()
        self.lazuz_client = LazuzClient()
        self.notifier = TelegramNotifier()
        
        # Track notified slots to avoid duplicate notifications
        self.notified_slots: Set[str] = set()
        
        # Load previously notified slots from file if exists
        self.load_notified_slots()
    
    def load_notified_slots(self):
        """Load previously notified slots from file"""
        try:
            with open('notified_slots.json', 'r') as f:
                data = json.load(f)
                self.notified_slots = set(data.get('notified_slots', []))
                logger.info(f"Loaded {len(self.notified_slots)} previously notified slots")
        except FileNotFoundError:
            logger.info("No previous notification history found")
        except Exception as e:
            logger.error(f"Error loading notification history: {e}")
    
    def save_notified_slots(self):
        """Save notified slots to file"""
        try:
            # Write to a temporary file first, then rename to avoid corruption
            temp_file = 'notified_slots.json.tmp'
            with open(temp_file, 'w') as f:
                json.dump({'notified_slots': list(self.notified_slots)}, f, indent=2)
            
            # Atomic move to prevent corruption
            import os
            os.rename(temp_file, 'notified_slots.json')
            logger.debug(f"Saved {len(self.notified_slots)} notified slots to file")
        except Exception as e:
            logger.error(f"Error saving notification history: {e}")
            # Try to clean up temp file if it exists
            try:
                import os
                if os.path.exists('notified_slots.json.tmp'):
                    os.remove('notified_slots.json.tmp')
            except:
                pass
    
    def create_slot_key(self, facility_id: str, date: str, slots: List[Dict], client_type: str = "padel_israel") -> str:
        """Create a unique key for a slot group to track notifications"""
        if not slots:
            return ""
        
        if client_type == "padel_israel":
            # For Padel Israel slots
            start_time = slots[0]["secondsFromMidnight"]
            end_time = slots[-1]["secondsFromMidnight"]
            return f"{client_type}_{facility_id}_{date}_{start_time}_{end_time}"
        elif client_type == "lazuz":
            # For Lazuz slots
            start_time = slots["start_time"].replace(":", "")
            end_time = slots["end_time"].replace(":", "")
            court_id = slots["court_id"]
            return f"{client_type}_{facility_id}_{date}_{court_id}_{start_time}_{end_time}"
        else:
            return f"{client_type}_{facility_id}_{date}"
    
    def check_padel_israel_facility(self, facility_id: str, facility_name: str, 
                                  date: str = None) -> bool:
        """
        Check availability for a specific facility and send notifications if needed.
        
        Args:
            facility_id: The facility ID to check
            facility_name: Human-readable facility name
            date: Date to check (defaults to today)
            
        Returns:
            True if notifications were sent, False otherwise
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        logger.info(f"Checking availability for {facility_name} ({facility_id}) on {date}")
        
        # Get available hours from API
        available_hours = self.padel_client.get_available_hours(facility_id, date)
        
        if not available_hours:
            logger.warning(f"No data received for facility {facility_id}")
            return False
        
        # Find consecutive available slots
        consecutive_slots = self.padel_client.find_consecutive_available_slots(
            available_hours, 
            MONITOR_START_TIME, 
            MONITOR_END_TIME,
            MIN_CONSECUTIVE_SPOTS
        )
        
        # If no 3-slot groups found, try 2-slot groups
        if not consecutive_slots:
            consecutive_slots = self.padel_client.find_consecutive_available_slots(
                available_hours, 
                MONITOR_START_TIME, 
                MONITOR_END_TIME,
                ALTERNATIVE_MIN_SPOTS
            )
        
        if not consecutive_slots:
            logger.info(f"No available slots found for {facility_name}")
            return False
        
        # Check which slots haven't been notified yet
        new_slots = []
        for slot_group in consecutive_slots:
            slot_key = self.create_slot_key(facility_id, date, slot_group, "padel_israel")
            if slot_key not in self.notified_slots:
                new_slots.append(slot_group)
                self.notified_slots.add(slot_key)
        
        if new_slots:
            logger.info(f"Found {len(new_slots)} new available slot groups for {facility_name}")
            
            # Send notification
            success = self.notifier.send_availability_notification(
                facility_name, facility_id, date, new_slots
            )
            
            if success:
                self.save_notified_slots()
                logger.info(f"Notification sent for {facility_name}")
                return True
            else:
                # Remove from notified slots if notification failed and save the state
                for slot_group in new_slots:
                    slot_key = self.create_slot_key(facility_id, date, slot_group, "padel_israel")
                    self.notified_slots.discard(slot_key)
                # Save the updated state to prevent re-notification attempts
                self.save_notified_slots()
                logger.warning(f"Failed to send notification for {facility_name}, removed slots from tracking")
                
        return False
    
    def check_lazuz_facility(self, club_id: str, club_name: str, 
                           date: str = None) -> bool:
        """
        Check availability for a specific Lazuz club and send notifications if needed.
        
        Args:
            club_id: The club ID to check
            club_name: Human-readable club name
            date: Date to check (defaults to today)
            
        Returns:
            True if notifications were sent, False otherwise
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        logger.info(f"Checking Lazuz availability for {club_name} ({club_id}) on {date}")
        
        # Get available slots from API
        courts = self.lazuz_client.get_available_slots(club_id, date)
        
        if not courts:
            logger.warning(f"No data received for Lazuz club {club_id}")
            return False
        
        # Find consecutive available slots
        consecutive_slots = self.lazuz_client.find_consecutive_available_slots(
            courts, 
            MONITOR_START_TIME, 
            MONITOR_END_TIME,
            MIN_CONSECUTIVE_SPOTS
        )
        
        # If no 3-slot groups found, try 2-slot groups
        if not consecutive_slots:
            consecutive_slots = self.lazuz_client.find_consecutive_available_slots(
                courts, 
                MONITOR_START_TIME, 
                MONITOR_END_TIME,
                ALTERNATIVE_MIN_SPOTS
            )
        
        if not consecutive_slots:
            logger.info(f"No available slots found for Lazuz club {club_name}")
            return False
        
        # Check which slots haven't been notified yet
        new_slots = []
        for slot_group in consecutive_slots:
            slot_key = self.create_slot_key(club_id, date, slot_group, "lazuz")
            if slot_key not in self.notified_slots:
                new_slots.append(slot_group)
                self.notified_slots.add(slot_key)
        
        if new_slots:
            logger.info(f"Found {len(new_slots)} new available slot groups for Lazuz club {club_name}")
            
            # Send notification (need to adapt the format for Lazuz)
            success = self.send_lazuz_notification(
                club_name, club_id, date, new_slots
            )
            
            if success:
                self.save_notified_slots()
                logger.info(f"Notification sent for Lazuz club {club_name}")
                return True
            else:
                # Remove from notified slots if notification failed and save the state
                for slot_group in new_slots:
                    slot_key = self.create_slot_key(club_id, date, slot_group, "lazuz")
                    self.notified_slots.discard(slot_key)
                # Save the updated state to prevent re-notification attempts
                self.save_notified_slots()
                logger.warning(f"Failed to send notification for Lazuz club {club_name}, removed slots from tracking")
                
        return False
    
    def send_lazuz_notification(self, club_name: str, club_id: str, 
                              date: str, available_slots: list) -> bool:
        """
        Send a formatted notification about available Lazuz games.
        
        Args:
            club_name: Name of the club
            club_id: ID of the club
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
        
        message = f"🎾 *Lazuz Game Available!*\n\n"
        message += f"📍 *Club:* {club_name} (ID: `{club_id}`)\n"
        message += f"📅 *Date:* `{formatted_date}` ({day_name})\n\n"
        
        for i, slot_group in enumerate(available_slots, 1):
            court_id = slot_group["court_id"]
            start_time = slot_group["start_time"]
            end_time = slot_group["end_time"]
            duration = slot_group["duration"]
            
            message += f"⏰ *Slot {i}:* Court `{court_id}` - `{start_time}` - `{end_time}` ({duration} hours)\n"
        
        message += f"\n🔔 [Book now on Lazuz](https://server.lazuz.co.il)"
        
        return self.notifier.send_message(message)
    
    def generate_date_range(self, start_date: str = None, days_ahead: int = DAYS_AHEAD_TO_CHECK) -> List[str]:
        """
        Generate a list of dates to check.
        
        Args:
            start_date: Starting date in YYYY-MM-DD format (defaults to today)
            days_ahead: Number of days ahead to check (including start date)
            
        Returns:
            List of date strings in YYYY-MM-DD format
        """
        if start_date is None:
            start_date = datetime.now().strftime("%Y-%m-%d")
        
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        dates = []
        
        for i in range(days_ahead):
            check_date = start_dt + timedelta(days=i)
            dates.append(check_date.strftime("%Y-%m-%d"))
        
        return dates

    def check_all_facilities(self, date: str = None) -> int:
        """
        Check all configured facilities for availability across multiple dates.
        
        Args:
            date: Starting date to check (defaults to today)
            
        Returns:
            Number of facility-date combinations that had new availability
        """
        notifications_sent = 0
        
        # Generate date range to check
        if date:
            # If specific date provided, check only that date
            dates_to_check = [date]
        else:
            # Check the entire week
            dates_to_check = self.generate_date_range()
        
        logger.info(f"Checking {len(dates_to_check)} dates: {dates_to_check[0]} to {dates_to_check[-1]}")
        
        for check_date in dates_to_check:
            # Check Padel Israel facilities
            for facility_id, facility_name in PADEL_ISRAEL_FACILITIES.items():
                try:
                    if self.check_padel_israel_facility(facility_id, facility_name, check_date):
                        notifications_sent += 1
                        
                    # Small delay between facility checks to be nice to the API
                    time.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Error checking Padel Israel facility {facility_name} on {check_date}: {e}")
                    self.notifier.send_error_notification(
                        f"Error checking Padel Israel facility {facility_name} on {check_date}: {str(e)}"
                    )
            
            # Check Lazuz clubs
            # for club_id, club_name in LAZUZ_CLUBS.items():
            #     try:
            #         if self.check_lazuz_facility(club_id, club_name, check_date):
            #             notifications_sent += 1
                        
            #         # Small delay between facility checks to be nice to the API
            #         time.sleep(1)
                    
            #     except Exception as e:
            #         logger.error(f"Error checking Lazuz club {club_name} on {check_date}: {e}")
            #         self.notifier.send_error_notification(
            #             f"Error checking Lazuz club {club_name} on {check_date}: {str(e)}"
            #         )
        
        return notifications_sent
    
    def cleanup_old_notifications(self, days_old: int = 1):
        """
        Clean up old notification records to prevent memory bloat.
        Removes notifications for dates that are older than specified days.
        
        Args:
            days_old: Remove notifications older than this many days
        """
        current_hour = datetime.now().hour
        
        # Clean up at 6 AM daily
        if current_hour == 6:
            today = datetime.now().date()
            cutoff_date = today - timedelta(days=days_old)
            
            # Filter out old notifications based on date in slot key
            old_slots = set()
            for slot_key in self.notified_slots:
                try:
                    # Extract date from slot key format: "facility_id_date_start_time_end_time"
                    parts = slot_key.split('_')
                    if len(parts) >= 3:
                        date_str = parts[2]  # Date should be in YYYY-MM-DD format
                        slot_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                        if slot_date < cutoff_date:
                            old_slots.add(slot_key)
                except (ValueError, IndexError):
                    # If we can't parse the date, keep the slot (safer approach)
                    continue
            
            # Remove old slots
            if old_slots:
                self.notified_slots -= old_slots
                self.save_notified_slots()
                logger.info(f"Cleaned up {len(old_slots)} old notification records (older than {days_old} days)")
            else:
                logger.debug("No old notification records to clean up")
    
    def run_continuous_monitoring(self):
        """Run continuous monitoring loop"""
        logger.info("Starting continuous padel monitoring...")
        
        # Send startup notification
        total_facilities = len(PADEL_ISRAEL_FACILITIES) + len(LAZUZ_CLUBS)
        startup_message = "🚀 *Padel Monitor Started!*\n\n🔍 Watching for available games...\n\n📅 *Checking dates:* Next `{} days`\n🏢 *Facilities:* `{} Padel Israel` + `{} Lazuz` = `{} total`\n⏰ *Check interval:* `{} minutes`".format(
            DAYS_AHEAD_TO_CHECK, 
            len(PADEL_ISRAEL_FACILITIES), 
            len(LAZUZ_CLUBS), 
            total_facilities, 
            CHECK_INTERVAL_MINUTES
        )
        self.notifier.send_message(startup_message)
        
        while True:
            try:
                logger.info("Starting monitoring cycle...")
                
                # Check all facilities
                notifications_sent = self.check_all_facilities()
                
                if notifications_sent > 0:
                    logger.info(f"Sent notifications for {notifications_sent} facilities")
                else:
                    logger.info("No new availability found")
                
                # Cleanup old notifications
                self.cleanup_old_notifications()
                
                # Wait before next check
                sleep_seconds = CHECK_INTERVAL_MINUTES * 60
                logger.info(f"Sleeping for {CHECK_INTERVAL_MINUTES} minutes...")
                time.sleep(sleep_seconds)
                
            except KeyboardInterrupt:
                logger.info("Monitoring stopped by user")
                self.notifier.send_message("⏹️ *Padel Monitor Stopped*\n\n👋 Monitoring session ended by user")
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                self.notifier.send_error_notification(f"Monitoring error: {str(e)}")
                time.sleep(60)  # Wait a minute before retrying
    
    def run_single_check(self, date: str = None):
        """Run a single check for testing purposes"""
        logger.info("Running single availability check...")
        
        notifications_sent = self.check_all_facilities(date)
        
        if notifications_sent > 0:
            print(f"✅ Sent notifications for {notifications_sent} facilities")
        else:
            print("ℹ️  No new availability found")
        
        return notifications_sent 