#regex_validation
import re
import logging
import os
logger = logging.getLogger(__name__)

def preprocess_input(text):
    text = ' '.join(text.strip().split())
    corrections = {
        "gamil.com": "gmail.com",
        "volumne": "volume",
        "brigtness": "brightness",
        "play on": "search on",
        "sound": "volume"
    }
    text_lower = text.lower()
    for wrong, correct in corrections.items():
        text_lower = text_lower.replace(wrong, correct)
    return text_lower

def match_command(text):
    patterns = [
        r"(?:send\s+a\s*)?(formal|informal)?\s*email\s*to\s*([\w@.]+)\s*(.*)",
        r"(?:open\s*notepad\s*and\s*)?(?:write|write\s+me|generate)\s*(?:the\s*)?(.+?)\s*in\s*notepad",
        r"send\s+a\s*message\s*to\s*(\+?\d+)\s*(?:to|about|regarding|concerning)?\s*(.+)",
        r"send\s+a\s*([\w\s]+)\s*to\s*(\+?\d+)\s*on\s*(\w+)",
        r"set\s+(brightness|volume)\s+to\s+(\d+)%",
        r"(?:search|play)\s+(.+?)\s+on\s+(\w+)",
        r"search\s+(.+?)\s+in\s+store",
        r"(?:create|add)\s+(?:a\s+)?task\s*[.:]?\s*(.+?)(?:\s+due\s+(.+?))?$",
        r"(?:list|show|view)\s+(?:all\s+)?tasks?",
        r"(?:update|edit)\s+task\s+(.+?)(?:\s+to\s+(.+))?$",
        r"(?:delete|remove)\s+task\s+(.+)",
        r"(?:create|schedule|add)\s+(?:an\s+)?event\s*[.:]?\s*(.+?)(?:\s+(?:on|at|for)\s+(.+?))?$",
        r"(?:show|list|view)\s+(?:all\s+)?events?(?:\s+(?:for|on)\s+(.+))?$",
        r"(?:update|edit|change)\s+event\s+(.+?)(?:\s+to\s+(.+))?$",
        r"(?:delete|remove|cancel)\s+event\s+(.+)"
    ]
    for pattern in patterns:
        if re.match(pattern, text.lower(), re.IGNORECASE):
            return True
    return False

def is_safe_command(code):
    dangerous_keywords = ['rm -rf', 'del /F /Q', 'format ', 'os.remove', 'sys.exit']
    code_lower = code.lower()
    for keyword in dangerous_keywords:
        if keyword in code_lower:
            logger.warning(f"Blocked unsafe command containing: {keyword}")
            return False
    return True

def safe_file_path(path):
    return path.startswith(os.path.expanduser("~"))