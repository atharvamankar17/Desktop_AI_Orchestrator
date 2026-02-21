# Desktop AI Orchestrator - Regex-LLM System for OS Automation

## 1. Overview

Desktop AI Orchestrator is a Regex + LLM powered desktop automation system that enables natural language control over operating system tasks, desktop applications, web services, and system workflows.

The system combines:

* Regex-based command validation and intent routing
* LLM-based conversational reasoning
* OS-level automation using PyAutoGUI and window management
* API integrations (GitHub, Email, Weather)
* Web automation for YouTube, Spotify, Google, Discord, Instagram, and more

It acts as a lightweight personal automation engine capable of translating natural language commands into deterministic system actions.

---

## 2. Core Architecture

The application follows a modular architecture:

User Input → Conversation Engine → Regex Validation → Intent Router → App/OS Handlers → Automation Execution

Key design principles:

* Deterministic execution layer (Regex + predefined handlers)
* LLM-assisted reasoning for flexible command interpretation
* Strict validation of user input to prevent unsafe execution
* Modular separation of concerns

---

## 3. Features

### 3.1 Operating System Automation

* Open and switch between applications
* Detect active application
* File Explorer search automation
* Microsoft Store search
* Weather lookup

### 3.2 Application Automation

Supports automation workflows for:

* Spotify (search, play, control)
* YouTube (search and play)
* Discord (send messages)
* Instagram (send messages via web)
* VSCode (save, format, new file)
* Email (send emails programmatically)

### 3.3 Web Search

Supports site-specific searches:

* Google
* YouTube
* Spotify
* Discord
* Instagram

### 3.4 GitHub Integration

* Search repositories using GitHub API
* Uses Personal Access Token (optional but recommended)

### 3.5 Email Integration

* Send emails via configured Google credentials
* Automatic typo correction for common domain mistakes

### 3.6 Local LLM Integration

The system uses a fully local LLM via Ollama.

* No cloud-based AI APIs are required.
* No external AI calls are made.
* All reasoning and content generation happens locally.

This ensures:

* Privacy
* Offline capability (after model download)
* No API costs
* Full control over model selection

---

## 4. Project File Structure

```
Desktop_AI_Orchestrator/
│
├── app_functionality.py      # Core automation handlers
├── os_operations.py          # OS-level app detection & switching
├── regex_validation.py       # Input validation & safe file path handling
├── google_services.py        # Email service integration
├── notepad_operations.py     # Notepad-specific automation
├── signals.py                # Event signaling & communication logic
├── conversation.py           # LLM interaction & conversation memory
├── config_manager.py         # Configuration loader
├── config.json               # API & model configuration
├── ui.py                     # Application UI layer
└── requirements.txt          # Python dependencies
```

---

## 5. Installation Guide

### 5.1 Prerequisites

* Python 3.9+
* Windows OS (primary support due to PyAutoGUI & window automation)
* Internet connection for API integrations

### 5.2 Clone the Repository

```
git clone https://github.com/atharvamankar17/Desktop_AI_Orchestrator.git
cd Desktop_AI_Orchestrator
```

### 5.3 Create a Virtual Environment (Recommended)

It is strongly recommended to create a dedicated virtual environment to isolate project dependencies.

On Windows:

```bash
python -m venv venv
venv\\Scripts\\activate
```

On macOS / Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

Once activated, your terminal should display the virtual environment name.

---

### 5.4 Install Project Requirements

After activating the virtual environment, install all required dependencies:

```bash
pip install -r requirements.txt
```

This installs all automation, window management, API, and local LLM dependencies required by the application.

```

---

## 6. Configuration Setup

All configuration is managed via config.json.

### 6.1 GitHub Token (Optional but Recommended)

1. Generate a GitHub Personal Access Token
2. Open config.json
3. Replace:

```

"your_github_personal_access_token"

```

with your token.

### 6.2 Local LLM Configuration (Ollama)

Install Ollama from the official website and ensure it is running locally.

Pull the required model:

```

ollama pull phi3

```

Start the Ollama server (if not auto-started):

```

ollama run phi3

```

Update config.json if needed:

```

"ollama": {
"url": "[http://localhost:11434](http://localhost:11434)",
"model": "phi3"
}

```

The application will automatically connect to the local Ollama server.

---

### 6.3 AI_API Section (Disabled by Default)

The AI_API section exists in config.json for legacy compatibility but is not required.

You may leave it unchanged. The system operates entirely using the local Ollama model.

--- (Local LLM)

Ensure Ollama is running locally:

```

ollama run phi3

```

Update config.json if needed:

```

"ollama": {
"url": "[http://localhost:11434](http://localhost:11434)",
"model": "phi3"
}

```

---

## 7. How to Run the Application

```

python ui.py

```

The UI will launch and accept natural language commands.

---

## 8. Example Commands

Below is a comprehensive list of supported natural language commands grouped by feature category.

The system supports flexible phrasing, but examples below demonstrate the intended structure.

---

### 8.1 Application Launch & Switching

- "Open Notepad"
- "Open Spotify"
- "Open VSCode"
- "Open Discord"
- "Open File Explorer"
- "Switch to Spotify"
- "Open Microsoft Store"

The system attempts to detect installed executables or fallback to web versions where applicable.

---

### 8.2 Notepad Content Generation

Generate and write structured content directly into Notepad.

- "Write a poem in notepad"
- "Generate a motivational quote in notepad"
- "Write a to-do list in notepad"
- "Write a resignation letter in notepad"
- "Write code for Fibonacci series in C language in notepad"
- "Write code for bubble sort in Python in notepad"
- "Generate HTML for a login page in notepad"

The LLM generates content and the automation layer types it into Notepad.

---

### 8.3 Volume & Brightness Control

- "Set volume to 50%"
- "Set volume to 0%"
- "Set brightness to 70%"
- "Set brightness to 30%"

Supports values from 0–100.

---

### 8.4 Web Search & Media Search

General Web Search:

- "Search artificial intelligence on Google"
- "Search latest AI research"

YouTube:

- "Search machine learning tutorials on YouTube"
- "Play lo-fi music on YouTube"

Spotify:

- "Search Arijit Singh on Spotify"
- "Play Shape of You on Spotify"

Instagram & Discord (Web/Open App Context):

- "Search user on Instagram"
- "Open Discord"

---

### 8.5 Spotify Automation (Desktop)

- "Play Believer on Spotify"
- "Pause Spotify"
- "Next song on Spotify"
- "Volume up in Spotify"

---

### 8.6 Discord & Instagram Messaging

Discord:

- "Send message to username on Discord"
- "Send message to username; Hello there"

Instagram:

- "Send message to username on Instagram"

---

### 8.7 File Explorer Automation

- "Search project report in File Explorer"
- "Search budget.xlsx in File Explorer"
- "Search notes in filemanager"

---

### 8.8 Microsoft Store Search

- "Search Python in store"
- "Search VSCode in Microsoft Store"

---

### 8.9 GitHub Repository Search

Requires GitHub token (optional for higher rate limits).

- "Search repositories for desktop automation"
- "Search repositories for machine learning"
- "Search GitHub for regex projects"

Returns top repositories with description and star count.

---

### 8.10 Email Automation

Direct Send:

- "Send email to example@gmail.com; Meeting Update; The meeting is rescheduled to 5 PM"

Generated Email:

- "Send a formal email to professor@gmail.com about internship request"
- "Send an informal email to friend@gmail.com about trip plans"

The LLM generates subject and body automatically when requested.

---

### 8.11 Calendar Commands

View Events:

- "Show events for today"
- "Show events for 08/15/2025"
- "List events on 12/25/2025"

Create Event:

- "Create event Project Review on 2025-08-20 14:00"

Update Event:

- "Update event Meeting to 2025-08-21 16:00"

Delete Event:

- "Delete event Team Sync"

---

### 8.12 Task Management

List Tasks:

- "Show all tasks"
- "List tasks"

Create Task:

- "Create task Finish report"
- "Add task Submit assignment due 2025-08-15"

Update Task:

- "Update task Finish report to Completed"

Delete Task:

- "Delete task Submit assignment"

---

### 8.13 Weather Lookup

- "Get weather in Pune"
- "Weather in Mumbai"

---

### 8.14 Conversational Queries

The system can also respond conversationally when no automation intent is detected:

- "Explain what machine learning is"
- "What is recursion?"
- "How does the internet work?"

In conversational mode, it returns concise plain text responses.

---

### 8.15 Mixed Natural Language Examples

- "Open notepad and write a short story about AI in notepad"
- "Search Python automation tutorials on YouTube"
- "Set brightness to 60% and volume to 40%"
- "Create task Prepare presentation due 2025-09-01"

---


## 9. Safety & Validation

The system uses:

- Regex-based input validation
- Sanitization for file paths
- Query filtering to block newline or command injection
- Controlled hotkey execution

Fail-safe is re-enabled after every automation block.

---

## 10. Technical Stack

- Python
- PyAutoGUI
- Requests
- Webbrowser
- PyGetWindow
- Ollama (Local LLM)

---

## 11. Design Philosophy

Desktop AI Orchestrator is built around hybrid intelligence:

Regex ensures deterministic safety.
LLMs provide flexible reasoning.
Automation layer executes with precision.

This separation ensures both safety and adaptability.

---

## 12. Known Limitations

- Primarily optimized for Windows
- UI automation depends on window focus
- Web page layout changes may affect automation
- Requires API keys for full functionality

---

## 13. Future Improvements

- Cross-platform support (Linux/macOS)
- Plugin system for new applications
- Voice interface integration
- Task scheduling engine
- Advanced permission sandboxing

---
