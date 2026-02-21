#app_functionality 
import logging
import pyautogui
import time
import webbrowser
import urllib.parse
import requests
import os
from os_operations import find_app_executable, get_active_app, switch_to_app, app_mappings
from regex_validation import safe_file_path
from google_services import send_email
import pywhatkit
logger = logging.getLogger(__name__)

app_shortcuts = {
    "discord": {
        "send message": ["type", "enter"],
        "join server": ["ctrl", "shift", "t"],
        "mute": ["ctrl", "shift", "m"],
        "switch channel": ["ctrl", "b"]
    },
    "email": {
        "send": ["ctrl", "enter"],
        "new email": ["ctrl", "t"],
        "attach": ["alt", "f"]
    },
    "spotify": {
        "play": ["ctrl", "k", "type", "enter"],
        "pause": ["space"],
        "next": ["ctrl", "right"],
        "volume up": ["ctrl", "volume down"]
    },
    "vscode": {
        "save": ["ctrl", "s"],
        "new file": ["ctrl", "t"],
        "format": ["alt", "f"]
    },
    "filemanager": {
        "search": ["ctrl", "f"]
    }
}

def handle_app_action(app, action, params):
    try:
        if app.lower() != get_active_app() and app.lower() != "email":
            if not switch_to_app(app):
                return f"Failed to switch to {app}."
        app_path = find_app_executable(app)
        is_web = "https://" in app_path if app_path else True
        action_key = action.lower()
        pyautogui.FAILSAFE = False
        try:
            if action_key in app_shortcuts.get(app.lower(), {}):
                actions = app_shortcuts[app.lower()][action_key]
                import pygetwindow as gw
                for window in gw.getAllWindows():
                    if app.lower() in window.title.lower():
                        logger.info(f"Activating window for {app}: {window.title}")
                        window.activate()
                        time.sleep(1.5)
                        break
                for cmd in actions:
                    if cmd == "type":
                        pyautogui.write(params, interval=0.05)
                        time.sleep(0.2)
                    elif cmd == "enter":
                        pyautogui.press('enter')
                        time.sleep(0.5)
                    elif cmd == "tab":
                        pyautogui.press('tab')
                        time.sleep(0.2)
                    else:
                        pyautogui.hotkey(*cmd.split())
                        time.sleep(0.3)
                return f"Performed {action} in {app}."
            
            if app.lower() == "spotify" and action_key == "play" and not is_web:
                import pygetwindow as gw
                for window in gw.getAllWindows():
                    if "spotify" in window.title.lower():
                        logger.info(f"Activating Spotify window: {window.title}")
                        window.activate()
                        time.sleep(1.5)
                        break
                for cmd in ["ctrl k", "type", "enter"]:
                    if cmd == "type":
                        pyautogui.write(params, interval=0.05)
                        time.sleep(0.2)
                    elif cmd == "enter":
                        pyautogui.press('enter')
                        time.sleep(0.5)
                    else:
                        pyautogui.hotkey(*cmd.split())
                        time.sleep(0.3)
                return f"Played {params} in Spotify."
            
            if app.lower() == "discord":
                if action_key =="send message to":
                    recipient, message = params.split(";", 1) if ";" in params else (params, "Hello")
                    pyautogui.hotkey('ctrl', 'k')
                    time.sleep(0.5)
                    pyautogui.write(recipient, interval=0.05)
                    pyautogui.press('enter')
                    time.sleep(0.5)
                    pyautogui.write(message, interval=0.05)
                    pyautogui.press('enter')
                    return f"Sent message to {recipient} in Discord."
            
            if app.lower() == "instagram":
                if action_key == "send message to":
                    recipient, message = params.split(";", 1) if ";" in params else (params, "Hello")
                    webbrowser.open(f"https://www.instagram.com/direct/t/{urllib.parse.quote(recipient)}/")
                    time.sleep(15)
                    pyautogui.write(message, interval=0.05)
                    pyautogui.press('enter')
                    return f"Sent message to {recipient} in Instagram."
            
            return f"No predefined action '{action}' for {app}."
        finally:
            pyautogui.FAILSAFE = True
    except Exception as e:
        pyautogui.FAILSAFE = True
        return f"Failed to perform {action} in {app}: {e}"

def handle_email(recipient, subject, body):
    try:
        recipient = recipient.lower().replace("gamil.com", "gmail.com")
        result = send_email(recipient, subject, body)
        return result
    except Exception as e:
        return f"Email failed: {e}"

def handle_youtube(query):
    try:
        if not query or ';' in query or '\n' in query:
            logger.error(f"Invalid YouTube query: {query}")
            return "Invalid YouTube search query."
        logger.info(f"Opening YouTube URL: https://www.youtube.com/results?search_query={urllib.parse.quote(query)}")
        webbrowser.open(f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}")
        time.sleep(5)
        for attempt in range(3):
            import pygetwindow as gw
            for window in gw.getAllWindows():
                if "youtube" in window.title.lower():
                    logger.info(f"Activating YouTube window: {window.title}")
                    window.activate()
                    window.maximize()
                    time.sleep(2)
                    if "youtube" in get_active_app():
                        break
            else:
                logger.warning(f"YouTube focus attempt {attempt + 1} failed.")
                time.sleep(2)
                continue
            break
        else:
            logger.error("Failed to focus YouTube after 3 attempts")
            return "Failed to focus YouTube."
        pyautogui.FAILSAFE = False
        try:
            pyautogui.press('tab', presses=2, interval=0.2)
            pyautogui.write(query, interval=0.05)
            pyautogui.press('enter')
            return f"Searching for {query} on YouTube."
        finally:
            pyautogui.FAILSAFE = True
    except Exception as e:
        pyautogui.FAILSAFE = True
        return f"YouTube search failed: {e}"

def handle_spotify_search(query):
    try:
        if not query or ';' in query or '\n' in query:
            logger.error(f"Invalid Spotify query: {query}")
            return "Invalid Spotify search query."
        app_path = find_app_executable("spotify")
        is_web = "https://" in app_path if app_path else True
        if not is_web:
            logger.info(f"Opening Spotify desktop with command: {app_path}")
            import subprocess
            subprocess.run(app_path, shell=True, check=True)
        else:
            url = f"https://open.spotify.com/search/{urllib.parse.quote(query)}"
            logger.info(f"Opening Spotify web URL: {url}")
            webbrowser.open(url)
        time.sleep(15 if is_web else 8)
        for attempt in range(3):
            import pygetwindow as gw
            for window in gw.getAllWindows():
                if "spotify" in window.title.lower():
                    logger.info(f"Activating Spotify window: {window.title}")
                    window.activate()
                    window.maximize()
                    time.sleep(2)
                    if get_active_app() == "spotify":
                        break
            else:
                logger.warning(f"Spotify focus attempt {attempt + 1} failed.")
                time.sleep(2)
                continue
            break
        else:
            logger.error("Failed to focus Spotify after 3 attempts")
            return "Failed to focus Spotify."
        pyautogui.FAILSAFE = False
        try:
            logger.info(f"Performing search for: {query}")
            pyautogui.hotkey('ctrl', 'k')
            time.sleep(0.5)
            pyautogui.write(query, interval=0.05)
            time.sleep(0.5)
            pyautogui.press('enter')
            time.sleep(2)
            pyautogui.press('enter')
            return f"Playing {query} on Spotify."
        finally:
            pyautogui.FAILSAFE = True
    except Exception as e:
        pyautogui.FAILSAFE = True
        return f"Spotify search failed: {e}"

def handle_filemanager_search(query):
    try:
        if not query or ';' in query or '\n' in query:
            logger.error(f"Invalid File Explorer query: {query}")
            return "Invalid File Explorer search query."
        app_path = find_app_executable("filemanager")
        if not app_path:
            logger.error("File Explorer executable not found")
            return "Could not open File Explorer."
        logger.info(f"Opening File Explorer with command: {app_path}")
        import subprocess
        subprocess.run(app_path, shell=True, check=True)
        time.sleep(5)
        for attempt in range(3):
            import pygetwindow as gw
            for window in gw.getAllWindows():
                if any(pattern in window.title.lower() for pattern in app_mappings["filemanager"]):
                    logger.info(f"Activating File Explorer window: {window.title}")
                    window.activate()
                    window.maximize()
                    time.sleep(2)
                    if get_active_app() == "filemanager":
                        break
            else:
                logger.warning(f"File Explorer focus attempt {attempt + 1} failed.")
                time.sleep(2)
                continue
            break
        else:
            logger.error("Failed to focus File Explorer after 3 attempts")
            return "Failed to focus File Explorer."
        pyautogui.FAILSAFE = False
        try:
            logger.info(f"Performing search for: {query}")
            pyautogui.hotkey('ctrl', 'e')
            time.sleep(0.5)
            pyautogui.write(query, interval=0.05)
            pyautogui.press('enter')
            time.sleep(0.5)
            return f"Searching for {query} in File Explorer."
        finally:
            pyautogui.FAILSAFE = True
    except Exception as e:
        pyautogui.FAILSAFE = True
        return f"File Explorer search failed: {e}"

def handle_github_search(query):
    try:
        if not query or ';' in query or '\n' in query:
            logger.error(f"Invalid GitHub query: {query}")
            return "Invalid GitHub search query."
        from config_manager import get_config
        config = get_config()
        url = f"https://api.github.com/search/repositories?q={urllib.parse.quote(query)}"
        headers = {'Authorization': f'Token {config["github"]["token"]}'} if config["github"]["token"] != "your_github_personal_access_token" else {}
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code != 200:
            return f"GitHub API error: {response.text}"
        repos = response.json().get('items', [])[:5]
        result = f"Found {len(repos)} repositories for '{query}':\n"
        for repo in repos:
            result += f"- {repo['full_name']}: {repo['description'] or 'No description'} (Stars: {repo['stargazers_count']})\n"
        return result or "No repositories found."
    except Exception as e:
        return f"GitHub search failed: {e}"

def handle_web_search(command):
    try:
        site, query = command.split(";") if ";" in command else ("google", command)
        site = site.lower()
        if not query or ';' in query or '\n' in query:
            logger.error(f"Invalid web search query: {query}")
            return "Invalid web search query."
        search_urls = {
            "google": f"https://www.google.com/search?q={urllib.parse.quote(query)}",
            "youtube": f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}",
            "spotify": f"https://open.spotify.com/search/{urllib.parse.quote(query)}",
            "instagram": f"https://www.instagram.com",
            "discord": f"https://discord.com/app",
        }
        if site == "youtube":
            return handle_youtube(query)
        elif site == "spotify":
            return handle_spotify_search(query)
        elif site == "filemanager":
            return handle_filemanager_search(query)
        url = search_urls.get(site, f"https://www.google.com/search?q={urllib.parse.quote(query)}")
        logger.info(f"Opening web search URL: {url}")
        webbrowser.open(url)
        time.sleep(3)
        pyautogui.FAILSAFE = False
        try:
            pyautogui.press('enter')
            return f"Searching {query} on {site.capitalize()}."
        finally:
            pyautogui.FAILSAFE = True
    except Exception as e:
        pyautogui.FAILSAFE = True
        return f"Web search failed: {e}"

def handle_store_search(query):
    try:
        if not query or '\n' in query:
            logger.error(f"Invalid store query: {query}")
            return "Invalid store search query."
        logger.info(f"Opening Microsoft Store with search: {query}")
        import subprocess
        subprocess.run("start ms-windows-store:", shell=True)
        time.sleep(5)
        for attempt in range(3):
            import pygetwindow as gw
            for window in gw.getAllWindows():
                if "microsoft store" in window.title.lower():
                    logger.info(f"Activating Microsoft Store window: {window.title}")
                    window.activate()
                    window.maximize()
                    time.sleep(2)
                    if get_active_app() == "store":
                        break
            else:
                logger.warning(f"Microsoft Store focus attempt {attempt + 1} failed.")
                time.sleep(2)
                continue
            break
        else:
            logger.error("Failed to focus Microsoft Store after 3 attempts")
            return "Failed to focus Microsoft Store."
        pyautogui.FAILSAFE = False
        try:
            pyautogui.write(query, interval=0.05)
            pyautogui.press('enter')
            return f"Searching {query} in Microsoft Store."
        finally:
            pyautogui.FAILSAFE = True
    except Exception as e:
        pyautogui.FAILSAFE = True
        return f"Microsoft Store search failed: {e}"

def get_weather(city):
    try:
        response = requests.get(f"https://wttr.in/{urllib.parse.quote(city)}?format=3")
        return response.text.strip()
    except Exception as e:
        return f"Weather fetch failed: {str(e)}"