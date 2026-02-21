#google_services
import os
import pickle
import logging
from datetime import datetime, time, timedelta
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from config_manager import get_config

logger = logging.getLogger(__name__)
config = get_config()

SCOPES =[
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',  
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/tasks.readonly']

def get_credentials(service_type):
    """Get valid user credentials for the specified service."""
    creds = None
    token_file = config.get('google', {}).get('token_file', 'token.pickle')
    client_secrets_file = config.get('google', {}).get('client_secrets_file', 'client_secret.json')
    
    if os.path.exists(token_file):
        try:
            with open(token_file, 'rb') as token:
                creds = pickle.load(token)
        except (pickle.UnpicklingError, EOFError, KeyError) as e:
            logger.error(f"Error loading token file: {e}. Token file may be corrupted.")
            try:
                os.remove(token_file)
                logger.info("Deleted corrupted token file.")
            except Exception as e:
                logger.error(f"Error deleting token file: {e}")
            creds = None
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                logger.error(f"Error refreshing token: {e}")
                if os.path.exists(token_file):
                    try:
                        os.remove(token_file)
                        logger.info("Deleted token file due to refresh failure.")
                    except Exception as e:
                        logger.error(f"Error deleting token file: {e}")
                creds = None
        
        if not creds:
            try:
                flow = InstalledAppFlow.from_client_secrets_file(client_secrets_file, scopes=SCOPES)
                creds = flow.run_local_server(port=0)
            except Exception as e:
                logger.error(f"Error during authentication flow: {e}")
                return None
        try:
            with open(token_file, 'wb') as token:
                pickle.dump(creds, token)
        except Exception as e:
            logger.error(f"Error saving token file: {e}")
    
    return creds

def list_events(date_str=None):
    """List events for a specific date."""
    try:
        creds = get_credentials('calendar')
        if not creds:
            return ["Error: Failed to authenticate with Google Calendar. Please try again."]
            
        service = build('calendar', 'v3', credentials=creds)
        
        if not date_str:
            date_obj = datetime.now()
        else:
            try:
                date_obj = datetime.strptime(date_str, '%m/%d/%Y')
            except ValueError:
                logger.error(f"Invalid date format: {date_str}")
                return [f"Error: Invalid date format '{date_str}'. Please use MM/DD/YYYY format."]
        time_min = datetime.combine(date_obj.date(), time.min).isoformat() + 'Z'
        
        time_max = datetime.combine(date_obj.date(), time.max).isoformat() + 'Z'
        
        logger.info(f"Fetching events between {time_min} and {time_max}")
        
        events_result = service.events().list(
            calendarId='primary',
            timeMin=time_min,
            timeMax=time_max,
            maxResults=10,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        if not events:
            return [f"No events found for {date_str}."]
        
        event_list = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            
            if 'T' in start:
                
                start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(end.replace('Z', '+00:00'))
                
                start_str = start_dt.strftime('%I:%M %p')
                end_str = end_dt.strftime('%I:%M %p')
                
                event_list.append(f"{start_str} - {end_str}: {event['summary']}")
            else:
                event_list.append(f"All day: {event['summary']}")
        
        return event_list
    except Exception as e:
        logger.error(f"Error listing events: {e}")
        return [f"Error fetching calendar events: {str(e)}"]

def create_event(title, start_time, end_time, description=None, location=None):
    """Create a new calendar event."""
    try:
        creds = get_credentials('calendar')
        if not creds:
            return "Error: Failed to authenticate with Google Calendar. Please try again."
            
        service = build('calendar', 'v3', credentials=creds)
        
        try:
            start_dt = datetime.strptime(start_time, '%Y-%m-%d %H:%M')
            end_dt = datetime.strptime(end_time, '%Y-%m-%d %H:%M')
        except ValueError:
            logger.error(f"Invalid datetime format: {start_time}, {end_time}")
            return "Error: Invalid datetime format. Please use YYYY-MM-DD HH:MM format."
        
        event = {
            'summary': title,
            'location': location,
            'description': description,
            'start': {
                'dateTime': start_dt.isoformat(),
                'timeZone': 'UTC',
            },
            'end': {
                'dateTime': end_dt.isoformat(),
                'timeZone': 'UTC',
            },
        }
        
        event = service.events().insert(calendarId='primary', body=event).execute()
        return f"Event created: {event.get('htmlLink')}"
    except Exception as e:
        logger.error(f"Error creating event: {e}")
        return f"Error creating event: {str(e)}"

def update_event(event_id, title=None, start_time=None, end_time=None, description=None, location=None):
    """Update an existing calendar event."""
    try:
        creds = get_credentials('calendar')
        if not creds:
            return "Error: Failed to authenticate with Google Calendar. Please try again."
            
        service = build('calendar', 'v3', credentials=creds)
        
        event = service.events().get(calendarId='primary', eventId=event_id).execute()
        
        if title:
            event['summary'] = title
        if description:
            event['description'] = description
        if location:
            event['location'] = location
        
        if start_time:
            try:
                start_dt = datetime.strptime(start_time, '%Y-%m-%d %H:%M')
                event['start']['dateTime'] = start_dt.isoformat()
            except ValueError:
                logger.error(f"Invalid start time format: {start_time}")
                return "Error: Invalid start time format. Please use YYYY-MM-DD HH:MM format."
        
        if end_time:
            try:
                end_dt = datetime.strptime(end_time, '%Y-%m-%d %H:%M')
                event['end']['dateTime'] = end_dt.isoformat()
            except ValueError:
                logger.error(f"Invalid end time format: {end_time}")
                return "Error: Invalid end time format. Please use YYYY-MM-DD HH:MM format."
        
        updated_event = service.events().update(calendarId='primary', eventId=event_id, body=event).execute()
        return f"Event updated: {updated_event.get('htmlLink')}"
    except Exception as e:
        logger.error(f"Error updating event: {e}")
        return f"Error updating event: {str(e)}"

def delete_event(event_id):
    """Delete a calendar event."""
    try:
        creds = get_credentials('calendar')
        if not creds:
            return "Error: Failed to authenticate with Google Calendar. Please try again."
            
        service = build('calendar', 'v3', credentials=creds)
        
        service.events().delete(calendarId='primary', eventId=event_id).execute()
        return "Event deleted successfully."
    except Exception as e:
        logger.error(f"Error deleting event: {e}")
        return f"Error deleting event: {str(e)}"

def list_emails():
    """List the user's emails."""
    try:
        creds = get_credentials('gmail')
        if not creds:
            return ["Error: Failed to authenticate with Gmail. Please try again."]
            
        service = build('gmail', 'v1', credentials=creds)
        
        results = service.users().messages().list(userId='me', maxResults=5, q="in:inbox").execute()
        messages = results.get('messages', [])
        
        if not messages:
            return ["No emails found."]
        
        email_list = []
        for message in messages:
            msg = service.users().messages().get(userId='me', id=message['id']).execute()
            
            headers = msg['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), "No Subject")
            sender = next((h['value'] for h in headers if h['name'] == 'From'), "Unknown Sender")
            
            snippet = msg.get('snippet', '')
            if len(snippet) > 50:
                snippet = snippet[:50] + "..."
            
            email_list.append(f"{sender}: {subject} - {snippet}")
        
        return email_list
    except Exception as e:
        logger.error(f"Error listing emails: {e}")
        return [f"Error fetching emails: {str(e)}"]

def send_email(to, subject, body):
    """Send an email."""
    try:
        creds = get_credentials('gmail')
        if not creds:
            return "Error: Failed to authenticate with Gmail. Please try again."
            
        service = build('gmail', 'v1', credentials=creds)
        
        from email.mime.text import MIMEText
        import base64
        
        message = MIMEText(body)
        message['to'] = to
        message['subject'] = subject
        
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        
        message = service.users().messages().send(userId='me', body={'raw': raw}).execute()
        return f"Email sent: {message['id']}"
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        return f"Error sending email: {str(e)}"

def list_tasks():
    """List the user's tasks."""
    try:
        creds = get_credentials('tasks')
        if not creds:
            return ["Error: Failed to authenticate with Google Tasks. Please try again."]
            
        service = build('tasks', 'v1', credentials=creds)
        
        results = service.tasks().list(tasklist='@default').execute()
        tasks = results.get('items', [])
        
        if not tasks:
            return ["No tasks found."]
        
        task_list = []
        for task in tasks:
            title = task.get('title', 'No Title')
            due = task.get('due', '')
            status = task.get('status', 'needsAction')
            
            if due:
                due_date = datetime.fromisoformat(due.replace('Z', '+00:00')).strftime('%Y-%m-%d')
            else:
                due_date = "No due date"
            
            status_str = "Completed" if status == 'completed' else "Pending"
            
            task_list.append(f"{due_date} - {title} ({status_str})")
        
        return task_list
    except Exception as e:
        logger.error(f"Error listing tasks: {e}")
        return [f"Error fetching tasks: {str(e)}"]

def create_task(title, due_date=None, notes=None):
    """Create a new task."""
    try:
        creds = get_credentials('tasks')
        if not creds:
            return "Error: Failed to authenticate with Google Tasks. Please try again."
            
        service = build('tasks', 'v1', credentials=creds)
        
        task = {
            'title': title,
            'status': 'needsAction'
        }
        
        if due_date:
            try:
                due_dt = datetime.strptime(due_date, '%Y-%m-%d')
                task['due'] = due_dt.isoformat() + 'Z'
            except ValueError:
                logger.error(f"Invalid due date format: {due_date}")
                return "Error: Invalid due date format. Please use YYYY-MM-DD format."
        
        if notes:
            task['notes'] = notes
        
        result = service.tasks().insert(tasklist='@default', body=task).execute()
        return f"Task created: {result.get('id')}"
    except Exception as e:
        logger.error(f"Error creating task: {e}")
        return f"Error creating task: {str(e)}"

def update_task(task_id, title=None, due_date=None, notes=None, status=None):
    """Update an existing task."""
    try:
        creds = get_credentials('tasks')
        if not creds:
            return "Error: Failed to authenticate with Google Tasks. Please try again."
            
        service = build('tasks', 'v1', credentials=creds)
        
        task = service.tasks().get(tasklist='@default', taskId=task_id).execute()
        
        if title:
            task['title'] = title
        if notes:
            task['notes'] = notes
        if status:
            task['status'] = status
        
        if due_date:
            try:
                due_dt = datetime.strptime(due_date, '%Y-%m-%d')
                task['due'] = due_dt.isoformat() + 'Z'
            except ValueError:
                logger.error(f"Invalid due date format: {due_date}")
                return "Error: Invalid due date format. Please use YYYY-MM-DD format."
        
        updated_task = service.tasks().update(tasklist='@default', taskId=task_id, body=task).execute()
        return f"Task updated: {updated_task.get('id')}"
    except Exception as e:
        logger.error(f"Error updating task: {e}")
        return f"Error updating task: {str(e)}"

def delete_task(task_id):
    """Delete a task."""
    try:
        creds = get_credentials('tasks')
        if not creds:
            return "Error: Failed to authenticate with Google Tasks. Please try again."
            
        service = build('tasks', 'v1', credentials=creds)
        
        service.tasks().delete(tasklist='@default', taskId=task_id).execute()
        return "Task deleted successfully."
    except Exception as e:
        logger.error(f"Error deleting task: {e}")
        return f"Error deleting task: {str(e)}"