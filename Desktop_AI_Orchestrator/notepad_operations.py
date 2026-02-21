#notepad_operations
import logging
import pyautogui
import time
from os_operations import find_app_executable, get_active_app

logger = logging.getLogger(__name__)

def write_to_notepad(text):
    try:
        if not text and text != '':
            logger.warning("Empty content for Notepad")
            return "Invalid content: No content provided."
        logger.info(f"Writing content to Notepad: {text[:50]}...")
        app_path = find_app_executable("notepad")
        if app_path:
            logger.info(f"Opening Notepad with command: {app_path}")
            import subprocess
            subprocess.run(app_path, shell=True, check=True)
            time.sleep(5)
            max_attempts = 3
            for attempt in range(max_attempts):
                import pygetwindow as gw
                for window in gw.getAllWindows():
                    if "notepad" in window.title.lower():
                        logger.info(f"Activating Notepad window: {window.title}")
                        window.activate()
                        window.maximize()
                        time.sleep(2)
                        if get_active_app() == 'notepad':
                            break
                else:
                    logger.warning(f"Notepad focus attempt {attempt + 1} failed.")
                    time.sleep(2)
                    continue
                break
            else:
                logger.error("Failed to focus Notepad after 3 attempts")
                return "Failed to focus Notepad."
            pyautogui.FAILSAFE = False
            try:
                logger.info("Clearing Notepad and writing content")
                pyautogui.hotkey('ctrl', 'a')
                time.sleep(0.2)
                pyautogui.press('delete')
                time.sleep(0.2)
                lines = text.split('\n')
                for i, line in enumerate(lines):
                    pyautogui.write(line, interval=0.05)
                    if i < len(lines) - 1:
                        pyautogui.press('enter')
                    time.sleep(0.1)
                return "Wrote content in Notepad."
            finally:
                pyautogui.FAILSAFE = True
        else:
            logger.error("Could not find Notepad executable")
            return "Could not open Notepad."
    except Exception as e:
        pyautogui.FAILSAFE = True
        return f"Failed to write to Notepad: {e}"