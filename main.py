#!/usr/bin/env python3
"""
Padel Game Monitor - Main Entry Point

This script monitors available padel games and sends notifications via Telegram
when consecutive free slots are found during specified hours.
"""

import logging
import argparse
import sys
from datetime import datetime

from monitor import PadelMonitor
from telegram_bot import TelegramNotifier

def setup_logging(log_level: str = "INFO"):
    """Set up logging configuration"""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('padel_monitor.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def test_telegram_connection():
    """Test Telegram bot connection"""
    print("Testing Telegram bot connection...")
    notifier = TelegramNotifier()
    
    if notifier.send_test_message():
        print("✅ Telegram bot is working correctly!")
        return True
    else:
        print("❌ Telegram bot test failed. Check your configuration.")
        return False

def print_config_help():
    """Print help information about configuration"""
    print("\n🔧 Configuration Help:")
    print("=" * 50)
    print("1. Set up your Telegram bot:")
    print("   - Create a bot via @BotFather on Telegram")
    print("   - Get your bot token")
    print("   - Get your chat ID (send a message to your bot and check /getUpdates)")
    print("   - Update TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in config.py")
    print()
    print("2. Configure facility IDs:")
    print("   - Add facility IDs to PADEL_ISRAEL_FACILITIES in config.py")
    print("   - The current configuration includes facility '540'")
    print()
    print("3. Adjust monitoring settings:")
    print("   - Modify MIN_CONSECUTIVE_SPOTS (default: 3 slots = 1.5 hours)")
    print("   - Adjust MONITOR_START_TIME and MONITOR_END_TIME (default: 19:00-22:00)")
    print("   - Change CHECK_INTERVAL_MINUTES (default: 5 minutes)")
    print()

def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Monitor padel game availability and send Telegram notifications"
    )
    parser.add_argument(
        "--mode", 
        choices=["monitor", "test", "single", "config"],
        default="monitor",
        help="Run mode: monitor (continuous), test (test telegram), single (one check), config (show help)"
    )
    parser.add_argument(
        "--date", 
        type=str, 
        help="Date to check in YYYY-MM-DD format (default: today)"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Set logging level"
    )
    
    args = parser.parse_args()
    
    # Set up logging
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    
    print("🎾 Padel Game Monitor")
    print("=" * 30)
    
    if args.mode == "config":
        print_config_help()
        return
    
    if args.mode == "test":
        success = test_telegram_connection()
        sys.exit(0 if success else 1)
    
    # Validate date if provided
    if args.date:
        try:
            datetime.strptime(args.date, "%Y-%m-%d")
        except ValueError:
            print("❌ Invalid date format. Use YYYY-MM-DD")
            sys.exit(1)
    
    # Initialize monitor
    try:
        monitor = PadelMonitor()
    except Exception as e:
        logger.error(f"Failed to initialize monitor: {e}")
        print(f"❌ Failed to initialize monitor: {e}")
        print("\nRun with --mode config for setup help")
        sys.exit(1)
    
    # Run based on mode
    if args.mode == "single":
        if args.date:
            print(f"Running single check for {args.date}...")
        else:
            print("Running single check for the next 7 days...")
        monitor.run_single_check(args.date)
    
    elif args.mode == "monitor":
        print("Starting continuous monitoring...")
        print("Press Ctrl+C to stop")
        print()
        
        try:
            monitor.run_continuous_monitoring()
        except KeyboardInterrupt:
            print("\n👋 Monitoring stopped by user")
            logger.info("Monitoring stopped by user")

if __name__ == "__main__":
    main() 