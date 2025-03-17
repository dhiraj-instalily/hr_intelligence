"""
Helpers module for common utility functions.
"""

import json
import os
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Union, Any

from .logger import get_logger

logger = get_logger(__name__)

def load_config(config_path: Union[str, Path] = None) -> Dict[str, Any]:
    """
    Load configuration from a YAML file.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        Configuration dictionary
    """
    if config_path is None:
        config_dir = os.environ.get('CONFIG_DIR', 'config')
        config_path = Path(config_dir) / 'config.yaml'
    else:
        config_path = Path(config_path)
        
    logger.info(f"Loading configuration from {config_path}")
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            
        return config
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        return {}

def load_prompt(prompt_name: str) -> str:
    """
    Load a prompt template from a file.
    
    Args:
        prompt_name: Name of the prompt file (without extension)
        
    Returns:
        Prompt template as a string
    """
    config_dir = os.environ.get('CONFIG_DIR', 'config')
    prompt_path = Path(config_dir) / 'prompts' / f"{prompt_name}.txt"
    
    logger.info(f"Loading prompt from {prompt_path}")
    
    try:
        with open(prompt_path, 'r', encoding='utf-8') as f:
            prompt = f.read()
            
        return prompt
    except Exception as e:
        logger.error(f"Error loading prompt: {e}")
        return ""

def ensure_dir(directory: Union[str, Path]) -> Path:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        directory: Directory path
        
    Returns:
        Path object for the directory
    """
    directory = Path(directory)
    directory.mkdir(exist_ok=True, parents=True)
    return directory

def save_json(data: Any, file_path: Union[str, Path], indent: int = 2) -> bool:
    """
    Save data as a JSON file.
    
    Args:
        data: Data to save
        file_path: Path to save the file
        indent: JSON indentation level
        
    Returns:
        True if successful, False otherwise
    """
    file_path = Path(file_path)
    
    # Ensure parent directory exists
    file_path.parent.mkdir(exist_ok=True, parents=True)
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent)
            
        logger.info(f"Saved JSON data to {file_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving JSON data: {e}")
        return False

def load_json(file_path: Union[str, Path]) -> Optional[Any]:
    """
    Load data from a JSON file.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        Loaded data, or None if an error occurred
    """
    file_path = Path(file_path)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        return data
    except Exception as e:
        logger.error(f"Error loading JSON data: {e}")
        return None

def format_error(error: Exception) -> Dict[str, str]:
    """
    Format an exception as a dictionary.
    
    Args:
        error: Exception to format
        
    Returns:
        Dictionary with error information
    """
    return {
        "error": str(error),
        "type": error.__class__.__name__
    }