# Desktop AI Orchestrator - Regex-LLM System for OS Automation

## 1. Overview

Desktop AI Orchestrator is a Regex + Local LLM powered desktop automation system that enables natural language control over operating system tasks, desktop applications, web services, and structured workflows.

The system combines:

* Regex-based command validation and intent routing
* Local LLM-based reasoning (Ollama)
* OS-level automation using PyAutoGUI and window management
* API integrations (GitHub, Email, Weather)
* Web automation for YouTube, Spotify, Google, Discord, and Instagram

It acts as a structured personal automation engine that translates natural language commands into deterministic system actions.

---

## 2. Core Architecture

User Input → Conversation Engine → Regex Validation → Intent Router → App/OS Handlers → Automation Execution

Design principles:

* Deterministic execution layer (Regex + predefined handlers)
* Local LLM-assisted reasoning
* Strict validation of user input
* Modular separation of concerns

---

## 3. Features

### 3.1 Operating System Automation

* Open and switch applications
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

* Google search
* YouTube search
* Spotify search
* Instagram lookup
* Discord navigation

### 3.4 GitHub Integration

* Search repositories using GitHub API
* Supports Personal Access Token for higher rate limits

### 3.5 Email Integration

* Send emails via configured Google credentials
* Automatic typo correction for domains

### 3.6 Local LLM Integration

* Fully local inference using Ollama
* No cloud-based AI usage
* Offline capable after model download
* No API costs

---

## 4. Project File Structure

```
Desktop_AI_Orchestrator/
│
├── app_functionality.py      # Core automation handlers
├── os_operations.py          # OS-level app detection & switching
├── regex_validation.py       # Input validation & sanitization
├── google_services.py        # Email service integration
├── notepad_operations.py     # Notepad automation
├── signals.py                # Event signaling logic
├── conversation.py           # Local LLM interaction & memory
├── config_manager.py         # Configuration loader
├── config.json               # App configuration
├── ui.py                     # Application UI
└── requirements.txt          # Dependencies
```

---

## 5. Installation Guide

### 5.1 Prerequisites

* Python 3.9+
* Windows OS (primary support)
* Internet connection (only for initial Ollama model pull)

### 5.2 Clone the Repository

```bash
git clone https://github.com/atharvamankar17/Desktop_AI_Orchestrator.git
cd Desktop_AI_Orchestrator
```

### 5.3 Create a Virtual Environment (Recommended)

On Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

On macOS / Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 5.4 Install Requirements

```bash
pip install -r requirements.txt
```

---

## 6. Local LLM Setup (Ollama)

Install Ollama and pull a model:

```bash
ollama pull phi3
```

Ensure Ollama is running locally.

Update config.json if required:

```
"ollama": {
    "url": "http://localhost:11434",
    "model": "phi3"
}
```

---

## 7. Running the Application

```bash
python ui.py
```

---

## 8. Complete Feature Command Reference

This section provides an exhaustive mapping of supported natural language commands across all implemented modules. Commands are flexible in phrasing, but examples below represent validated formats.

---

### 8.1 Application Launch & Window Management

Open Applications:

* Open Notepad
* Open Spotify
* Open Discord
* Open VSCode
* Open File Explorer
* Open Microsoft Store
* Open Chrome

Switch / Focus Applications:

* Switch to Spotify
* Bring Discord to front
* Focus on VSCode
* What application is currently active?

---

### 8.2 Notepad Automation (LLM + Typing Engine)

Content Generation:

* Write a poem in notepad
* Write a motivational speech in notepad
* Write a resignation letter in notepad
* Generate meeting notes in notepad

Code Generation:

* Write Fibonacci series in Python in notepad
* Write bubble sort in C++ in notepad
* Generate HTML login page in notepad
* Write SQL query to fetch all users in notepad

Structured Lists:

* Create a to-do list in notepad
* Create shopping list in notepad

---

### 8.3 System Controls

Volume Control:

* Set volume to 50%
* Increase volume to 80%
* Mute system volume

Brightness Control:

* Set brightness to 70%
* Decrease brightness to 40%

---

### 8.4 Web & Media Search

Google Search:

* Search artificial intelligence on Google
* Search latest machine learning research

YouTube:

* Search machine learning tutorials on YouTube
* Play lo-fi music on YouTube
* Search coding interviews on YouTube

Spotify (Search & Play):

* Search Arijit Singh on Spotify
* Play Shape of You on Spotify
* Play Believer on Spotify

---

### 8.5 Spotify Desktop Controls

* Pause Spotify
* Resume Spotify
* Next song on Spotify
* Previous song on Spotify
* Increase Spotify volume
* Decrease Spotify volume

---

### 8.6 Discord Automation

Open / Navigate:

* Open Discord
* Switch to Discord

Messaging:

* Send message to username on Discord; Hello there
* Send message to John on Discord; Meeting at 5 PM

---

### 8.7 Instagram Automation (Web-Based)

* Open Instagram
* Send message to username on Instagram; Hi there
* Message Rahul on Instagram; Are you coming today?

---

### 8.8 File Explorer Automation

Search Files:

* Search project report in File Explorer
* Search budget.xlsx in File Explorer
* Find presentation.pptx in explorer
* Search notes in file manager

---

### 8.9 Microsoft Store Automation

* Search Python in Microsoft Store
* Search VSCode in store
* Find Spotify in Microsoft Store

---

### 8.10 GitHub Repository Search

* Search repositories for desktop automation
* Search repositories for machine learning
* Search GitHub for regex projects
* Find top repositories for OS automation

Returns repository name, description, and star count.

---

### 8.11 Email Automation

Direct Email (Manual Subject & Body):

* Send email to [example@gmail.com](mailto:example@gmail.com); Meeting Update; The meeting is rescheduled to 5 PM

LLM-Generated Email:

* Send a formal email to [professor@gmail.com](mailto:professor@gmail.com) about internship request
* Send an informal email to [friend@gmail.com](mailto:friend@gmail.com) about trip plans
* Draft a professional email to [HR@gmail.com](mailto:HR@gmail.com) about job application

---

### 8.12 Calendar Management

View Events:

* Show events for today
* Show events for 2025-08-20
* List events on 12/25/2025

Create Event:

* Create event Project Review on 2025-08-20 14:00
* Schedule meeting Team Sync on 2025-09-01 10:30

Update Event:

* Update event Project Review to 2025-08-21 16:00

Delete Event:

* Delete event Team Sync
* Remove event Project Review

---

### 8.13 Task Management

View Tasks:

* Show all tasks
* List tasks

Create Task:

* Create task Finish report
* Add task Submit assignment due 2025-08-15

Update Task:

* Update task Finish report to Completed
* Mark task Submit assignment as Done

Delete Task:

* Delete task Submit assignment
* Remove task Finish report

---

### 8.14 Weather Lookup

* Get weather in Pune
* Weather in Mumbai
* Show weather for Delhi

---

### 8.15 VSCode Automation

* Create new file in VSCode
* Save current file in VSCode
* Format document in VSCode
* Close file in VSCode

---

### 8.16 Multi-Intent Commands

If chaining is supported, examples include:

* Open Notepad and write a short story about AI
* Set brightness to 60% and volume to 40%
* Open Spotify and play Believer

---

### 8.17 Conversational Mode (Fallback)

When no automation intent is detected, the system responds conversationally:

* Explain recursion
* What is machine learning?
* How does the internet work?

---

## 9. Safety & Validation

Safety & Validation

* Regex-based input validation
* Sanitized file paths
* Injection prevention
* Controlled hotkey execution

---

## 10. Technical Stack

* Python
* PyAutoGUI
* Requests
* Webbrowser
* PyGetWindow
* Ollama (Local LLM)

---
