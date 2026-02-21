#OS_operations
import os
import subprocess
import time
import logging
import pyautogui
import pygetwindow as gw
import screen_brightness_control as sbc
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
import re

logger = logging.getLogger(__name__)

volume_control = None
try:
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume_control = cast(interface, POINTER(IAudioEndpointVolume))
    logger.info("Volume control initialized with pycaw")
except Exception as e:
    logger.error(f"Volume control initialization error: {e}")

app_mappings = {
    "notepad": [r"notepad(\.exe)?", r"untitled - notepad", r"\.txt - notepad"],
    "browser": [r"chrome", r"firefox", r"edge", r"opera", r"safari"],
    "outlook": [r"outlook", r"microsoft outlook"],
    "store": [r"microsoft store"],
    "excel": [r"excel", r"\.xlsx - excel"],
    "slack": [r"slack"],
    "teams": [r"microsoft teams"],
    "vscode": [r"visual studio code"],
    "spotify": [r"spotify"],
    "vlc": [r"vlc media player"],
    "pycharm": [r"pycharm"],
    "photoshop": [r"photoshop"],
    "discord": [r"discord"],
    "word": [r"winword", r"\.docx - word"],
    "whatsapp": [r"whatsapp", r"web.whatsapp.com"],
    "instagram": [r"instagram", r"www.instagram.com"],
    "filemanager": [r"file explorer", r"this pc", r"quick access"]
}

app_executables = {
    "notepad": "notepad.exe",
    "spotify": "Spotify.exe",
    "vscode": "Code.exe",
    "excel": "EXCEL.EXE",
    "word": "WINWORD.EXE",
    "pycharm": "pycharm64.exe",
    "photoshop": "Photoshop.exe",
    "slack": "Slack.exe",
    "teams": "Teams.exe",
    "discord": "Discord.exe",
    "vlc": "vlc.exe",
    "whatsapp": "WhatsApp.exe",
    "instagram": "Instagram.exe",
    "outlook": "OUTLOOK.EXE",
    "filemanager": "explorer.exe"
}

cached_app = None

def find_app_executable(app_name):
    app_name = app_name.lower()
    executable = app_executables.get(app_name)
    if executable:
        search_paths = [
            os.path.expanduser("~\\AppData\\Local"),
            os.path.expanduser("~\\AppData\\Roaming"),
            "C:\\Program Files",
            "C:\\Program Files (x86)",
            "C:\\Windows",
            "C:\\Windows\\System32",
            "C:\\ProgramData"
        ]
        for path in search_paths:
            full_path = os.path.join(path, executable)
            if os.path.exists(full_path):
                logger.info(f"Found executable for {app_name}: {full_path}")
                return f"start \"\" \"{full_path}\""
        start_menu = os.path.expanduser("~\\AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs")
        for root, _, files in os.walk(start_menu):
            for file in files:
                if file.lower().endswith(".lnk") and app_name in file.lower():
                    full_path = os.path.join(root, file)
                    logger.info(f"Found shortcut for {app_name}: {full_path}")
                    return f"start \"{full_path}\""
    if app_name in ["whatsapp", "instagram", "discord", "spotify"]:
        url = {
            "whatsapp": "https://web.whatsapp.com",
            "instagram": "https://www.instagram.com",
            "discord": "https://discord.com/app",
            "spotify": "https://open.spotify.com"
        }[app_name]
        logger.info(f"Using web URL for {app_name}: {url}")
        return f"start \"{url}\""
    if app_name == "email":
        outlook_path = find_app_executable("outlook")
        return outlook_path or "email_fallback"
    logger.warning(f"No executable or shortcut found for {app_name}")
    return None

def get_active_app():
    global cached_app
    try:
        window = gw.getActiveWindow()
        if not window or not window.title:
            logger.debug(f"No active window, returning cached app: {cached_app}")
            return cached_app or "app"
        title = window.title.lower()
        for app, patterns in app_mappings.items():
            if any(re.search(pattern, title) for pattern in patterns):
                cached_app = app
                logger.debug(f"Active app detected: {app}")
                return app
        cached_app = "app"
        logger.debug("No matching app, defaulting to 'app'")
        return "app"
    except Exception as e:
        logger.warning(f"App detection error: {e}")
        return cached_app or "app"

def switch_to_app(app_name):
    global cached_app
    app_path = find_app_executable(app_name)
    if app_path:
        try:
            logger.info(f"Attempting to open {app_name} with command: {app_path}")
            subprocess.run(app_path, shell=True, check=True)
            timeout = time.time() + 20
            while time.time() < timeout:
                for window in gw.getAllWindows():
                    if app_name.lower() in window.title.lower():
                        logger.info(f"Found window for {app_name}: {window.title}")
                        window.activate()
                        window.maximize()
                        time.sleep(1)
                        if get_active_app() == app_name.lower():
                            cached_app = app_name
                            logger.info(f"Successfully switched to {app_name}")
                            return True
                time.sleep(1)
            logger.error(f"Failed to focus {app_name} within timeout")
            return False
        except Exception as e:
            logger.error(f"Error opening {app_name}: {e}")
            return False
    logger.error(f"Could not find {app_name}")
    return False

def handle_brightness(command):
    try:
        logger.info(f"Processing brightness command: '{command}'")
        if not command or ';' not in command:
            logger.error(f"Invalid brightness command format: '{command}'")
            return "Invalid command. Use format: 'set brightness to X%' where X is 0-100."
        parts = command.split(";", 1)
        action = parts[0].strip() if parts[0] else ""
        value = parts[1].replace("%", "").strip() if len(parts) > 1 else ""
        if action != "set" or not value.isdigit() or not 0 <= int(value) <= 100:
            logger.error(f"Invalid brightness command: action='{action}', value='{value}'")
            return "Invalid command. Use format: 'set brightness to X%' where X is 0-100."
        value = int(value)
        try:
            sbc.set_brightness(value, display=0)
            current_brightness = sbc.get_brightness(display=0)
            logger.info(f"Brightness set to {value}%. Current brightness: {current_brightness}%")
            return f"Brightness set to {value}%."
        except Exception as e:
            if "EDIDParseError" in str(e):
                logger.debug(f"Suppressed EDIDParseError: {e}")
                current_brightness = sbc.get_brightness(display=0)
                logger.info(f"Brightness set to {value}%. Current brightness: {current_brightness}%")
                return f"Brightness set to {value}%."
            logger.error(f"Brightness control failed: {e}")
            return "Brightness control unavailable. Ensure your monitor supports DDC/CI."
    except Exception as e:
        logger.error(f"Brightness command parsing failed: {e}")
        return f"Failed to set brightness: {str(e)}"

def handle_volume(command):
    try:
        logger.info(f"Processing volume command: '{command}'")
        if not command or ';' not in command:
            logger.error(f"Invalid volume command format: '{command}'")
            return "Invalid command. Use format: 'set volume to X%' where X is 0-100."
        parts = command.split(";", 1)
        action = parts[0].strip() if parts[0] else ""
        value = parts[1].replace("%", "").strip() if len(parts) > 1 else ""
        if action != "set" or not value.isdigit() or not 0 <= int(value) <= 100:
            logger.error(f"Invalid volume command: action='{action}', value='{value}'")
            return "Invalid command. Use format: 'set volume to X%' where X is 0-100."
        value = int(value)
        if not volume_control:
            logger.error("Volume control not initialized. Ensure audio drivers are installed.")
            return "Volume control unavailable. Ensure audio drivers are installed."
        try:
            scalar_value = value / 100.0
            logger.info(f"Setting volume to {value}% (scalar: {scalar_value:.2f})")
            volume_control.SetMasterVolumeLevelScalar(scalar_value, None)
            volume_control.SetMute(0 if value > 0 else 1, None)
            current_scalar = volume_control.GetMasterVolumeLevelScalar()
            current_percent = int(current_scalar * 100)
            logger.info(f"Volume set to {current_percent}% (scalar: {current_scalar:.2f})")
            return f"Volume set to {value}%."
        except Exception as e:
            logger.error(f"Volume control failed: {e}")
            return "Volume control failed. Ensure audio drivers support volume control."
    except Exception as e:
        logger.error(f"Volume command parsing failed: {e}")
        return f"Failed to set volume: {str(e)}"

def read_screen():
    pyautogui.hotkey('ctrl', 'c')
    time.sleep(0.2)
    import pyperclip
    text = pyperclip.paste()
    if text:
        return "Screen text copied to clipboard."
    return "No text selected."