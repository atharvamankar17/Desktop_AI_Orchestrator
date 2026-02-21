#UI
import sys
import queue
import threading
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QListWidget, QLineEdit, QGroupBox, QCalendarWidget
)
from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from signals import signals
from backend import shutdown_event, response_queue
from google_services import list_emails, list_tasks
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

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

class ResponseThread(QThread):
    response_signal = pyqtSignal(str)
    def __init__(self):
        super().__init__()
        self.running = True
    def run(self):
        while self.running:
            try:
                response = response_queue.get(timeout=1)
                self.response_signal.emit(response)
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Response thread error: {e}")
    def stop(self):
        self.running = False

class WorkerThread(QThread):
    def __init__(self, input_queue):
        super().__init__()
        self.input_queue = input_queue
    def run(self):
        from backend import schedule_tasks
        scheduler_thread = threading.Thread(target=schedule_tasks, daemon=True)
        scheduler_thread.start()
        from backend import ai_processing
        ai_processing(self.input_queue)
        shutdown_event.set()
        scheduler_thread.join(timeout=1.0)

class DashboardWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Dashboard")
        self.setFixedSize(1300, 850)
        self.dark_mode = False
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.layout = QVBoxLayout(self.main_widget)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)
        self.input_queue = queue.Queue()
        self.init_header()
        self.main_layout = QHBoxLayout()
        self.main_layout.setSpacing(10)
        self.chat_widget = self.create_chat_widget()
        self.main_layout.addWidget(self.chat_widget, 1)
        self.right_layout = QVBoxLayout()
        self.right_layout.setSpacing(10)
        self.right_layout.addWidget(self.create_calendar_widget(), 2)
        self.right_layout.addWidget(self.create_email_widget(), 1)
        self.right_layout.addWidget(self.create_task_widget(), 1)
        self.right_container = QWidget()
        self.right_container.setLayout(self.right_layout)
        self.main_layout.addWidget(self.right_container, 1)
        self.layout.addLayout(self.main_layout)
        self.apply_light_theme()
        self.setStyleSheet(self.base_stylesheet())
        self.worker = WorkerThread(self.input_queue)
        self.worker.start()
        self.response_thread = ResponseThread()
        self.response_thread.response_signal.connect(self.update_chat_display)
        signals.email_signal.connect(self.update_email_widget)
        signals.task_signal.connect(self.update_task_widget)
        self.response_thread.start()
        self.fetch_initial_data()
    
    def init_header(self):
        header_layout = QHBoxLayout()
        header_label = QLabel("Welcome to AI Assistant")
        header_label.setStyleSheet("font-size: 20px; font-weight: 600; padding: 8px;")
        self.toggle_theme_btn = QPushButton("Toggle Dark Mode")
        self.toggle_theme_btn.setStyleSheet("font-weight: 600; padding: 6px 16px; font-size: 13px;")
        self.toggle_theme_btn.clicked.connect(self.toggle_theme)
        header_layout.addWidget(header_label)
        header_layout.addStretch()
        header_layout.addWidget(self.toggle_theme_btn)
        self.layout.addLayout(header_layout)
    
    def base_stylesheet(self):
        return """
            QGroupBox {
                border: 1px solid #999;
                border-radius: 8px;
                padding: 10px;
                font-weight: 600;
                font-size: 16px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 6px;
            }
            QPushButton {
                padding: 6px 12px;
                border-radius: 6px;
                background-color: #3498db;
                font-weight: 600;
                color: white;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QLineEdit, QTextEdit {
                border: 1px solid #ccc;
                border-radius: 6px;
                padding: 6px;
            }
            QListWidget, QCheckBox {
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 13px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #eee;
            }
            QCalendarWidget {
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 13px;
            }
        """
    
    def create_email_widget(self):
        self.email_box = QGroupBox("Email Assistant")
        layout = QVBoxLayout()
        layout.setSpacing(4)
        self.email_list = QListWidget()
        layout.addWidget(self.email_list)
        self.email_box.setLayout(layout)
        return self.email_box
    
    def create_calendar_widget(self):
        box = QGroupBox("Calendar")
        layout = QVBoxLayout()
        layout.setSpacing(4)
        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.setStyleSheet("font-size: 11px;")
        self.calendar.selectionChanged.connect(self.show_selected_date)
        layout.addWidget(self.calendar)
        box.setLayout(layout)
        return box
    
    def show_selected_date(self):
        selected = self.calendar.selectedDate()
        self.chat_display.append(f"You: Selected Date: {selected.toString('dd MMM yyyy')}")

        date_str = selected.toString('MM/dd/yyyy')  
        logger.info(f"User selected date: {date_str}")
        self.input_queue.put(f"show events for {date_str}")
    
    def create_chat_widget(self):
        box = QGroupBox("Chat with AI")
        layout = QVBoxLayout()
        layout.setSpacing(5)
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Ask something to AI (e.g., 'set volume to 50%', 'write a poem in notepad')...")
        self.chat_input.returnPressed.connect(self.send_message)
        send_btn = QPushButton("Send")
        send_btn.setFixedSize(100, 36)
        send_btn.setStyleSheet("""
            QPushButton {
                font-size: 13px;
                font-weight: 600;
                background-color: #27ae60;
                color: white;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #219150;
            }
        """)
        send_btn.clicked.connect(self.send_message)
        input_layout = QHBoxLayout()
        input_layout.setSpacing(5)
        input_layout.addWidget(self.chat_input)
        input_layout.addWidget(send_btn)
        layout.addWidget(self.chat_display)
        layout.addLayout(input_layout)
        box.setLayout(layout)
        return box
    
    def create_task_widget(self):
        self.task_box = QGroupBox("Task Manager")
        layout = QVBoxLayout()
        layout.setSpacing(4)
        self.task_list = QListWidget()
        layout.addWidget(self.task_list)
        self.task_box.setLayout(layout)
        return self.task_box
    
    def send_message(self):
        user_message = self.chat_input.text().strip()
        if user_message:
            self.chat_display.append(f"You: {user_message}")
            self.chat_input.clear()
            self.input_queue.put(user_message)
    
    def update_chat_display(self, response):
        try:
            if response.startswith("Error:"):
                self.chat_display.append(f"AI: {response}")
                self.chat_display.setTextColor(QColor("red"))
                self.chat_display.append(f"⚠️ {response}")
                self.chat_display.setTextColor(QColor("black"))
            else:
                self.chat_display.append(f"AI: {response}")
        except Exception as e:
            logger.error(f"Error updating chat display: {e}")
            self.chat_display.append(f"System Error: Could not display response properly")
        
        self.chat_display.ensureCursorVisible()
    
    def update_email_widget(self, emails):
        try:
            self.email_list.clear()
            self.email_list.addItems(emails if emails else ["No emails found."])
        except Exception as e:
            logger.error(f"Error updating email widget: {e}")
            self.email_list.clear()
            self.email_list.addItems(["Error loading emails"])
    
    def update_task_widget(self, tasks):
        try:
            self.task_list.clear()
            self.task_list.addItems(tasks if tasks else ["No tasks found."])
        except Exception as e:
            logger.error(f"Error updating task widget: {e}")
            self.task_list.clear()
            self.task_list.addItems(["Error loading tasks"])
    
    def fetch_initial_data(self):
        try:
            self.input_queue.put("show events for today")
            logger.info("Sent natural language command: show events for today")
            
            emails = list_emails()
            self.update_email_widget(emails)
            
            tasks = list_tasks()
            self.update_task_widget(tasks)
        except Exception as e:
            logger.error(f"Error fetching initial data: {e}")
            self.chat_display.append(f"System: Error loading initial data: {str(e)}")
    
    def toggle_theme(self):
        if not self.dark_mode:
            self.apply_dark_theme()
            self.toggle_theme_btn.setText("Toggle Light Mode")
        else:
            self.apply_light_theme()
            self.toggle_theme_btn.setText("Toggle Dark Mode")
        self.dark_mode = not self.dark_mode
        self.setStyleSheet(self.base_stylesheet())
    
    def apply_dark_theme(self):
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.ColorRole.Window, QColor(33, 33, 33))
        dark_palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
        dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.Button, QColor(45, 45, 45))
        dark_palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(100, 100, 255))
        dark_palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.white)
        QApplication.setPalette(dark_palette)
        
        self.chat_input.setStyleSheet("""
            QLineEdit {
                color: white;
                background-color: #252525;
                border: 1px solid #555;
                border-radius: 6px;
                padding: 6px;
            }
            QLineEdit::placeholder {
                color: #aaaaaa;
            }
        """)
    
    def apply_light_theme(self):
        light_palette = QPalette()
        light_palette.setColor(QPalette.ColorRole.Window, QColor("#ffffff"))
        light_palette.setColor(QPalette.ColorRole.WindowText, QColor("#000000"))
        light_palette.setColor(QPalette.ColorRole.Base, QColor("#f8f8f8"))
        light_palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#ffffff"))
        light_palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("#ffffff"))
        light_palette.setColor(QPalette.ColorRole.ToolTipText, QColor("#000000"))
        light_palette.setColor(QPalette.ColorRole.Text, QColor("#000000"))
        light_palette.setColor(QPalette.ColorRole.Button, QColor("#ffffff"))
        light_palette.setColor(QPalette.ColorRole.ButtonText, QColor("#000000"))
        light_palette.setColor(QPalette.ColorRole.Highlight, QColor("#3498db"))
        light_palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
        QApplication.setPalette(light_palette)
        
        self.chat_input.setStyleSheet("""
            QLineEdit {
                color: black;
                background-color: white;
                border: 1px solid #cccccc;
                border-radius: 6px;
                padding: 6px;
            }
            QLineEdit::placeholder {
                color: #777777;
            }
        """)
    
    def closeEvent(self, event):
        """Handle window close event to shut down backend."""
        shutdown_event.set()
        self.response_thread.stop()
        self.worker.quit()
        self.response_thread.quit()
        self.worker.wait()
        self.response_thread.wait()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = DashboardWindow()
    window.show()
    sys.exit(app.exec())