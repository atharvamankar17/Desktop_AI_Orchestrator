#conversation
import logging
import requests
import ollama
import re
from collections import deque
from config_manager import get_config

logger = logging.getLogger(__name__)
config = get_config()

try:
    response = requests.get(config['ollama']['url'], timeout=2)
    if response.status_code != 200:
        raise Exception("Ollama server not responding.")
    logger.info("Ollama server running")
    ollama_available = True
except Exception as e:
    logger.error(f"Ollama error: {e}")
    ollama_available = False

conversation_history = deque(maxlen=10)

def authenticate(text):
    return "my passphrase is xyz" in text.lower()

def generate_content(content_type, recipient=None):
    if recipient:
        recipient = recipient.lower().replace("gamil.com", "gmail.com")
    email_match = re.match(r"(?:send\s+a\s*)?(formal|informal)?\s*email\s*(?:to\s*[\w@.]+)?\s*(.*)", content_type.lower(), re.IGNORECASE)
    if email_match:
        formality, purpose = email_match.groups()
        formality = formality or "formal"
        purpose = purpose.strip() or "general communication"
        prompt = f"Generate a {formality} email body for {purpose}. Include a suitable subject line. Return in the format: ```email\n<recipient>;<subject>;<body>\n```"
        logger.info(f"Generating email content with prompt: {prompt}")
        response = query_ollama(prompt)
        content = response.strip()
        if content.startswith('```email') and content.endswith('```'):
            content = content.strip('```email\n').strip('\n```')
            parts = content.split(";")
            if len(parts) >= 3:
                recipient_part = parts[0].strip()
                subject_part = parts[1].strip()
                body_part = ";".join(parts[2:]).strip()
                
                if recipient and '@' in recipient and '.' in recipient.split('@')[1]:
                    content = f"{recipient_part};{subject_part};{body_part}"
                    return f"Subject: {subject_part}\n\n{body_part}", recipient_part
                else:
                    logger.error(f"Invalid recipient email: {recipient_part}")
                    return "Error: Invalid recipient email address."
        
        logger.warning("Invalid email response from AI, generating fallback email")
        if formality == "formal":
            subject = f"Request Regarding {purpose.capitalize()}"
            body = (
                f"Dear {recipient.split('@')[0].capitalize()},\n\n"
                f"I hope this message finds you well. I am writing to discuss {purpose}. "
                f"Please let me know a suitable time to address this matter further.\n\n"
                f"Best regards,\nYour Name"
            )
        else:
            subject = f"About {purpose.capitalize()}"
            body = (
                f"Hi {recipient.split('@')[0].capitalize()},\n\n"
                f"Just reaching out about {purpose}. Let me know what you think!\n\n"
                f"Cheers,\nYour Name"
            )
        content = f"Subject: {subject}\n\n{body}"
        logger.info(f"Generated email content: {content[:50]}...")
        return content, recipient
    code_match = re.match(r"code\s+for\s+(.+?)\s+in\s+(\w+)\s*(?:language)?", content_type.lower(), re.IGNORECASE)
    if code_match:
        task, language = code_match.groups()
        if "fibonacci" in task.lower():
            task = task.replace("upto n digits", "up to n terms").replace("up to n digits", "up to n terms")
        prompt = f"Generate complete, executable code for {task} in {language} (no titles, no explanations, only the code). Return in the format: ```content\n<content>\n```"
    else:
        prompt = f"Generate a concise {content_type} (no titles, no extra formatting, only the content). Return in the format: ```content\n<content>\n```"
    logger.info(f"Generating content for: {content_type} with prompt: {prompt}")
    response = query_ollama(prompt)
    content = response.strip()
    if content.startswith('```content') and content.endswith('```'):
        content = content.strip('```content\n').strip('\n```').strip('\n')
    elif code_match and ("sorry" not in content.lower()):
        code_block = re.search(rf'```(?:{language}|{language.upper()}|c\+\+|cpp)\n([\s\S]*?)\n```', content, re.IGNORECASE)
        if code_block:
            content = code_block.group(1).strip('\n')
        else:
            logger.error(f"No valid code block for {language} in response: {content[:50]}...")
            content = f"Error: Unable to generate {language} code for requested task."
    elif not code_match and "sorry" not in content.lower():
        content = content.strip('\n')
    else:
        logger.error(f"Invalid AI response for {content_type}: {content[:50]}...")
        content = f"Error: Unable to generate requested {content_type}."
    logger.info(f"Generated {content_type}: {content[:50]}...")
    return content, None

def query_ollama(text, is_conversational=False, api_key=None):
    try:
        if "sensitive" in text.lower() and not authenticate(text):
            logger.error("Authentication failed for sensitive query")
            return "Authentication failed."
        
        ai_api_config = config.get('AI_API', {})
        api_key = api_key or ai_api_config.get('api_key')
        provider = ai_api_config.get('provider', 'openai')
        model = ai_api_config.get('model', 'gpt-3.5-turbo')
        endpoint = ai_api_config.get('endpoint', 'https://api.openai.com/v1/chat/completions')
        
        if api_key and api_key != "your_openai_api_key":
            try:
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                data = {
                    "model": model,
                    "messages": [{"role": "user", "content": text}]
                }
                logger.info(f"Attempting API call to {provider} at {endpoint}")
                response = requests.post(endpoint, headers=headers, json=data, timeout=10)
                if response.status_code == 200:
                    logger.info("API call successful")
                    return response.json()["choices"][0]["message"]["content"]
                else:
                    logger.warning(f"API call failed: {response.status_code} - {response.text}")
            except Exception as e:
                logger.warning(f"API call error: {e}")
        
        if not ollama_available:
            logger.error("Both API and local Ollama unavailable")
            return "Both API and local Ollama unavailable. Please configure an API key or start Ollama."
        
        logger.info("Using Ollama for request")
        messages = [
            {
                "role": "system",
                "content": """You are a versatile AI assistant. For general queries (e.g., questions, explanations, conversations) or if explicitly marked as conversational, return a concise, plain text response with no markdown, code blocks, or command blocks. For specific commands, adhere strictly to these formats:
- For code generation (e.g., 'write code for [...] in <language> in notepad'), return only the complete, executable code in the specified language (no titles, no explanations, only the code) in the format: ```content\n<content>\n```. Ensure the code is syntactically correct and matches the requested language (e.g., C for 'C language').
- For text content (e.g., 'write a poem in notepad', 'product a list in notepad'), return only the content (no titles, no extra formatting, only the content) in the format: ```content\n<content>\n```. Allow any valid content, including single lines, single characters, multiple paragraphs, or empty lines.
- Preserve all formatting including empty lines, single characters, or unconventional formatting in content blocks.
- For search commands (e.g., 'search [...] on [...]'), return: ```youtube\n<query>\n```, ```spotify\n<query>\n```, or ```web\n<platform>;<query>\n``` where query is a single string without semicolons or newlines.
- For brightness control, return: ```brightness\nset;<value>\n``` where value is 0-100.
- For volume control, return: ```volume\nset;<value>\n``` where value is 0-100.
- For calendar commands, return: ```calendar\nfetch;<date>\n``` where date is in MM/DD/YYYY format.
- For emails, return: ```email\n<recipient>;<subject>;<body>\n``` where recipient is a complete email address, subject is concise, and body is the email content.
- Other commands use ```cmd```, ```app_action```, ```filemanager```, ```github```, ```task``` or ```store``` formats.
- Return exactly one response: either plain text for conversational queries or a single command block for commands. For code or text content for Notepad, ensure the response is a single ```content``` block with the requested content, preserving all lines including blank ones. Do not reject content based on length or structure. If the command includes 'Fibonacci series up to n digits', interpret it as 'up to n terms'.
- For shell-like commands such as "cal -y \"8/13/2025\"", convert them to the appropriate internal command format. For example, calendar commands should be converted to ```calendar\nfetch;MM/DD/YYYY\n```."""
            }
        ]
        messages.extend(conversation_history)
        messages.append({"role": "user", "content": text})
        
        try:
            response = ollama.chat(model=config['ollama']['model'], messages=messages)
            content = response["message"]["content"].strip()
            logger.info(f"Ollama response: {content[:50]}...")
            
            if is_conversational:
                if content.startswith('```') and content.endswith('```'):
                    content = re.sub(r'^```[\w\s]*\n([\s\S]*?)\n```$', r'\1', content).strip()
                    logger.info(f"Stripped command block from conversational response: {content[:50]}...")
                elif '```' in content:
                    match = re.search(r'```[\w\s]*\n([\s\S]*?)\n```', content)
                    if match:
                        content = match.group(1).strip()
                        logger.info(f"Extracted first command block from conversational response: {content[:50]}...")
                return content
            
            content_match = re.match(r"(?:open\s*notepad\s*and\s*)?(?:write|write\s+me|generate)\s*(?:the\s*)?(.+?)\s*in\s*notepad", text.lower(), re.IGNORECASE)
            if content_match:
                if not content.startswith('```content') or not content.endswith('```'):
                    code_block = re.search(r'```(?:\w+\s*)?\n([\s\S]*?)\n```', content, re.IGNORECASE)
                    if code_block:
                        stripped_code = code_block.group(1).rstrip()
                        content = f"```content\n{stripped_code}\n```"
                    else:
                        stripped_content = content.rstrip()
                        content = f"```content\n{stripped_content}\n```"
                        logger.info(f"Wrapped plain AI response in content block: {content[:50]}...")
            
            if '\n\n' in content and content.startswith('```'):
                logger.warning(f"Multiple command blocks detected in response: {content[:50]}...")
                blocks = content.split('\n\n')
                for block in blocks:
                    if block.startswith('```content\n'):
                        content = block
                        break
                else:
                    content = blocks[0]
            
            return content
        except Exception as ollama_error:
            logger.error(f"Ollama processing error: {ollama_error}")
            return f"Error with local AI: {str(ollama_error)}"
            
    except Exception as e:
        import traceback
        logger.error(f"AI processing error: {e}\n{traceback.format_exc()}")
        return f"Sorry, I encountered an error while processing your request: {str(e)}"