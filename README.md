Desktop AI Orchestrator - Regex-LLM System for OS Automation 

This is a Python-based AI assistant that provides a graphical user interface (GUI) to interact with various system functions, applications, and online services. The program integrates with Outlook for email and task management, controls system settings like brightness and volume, automates app interactions, and supports natural language queries via a local Ollama AI server.
Features

Chat Interface: Send commands or ask questions via a PyQt6-based GUI.
System Control: Adjust screen brightness and system volume.
App Automation: Open and interact with apps like Notepad, Spotify, WhatsApp, and more.
Email and Task Management: Fetch and send emails, create tasks, and manage calendar events using Outlook or SMTP.
Web Searches: Search on Google, YouTube, Spotify, or GitHub.
Notifications: Receive desktop notifications for tasks and calendar reminders.
Theming: Toggle between light and dark themes.

Prerequisites :

    Operating System: Windows (due to dependencies like pywin32 and pycaw).
    Python: Version 3.8 or higher.
    Ollama Server: A local Ollama server running on http://localhost:11434 with the phi3 model installed.
    Outlook: Microsoft Outlook (optional, for email/task/calendar features; SMTP fallback available).
    Environment Variables:
    SMTP_SERVER: SMTP server (e.g., smtp.gmail.com).
    SMTP_PORT: SMTP port (e.g., 587).
    SMTP_USER: SMTP email address (e.g., your_email@gmail.com).
    SMTP_PASS: SMTP app password.
    GITHUB_TOKEN: GitHub personal access token (optional, for GitHub searches).

Installation :

Clone the Repository:
    git clone <repository-url>
    cd <repository-directory>

Set Up a Virtual Environment:
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate

Install Dependencies:
    pip install -r requirements.txt

    Configure Environment Variables:Create a .env file or set environment variables:
    export SMTP_SERVER="smtp.gmail.com"
    export SMTP_PORT=587
    export SMTP_USER="your_email@gmail.com"
    export SMTP_PASS="your_app_password"
    export GITHUB_TOKEN="your_github_personal_access_token"

    On Windows, use set instead of export or create a .env file and load it using a library like python-dotenv.

Set Up Ollama:
    Install Ollama: Follow instructions at ollama.ai.
    Start the Ollama server:ollama serve
    Ensure the phi3 model is installed:ollama pull phi3

Run the Application:
    python frontend.py

Usage :
    Launch the Application:Run frontend.py to open the GUI dashboard. The interface includes:

    Chat Widget: Enter commands or questions.
    Calendar: Select dates to view events.
    Email Assistant: View recent emails.
    Task Manager: View tasks and their due dates.
    Theme Toggle: Switch between light and dark themes.

Interact via Chat:
    Type commands in the chat input box and press "Send" or Enter.
    The AI processes commands and responds in the chat display.
    Emails and tasks are updated in their respective widgets.
    Calendar selections trigger event fetches for the selected date.

Supported Commands:
    The assistant supports commands matching specific patterns. Below are the patterns and examples:

1. Send Email
    Pattern: (?:send\s+a\s*)?(formal|informal)?\s*email\s*to\s*([\w@.]+)\s*(.*)
    Description: Sends an email to the specified recipient with an optional formality and purpose.
    
    Examples:

    send a formal email to user@gmail.com about project update
    Sends a formal email to user@gmail.com about a project update.

    informal email to friend@outlook.com
    Sends an informal email to friend@outlook.com with a generic subject.

    email to user@gmail.com regarding meeting
    Sends a formal email (default) to user@gmail.com about a meeting.

2. Write Content in Notepad
    Pattern: (?:open\s*notepad\s*and\s*)?(?:write|write\s+me|generate)\s*(?:the\s*)?(.+?)\s*in\s*notepadDescription: Opens Notepad and writes the specified content (e.g., code, poem, list).Examples:

    write a poem in notepad
    Opens Notepad and writes a generated poem.

    generate code for fibonacci series in python in notepad
    Opens Notepad and writes Python code for the Fibonacci series.

    write me a to-do list in notepad
    Opens Notepad and writes a to-do list.

3. Send Message on Messaging Apps
    Pattern: send\s+a\s*([\w\s]+)\s*to\s*(\+?\d+)\s*on\s*(\w+)Description: Sends a message or media to a phone number on WhatsApp or other supported messaging apps.Examples:

    send a message to +1234567890 on WhatsApp
    Sends a generated message to +1234567890 via WhatsApp.

    send a media to +9876543210 on WhatsApp
    Sends a media file (default: ~/Desktop/sample.jpg) to +9876543210 via WhatsApp.

    send a hello message to +1234567890 on Discord
    Sends a "hello" message to the specified user on Discord.

4. Set Brightness or Volume
    Pattern: set\s+(brightness|volume)\s+to\s+(\d+)%Description: Adjusts screen brightness or system volume to a percentage (0-100).Examples:

    set brightness to 50%
    Sets screen brightness to 50%.

    set volume to 75%
    Sets system volume to 75%.

5. Search or Play on Platforms
    Pattern: (?:search|play)\s+(.+?)\s+on\s+(\w+)Description: Searches or plays content on platforms like YouTube, Spotify, File Explorer, or others.Examples:

    search python tutorial on YouTube
    Opens YouTube and searches for "python tutorial".

    play jazz on Spotify
    Opens Spotify and plays "jazz".

    search documents on filemanager
    Opens File Explorer and searches for "documents".

    search flask on google
    Opens Google and searches for "flask".

6. Conversational Queries
    Description: Any input not matching the above patterns is treated as a conversational query, answered by the Ollama AI.Examples:

    What is the capital of France?
    Returns "The capital of France is Paris."

    Tell me a joke
    Returns a joke from the AI.

    my passphrase is xyz
    Authenticates for sensitive queries (if required).

Calendar Interaction:
    Click a date in the calendar to fetch events for that day (e.g., fetch;MM/dd/yyyy is sent to the backend).
    Example output in chat: "Events for 07/26/2025: - Meeting at 14:00".

Email and Task Widgets:
    The email widget shows the 10 most recent emails from Outlook (or an error if Outlook/SMTP is unavailable).
    The task widget shows tasks with due dates and status (e.g., "2025-07-30 - Finish report (Pending)").
    Both are updated every 5 minutes or after relevant actions (e.g., sending an email).

Troubleshooting
    Ollama Server Not Running:
    Ensure the Ollama server is running (ollama serve) and the phi3 model is installed.
    Check http://localhost:11434 is accessible.

Outlook Unavailable:
    Configure SMTP credentials in environment variables for email fallback.
    Verify Outlook is installed and configured.

App Not Found:
    Ensure the target app (e.g., Spotify, Notepad) is installed.
    Check app_mappings and app_executables in backend.py for correct app names/paths.

Brightness/Volume Errors:
    Ensure your monitor supports DDC/CI for brightness control.
    Verify audio drivers support pycaw for volume control.

Limitations

    Platform: Windows-only due to dependencies (pywin32, pycaw, Outlook COM).
    Ollama Dependency: Requires a local Ollama server.
    Regex Sensitivity: Commands must closely match patterns; misspellings may fail (e.g., "volumne" is corrected to "volume", but others may not be).
    Security: Limited command safety checks; avoid running untrusted inputs.

Contributing
Contributions are welcome! Please: