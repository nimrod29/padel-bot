# Configuration for Padel Game Monitor
import os

# Monitoring settings
MIN_CONSECUTIVE_SPOTS = 3  # Minimum consecutive free spots (1.5 hours)
ALTERNATIVE_MIN_SPOTS = 2  # Alternative minimum spots (1 hour)

# Time range for monitoring (in 24-hour format)
MONITOR_START_TIME = "18:00"  # 6:00 PM
MONITOR_END_TIME = "23:00"  # 11:00 PM

# Facility IDs for different locations
PADEL_ISRAEL_FACILITIES = {
    "654": "Rishon Lezion",
    "540": "Tel Aviv University",  # Add more facilities as needed
    "652": "Hamacabiah Ramat Gan",
    "653": "Park Kfar Saba",
}

# Padel Israel API Configuration
PADEL_ISRAEL_CONFIG = {
    "base_url": "https://book.padelstore.co.il",
    "endpoint": "/graphql",
    "headers": {
        "Content-Type": "application/json",
        "Fooly": "cooly",
        "Accept": "*/*",
        "Baggage": "sentry-environment=production,sentry-public_key=0ef931a9e71886034c7d09886158ddc9,sentry-release=com.playbypoint.migrashimpadel%403.0.11%2B2,sentry-trace_id=4c4eb11a99e14d0982b84717b1dd791d",
        "Authorization": "Basic cGJjMjE6ZmVkZXJlcg==",
        "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Token": "U2MceR_T8dUTUpMj9UFcrclmpmGES83cXJhVnFuQicPliHeRl_77_Ndd7JxyRoJ8",
        "Sentry-Trace": "4c4eb11a99e14d0982b84717b1dd791d-6791056ebe194e94-0",
        "User-Agent": "playbypoint/2 CFNetwork/1474.1 Darwin/23.0.0",
    },
}

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")  # Replace with your chat ID

# Lazuz Configuration
LAZUZ_CLUBS = {
    "215": "House Padel Beit Berl",
    # Add more clubs as needed
}

LAZUZ_CONFIG = {
    "base_url": "https://server.lazuz.co.il",
    "endpoint": "/client-app/club/availble-slots/",
    "duration": 60,  # Duration in minutes
    "court_type": 9,  # Court type for padel
    "from_time": "10:00:00",  # Starting time for search
    "headers": {
        "User-Agent": "Dart/3.4 (dart:io)",
        "App_version": "5.0.15",
        "Accept-Encoding": "gzip, deflate, br",
        "X-Appcheck-Server": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhcHAiOiJMYXp1eiIsInZlcnNpb24iOiI1LjAuMTUiLCJpYXQiOjE3NTIzOTQ2NTksImV4cCI6MTc1MjM5ODI1OX0.bjRK08dY8wE-X5mXIg1qm-ZWkOgrMCEcbpL3Z-CNEg4",
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxMzA4ODEsInR5cGUiOiJTdWJzY3JpYmVyIiwiaWF0IjoxNzUyMzk1NjI5LCJleHAiOjE3NTIzOTY2Mjl9.xb9CvTXojU9l-0Nh_nKWfefKA1Aramxd192A7EtdvnA",
    },
}

# Monitoring intervals
CHECK_INTERVAL_MINUTES = 5  # How often to check for available games
DAYS_AHEAD_TO_CHECK = 7  # Number of days ahead to check (including today)
