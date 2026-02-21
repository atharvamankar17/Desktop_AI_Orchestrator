#config_manager
import json
import os
import logging
logger = logging.getLogger(__name__)
CONFIG_FILE = 'config.json'

def load_config():
    """Load configuration from JSON file."""
    if not os.path.exists(CONFIG_FILE):
        logger.warning(f"Config file not found. Creating default: {CONFIG_FILE}")
        default_config = {
            "github": {
                "token": "your_github_personal_access_token"
            },
            "google": {
                "client_secrets_file": "client_secret.json",
                "token_file": "token.pickle"
            },
            "ollama": {
                "url": "http://localhost:11434",
                "model": "phi3"
            },
            "AI_API": {  
                "provider": "openai",  
                "api_key": "your_openai_api_key",
                "model": "gpt-3.5-turbo",
                "endpoint": "https://api.openai.com/v1/chat/completions"  
            }
        }
        with open(CONFIG_FILE, 'w') as f:
            json.dump(default_config, f, indent=4)
        return default_config
    
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
        
        
        if "api_AI" in config and "AI_API" not in config:
            logger.info("Migrating config from 'api_AI' to 'AI_API'")
            config["AI_API"] = config.pop("api_AI")
            
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=4)
        
        return config
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return None

def get_config():
    """Get the configuration dictionary."""
    config = load_config()
    if not config:
        raise RuntimeError("Failed to load configuration")
    return config