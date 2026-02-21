#backend
import logging
import os
import queue
import threading
import time
import schedule
import re
import pyautogui
from datetime import datetime, timedelta
from plyer import notification
from signals import signals
from os_operations import volume_control, get_active_app, handle_brightness, handle_volume
from regex_validation import preprocess_input, match_command, is_safe_command
from conversation import query_ollama, generate_content, authenticate, conversation_history
from notepad_operations import write_to_notepad
from app_functionality import (
    handle_app_action, handle_email, handle_youtube, handle_spotify_search,
    handle_filemanager_search, handle_github_search, handle_web_search,
    handle_store_search, get_weather, app_shortcuts
)
from google_services import (
    list_emails, send_email, list_events, create_event, update_event, delete_event,
    list_tasks, create_task, update_task, delete_task
)
from config_manager import get_config

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

try:
    config = get_config()
    ai_api_config = config.get('AI_API', {})
    logger.info(f"AI API Provider: {ai_api_config.get('provider', 'Not configured')}")
    logger.info(f"AI API Model: {ai_api_config.get('model', 'Not configured')}")
   
    from conversation import ollama_available
    logger.info(f"Ollama Available: {ollama_available}")
except Exception as e:
    logger.error(f"Failed to load configuration: {e}")
    config = {}

GITHUB_TOKEN = config.get('github', {}).get('token', 'your_github_personal_access_token')
response_queue = queue.Queue(maxsize=15)
shutdown_event = threading.Event()

def format_date_for_calendar(date_str):
    """Convert various date formats to the format expected by the calendar API."""
    formats = [
        '%m-%d-%Y',    
        '%m/%d/%Y',    
        '%Y-%m-%d',    
        '%d %b %Y',    
        '%B %d, %Y',   
        '%b %d, %Y',   
        '%d %B %Y',    
        '%m/%d/%y',    
        '%d-%m-%Y',    
    ]
    
    for fmt in formats:
        try:
            parsed_date = datetime.strptime(date_str, fmt)
            return parsed_date.strftime('%m/%d/%Y')  
        except ValueError:
            continue
    
    logger.warning(f"Could not parse date: {date_str}")
    return date_str

def notify_user(message):
    try:
        notification.notify(title="Assistive AI", message=message[:50], timeout=5)
    except Exception as e:
        logger.warning(f"Notification error: {e}")

def schedule_tasks():
    logger.info("Scheduler started")
    schedule.every(10).minutes.do(lambda: check_calendar_reminders())
    schedule.every(10).minutes.do(lambda: check_task_reminders())
    
    schedule.every(5).minutes.do(lambda: safe_emit_signal(signals.email_signal, list_emails()))
    schedule.every(5).minutes.do(lambda: safe_emit_signal(signals.task_signal, list_tasks()))
    
    while not shutdown_event.is_set():
        schedule.run_pending()
        time.sleep(1)

def safe_emit_signal(signal, data):
    try:
        signal.emit(data)
    except Exception as e:
        logger.error(f"Error emitting signal: {e}")

def check_calendar_reminders():
    try:
        now = datetime.now()
        soon = now + timedelta(minutes=60)
        events = list_events(now.strftime('%m/%d/%Y'))
        
        for event in events[1:]:
            if "at " in event:
                event_time_str = event.split("at ")[1].split(" -")[0]
                try:
                    event_time = datetime.strptime(event_time_str, '%H:%M').time()
                    event_datetime = datetime.combine(now.date(), event_time)
                    
                    if now <= event_datetime <= soon:
                        event_title = event.split("at ")[1].split(" - ")[1]
                        notification.notify(
                            title="Calendar Reminder",
                            message=f"Upcoming: {event_title} at {event_time_str}",
                            timeout=10
                        )
                except ValueError:
                    continue
    except Exception as e:
        logger.error(f"Error checking calendar reminders: {e}")

def check_task_reminders():
    try:
        tasks = list_tasks()
        now = datetime.now()
        tomorrow = now + timedelta(days=1)
        
        for task in tasks:
            if " - " in task and " (Pending)" in task:
                due_date_str = task.split(" - ")[0]
                if due_date_str != "No due date":
                    try:
                        due_date = datetime.strptime(due_date_str, '%Y-%m-%d')
                        if now.date() <= due_date <= tomorrow.date():
                            task_title = task.split(" - ")[1].split(" (")[0]
                            notification.notify(
                                title="Task Reminder",
                                message=f"Task due: {task_title}",
                                timeout=10
                            )
                    except ValueError:
                        continue
    except Exception as e:
        logger.error(f"Error checking task reminders: {e}")

def execute_command(response, expected_type=None):
    try:
        if not response.startswith('```') or not response.endswith('```'):
            logger.info("Returning conversational response")
            return response
        if '\n\n' in response:
            logger.warning(f"Multiple commands detected in response: {response[:50]}... Using first valid block.")
            blocks = response.split('\n\n')
            for block in blocks:
                if expected_type and block.startswith(f"```{expected_type}"):
                    response = block
                    break
            else:
                response = blocks[0]
        response = response.replace("sound", "volume").replace("audio", "volume").replace("music", "spotify")
        if expected_type and not response.startswith(f"```{expected_type}"):
            logger.error(f"Expected {expected_type} command, got: {response[:50]}...")
            return f"Invalid command format. Expected {expected_type}."
        if response.startswith('```brightness'):
            command_match = re.search(r'```brightness\n(.+?)\n```', response, re.DOTALL)
            if not command_match:
                logger.error(f"Failed to extract brightness command from: {response}")
                return "Invalid brightness command format."
            command = command_match.group(1).strip()
            logger.info(f"Executing brightness command: '{command}'")
            return handle_brightness(command)
        elif response.startswith('```volume'):
            command_match = re.search(r'```volume\n(.+?)\n```', response, re.DOTALL)
            if not command_match:
                logger.error(f"Failed to extract volume command from: {response}")
                return "Invalid volume command format."
            command = command_match.group(1).strip()
            logger.info(f"Executing volume command: '{command}'")
            return handle_volume(command)
        elif response.startswith('```cmd'):
            cmd = response.strip('```cmd\n').strip('\n```')
            if not is_safe_command(cmd):
                return "Command blocked."
            logger.info(f"Executing command: {cmd}")
            import subprocess
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=20)
            return result.stdout.strip() or "Command executed."
        elif response.startswith('```python'):
            code = response.strip('```python\n').strip('\n```')
            if not is_safe_command(code):
                return "Command blocked."
            logger.info(f"Executing Python code: {code[:50]}...")
            local_vars = {}
            exec(code, {"__builtins__": {}, "os": os, "pyautogui": pyautogui}, local_vars)
            return local_vars.get('result', "Command executed.")
        elif response.startswith('```content'):
            text = response.strip('```content\n').strip('\n```')
            if not text and text != '':
                logger.warning("Empty content for Notepad")
                return "Invalid content: No content provided."
            logger.info(f"Writing content to Notepad: {text[:50]}...")
            return write_to_notepad(text)
        elif response.startswith('```youtube'):
            query = response.strip('```youtube\n').strip('\n```')
            return handle_youtube(query)
        elif response.startswith('```spotify'):
            query = response.strip('```spotify\n').strip('\n```')
            return handle_spotify_search(query)
        elif response.startswith('```filemanager'):
            query = response.strip('```filemanager\n').strip('\n```')
            return handle_filemanager_search(query)
        elif response.startswith('```github'):
            query = response.strip('```github\n').strip('\n```')
            return handle_github_search(query)
        elif response.startswith('```web'):
            command = response.strip('```web\n').strip('\n```')
            return handle_web_search(command)
        elif response.startswith('```store'):
            query = response.strip('```store\n').strip('\n```')
            return handle_store_search(query)
        elif response.startswith('```email'):
            email_content = response.strip('```email\n').strip('\n```')
            
            parts = email_content.split(";")
            if len(parts) < 3:
                logger.error(f"Invalid email command format: {email_content}")
                return "Invalid email command format."
            
            recipient = parts[0].strip()
            subject = parts[1].strip()
            body = ";".join(parts[2:]).strip()  
            
            if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', recipient):
                logger.error(f"Invalid email address: {recipient}")
                return f"Invalid email address: {recipient}"
            
            logger.info(f"Sending email to: {recipient}")
            result = send_email(recipient, subject, body)
            
            safe_emit_signal(signals.email_signal, list_emails())
            return result
        elif response.startswith('```calendar'):
            command = response.strip('```calendar\n').strip('\n```')
            parts = command.split(";")
            action = parts[0].lower() if parts else ""
            
            if action == "fetch":
                date_str = parts[1] if len(parts) > 1 else None
                logger.info(f"Fetching calendar events for date: {date_str}")
                
                if date_str:
                    try:
                        from datetime import datetime
                        
                        try:
                            parsed_date = datetime.strptime(date_str, '%m-%d-%Y')
                            formatted_date = parsed_date.strftime('%m/%d/%Y')
                        except ValueError:
                            try:
                                parsed_date = datetime.strptime(date_str, '%m/%d/%Y')
                                formatted_date = date_str  
                            except ValueError:
                                try:
                                    parsed_date = datetime.strptime(date_str, '%Y-%m-%d')
                                    formatted_date = parsed_date.strftime('%m/%d/%Y')
                                except ValueError:
                                    logger.error(f"Unrecognized date format: {date_str}")
                                    return f"Error: Unrecognized date format '{date_str}'. Please use MM-DD-YYYY, MM/DD/YYYY, or YYYY-MM-DD."
                        
                        logger.info(f"Formatted date for calendar API: {formatted_date}")
                        events = list_events(formatted_date)
                        
                        if not events:
                            return f"No events found for {date_str}."
                        
                        return "\n".join(events)
                    except Exception as e:
                        logger.error(f"Error processing date or fetching events: {e}")
                        return f"Error fetching calendar events: {str(e)}"
                else:
                    from datetime import datetime
                    today = datetime.now().strftime('%m/%d/%Y')
                    events = list_events(today)
                    return "\n".join(events) if events else "No events found for today."
            elif action == "schedule":
                if len(parts) < 4:
                    return "Invalid calendar command. Format: schedule;title;start_time;end_time[;description;location]"
                title = parts[1]
                start_time = parts[2]
                end_time = parts[3]
                description = parts[4] if len(parts) > 4 else None
                location = parts[5] if len(parts) > 5 else None
                return create_event(title, start_time, end_time, description, location)
            elif action == "update":
                if len(parts) < 2:
                    return "Invalid calendar command. Format: update;event_id[;title;start_time;end_time;description;location]"
                event_id = parts[1]
                title = parts[2] if len(parts) > 2 else None
                start_time = parts[3] if len(parts) > 3 else None
                end_time = parts[4] if len(parts) > 4 else None
                description = parts[5] if len(parts) > 5 else None
                location = parts[6] if len(parts) > 6 else None
                return update_event(event_id, title, start_time, end_time, description, location)
            elif action == "delete":
                if len(parts) < 2:
                    return "Invalid calendar command. Format: delete;event_id"
                event_id = parts[1]
                return delete_event(event_id)
            else:
                return f"Invalid calendar command: {command}"
        elif response.startswith('```task'):
            command = response.strip('```task\n').strip('\n```')
            parts = command.split(";")
            action = parts[0].lower() if parts else ""
            
            if action == "fetch":
                return "\n".join(list_tasks())
            elif action == "create":
                if len(parts) < 2:
                    return "Invalid task command. Format: create;title[;due_date;notes]"
                title = parts[1]
                due_date = parts[2] if len(parts) > 2 else None
                notes = parts[3] if len(parts) > 3 else None
                result = create_task(title, due_date, notes)
        
                safe_emit_signal(signals.task_signal, list_tasks())
                return result
            elif action == "update":
                if len(parts) < 2:
                    return "Invalid task command. Format: update;task_id[;title;due_date;notes;status]"
                task_id = parts[1]
                title = parts[2] if len(parts) > 2 else None
                due_date = parts[3] if len(parts) > 3 else None
                notes = parts[4] if len(parts) > 4 else None
                status = parts[5] if len(parts) > 5 else None
                result = update_task(task_id, title, due_date, notes, status)
                safe_emit_signal(signals.task_signal, list_tasks())
                return result
            elif action == "delete":
                if len(parts) < 2:
                    return "Invalid task command. Format: delete;task_id"
                task_id = parts[1]
                result = delete_task(task_id)
                safe_emit_signal(signals.task_signal, list_tasks())
                return result
            else:
                return f"Invalid task command: {command}"
        elif response.startswith('```app'):
            parts = response.strip('```app\n').strip('\n```').split(";")
            if len(parts) < 2:
                logger.error(f"Invalid app command format: {response}")
                return "Invalid app command format."
            action, value = parts
            target_app = get_active_app()
            if action in app_shortcuts.get(target_app, {}):
                actions = app_shortcuts[target_app][action]
                pyautogui.FAILSAFE = False
                try:
                    import pygetwindow as gw
                    for window in gw.getAllWindows():
                        if target_app in window.title.lower():
                            logger.info(f"Activating window for {target_app}: {window.title}")
                            window.activate()
                            time.sleep(2)
                            break
                    for cmd in actions:
                        if cmd == "type":
                            pyautogui.write(value, interval=0.05)
                            time.sleep(0.2)
                        elif cmd == "enter" or cmd == "tab":
                            pyautogui.press(cmd)
                            time.sleep(0.3 if cmd == "enter" else 0.2)
                        else:
                            pyautogui.hotkey(*cmd.split())
                            time.sleep(0.3)
                    return f"Performed {action} in {target_app}."
                finally:
                    pyautogui.FAILSAFE = True
            elif action == "switch app":
                from os_operations import switch_to_app
                return f"Switched to {value}." if switch_to_app(value) else f"Could not open {value}."
        elif response.startswith('```whatsapp'):
            content = response.strip('```whatsapp\n').strip('\n```')
            import pywhatkit
            try:
                if content.startswith('"') and content.endswith('"'):
                    import json
                    try:
                        parsed = json.loads(content)
                        if isinstance(parsed, dict) and "id" in parsed and "input" in parsed:
                            input_text = parsed["input"]
                            phone_match = re.search(r'(\+\d+)', input_text)
                            if phone_match:
                                recipient = phone_match.group(1)
                                message_match = re.search(r'"([^"]+)"', input_text)
                                if message_match:
                                    message = message_match.group(1)
                                else:
                                    message = input_text.replace(recipient, "").strip()
                                    message = re.sub(r'^(to|about|regarding|concerning)\s+', '', message)
                            else:
                                return "Could not parse phone number from the command."
                        else:
                            if ";" in content:
                                recipient, message = content.split(";", 1)
                            else:
                                phone_match = re.search(r'(\+\d+)', content)
                                if phone_match:
                                    recipient = phone_match.group(1)
                                    message = content.replace(recipient, "").strip()
                                    message = re.sub(r'^(to|about|regarding|concerning)\s+', '', message)
                                else:
                                    return "Could not parse phone number from the command."
                    except json.JSONDecodeError:
                        if ";" in content:
                            recipient, message = content.split(";", 1)
                        else:
                            phone_match = re.search(r'(\+\d+)', content)
                            if phone_match:
                                recipient = phone_match.group(1)
                                message = content.replace(recipient, "").strip()
                                message = re.sub(r'^(to|about|regarding|concerning)\s+', '', message)
                            else:
                                return "Could not parse phone number from the command."
                else:
                    if ";" in content:
                        recipient, message = content.split(";", 1)
                    else:
                        phone_match = re.search(r'(\+\d+)', content)
                        if phone_match:
                            recipient = phone_match.group(1)
                            message = content.replace(recipient, "").strip()
                            message = re.sub(r'^(to|about|regarding|concerning)\s+', '', message)
                        else:
                            return "Could not parse phone number from the command."
                
                message = message.replace('"', '').replace("'", '').strip()
            
                if not recipient.startswith('+'):
                    recipient = '+' + recipient
                
                recipient = '+' + ''.join(filter(str.isdigit, recipient[1:]))
                pywhatkit.sendwhatmsg_instantly(recipient, message)
                return f"Sent message to {recipient} on WhatsApp."
            except Exception as e:
                logger.error(f"WhatsApp sending error: {e}")
                return f"Failed to send WhatsApp message: {str(e)}"
        logger.error(f"Unknown command format: {response[:50]}...")
        return "Unknown command format."
    except Exception as e:
        pyautogui.FAILSAFE = True
        logger.error(f"Command execution failed: {str(e)}")
        return f"Command failed: {str(e)}"

def ai_processing(input_queue):
    logger.info("AI processing started")
    while not shutdown_event.is_set():
        try:
            text = input_queue.get(timeout=1)
            if text == "exit":
                break
            text = preprocess_input(text)
            logger.info(f"Processing input: '{text}'")
            executed_responses = []
            import pyperclip
            pyperclip.copy("")
            
            calendar_match = re.match(r"(?:show|list|view)\s+(?:all\s+)?events?\s*(?:for\s+)?(.+)", text.lower(), re.IGNORECASE)
            if calendar_match:
                date_expr = calendar_match.group(1).strip()
                if date_expr.lower() == "today":
                    from datetime import datetime
                    date_str = datetime.now().strftime('%m/%d/%Y')
                    logger.info(f"Recognized 'today' in calendar command, using date: {date_str}")
                else:
                    date_str = format_date_for_calendar(date_expr)
                    logger.info(f"Parsed date expression '{date_expr}' to: {date_str}")
                    
                    if not re.match(r'^\d{2}/\d{2}/\d{4}$', date_str):
                        date_conversion_prompt = f"Convert this date expression to MM/DD/YYYY format: {date_expr}"
                        date_str = query_ollama(date_conversion_prompt, is_conversational=False).strip()
                        logger.info(f"AI converted date expression '{date_expr}' to: {date_str}")
                        
                        if not re.match(r'^\d{2}/\d{2}/\d{4}$', date_str):
                            logger.error(f"Invalid date format for calendar: {date_str}")
                            response_queue.put("Error: Invalid date format. Please use a format like 'today', 'August 20, 2025', or '08/20/2025'.")
                            continue
                
                response = execute_command(f"```calendar\nfetch;{date_str}\n```")
                executed_responses.append(response)
                response_queue.put("\n".join(str(resp) for resp in executed_responses if resp))
                continue
            
            if not match_command(text):
                logger.info(f"No regex match for input: {text}. Handling as conversational query.")
                ai_response = query_ollama(text, is_conversational=True)
                conversation_history.append({"role": "user", "content": text})
                conversation_history.append({"role": "assistant", "content": ai_response})
                response_queue.put(ai_response)
                notify_user(ai_response)
                executed_responses.append(ai_response)
                continue
            
            email_match = re.match(r"(?:send\s+a\s*)?(formal|informal)?\s*email\s*to\s*([\w@.]+)\s*(.*)", text.lower(), re.IGNORECASE)
            if email_match:
                formality, recipient, purpose = email_match.groups()
                content, _ = generate_content(f"{formality or 'formal'} email {purpose}", recipient)
                if not content.startswith("Failed"):
                    subject, body = content.split("\n\n", 1) if "\n\n" in content else (content, "")
                    subject = subject.replace("Subject: ", "").strip()
                    response = execute_command(f"```email\n{recipient};{subject};{body}\n```")
                    executed_responses.append(response)
                else:
                    executed_responses.append(content)
                    
            elif re.match(r"(?:open\s*notepad\s*and\s*)?(?:write|write\s+me|generate)\s*(?:the\s*)?(.+?)\s*in\s*notepad", text.lower(), re.IGNORECASE):
                content_match = re.match(r"(?:open\s*notepad\s*and\s*)?(?:write|write\s+me|generate)\s*(?:the\s*)?(.+?)\s*in\s*notepad", text.lower(), re.IGNORECASE)
                content_type = content_match.group(1).strip()
                content, _ = generate_content(content_type)
                logger.info(f"Generated content for Notepad: {content[:50]}...")
                if not content.startswith("Failed"):
                    response = execute_command(f"```content\n{content}\n```")
                    executed_responses.append(response)
                else:
                    executed_responses.append(content)
                    
            elif re.match(r"send\s+a\s*message\s*to\s*(\+?\d+)\s*(?:to|about|regarding|concerning)?\s*(.+)", text.lower(), re.IGNORECASE):
                message_match = re.match(r"send\s+a\s*message\s*to\s*(\+?\d+)\s*(?:to|about|regarding|concerning)?\s*(.+)", text.lower(), re.IGNORECASE)
                recipient = message_match.group(1).strip()
                message_context = message_match.group(2).strip()
                
                if not recipient.startswith('+'):
                    recipient = '+' + recipient
                
                recipient = '+' + ''.join(filter(str.isdigit, recipient[1:]))
                generated_message, _ = generate_content(f"WhatsApp message about {message_context}")
                
                if generated_message.startswith("Failed"):
                    executed_responses.append("Failed to generate message content.")
                else:
                    if "\n\n" in generated_message:
                        generated_message = generated_message.split("\n\n", 1)[1]
                    generated_message = generated_message.replace('"', '').replace("'", '').strip()
                    
                    command = f"```whatsapp\n{recipient};{generated_message}\n```"
                    response = execute_command(command)
                    executed_responses.append(response)
                    
            elif re.match(r"send\s+a\s*([\w\s]+)\s*to\s*(\+?\d+)\s*on\s*(\w+)", text.lower(), re.IGNORECASE):
                content_match = re.match(r"send\s+a\s*([\w\s]+)\s*to\s*(\+?\d+)\s*on\s*(\w+)", text.lower(), re.IGNORECASE)
                content_type, recipient, app_name = content_match.groups()
                if not recipient.startswith('+'):
                    recipient = '+' + recipient
                content, _ = generate_content(content_type)
                if not content.startswith("Failed"):
                    from os_operations import find_app_executable
                    app_path = find_app_executable(app_name)
                    if app_path:
                        logger.info(f"Opening {app_name} with command: {app_path}")
                        response = execute_command(f"```cmd\n{app_path}\n```")
                        executed_responses.append(response)
                        time.sleep(15 if app_name.lower() in ["whatsapp", "twitter", "instagram", "discord"] else 8)
                    response = execute_command(f"```app_action\n{app_name};send message to;{recipient};{content}\n```")
                    executed_responses.append(response)
                else:
                    executed_responses.append(content)
                    
            elif re.match(r"set\s+(brightness|volume)\s+to\s+(\d+)%", text.lower(), re.IGNORECASE):
                match = re.match(r"set\s+(brightness|volume)\s+to\s+(\d+)%", text.lower(), re.IGNORECASE)
                type_, value = match.groups()
                logger.info(f"Parsed command: type={type_}, value={value}")
                command = f"```{type_}\nset;{value}\n```"
                logger.info(f"Constructed command: {command}")
                response = execute_command(command, expected_type=type_)
                executed_responses.append(response)
                
            elif re.match(r"(?:search|play)\s+(.+?)\s+on\s+(\w+)", text.lower(), re.IGNORECASE):
                search_match = re.match(r"(?:search|play)\s+(.+?)\s+on\s+(\w+)", text.lower(), re.IGNORECASE)
                query, platform = search_match.groups()
                command_type = 'youtube' if platform.lower() == 'youtube' else 'spotify' if platform.lower() == 'spotify' else 'filemanager' if platform.lower() == 'filemanager' else 'web'
                command = f"```{command_type}\n{query}\n```"
                response = execute_command(command, expected_type=command_type)
                executed_responses.append(response)
                
            elif re.match(r"search\s+(.+?)\s+in\s+store", text.lower(), re.IGNORECASE):
                store_match = re.match(r"search\s+(.+?)\s+in\s+store", text.lower(), re.IGNORECASE)
                query = store_match.group(1).strip()
                command = f"```store\n{query}\n```"
                response = execute_command(command)
                executed_responses.append(response)
                
            elif re.match(r"(?:create|add)\s+(?:a\s+)?task\s*[.:]?\s*(.+?)(?:\s+due\s+(.+?))?$", text.lower(), re.IGNORECASE):
                task_match = re.match(r"(?:create|add)\s+(?:a\s+)?task\s*[.:]?\s*(.+?)(?:\s+due\s+(.+?))?$", text.lower(), re.IGNORECASE)
                title = task_match.group(1).strip()
                due_date = task_match.group(2).strip() if task_match.group(2) else None
                if due_date and not re.match(r'^\d{4}-\d{2}-\d{2}$', due_date):
                    date_conversion = query_ollama(f"Convert this date to YYYY-MM-DD format: {due_date}")
                    due_date = date_conversion.strip() if date_conversion else due_date
                command = f"create;{title};{due_date or ''};"
                response = execute_command(f"```task\n{command}\n```")
                executed_responses.append(response)
                
            elif re.match(r"(?:list|show|view)\s+(?:all\s+)?tasks?", text.lower(), re.IGNORECASE):
                response = execute_command("```task\nfetch\n```")
                executed_responses.append(response)
                
            elif re.match(r"(?:update|edit)\s+task\s+(.+?)(?:\s+to\s+(.+))?$", text.lower(), re.IGNORECASE):
                update_match = re.match(r"(?:update|edit)\s+task\s+(.+?)(?:\s+to\s+(.+))?$", text.lower(), re.IGNORECASE)
                task_id = update_match.group(1).strip()
                new_value = update_match.group(2).strip() if update_match.group(2) else None
                if new_value:
                    if re.match(r'^\d{4}-\d{2}-\d{2}$', new_value):
                        command = f"update;{task_id};;{new_value};;"
                    elif new_value.lower() in ['pending', 'completed', 'in-progress']:
                        command = f"update;{task_id};;;;{new_value}"
                    else:
                        command = f"update;{task_id};{new_value};;;"
                else:
                    command = f"update;{task_id};;;"
                
                response = execute_command(f"```task\n{command}\n```")
                executed_responses.append(response)
                
            elif re.match(r"(?:delete|remove)\s+task\s+(.+)", text.lower(), re.IGNORECASE):
                delete_match = re.match(r"(?:delete|remove)\s+task\s+(.+)", text.lower(), re.IGNORECASE)
                task_id = delete_match.group(1).strip()
                response = execute_command(f"```task\ndelete;{task_id}\n```")
                executed_responses.append(response)
                
            elif re.match(r"(?:create|schedule|add)\s+(?:an\s+)?event\s*[.:]?\s*(.+?)(?:\s+(?:on|at|for)\s+(.+?))?$", text.lower(), re.IGNORECASE):
                event_match = re.match(r"(?:create|schedule|add)\s+(?:an\s+)?event\s*[.:]?\s*(.+?)(?:\s+(?:on|at|for)\s+(.+?))?$", text.lower(), re.IGNORECASE)
                title = event_match.group(1).strip()
                datetime_str = event_match.group(2).strip() if event_match.group(2) else None
                
                if datetime_str:
                    datetime_prompt = f"""
                    Parse this datetime expression: "{datetime_str}"
                    Return in this format exactly:
                    YYYY-MM-DD HH:MM;YYYY-MM-DD HH:MM
                    (start time;end time - assume 1 hour duration if not specified)
                    Example: "tomorrow at 2pm" -> "2023-12-15 14:00;2023-12-15 15:00"
                    """
                    parsed_datetime = query_ollama(datetime_prompt, is_conversational=False).strip()
                    
                    if ";" in parsed_datetime:
                        start_time, end_time = parsed_datetime.split(";", 1)
                        command = f"schedule;{title};{start_time};{end_time};;"
                        response = execute_command(f"```calendar\n{command}\n```")
                        executed_responses.append(response)
                    else:
                        executed_responses.append("Failed to parse event time. Please try again with a clearer time expression.")
                else:
                    executed_responses.append("Please specify when the event should occur (e.g., 'tomorrow at 2pm').")
                
            elif re.match(r"(?:show|list|view)\s+(?:all\s+)?events?(?:\s+(?:for|on)\s+(.+))?$", text.lower(), re.IGNORECASE):
                event_match = re.match(r"(?:show|list|view)\s+(?:all\s+)?events?(?:\s+(?:for|on)\s+(.+))?$", text.lower(), re.IGNORECASE)
                date_str = event_match.group(1).strip() if event_match.group(1) else None
                
                if date_str and not re.match(r'^\d{2}/\d{2}/\d{4}$', date_str):
                    date_conversion = query_ollama(f"Convert this date to MM/DD/YYYY format: {date_str}")
                    date_str = date_conversion.strip() if date_conversion else None
                
                command = f"fetch;{date_str or ''}"
                response = execute_command(f"```calendar\n{command}\n```")
                executed_responses.append(response)
                
            elif re.match(r"(?:update|edit|change)\s+event\s+(.+?)(?:\s+to\s+(.+))?$", text.lower(), re.IGNORECASE):
                update_match = re.match(r"(?:update|edit|change)\s+event\s+(.+?)(?:\s+to\s+(.+))?$", text.lower(), re.IGNORECASE)
                event_id = update_match.group(1).strip()
                new_value = update_match.group(2).strip() if update_match.group(2) else None
                
                if new_value:
                    datetime_prompt = f"""
                    Is this a datetime expression? Answer only "yes" or "no": "{new_value}"
                    """
                    is_datetime = query_ollama(datetime_prompt, is_conversational=False).strip().lower()
                    
                    if "yes" in is_datetime:
                        datetime_prompt = f"""
                        Parse this datetime expression: "{new_value}"
                        Return in this format exactly:
                        YYYY-MM-DD HH:MM;YYYY-MM-DD HH:MM
                        (start time;end time - assume 1 hour duration if not specified)
                        """
                        parsed_datetime = query_ollama(datetime_prompt, is_conversational=False).strip()
                        if ";" in parsed_datetime:
                            start_time, end_time = parsed_datetime.split(";", 1)
                            command = f"update;{event_id};;{start_time};{end_time};;"
                        else:
                            command = f"update;{event_id};{new_value};;;" 
                    else:
                        command = f"update;{event_id};{new_value};;;"
                else:
                    command = f"update;{event_id};;;"
                
                response = execute_command(f"```calendar\n{command}\n```")
                executed_responses.append(response)
                
            elif re.match(r"(?:delete|remove|cancel)\s+event\s+(.+)", text.lower(), re.IGNORECASE):
                delete_match = re.match(r"(?:delete|remove|cancel)\s+event\s+(.+)", text.lower(), re.IGNORECASE)
                event_id = delete_match.group(1).strip()
                response = execute_command(f"```calendar\ndelete;{event_id}\n```")
                executed_responses.append(response)
                
            else:
                logger.error(f"Input matched regex but no handler found: {text}")
                response = "Command recognized but no handler found."
                executed_responses.append(response)
            
            combined_response = "\n".join(str(resp) for resp in executed_responses if resp)
            conversation_history.append({"role": "user", "content": text})
            conversation_history.append({"role": "assistant", "content": combined_response})
            response_queue.put(combined_response)
            notify_user(combined_response)
        except queue.Empty:
            continue
        except Exception as e:
            logger.error(f"AI processing error: {e}")
            error_response = f"Error: {e}"
            response_queue.put(error_response)

def main():
    logger.info("Starting application.")
    input_queue = queue.Queue()
    threads = [
        threading.Thread(target=ai_processing, args=(input_queue,), daemon=True),
        threading.Thread(target=schedule_tasks, daemon=True)
    ]
    for thread in threads:
        thread.start()
    return input_queue

if __name__ == '__main__':
    input_queue = main()