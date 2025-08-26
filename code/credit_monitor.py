#!/usr/bin/env python3
"""
Real-time TomTom API Credit Monitor
Continuously displays credit usage in terminal
"""

import sys
import os
import time
import signal
from pathlib import Path
from datetime import datetime

# Add current directory to path
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

class CreditMonitor:
    """Real-time credit monitoring"""
    
    def __init__(self):
        self.running = True
        self.refresh_interval = 10  # seconds
        
        # Handle Ctrl+C gracefully
        signal.signal(signal.SIGINT, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Handle Ctrl+C"""
        print("\n\n🛑 Monitor stopped by user")
        self.running = False
        sys.exit(0)
    
    def clear_screen(self):
        """Clear terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def display_header(self):
        """Display monitor header"""
        print("╔" + "═" * 68 + "╗")
        print("║" + " " * 18 + "TomTom API Credit Monitor" + " " * 25 + "║")
        print("║" + f" Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}" + " " * 24 + "║")
        print("╠" + "═" * 68 + "╣")
    
    def display_credit_status(self):
        """Display current credit status"""
        try:
            from utils.credit_tracker import get_credit_tracker
            tracker = get_credit_tracker()
            status = tracker.get_credit_status()
            
            # Format data
            requests_today = status['requests_today']
            successful = status['successful_today']
            failed = status['failed_today']
            quota = status['daily_quota']
            remaining = status['remaining']
            usage_percent = status['usage_percent']
            exhausted = status['credits_exhausted']
            
            # Status color and text
            if exhausted:
                status_color = "🔴"
                status_text = "EXHAUSTED"
            elif usage_percent > 90:
                status_color = "🟡"
                status_text = "CRITICAL"
            elif usage_percent > 75:
                status_color = "🟡"
                status_text = "WARNING"
            else:
                status_color = "🟢"
                status_text = "OK"
            
            # Display status
            print(f"║ Status: {status_color} {status_text:<10} Usage: {usage_percent:>6.1f}%" + " " * 20 + "║")
            print(f"║ Requests Today: {requests_today:>8,} / {quota:>8,} (Remaining: {remaining:>8,})" + " " * 7 + "║")
            print(f"║ Successful: {successful:>8,}     Failed: {failed:>8,}" + " " * 19 + "║")
            
            # Progress bar
            bar_width = 50
            filled = int(bar_width * usage_percent / 100)
            bar = "█" * filled + "░" * (bar_width - filled)
            print(f"║ [{bar}] {usage_percent:>5.1f}%" + " " * 8 + "║")
            
            return status
            
        except Exception as e:
            print(f"║ Error: {str(e):<56} ║")
            return None
    
    def display_collection_status(self):
        """Display collection status"""
        try:
            from utils.enhanced_traffic_collector import get_enhanced_collector
            collector = get_enhanced_collector()
            status = collector.get_collection_status()
            
            is_collecting = status.get('is_collecting', False)
            zones = status.get('zones_configured', 0)
            
            collecting_text = "🟢 Active" if is_collecting else "🔴 Stopped"
            
            print("╠" + "═" * 68 + "╣")
            print(f"║ Data Collection: {collecting_text:<15} Zones: {zones:<8}" + " " * 23 + "║")
            
            return status
            
        except Exception as e:
            print(f"║ Collection Error: {str(e):<48} ║")
            return None
    
    def display_recent_activity(self):
        """Display recent API activity"""
        try:
            from utils.credit_tracker import get_credit_tracker
            tracker = get_credit_tracker()
            history = tracker.get_usage_history(3)  # Last 3 days
            
            print("╠" + "═" * 68 + "╣")
            print("║ Recent Activity:" + " " * 50 + "║")
            
            for entry in history:
                date = entry['date']
                requests = entry['requests_made']
                successful = entry['successful_requests']
                failed = entry['failed_requests']
                
                if entry['credits_exhausted']:
                    status_icon = "🔴"
                elif requests > 40000:
                    status_icon = "🟡"
                else:
                    status_icon = "🟢"
                
                print(f"║ {status_icon} {date}: {requests:>6,} total ({successful:>6,} success, {failed:>4,} failed)" + " " * 8 + "║")
            
        except Exception as e:
            print(f"║ Activity Error: {str(e):<49} ║")
    
    def display_footer(self):
        """Display monitor footer"""
        print("╠" + "═" * 68 + "╣")
        print("║ Commands: Ctrl+C to stop, python code/check_api_status.py for details" + " " * 4 + "║")
        print("╚" + "═" * 68 + "╝")
    
    def run(self):
        """Run the monitor"""
        print("🚀 Starting TomTom API Credit Monitor...")
        print("Press Ctrl+C to stop")
        time.sleep(2)
        
        while self.running:
            try:
                self.clear_screen()
                self.display_header()
                
                credit_status = self.display_credit_status()
                self.display_collection_status()
                self.display_recent_activity()
                self.display_footer()
                
                # Alert if credits are exhausted
                if credit_status and credit_status.get('credits_exhausted'):
                    print("\n🚨 ALERT: API Credits Exhausted!")
                    print("Run 'python code/emergency_stop_collection.py' to stop collection")
                    print("Run 'python code/reset_credit_flag.py' after adding credits")
                
                # Wait before next refresh
                time.sleep(self.refresh_interval)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Monitor error: {e}")
                time.sleep(5)
        
        print("\n🛑 Monitor stopped")

if __name__ == "__main__":
    try:
        monitor = CreditMonitor()
        monitor.run()
    except Exception as e:
        print(f"Error starting monitor: {e}")
        sys.exit(1)