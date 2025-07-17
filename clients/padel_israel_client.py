import requests
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging

from config import PADEL_ISRAEL_CONFIG

logger = logging.getLogger(__name__)

class PadelIsraelClient:
    def __init__(self):
        self.base_url = PADEL_ISRAEL_CONFIG["base_url"]
        self.endpoint = PADEL_ISRAEL_CONFIG["endpoint"]
        self.headers = PADEL_ISRAEL_CONFIG["headers"]
        
    def get_available_hours(self, facility_id: str, date: str = None) -> List[Dict]:
        """
        Get available hours for a specific facility and date.
        
        Args:
            facility_id: The facility ID to check
            date: Date in YYYY-MM-DD format (defaults to today)
            
        Returns:
            List of available hour slots
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
            
        query = {
            "operationName": "getAvailableHours",
            "variables": {
                "facilityId": facility_id,
                "input": {
                    "surface": "padel",
                    "date": date,
                    "kind": "RESERVATION"
                }
            },
            "query": """
                query getAvailableHours($facilityId: ID!, $input: BookingAvailableHoursInput!) {
                    facility(id: $facilityId) {
                        bookingAvailableHours(input: $input) {
                            secondsFromMidnight
                            formattedHourStart
                            formattedHourEnd
                            inWaitlist
                            available
                            schedule
                            group
                            __typename
                        }
                        __typename
                    }
                }
            """
        }
        
        try:
            response = requests.post(
                f"{self.base_url}{self.endpoint}",
                json=query,
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            
            if "data" in data and "facility" in data["data"]:
                return data["data"]["facility"]["bookingAvailableHours"]
            else:
                logger.error(f"Unexpected response format: {data}")
                return []
                
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            return []
    
    def seconds_to_time_string(self, seconds: int) -> str:
        """Convert seconds from midnight to HH:MM format"""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours:02d}:{minutes:02d}"
    
    def is_time_in_range(self, time_str: str, start_time: str, end_time: str) -> bool:
        """Check if a time string is within the specified range"""
        time_obj = datetime.strptime(time_str, "%H:%M").time()
        start_obj = datetime.strptime(start_time, "%H:%M").time()
        end_obj = datetime.strptime(end_time, "%H:%M").time()
        
        return start_obj <= time_obj <= end_obj
    
    def find_consecutive_available_slots(self, available_hours: List[Dict], 
                                       start_time: str, end_time: str,
                                       min_consecutive: int = 3) -> List[Dict]:
        """
        Find consecutive available slots within the specified time range.
        
        Args:
            available_hours: List of available hour slots from API
            start_time: Start time in HH:MM format
            end_time: End time in HH:MM format
            min_consecutive: Minimum consecutive slots required
            
        Returns:
            List of consecutive slot groups that meet criteria
        """
        # Filter slots that are available and within time range
        filtered_slots = []
        for slot in available_hours:
            if slot["available"] and not slot["inWaitlist"]:
                slot_time = self.seconds_to_time_string(slot["secondsFromMidnight"])
                if self.is_time_in_range(slot_time, start_time, end_time):
                    filtered_slots.append(slot)
        
        # Sort by time
        filtered_slots.sort(key=lambda x: x["secondsFromMidnight"])
        
        # Find consecutive groups
        consecutive_groups = []
        current_group = []
        
        for i, slot in enumerate(filtered_slots):
            if not current_group:
                current_group.append(slot)
            else:
                # Check if this slot is consecutive (30 minutes = 1800 seconds apart)
                prev_slot = current_group[-1]
                if slot["secondsFromMidnight"] - prev_slot["secondsFromMidnight"] == 1800:
                    current_group.append(slot)
                else:
                    # Gap found, save current group if it meets criteria
                    if len(current_group) >= min_consecutive:
                        consecutive_groups.append(current_group.copy())
                    current_group = [slot]
        
        # Check final group
        if len(current_group) >= min_consecutive:
            consecutive_groups.append(current_group)
        
        return consecutive_groups
    
    def format_time_slots(self, slots: List[Dict]) -> str:
        """Format time slots for display"""
        if not slots:
            return "No slots"
        
        start_time = slots[0]["formattedHourStart"]
        end_time = slots[-1]["formattedHourEnd"]
        duration = len(slots) * 0.5  # Each slot is 30 minutes
        
        return f"{start_time} - {end_time} ({duration} hours)" 