import requests
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging
import brotli

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
        
        # Try REST API first (more reliable with authentication)
        # result = self._get_available_hours_rest(facility_id, date)
        result = None
        
        # If REST API was not attempted or failed (returns None), try GraphQL fallback
        if result is None:
            logger.info(f"REST API not available for facility {facility_id}, trying GraphQL fallback...")
            result = self._get_available_hours_graphql(facility_id, date)
        
        # Return result (could be empty list if no slots, or list of slots)
        return result if result is not None else []
    
    def _get_available_hours_graphql(self, facility_id: str, date: str) -> Optional[List[Dict]]:
        """
        Get available hours using GraphQL API.
        
        Args:
            facility_id: The facility ID to check
            date: Date in YYYY-MM-DD format
            
        Returns:
            List of available hour slots, or empty list if GraphQL fails
        """
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
            
            # Check for 403 specifically to trigger fallback
            if response.status_code == 403:
                logger.warning(f"GraphQL API returned 403 for facility {facility_id}")
                return []
            
            response.raise_for_status()
            
            data = response.json()
            
            if "data" in data and "facility" in data["data"]:
                return data["data"]["facility"]["bookingAvailableHours"]
            else:
                logger.error(f"Unexpected GraphQL response format: {data}")
                return []
                
        except requests.exceptions.RequestException as e:
            logger.error(f"GraphQL API request failed: {e}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse GraphQL JSON response: {e}")
            return []
    
    def _get_available_hours_rest(self, facility_id: str, date: str) -> Optional[List[Dict]]:
        """
        Fallback method using REST API.
        Note: This requires authentication cookies and CSRF token.
        
        Args:
            facility_id: The facility ID to check
            date: Date in YYYY-MM-DD format
            
        Returns:
            List of available hour slots, or None if REST API is not configured/failed
        """
        try:
            # Get REST API config
            rest_config = PADEL_ISRAEL_CONFIG.get("rest_api", {})
            cookie = rest_config.get("cookie", "")
            csrf_token = rest_config.get("csrf_token", "")
            
            # If no authentication provided, skip REST API and return None to trigger fallback
            if not cookie or not csrf_token:
                logger.debug("REST API authentication not configured, will use GraphQL fallback")
                return None
            
            # Convert date to Unix timestamp (start of day)
            date_obj = datetime.strptime(date, "%Y-%m-%d")
            timestamp = int(date_obj.timestamp())
            
            # Prepare REST API headers exactly as browser sends them
            rest_headers = {
                "Cookie": cookie,
                "Sec-Ch-Ua-Full-Version-List": '"Chromium";v="142.0.7444.162", "Google Chrome";v="142.0.7444.162", "Not_A Brand";v="99.0.0.0"',
                "Sec-Ch-Ua-Platform": '"macOS"',
                "X-Csrf-Token": csrf_token,
                "Sec-Ch-Ua": '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
                "Sec-Ch-Ua-Bitness": '"64"',
                "Sec-Ch-Ua-Model": '""',
                "Sec-Ch-Ua-Mobile": "?0",
                "Baggage": "sentry-environment=production,sentry-public_key=ab3697c86cfee424c79bdb37a8edda90,sentry-trace_id=af07566ccf3643e4abf1ab288fa2ffc3,sentry-sampled=false,sentry-sample_rand=0.9930849765302066,sentry-sample_rate=0.05",
                "Sentry-Trace": "af07566ccf3643e4abf1ab288fa2ffc3-ad4462f1cc3068f9-0",
                "Sec-Ch-Ua-Arch": '"arm"',
                "X-Requested-With": "XMLHttpRequest",
                "Sec-Ch-Ua-Full-Version": '"142.0.7444.162"',
                "Accept": "*/*",
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
                "Sec-Ch-Ua-Platform-Version": '"14.0.0"',
                "Sec-Fetch-Site": "same-origin",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Dest": "empty",
                "Referer": "https://book.padelstore.co.il/book/hamacabiahramatgan",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept-Language": "en-US,en;q=0.9,he-IL;q=0.8,he;q=0.7",
                "Priority": "u=1, i"
            }
            
            # Make REST API request
            url = f"{self.base_url}/api/facilities/{facility_id}/available_hours"
            params = {
                "timestamp": timestamp,
                "surface": "padel",
                "kind": "reservation",
                "courts_for_pros": "false"
            }
            
            response = requests.get(
                url,
                params=params,
                headers=rest_headers,
                timeout=30
            )
            
            response.raise_for_status()
            
            # Log response details for debugging
            logger.debug(f"Response encoding: {response.encoding}")
            logger.debug(f"Response status: {response.status_code}")
            logger.debug(f"Content-Type: {response.headers.get('Content-Type', 'none')}")
            logger.debug(f"Content-Encoding: {response.headers.get('Content-Encoding', 'none')}")
            
            # Handle Brotli compression manually
            # Note: Sometimes the server sends Content-Encoding: br but the content is not actually compressed
            content_encoding = response.headers.get('Content-Encoding', '')
            
            try:
                if content_encoding == 'br':
                    # Try to decompress Brotli
                    try:
                        logger.debug(f"Attempting Brotli decompression ({len(response.content)} bytes)")
                        decompressed = brotli.decompress(response.content)
                        logger.debug(f"Brotli decompressed to {len(decompressed)} bytes")
                        data = json.loads(decompressed.decode('utf-8'))
                    except brotli.error:
                        # Content is not actually compressed, try parsing as-is
                        logger.debug("Brotli decompression failed, trying as plain JSON")
                        data = json.loads(response.content.decode('utf-8'))
                else:
                    # Normal JSON parsing
                    data = response.json()
                
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}")
                logger.error(f"Response headers: {dict(response.headers)}")
                logger.error(f"Response text (first 500 chars): {response.text[:500]}")
                return []
            
            # The REST API returns {"available_hours": [...], "meta": {...}}
            # We need to convert it to match GraphQL format
            if "available_hours" in data:
                available_hours = data["available_hours"]
                
                # Convert REST API format to GraphQL format
                converted_data = []
                for slot in available_hours:
                    seconds = int(slot["seconds_from_midnight"])
                    
                    # Map REST API fields to GraphQL fields
                    converted_slot = {
                        "secondsFromMidnight": seconds,
                        "formattedHourStart": self._seconds_to_formatted_time(seconds),
                        "formattedHourEnd": self._seconds_to_formatted_time(seconds + 1800),  # Add 30 minutes
                        "inWaitlist": slot["in_waitlist"],
                        "available": slot["available"],
                        "schedule": slot["schedule"],
                        "group": slot["group"],
                        "__typename": "AvailableHour"
                    }
                    converted_data.append(converted_slot)
                
                logger.info(f"REST API succeeded for facility {facility_id}, found {len(converted_data)} slots")
                return converted_data
            else:
                logger.error(f"Unexpected REST API response format: {data}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"REST API request failed: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse REST API JSON response: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in REST API fallback: {e}")
            return None
    
    def _seconds_to_formatted_time(self, seconds: int) -> str:
        """
        Convert seconds from midnight to formatted 12-hour time (e.g., '06:00 AM')
        
        Args:
            seconds: Seconds from midnight
            
        Returns:
            Formatted time string like '06:00 AM'
        """
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        
        # Convert to 12-hour format
        if hours == 0:
            formatted_hour = 12
            am_pm = "AM"
        elif hours < 12:
            formatted_hour = hours
            am_pm = "AM"
        elif hours == 12:
            formatted_hour = 12
            am_pm = "PM"
        else:
            formatted_hour = hours - 12
            am_pm = "PM"
        
        return f"{formatted_hour:02d}:{minutes:02d} {am_pm}"
    
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