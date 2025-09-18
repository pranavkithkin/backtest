"""
Enterprise Trading Signal Analysis Platform
===========================================

A comprehensive, scalable trading signal analysis platform designed for 
professional use across global markets with timezone support and advanced analytics.

Architecture:
- Modular design with clear separation of concerns
- Configuration-driven analysis
- Professional logging and monitoring
- Comprehensive testing framework
- Documentation and deployment ready
"""

__version__ = "2.0.0"
__author__ = "Trading Analytics Team"
__license__ = "MIT"

import os
import sys
from pathlib import Path

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Version and metadata
VERSION = __version__
PROJECT_NAME = "Enterprise Trading Signal Analyzer"
DESCRIPTION = "Professional-grade signal analysis with global timezone support"

# Configuration
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "default.yaml"
USER_CONFIG_PATH = PROJECT_ROOT / "config" / "user.yaml"

# Data directories
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"
REPORTS_DIR = PROJECT_ROOT / "reports"
LOGS_DIR = PROJECT_ROOT / "logs"

# Ensure directories exist
for directory in [DATA_DIR, OUTPUT_DIR, REPORTS_DIR, LOGS_DIR]:
    directory.mkdir(exist_ok=True)

# Import main components
from src.enterprise_analyzer import EnterpriseSignalAnalyzer
from src.utils.config_manager import ConfigManager
from src.utils.logger import setup_enterprise_logging

__all__ = [
    'EnterpriseSignalAnalyzer',
    'ConfigManager',
    'setup_enterprise_logging',
    'VERSION',
    'PROJECT_NAME',
    'DESCRIPTION'
]