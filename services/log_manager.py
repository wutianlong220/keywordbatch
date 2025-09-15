"""
Logging System for Keyword Batch Processing Application
Provides real-time logging with different levels and categories
"""

import logging
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from enum import Enum
from dataclasses import dataclass, asdict
from pathlib import Path
import threading

class LogLevel(Enum):
    """Log level enumeration"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"

class LogCategory(Enum):
    """Log category enumeration"""
    SYSTEM = "system"
    FILE_PROCESSING = "file_processing"
    API = "api"
    TASK_MANAGEMENT = "task_management"
    USER_INTERFACE = "user_interface"
    BUSINESS_LOGIC = "business_logic"

@dataclass
class LogEntry:
    """Log entry data class"""
    timestamp: str
    level: LogLevel
    category: LogCategory
    message: str
    details: Optional[Dict[str, Any]] = None
    job_id: Optional[str] = None

class LogManager:
    """Centralized logging management system"""

    def __init__(self, max_logs: int = 1000):
        self.max_logs = max_logs
        self.logs: List[LogEntry] = []
        self.lock = threading.Lock()
        self.file_handler = None
        self._setup_file_logging()

    def _setup_file_logging(self):
        """Setup file-based logging"""
        try:
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)

            log_file = log_dir / f"app_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

            # Setup Python logging
            logging.basicConfig(
                level=logging.DEBUG,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler(log_file),
                    logging.StreamHandler()
                ]
            )

            self.logger = logging.getLogger(__name__)
            self.logger.info("LogManager initialized")

        except Exception as e:
            print(f"Failed to setup file logging: {e}")
            self.logger = logging.getLogger(__name__)

    def log(self, level: LogLevel, category: LogCategory, message: str,
            details: Optional[Dict[str, Any]] = None, job_id: Optional[str] = None):
        """Add a log entry"""
        entry = LogEntry(
            timestamp=datetime.now().isoformat(),
            level=level,
            category=category,
            message=message,
            details=details or {},
            job_id=job_id
        )

        with self.lock:
            self.logs.append(entry)

            # Keep only the most recent logs
            if len(self.logs) > self.max_logs:
                self.logs = self.logs[-self.max_logs:]

        # Also log to Python's logging system
        log_method = {
            LogLevel.DEBUG: self.logger.debug,
            LogLevel.INFO: self.logger.info,
            LogLevel.WARNING: self.logger.warning,
            LogLevel.ERROR: self.logger.error,
            LogLevel.SUCCESS: self.logger.info
        }.get(level, self.logger.info)

        log_method(f"[{category.value}] {message}")

    def debug(self, category: LogCategory, message: str, **kwargs):
        """Log debug message"""
        self.log(LogLevel.DEBUG, category, message, **kwargs)

    def info(self, category: LogCategory, message: str, **kwargs):
        """Log info message"""
        self.log(LogLevel.INFO, category, message, **kwargs)

    def warning(self, category: LogCategory, message: str, **kwargs):
        """Log warning message"""
        self.log(LogLevel.WARNING, category, message, **kwargs)

    def error(self, category: LogCategory, message: str, **kwargs):
        """Log error message"""
        self.log(LogLevel.ERROR, category, message, **kwargs)

    def success(self, category: LogCategory, message: str, **kwargs):
        """Log success message"""
        self.log(LogLevel.SUCCESS, category, message, **kwargs)

    def get_logs(self, level: Optional[LogLevel] = None,
                 category: Optional[LogCategory] = None,
                 job_id: Optional[str] = None,
                 limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get filtered logs"""
        with self.lock:
            filtered_logs = self.logs.copy()

        # Apply filters
        if level:
            filtered_logs = [log for log in filtered_logs if log.level == level]

        if category:
            filtered_logs = [log for log in filtered_logs if log.category == category]

        if job_id:
            filtered_logs = [log for log in filtered_logs if log.job_id == job_id]

        # Apply limit and sort by timestamp (newest first)
        if limit:
            filtered_logs = filtered_logs[-limit:]

        # Sort by timestamp (newest first)
        filtered_logs.sort(key=lambda x: x.timestamp, reverse=True)

        # Convert to dictionaries
        return [asdict(log) for log in filtered_logs]

    def get_recent_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent logs"""
        return self.get_logs(limit=limit)

    def get_job_logs(self, job_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get logs for a specific job"""
        return self.get_logs(job_id=job_id, limit=limit)

    def clear_logs(self):
        """Clear all logs"""
        with self.lock:
            self.logs.clear()

    def export_logs(self, filename: str, format: str = 'json'):
        """Export logs to file"""
        try:
            export_path = Path("logs") / filename

            if format.lower() == 'json':
                with open(export_path, 'w', encoding='utf-8') as f:
                    json.dump(self.get_logs(), f, indent=2, ensure_ascii=False)

            elif format.lower() == 'csv':
                import csv
                with open(export_path, 'w', newline='', encoding='utf-8') as f:
                    if self.logs:
                        writer = csv.DictWriter(f, fieldnames=[
                            'timestamp', 'level', 'category', 'message',
                            'details', 'job_id'
                        ])
                        writer.writeheader()
                        for log in self.get_logs():
                            # Flatten details for CSV
                            log_row = log.copy()
                            if log_row['details']:
                                for key, value in log_row['details'].items():
                                    log_row[f'detail_{key}'] = value
                                del log_row['details']
                            writer.writerow(log_row)

            self.success(LogCategory.SYSTEM, f"Logs exported to {export_path}")
            return True

        except Exception as e:
            self.error(LogCategory.SYSTEM, f"Failed to export logs: {str(e)}")
            return False

# Global log manager instance
log_manager = LogManager()