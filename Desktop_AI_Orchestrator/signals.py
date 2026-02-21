#signals
from PyQt6.QtCore import QObject, pyqtSignal

class Signals(QObject):
    email_signal = pyqtSignal(list)
    task_signal = pyqtSignal(list)

signals = Signals()