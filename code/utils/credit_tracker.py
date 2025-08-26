#!/usr/bin/env python3
"""
TomTom API Credit Tracking System
Persistent tracking of API usage and credits
"""

import json
import os
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class CreditTracker:
    """Track TomTom API credits and usage persistently"""
    
    def __init__(self):
        self.db_path = self._get_db_path()
        self.init_database()
        
        # Load persisted state
        self.load_state()
        
    def _get_db_path(self) -> str:
        """Get database path for credit tracking"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(current_dir))
        data_dir = os.path.join(project_root, "data")
        os.makedirs(data_dir, exist_ok=True)
        return os.path.join(data_dir, "api_credits.db")
    
    def init_database(self):
        """Initialize credit tracking database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # API usage tracking table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                endpoint TEXT NOT NULL,
                status_code INTEGER NOT NULL,
                credits_used INTEGER DEFAULT 1,
                error_code TEXT,
                error_message TEXT
            )
        ''')
        
        # Daily credit summary table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_credits (
                date DATE PRIMARY KEY,
                requests_made INTEGER DEFAULT 0,
                successful_requests INTEGER DEFAULT 0,
                failed_requests INTEGER DEFAULT 0,
                credits_exhausted BOOLEAN DEFAULT FALSE,
                quota_limit INTEGER DEFAULT 50000,
                last_updated DATETIME
            )
        ''')
        
        # Credit state table (for persistence)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS credit_state (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def load_state(self):
        """Load persisted credit state"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        today = datetime.now().date()
        
        # Get or create today's record
        cursor.execute('''
            SELECT requests_made, successful_requests, failed_requests, 
                   credits_exhausted, quota_limit
            FROM daily_credits
            WHERE date = ?
        ''', (today,))
        
        result = cursor.fetchone()
        
        if result:
            self.requests_today = result[0]
            self.successful_today = result[1]
            self.failed_today = result[2]
            self.credits_exhausted = bool(result[3])
            self.daily_quota = result[4]
        else:
            # Initialize for today
            self.requests_today = 0
            self.successful_today = 0
            self.failed_today = 0
            self.credits_exhausted = False
            self.daily_quota = 50000
            
            cursor.execute('''
                INSERT INTO daily_credits 
                (date, requests_made, successful_requests, failed_requests, 
                 credits_exhausted, quota_limit, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (today, 0, 0, 0, 0, self.daily_quota, datetime.now()))
            conn.commit()
        
        conn.close()
        
        logger.info(f"Loaded credit state: {self.requests_today}/{self.daily_quota} requests")
    
    def record_api_call(self, endpoint: str, status_code: int, 
                       error_code: Optional[str] = None, 
                       error_message: Optional[str] = None):
        """Record an API call and update credits"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Record the API call
        cursor.execute('''
            INSERT INTO api_usage 
            (timestamp, endpoint, status_code, error_code, error_message)
            VALUES (?, ?, ?, ?, ?)
        ''', (datetime.now(), endpoint, status_code, error_code, error_message))
        
        # Update daily totals
        today = datetime.now().date()
        
        if status_code == 200:
            self.requests_today += 1
            self.successful_today += 1
        elif status_code == 403 and error_code == 'InsufficientFunds':
            self.credits_exhausted = True
            self.failed_today += 1
        else:
            self.requests_today += 1
            self.failed_today += 1
        
        # Update database
        cursor.execute('''
            UPDATE daily_credits
            SET requests_made = ?,
                successful_requests = ?,
                failed_requests = ?,
                credits_exhausted = ?,
                last_updated = ?
            WHERE date = ?
        ''', (self.requests_today, self.successful_today, self.failed_today,
              1 if self.credits_exhausted else 0, datetime.now(), today))
        
        conn.commit()
        conn.close()
        
        # Log credit status
        remaining = self.daily_quota - self.requests_today
        logger.info(f"API call recorded: {status_code} | Credits: {self.requests_today}/{self.daily_quota} used ({remaining} remaining)")
    
    def get_credit_status(self) -> Dict:
        """Get current credit status"""
        remaining = self.daily_quota - self.requests_today
        usage_percent = (self.requests_today / self.daily_quota * 100) if self.daily_quota > 0 else 0
        
        return {
            'requests_today': self.requests_today,
            'successful_today': self.successful_today,
            'failed_today': self.failed_today,
            'daily_quota': self.daily_quota,
            'remaining': remaining,
            'usage_percent': usage_percent,
            'credits_exhausted': self.credits_exhausted,
            'last_updated': datetime.now()
        }
    
    def get_usage_history(self, days: int = 7) -> list:
        """Get usage history for the last N days"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        start_date = datetime.now().date() - timedelta(days=days)
        
        cursor.execute('''
            SELECT date, requests_made, successful_requests, failed_requests, 
                   credits_exhausted, quota_limit
            FROM daily_credits
            WHERE date >= ?
            ORDER BY date DESC
        ''', (start_date,))
        
        results = cursor.fetchall()
        conn.close()
        
        history = []
        for row in results:
            history.append({
                'date': row[0],
                'requests_made': row[1],
                'successful_requests': row[2],
                'failed_requests': row[3],
                'credits_exhausted': bool(row[4]),
                'quota_limit': row[5]
            })
        
        return history
    
    def reset_credits(self):
        """Reset credit exhaustion flag (for when credits are added)"""
        self.credits_exhausted = False
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        today = datetime.now().date()
        cursor.execute('''
            UPDATE daily_credits
            SET credits_exhausted = 0,
                last_updated = ?
            WHERE date = ?
        ''', (datetime.now(), today))
        
        conn.commit()
        conn.close()
        
        logger.info("Credit exhaustion flag reset")
    
    def reset_daily_counter(self):
        """Reset daily counter (for new day)"""
        today = datetime.now().date()
        
        # Check if we need to create a new day's record
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM daily_credits WHERE date = ?', (today,))
        exists = cursor.fetchone()[0] > 0
        
        if not exists:
            cursor.execute('''
                INSERT INTO daily_credits 
                (date, requests_made, successful_requests, failed_requests, 
                 credits_exhausted, quota_limit, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (today, 0, 0, 0, 0, self.daily_quota, datetime.now()))
            conn.commit()
            
            # Reset counters
            self.requests_today = 0
            self.successful_today = 0
            self.failed_today = 0
            self.credits_exhausted = False
            
            logger.info(f"Daily counters reset for {today}")
        
        conn.close()
    
    def display_terminal_status(self):
        """Display formatted credit status in terminal"""
        status = self.get_credit_status()
        
        # Colors for terminal
        RED = '\033[91m'
        YELLOW = '\033[93m'
        GREEN = '\033[92m'
        BOLD = '\033[1m'
        RESET = '\033[0m'
        
        # Determine color based on usage
        if status['credits_exhausted']:
            color = RED
            status_text = "EXHAUSTED"
        elif status['usage_percent'] > 90:
            color = RED
            status_text = "CRITICAL"
        elif status['usage_percent'] > 75:
            color = YELLOW
            status_text = "WARNING"
        else:
            color = GREEN
            status_text = "OK"
        
        # Format the display
        print(f"\n{BOLD}TomTom API Credit Status{RESET}")
        print("=" * 50)
        print(f"Status: {color}{status_text}{RESET}")
        print(f"Requests Today: {status['requests_today']:,}")
        print(f"Daily Quota: {status['daily_quota']:,}")
        print(f"Remaining: {color}{status['remaining']:,}{RESET}")
        print(f"Usage: {status['usage_percent']:.1f}%")
        print(f"Successful: {status['successful_today']:,}")
        print(f"Failed: {status['failed_today']:,}")
        print(f"Last Updated: {status['last_updated'].strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 50)

# Global instance
_credit_tracker = None

def get_credit_tracker() -> CreditTracker:
    """Get global credit tracker instance"""
    global _credit_tracker
    if _credit_tracker is None:
        _credit_tracker = CreditTracker()
    return _credit_tracker