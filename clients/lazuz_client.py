import requests
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging
from urllib.parse import urlencode
import urllib3

from config import LAZUZ_CONFIG

# Suppress SSL warnings for Lazuz API
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)

class LazuzClient:
    def __init__(self):
        self.base_url = LAZUZ_CONFIG["base_url"]
        self.endpoint = LAZUZ_CONFIG["endpoint"]
        self.headers = LAZUZ_CONFIG["headers"]
        self.duration = LAZUZ_CONFIG["duration"]
        self.court_type = LAZUZ_CONFIG["court_type"]
        self.from_time = LAZUZ_CONFIG["from_time"]
        
    def get_available_slots(self, club_id: str, date: str = None) -> List[Dict]:
        """
        Get available time slots for a specific club and date.
        
        Args:
            club_id: The club ID to check
            date: Date in YYYY-MM-DD format (defaults to today)
            
        Returns:
            List of courts with their available time slots
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
            
        params = {
            "club_id": club_id,
            "date": date,
            "duration": self.duration,
            "court_type": self.court_type,
            "from_time": self.from_time
        }
        
        try:
            url = f"{self.base_url}{self.endpoint}"
            response = requests.get(
                url,
                params=params,
                headers=self.headers,
                timeout=30,
                verify=False  # Skip SSL certificate verification
            )
            response.raise_for_status()
            
            data = response.json()

            print(data)
            
            if "courts" in data:
                return data["courts"]
            else:
                logger.error(f"Unexpected response format: {data}")
                return []
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Lazuz API request failed: {e}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            return []
    
    def time_to_minutes(self, time_str: str) -> int:
        """Convert time string to minutes from midnight"""
        time_obj = datetime.strptime(time_str, "%H:%M:%S").time()
        return time_obj.hour * 60 + time_obj.minute
    
    def minutes_to_time(self, minutes: int) -> str:
        """Convert minutes from midnight to HH:MM format"""
        hours = minutes // 60
        mins = minutes % 60
        return f"{hours:02d}:{mins:02d}"
    
    def is_time_in_range(self, time_str: str, start_time: str, end_time: str) -> bool:
        """Check if a time string is within the specified range"""
        # Convert all times to minutes for comparison
        # time_str is already in HH:MM:SS format, start_time and end_time are in HH:MM format
        time_minutes = self.time_to_minutes(time_str)
        start_minutes = self.time_to_minutes(start_time + ":00")
        end_minutes = self.time_to_minutes(end_time + ":00")
        
        return start_minutes <= time_minutes <= end_minutes
    
    def find_consecutive_available_slots(self, courts: List[Dict], 
                                       start_time: str, end_time: str,
                                       min_consecutive: int = 3) -> List[Dict]:
        """
        Find consecutive available slots within the specified time range across all courts.
        
        Args:
            courts: List of courts with available time slots from API
            start_time: Start time in HH:MM format
            end_time: End time in HH:MM format
            min_consecutive: Minimum consecutive slots required
            
        Returns:
            List of consecutive slot groups that meet criteria
        """
        all_consecutive_groups = []
        
        for court in courts:
            court_id = court["courtId"]
            available_slots = court["availbleTimeSlot"]
            
            # Filter slots that are within time range
            filtered_slots = []
            for slot in available_slots:
                if self.is_time_in_range(slot, start_time, end_time):
                    filtered_slots.append(slot)
            
            # Convert to minutes and sort
            slot_minutes = [self.time_to_minutes(slot) for slot in filtered_slots]
            slot_minutes.sort()
            
            # Find consecutive groups
            current_group = []
            
            for i, slot_minute in enumerate(slot_minutes):
                if not current_group:
                    current_group.append(slot_minute)
                else:
                    # Check if this slot is consecutive (30 minutes apart)
                    prev_slot = current_group[-1]
                    if slot_minute - prev_slot == 30:
                        current_group.append(slot_minute)
                    else:
                        # Gap found, save current group if it meets criteria
                        if len(current_group) >= min_consecutive:
                            group_info = {
                                "court_id": court_id,
                                "start_time": self.minutes_to_time(current_group[0]),
                                "end_time": self.minutes_to_time(current_group[-1] + 30),  # Add 30 min for end time
                                "duration": len(current_group) * 0.5,
                                "slots": [self.minutes_to_time(m) for m in current_group]
                            }
                            all_consecutive_groups.append(group_info)
                        current_group = [slot_minute]
            
            # Check final group
            if len(current_group) >= min_consecutive:
                group_info = {
                    "court_id": court_id,
                    "start_time": self.minutes_to_time(current_group[0]),
                    "end_time": self.minutes_to_time(current_group[-1] + 30),  # Add 30 min for end time
                    "duration": len(current_group) * 0.5,
                    "slots": [self.minutes_to_time(m) for m in current_group]
                }
                all_consecutive_groups.append(group_info)
        
        return all_consecutive_groups
    
    def format_time_slots(self, slots: List[Dict]) -> str:
        """Format time slots for display"""
        if not slots:
            return "No slots"
        
        formatted_slots = []
        for slot in slots:
            formatted_slots.append(f"Court {slot['court_id']}: {slot['start_time']} - {slot['end_time']} ({slot['duration']} hours)")
        
        return "\n".join(formatted_slots) 