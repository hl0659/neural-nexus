"""
Neural Nexus v3.0 - Logging Utility
Configures logging to both console and file
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional


class CollectionLogger:
    """Sets up logging for collection services"""
    
    def __init__(self, service_name: str, log_dir: str = "F:/neural_nexus_data_v3/logs"):
        self.service_name = service_name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create timestamped log file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = self.log_dir / f"{service_name}_{timestamp}.log"
        
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """Configure logger with file and console handlers"""
        logger = logging.getLogger(self.service_name)
        logger.setLevel(logging.DEBUG)
        
        # Remove existing handlers
        logger.handlers = []
        
        # File handler (detailed logs)
        file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        
        # Console handler (important logs only)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter('%(message)s')
        console_handler.setFormatter(console_formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def get_logger(self) -> logging.Logger:
        """Get the configured logger"""
        return self.logger
    
    def info(self, message: str):
        """Log info message"""
        self.logger.info(message)
    
    def debug(self, message: str):
        """Log debug message"""
        self.logger.debug(message)
    
    def warning(self, message: str):
        """Log warning message"""
        self.logger.warning(message)
    
    def error(self, message: str):
        """Log error message"""
        self.logger.error(message)
    
    def critical(self, message: str):
        """Log critical message"""
        self.logger.critical(message)


def get_logger(service_name: str) -> CollectionLogger:
    """Quick helper to get a logger"""
    return CollectionLogger(service_name)


if __name__ == "__main__":
    # Test logger
    print("Testing Collection Logger...")
    print("="*60)
    
    logger = get_logger('test')
    
    print(f"\nLog file: {logger.log_file}")
    print("\nGenerating test logs...")
    
    logger.info("This is an info message (shown in console)")
    logger.debug("This is a debug message (file only)")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    
    print(f"\n✓ Logs written to: {logger.log_file}")
    print("\nCheck the log file to see detailed logs!")
    print("="*60)