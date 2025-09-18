"""
Enterprise Logging System
========================

Professional logging setup with rotation, formatting, and multiple handlers.
"""

import logging
import logging.handlers
import os
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime

class EnterpriseLogger:
    """Enterprise-grade logging with file rotation and structured output"""
    
    def __init__(self, name: str, config: Optional[Dict] = None):
        self.name = name
        self.config = config or self._get_default_config()
        self.logger = logging.getLogger(name)
        self._setup_logger()
    
    def _get_default_config(self) -> Dict:
        """Default logging configuration"""
        return {
            'level': 'INFO',
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'file_rotation': True,
            'max_file_size': '10MB',
            'backup_count': 5
        }
    
    def _setup_logger(self):
        """Setup logger with handlers and formatters"""
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Set level
        level = getattr(logging, self.config.get('level', 'INFO').upper())
        self.logger.setLevel(level)
        
        # Create formatter
        formatter = logging.Formatter(
            self.config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # File handler with rotation
        if self.config.get('file_rotation', True):
            logs_dir = Path(__file__).parent.parent.parent / "logs"
            logs_dir.mkdir(exist_ok=True)
            
            log_file = logs_dir / f"{self.name}.log"
            
            # Parse file size (e.g., "10MB" -> 10485760 bytes)
            max_size = self._parse_file_size(self.config.get('max_file_size', '10MB'))
            backup_count = self.config.get('backup_count', 5)
            
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=max_size,
                backupCount=backup_count
            )
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
        
        # Prevent propagation to root logger
        self.logger.propagate = False
    
    def _parse_file_size(self, size_str: str) -> int:
        """Parse size string like '10MB' to bytes"""
        units = {'B': 1, 'KB': 1024, 'MB': 1024**2, 'GB': 1024**3}
        size_str = size_str.upper().strip()
        
        for unit, multiplier in units.items():
            if size_str.endswith(unit):
                # Extract the numeric part correctly
                numeric_part = size_str[:-len(unit)]
                try:
                    return int(numeric_part) * multiplier
                except ValueError:
                    # If numeric part is empty or invalid, default to bytes
                    break
        
        # Default to bytes if no unit or invalid format
        try:
            return int(size_str)
        except ValueError:
            # Default fallback to 10MB
            return 10 * 1024 * 1024
    
    def get_logger(self) -> logging.Logger:
        """Get the configured logger instance"""
        return self.logger

def setup_enterprise_logging(config: Optional[Dict] = None) -> Dict[str, logging.Logger]:
    """Setup enterprise logging for all modules"""
    config = config or {}
    
    # Default loggers for different modules
    loggers = {}
    
    logger_configs = {
        'analyzer': config.get('loggers', {}).get('analyzer', 'INFO'),
        'data_processor': config.get('loggers', {}).get('data_processor', 'DEBUG'),
        'ml_engine': config.get('loggers', {}).get('ml_engine', 'INFO'),
        'exporter': config.get('loggers', {}).get('exporter', 'INFO'),
        'config': config.get('loggers', {}).get('config', 'INFO'),
        'main': config.get('loggers', {}).get('main', 'INFO')
    }
    
    # Create loggers
    for logger_name, level in logger_configs.items():
        logger_config = {
            'level': level,
            'format': config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
            'file_rotation': config.get('file_rotation', True),
            'max_file_size': config.get('max_file_size', '10MB'),
            'backup_count': config.get('backup_count', 5)
        }
        
        enterprise_logger = EnterpriseLogger(logger_name, logger_config)
        loggers[logger_name] = enterprise_logger.get_logger()
    
    return loggers

class AuditLogger:
    """Special logger for audit trails and compliance"""
    
    def __init__(self):
        self.logger = logging.getLogger('audit')
        self._setup_audit_logger()
    
    def _setup_audit_logger(self):
        """Setup audit logger with special formatting"""
        if self.logger.handlers:
            return  # Already configured
        
        # Audit logs have special format
        formatter = logging.Formatter(
            '%(asctime)s - AUDIT - %(levelname)s - %(message)s'
        )
        
        # File handler for audit trail
        logs_dir = Path(__file__).parent.parent.parent / "logs"
        logs_dir.mkdir(exist_ok=True)
        
        audit_file = logs_dir / "audit.log"
        file_handler = logging.handlers.RotatingFileHandler(
            audit_file,
            maxBytes=50*1024*1024,  # 50MB
            backupCount=10
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False
    
    def log_analysis_start(self, user: str, timezone: str, data_file: str):
        """Log analysis start for audit"""
        self.logger.info(f"ANALYSIS_START - User: {user}, Timezone: {timezone}, Data: {data_file}")
    
    def log_analysis_complete(self, user: str, duration: float, signals_count: int):
        """Log analysis completion for audit"""
        self.logger.info(f"ANALYSIS_COMPLETE - User: {user}, Duration: {duration:.2f}s, Signals: {signals_count}")
    
    def log_export(self, user: str, file_type: str, file_path: str):
        """Log data export for audit"""
        self.logger.info(f"DATA_EXPORT - User: {user}, Type: {file_type}, Path: {file_path}")
    
    def log_config_change(self, user: str, parameter: str, old_value: str, new_value: str):
        """Log configuration changes for audit"""
        self.logger.info(f"CONFIG_CHANGE - User: {user}, Parameter: {parameter}, Old: {old_value}, New: {new_value}")

class PerformanceLogger:
    """Logger for performance monitoring and metrics"""
    
    def __init__(self):
        self.logger = logging.getLogger('performance')
        self._setup_performance_logger()
    
    def _setup_performance_logger(self):
        """Setup performance logger"""
        if self.logger.handlers:
            return
        
        formatter = logging.Formatter(
            '%(asctime)s - PERF - %(message)s'
        )
        
        logs_dir = Path(__file__).parent.parent.parent / "logs"
        logs_dir.mkdir(exist_ok=True)
        
        perf_file = logs_dir / "performance.log"
        file_handler = logging.handlers.RotatingFileHandler(
            perf_file,
            maxBytes=20*1024*1024,  # 20MB
            backupCount=5
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False
    
    def log_timing(self, operation: str, duration: float, details: str = ""):
        """Log operation timing"""
        self.logger.info(f"TIMING - {operation}: {duration:.3f}s {details}")
    
    def log_memory_usage(self, operation: str, memory_mb: float):
        """Log memory usage"""
        self.logger.info(f"MEMORY - {operation}: {memory_mb:.2f}MB")
    
    def log_data_stats(self, operation: str, records_processed: int, rate_per_sec: float):
        """Log data processing statistics"""
        self.logger.info(f"DATA_STATS - {operation}: {records_processed} records, {rate_per_sec:.2f} rec/sec")

# Global logger instances
audit_logger = AuditLogger()
performance_logger = PerformanceLogger()

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance by name"""
    return logging.getLogger(name)

def log_timing(func):
    """Decorator to log function execution time"""
    import time
    import functools
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            performance_logger.log_timing(func.__name__, duration)
            return result
        except Exception as e:
            duration = time.time() - start_time
            performance_logger.log_timing(f"{func.__name__}_ERROR", duration, str(e))
            raise
    
    return wrapper