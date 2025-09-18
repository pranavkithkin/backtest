"""
Enterprise Configuration Manager
==============================

Handles configuration loading, validation, and management for the enterprise platform.
"""

import yaml
import os
from pathlib import Path
from typing import Dict, Any, Optional
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class TimezoneConfig:
    name: str
    code: str
    description: str

@dataclass
class AnalysisConfig:
    risk_ranges: list
    confidence_levels: list
    minimum_signals: dict

class ConfigManager:
    """Enterprise configuration manager with validation and defaults"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.project_root = Path(__file__).parent.parent.parent
        self.config_path = config_path or self.project_root / "config" / "default.yaml"
        self.user_config_path = self.project_root / "config" / "user.yaml"
        self._config = None
        self._load_config()
    
    def _load_config(self):
        """Load configuration from YAML files"""
        try:
            # Load default config
            with open(self.config_path, 'r') as f:
                self._config = yaml.safe_load(f)
            
            # Override with user config if exists
            if self.user_config_path.exists():
                with open(self.user_config_path, 'r') as f:
                    user_config = yaml.safe_load(f)
                    self._merge_configs(self._config, user_config)
            
            logger.info(f"Configuration loaded from {self.config_path}")
            
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            self._config = self._get_default_config()
    
    def _merge_configs(self, base_config: dict, override_config: dict):
        """Recursively merge user config into base config"""
        for key, value in override_config.items():
            if key in base_config and isinstance(base_config[key], dict) and isinstance(value, dict):
                self._merge_configs(base_config[key], value)
            else:
                base_config[key] = value
    
    def _get_default_config(self) -> dict:
        """Fallback default configuration"""
        return {
            'app': {
                'name': 'Enterprise Trading Signal Analyzer',
                'version': '2.0.0',
                'environment': 'production'
            },
            'timezones': {
                'default': 'Dubai',
                'supported': [
                    {'name': 'Dubai', 'code': 'Asia/Dubai', 'description': 'UAE Standard Time'}
                ]
            },
            'analysis': {
                'minimum_signals': {'risk_analysis': 5, 'time_analysis': 3}
            },
            'logging': {
                'level': 'INFO'
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot notation key"""
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_timezones(self) -> Dict[str, TimezoneConfig]:
        """Get supported timezones as TimezoneConfig objects"""
        timezones = {}
        for tz_data in self.get('timezones.supported', []):
            timezones[tz_data['name']] = TimezoneConfig(
                name=tz_data['name'],
                code=tz_data['code'],
                description=tz_data['description']
            )
        return timezones
    
    def get_analysis_config(self) -> AnalysisConfig:
        """Get analysis configuration"""
        return AnalysisConfig(
            risk_ranges=self.get('analysis.risk_ranges', []),
            confidence_levels=self.get('analysis.confidence_levels', [0.95]),
            minimum_signals=self.get('analysis.minimum_signals', {})
        )
    
    def get_asset_categories(self) -> Dict[str, Dict]:
        """Get asset category mappings"""
        return self.get('asset_categories', {})
    
    def get_market_sessions(self) -> Dict[str, Dict]:
        """Get market session definitions"""
        return self.get('market_sessions', {})
    
    def validate_config(self) -> bool:
        """Validate configuration completeness"""
        required_keys = [
            'app.name',
            'timezones.default',
            'analysis.minimum_signals'
        ]
        
        for key in required_keys:
            if self.get(key) is None:
                logger.error(f"Missing required configuration: {key}")
                return False
        
        return True
    
    def save_user_config(self, config_updates: dict):
        """Save user-specific configuration overrides"""
        try:
            self.user_config_path.parent.mkdir(exist_ok=True)
            with open(self.user_config_path, 'w') as f:
                yaml.dump(config_updates, f, default_flow_style=False)
            logger.info(f"User configuration saved to {self.user_config_path}")
        except Exception as e:
            logger.error(f"Failed to save user configuration: {e}")
    
    @property
    def config(self) -> dict:
        """Get full configuration dictionary"""
        return self._config.copy()
    
    def __str__(self) -> str:
        return f"ConfigManager(app={self.get('app.name')}, env={self.get('app.environment')})"