"""
Logger Configuration

Provides comprehensive logging setup and configuration for the test automation system.
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import json


class LoggerConfig:
    """
    Centralized logging configuration for the test automation system.
    
    Provides structured logging with multiple handlers, formatters, and log levels.
    """
    
    DEFAULT_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    DETAILED_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s'
    JSON_FORMAT = '{"timestamp": "%(asctime)s", "logger": "%(name)s", "level": "%(levelname)s", "message": "%(message)s", "module": "%(module)s", "function": "%(funcName)s", "line": %(lineno)d}'
    
    def __init__(self, 
                 log_dir: str = "logs",
                 log_level: str = "INFO",
                 max_file_size: int = 10 * 1024 * 1024,  # 10MB
                 backup_count: int = 5,
                 enable_console: bool = True,
                 enable_file: bool = True,
                 enable_json: bool = False,
                 enable_syslog: bool = False):
        
        self.log_dir = Path(log_dir)
        self.log_level = getattr(logging, log_level.upper())
        self.max_file_size = max_file_size
        self.backup_count = backup_count
        self.enable_console = enable_console
        self.enable_file = enable_file
        self.enable_json = enable_json
        self.enable_syslog = enable_syslog
        
        # Create log directory
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Logger instances
        self.loggers: Dict[str, logging.Logger] = {}
        
        # Handlers
        self.handlers: Dict[str, logging.Handler] = {}
        
        # Setup root logger
        self._setup_root_logger()
    
    def _setup_root_logger(self):
        """Setup root logger configuration"""
        root_logger = logging.getLogger()
        root_logger.setLevel(self.log_level)
        
        # Clear existing handlers
        root_logger.handlers.clear()
        
        # Add handlers
        if self.enable_console:
            self._add_console_handler(root_logger)
        
        if self.enable_file:
            self._add_file_handler(root_logger, "application.log")
        
        if self.enable_json:
            self._add_json_handler(root_logger, "application.json")
        
        if self.enable_syslog:
            self._add_syslog_handler(root_logger)
    
    def _add_console_handler(self, logger: logging.Logger):
        """Add console handler"""
        if 'console' not in self.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setLevel(self.log_level)
            
            # Use colored formatter if available
            try:
                from colorlog import ColoredFormatter
                formatter = ColoredFormatter(
                    '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    log_colors={
                        'DEBUG': 'cyan',
                        'INFO': 'green',
                        'WARNING': 'yellow',
                        'ERROR': 'red',
                        'CRITICAL': 'red,bg_white',
                    }
                )
            except ImportError:
                formatter = logging.Formatter(
                    self.DEFAULT_FORMAT,
                    datefmt='%Y-%m-%d %H:%M:%S'
                )
            
            handler.setFormatter(formatter)
            self.handlers['console'] = handler
        
        logger.addHandler(self.handlers['console'])
    
    def _add_file_handler(self, logger: logging.Logger, filename: str):
        """Add rotating file handler"""
        handler_name = f'file_{filename}'
        
        if handler_name not in self.handlers:
            file_path = self.log_dir / filename
            handler = logging.handlers.RotatingFileHandler(
                file_path,
                maxBytes=self.max_file_size,
                backupCount=self.backup_count,
                encoding='utf-8'
            )
            handler.setLevel(self.log_level)
            
            formatter = logging.Formatter(
                self.DETAILED_FORMAT,
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)
            
            self.handlers[handler_name] = handler
        
        logger.addHandler(self.handlers[handler_name])
    
    def _add_json_handler(self, logger: logging.Logger, filename: str):
        """Add JSON file handler"""
        handler_name = f'json_{filename}'
        
        if handler_name not in self.handlers:
            file_path = self.log_dir / filename
            handler = logging.handlers.RotatingFileHandler(
                file_path,
                maxBytes=self.max_file_size,
                backupCount=self.backup_count,
                encoding='utf-8'
            )
            handler.setLevel(self.log_level)
            
            formatter = JsonFormatter()
            handler.setFormatter(formatter)
            
            self.handlers[handler_name] = handler
        
        logger.addHandler(self.handlers[handler_name])
    
    def _add_syslog_handler(self, logger: logging.Logger):
        """Add syslog handler"""
        if 'syslog' not in self.handlers:
            try:
                if sys.platform.startswith('win'):
                    # Windows Event Log
                    handler = logging.handlers.NTEventLogHandler('TestAutomation')
                else:
                    # Unix syslog
                    handler = logging.handlers.SysLogHandler(address='/dev/log')
                
                handler.setLevel(self.log_level)
                
                formatter = logging.Formatter(
                    'TestAutomation: %(name)s - %(levelname)s - %(message)s'
                )
                handler.setFormatter(formatter)
                
                self.handlers['syslog'] = handler
                
            except Exception as e:
                print(f"Failed to setup syslog handler: {e}")
                return
        
        logger.addHandler(self.handlers['syslog'])
    
    def get_logger(self, name: str, 
                   log_file: Optional[str] = None,
                   log_level: Optional[str] = None) -> logging.Logger:
        """
        Get or create a logger with specific configuration.
        
        Args:
            name: Logger name
            log_file: Optional specific log file for this logger
            log_level: Optional specific log level for this logger
            
        Returns:
            Configured logger instance
        """
        if name in self.loggers:
            return self.loggers[name]
        
        logger = logging.getLogger(name)
        logger.setLevel(log_level or self.log_level)
        
        # Don't propagate to root logger if we're adding specific handlers
        if log_file:
            logger.propagate = False
            
            # Add console handler
            if self.enable_console:
                self._add_console_handler(logger)
            
            # Add specific file handler
            if self.enable_file:
                self._add_file_handler(logger, log_file)
            
            # Add JSON handler if enabled
            if self.enable_json:
                json_file = log_file.replace('.log', '.json')
                self._add_json_handler(logger, json_file)
        
        self.loggers[name] = logger
        return logger
    
    def get_agent_logger(self, agent_name: str) -> logging.Logger:
        """Get logger for specific agent"""
        return self.get_logger(
            f'agent.{agent_name}',
            log_file=f'agent_{agent_name}.log'
        )
    
    def get_workflow_logger(self, workflow_id: str) -> logging.Logger:
        """Get logger for specific workflow"""
        return self.get_logger(
            f'workflow.{workflow_id}',
            log_file=f'workflow_{workflow_id}.log'
        )
    
    def get_system_logger(self) -> logging.Logger:
        """Get system logger"""
        return self.get_logger(
            'system',
            log_file='system.log'
        )
    
    def get_api_logger(self) -> logging.Logger:
        """Get API logger"""
        return self.get_logger(
            'api',
            log_file='api.log'
        )
    
    def get_scheduler_logger(self) -> logging.Logger:
        """Get scheduler logger"""
        return self.get_logger(
            'scheduler',
            log_file='scheduler.log'
        )
    
    def set_log_level(self, level: str):
        """Set log level for all loggers"""
        self.log_level = getattr(logging, level.upper())
        
        # Update root logger
        logging.getLogger().setLevel(self.log_level)
        
        # Update all handlers
        for handler in self.handlers.values():
            handler.setLevel(self.log_level)
        
        # Update all loggers
        for logger in self.loggers.values():
            logger.setLevel(self.log_level)
    
    def add_custom_handler(self, name: str, handler: logging.Handler):
        """Add custom handler"""
        self.handlers[name] = handler
        
        # Add to root logger
        logging.getLogger().addHandler(handler)
    
    def remove_handler(self, name: str):
        """Remove handler"""
        if name in self.handlers:
            handler = self.handlers[name]
            
            # Remove from root logger
            logging.getLogger().removeHandler(handler)
            
            # Remove from all loggers
            for logger in self.loggers.values():
                logger.removeHandler(handler)
            
            # Close handler
            handler.close()
            
            del self.handlers[name]
    
    def cleanup(self):
        """Cleanup all handlers and loggers"""
        for handler in self.handlers.values():
            handler.close()
        
        self.handlers.clear()
        self.loggers.clear()
    
    def get_log_files(self) -> Dict[str, str]:
        """Get list of log files"""
        log_files = {}
        
        for log_file in self.log_dir.glob('*.log'):
            log_files[log_file.stem] = str(log_file)
        
        return log_files
    
    def get_log_stats(self) -> Dict[str, Any]:
        """Get logging statistics"""
        stats = {
            'log_directory': str(self.log_dir),
            'log_level': logging.getLevelName(self.log_level),
            'handlers_count': len(self.handlers),
            'loggers_count': len(self.loggers),
            'log_files': []
        }
        
        # Get log file information
        for log_file in self.log_dir.glob('*.log'):
            try:
                file_stats = log_file.stat()
                stats['log_files'].append({
                    'name': log_file.name,
                    'size': file_stats.st_size,
                    'modified': datetime.fromtimestamp(file_stats.st_mtime).isoformat()
                })
            except Exception:
                pass
        
        return stats


class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record):
        log_entry = {
            'timestamp': self.formatTime(record),
            'logger': record.name,
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                          'filename', 'module', 'lineno', 'funcName', 'created', 
                          'msecs', 'relativeCreated', 'thread', 'threadName', 
                          'processName', 'process', 'getMessage', 'exc_info', 
                          'exc_text', 'stack_info']:
                log_entry[key] = value
        
        return json.dumps(log_entry)


def setup_logging(config: Optional[Dict[str, Any]] = None) -> LoggerConfig:
    """
    Setup logging configuration for the application.
    
    Args:
        config: Optional configuration dictionary
        
    Returns:
        LoggerConfig instance
    """
    if config is None:
        config = {}
    
    # Default configuration
    default_config = {
        'log_dir': 'logs',
        'log_level': 'INFO',
        'max_file_size': 10 * 1024 * 1024,  # 10MB
        'backup_count': 5,
        'enable_console': True,
        'enable_file': True,
        'enable_json': False,
        'enable_syslog': False
    }
    
    # Merge with provided config
    default_config.update(config)
    
    # Create logger config
    logger_config = LoggerConfig(**default_config)
    
    return logger_config


def get_logger(name: str) -> logging.Logger:
    """
    Get logger instance.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


# Context manager for temporary log level
class LogLevel:
    """Context manager for temporary log level changes"""
    
    def __init__(self, logger: logging.Logger, level: str):
        self.logger = logger
        self.new_level = getattr(logging, level.upper())
        self.old_level = None
    
    def __enter__(self):
        self.old_level = self.logger.level
        self.logger.setLevel(self.new_level)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logger.setLevel(self.old_level)