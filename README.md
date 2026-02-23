# Desktop AI Orchestrator - Regex-LLM System for OS Automation

## 1. Overview

Desktop AI Orchestrator is a Regex + Local LLM powered desktop
automation system that enables natural language control over operating
system tasks, desktop applications, web services, and structured
workflows.

The system combines:

-   Regex-based command validation and intent routing
-   Local LLM-based reasoning (Openclaw)
-   OS-level automation using PyAutoGUI and window management
-   API integrations (GitHub, Email, Weather)
-   Web automation for YouTube, Spotify, Google, Discord, and Instagram

It acts as a structured personal automation engine that translates
natural language commands into deterministic system actions.

------------------------------------------------------------------------

## 2. Core Architecture

User Input → Conversation Engine → Regex Validation → Intent Router →
App/OS Handlers → Automation Execution

Design principles:

-   Deterministic execution layer (Regex + predefined handlers)
-   Local LLM-assisted reasoning via Openclaw runtime
-   Strict validation of user input
-   Modular separation of concerns

------------------------------------------------------------------------

## 3. Features

### 3.1 Operating System Automation

-   Open and switch applications
-   Detect active application
-   File Explorer search automation
-   Microsoft Store search
-   Weather lookup

### 3.2 Application Automation

Supports automation workflows for:

-   Spotify (search, play, control)
-   YouTube (search and play)
-   Discord (send messages)
-   Instagram (send messages via web)
-   VSCode (save, format, new file)
-   Email (send emails programmatically)

### 3.3 Web Search

-   Google search
-   YouTube search
-   Spotify search
-   Instagram lookup
-   Discord navigation

### 3.4 GitHub Integration

-   Search repositories using GitHub API
-   Supports Personal Access Token for higher rate limits

### 3.5 Email Integration

-   Send emails via configured Google credentials
-   Automatic typo correction for domains

### 3.6 Local LLM Integration

-   Fully local inference using Openclaw
-   No cloud-based AI usage
-   Offline capable after model download
-   No API costs
-   Configurable model routing via Openclaw runtime

------------------------------------------------------------------------

## 4. Project File Structure

    Desktop_AI_Orchestrator/
    │
    ├── app_functionality.py      # Core automation handlers
    ├── os_operations.py          # OS-level app detection & switching
    ├── regex_validation.py       # Input validation & sanitization
    ├── google_services.py        # Email service integration
    ├── notepad_operations.py     # Notepad automation
    ├── signals.py                # Event signaling logic
    ├── conversation.py           # Openclaw interaction & memory
    ├── config_manager.py         # Configuration loader
    ├── config.json               # App configuration
    ├── ui.py                     # Application UI
    └── requirements.txt          # Dependencies

------------------------------------------------------------------------

## 5. Installation Guide

### 5.1 Prerequisites

-   Python 3.9+
-   Windows OS (primary support)
-   Internet connection (only for initial Openclaw model pull)

### 5.2 Clone the Repository

``` bash
git clone https://github.com/atharvamankar17/Desktop_AI_Orchestrator.git
cd Desktop_AI_Orchestrator
```

### 5.3 Create a Virtual Environment (Recommended)

On Windows:

``` bash
python -m venv venv
venv\Scripts\activate
```

On macOS / Linux:

``` bash
python3 -m venv venv
source venv/bin/activate
```

### 5.4 Install Requirements

``` bash
pip install -r requirements.txt
```

------------------------------------------------------------------------

## 6. Local LLM Setup (Openclaw)

Install Openclaw runtime and pull a model:

``` bash
openclaw pull phi3
```

Ensure Openclaw is running locally.

Update config.json if required:

``` json
"openclaw": {
    "url": "http://localhost:11434",
    "model": "phi3"
}
```

------------------------------------------------------------------------

## 7. Running the Application

``` bash
python ui.py
```

------------------------------------------------------------------------

## 8. Conversational Fallback

When no automation intent is detected, Openclaw handles natural language
queries:

-   Explain recursion
-   What is machine learning?
-   How does the internet work?

------------------------------------------------------------------------

## 9. Safety & Validation

-   Regex-based input validation
-   Sanitized file paths
-   Injection prevention
-   Controlled hotkey execution
-   Deterministic handler constraints before LLM fallback

------------------------------------------------------------------------

## 10. Technical Stack

-   Python
-   PyAutoGUI
-   Requests
-   Webbrowser
-   PyGetWindow
-   Openclaw (Local LLM Runtime)
