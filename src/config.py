"""
Configuration Manager - Persistent settings storage.
"""
import os
import json
from typing import Optional, Any, Dict
from pathlib import Path


class ConfigManager:
    """
    Manages application configuration with persistent JSON storage.
    """
    
    DEFAULT_CONFIG = {
        'tesseract_path': r'C:\Program Files\Tesseract-OCR\tesseract.exe',
        'ocr_language': 'ces+eng',
        'theme': 'dark',
        'last_directory': '',
    }
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_dir: Directory to store config file. 
                       If None, uses app directory.
        """
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            # Store config next to the executable/script
            self.config_dir = Path(__file__).parent.parent
        
        self.config_file = self.config_dir / 'config.json'
        self.config: Dict[str, Any] = {}
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from file."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.config = {}
        
        # Merge with defaults (in case new settings were added)
        for key, default_value in self.DEFAULT_CONFIG.items():
            if key not in self.config:
                self.config[key] = default_value
    
    def save_config(self) -> None:
        """Save configuration to file."""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"Warning: Could not save config: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set a configuration value and save."""
        self.config[key] = value
        self.save_config()
    
    def get_tesseract_path(self) -> str:
        """Get Tesseract executable path."""
        return self.config.get('tesseract_path', self.DEFAULT_CONFIG['tesseract_path'])
    
    def set_tesseract_path(self, path: str) -> None:
        """Set Tesseract executable path."""
        self.set('tesseract_path', path)
    
    def get_ocr_language(self) -> str:
        """Get OCR language setting."""
        return self.config.get('ocr_language', self.DEFAULT_CONFIG['ocr_language'])
    
    def set_ocr_language(self, language: str) -> None:
        """Set OCR language."""
        self.set('ocr_language', language)
    
    def get_theme(self) -> str:
        """Get theme setting."""
        return self.config.get('theme', self.DEFAULT_CONFIG['theme'])
    
    def set_theme(self, theme: str) -> None:
        """Set theme."""
        self.set('theme', theme)


# Global config instance
_config_instance: Optional[ConfigManager] = None


def get_config() -> ConfigManager:
    """Get the global config manager instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigManager()
    return _config_instance
