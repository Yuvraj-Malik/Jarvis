import sys
import threading
import time
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QVBoxLayout, 
                             QLineEdit, QTextEdit, QFrame, QHBoxLayout, 
                             QGraphicsDropShadowEffect)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, pyqtSlot, QSize, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QColor, QPainter, QPen, QFont, QLinearGradient, QBrush
from utils import status 

_app_window = None

class JarvisGUI(QWidget):
    # Signals
    new_command_signal = pyqtSignal(str)
    add_text_signal = pyqtSignal(str) 
    update_status_signal = pyqtSignal(str) # NEW: For status bar updates
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        # Connect signals
        self.add_text_signal.connect(self._internal_add_text)
        self.update_status_signal.connect(self._internal_update_status)
        
    def init_ui(self):
        # Window Setup
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(450, 600)
        
        # Position: Bottom Right
        screen = QApplication.primaryScreen().availableGeometry()
        self.move(screen.width() - self.width() - 40, screen.height() - self.height() - 60)
        
        # Main Layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(15)
        
        # --- CONTAINER (The Glass Frame) ---
        self.container = QFrame()
        self.container.setObjectName("MainContainer")
        self.container.setStyleSheet("""
            #MainContainer {
                background-color: rgba(15, 20, 30, 220);
                border-radius: 25px;
                border: 1px solid rgba(0, 255, 255, 50);
            }
        """)
        
        # Shadow Effect
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(30)
        self.shadow.setColor(QColor(0, 255, 255, 40))
        self.shadow.setOffset(0, 0)
        self.container.setGraphicsEffect(self.shadow)
        
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(15, 15, 15, 15)
        
        # --- HEADER ---
        self.header = QLabel("J.A.R.V.I.S. 2.0")
        self.header.setAlignment(Qt.AlignCenter)
        self.header.setStyleSheet("color: rgba(0, 255, 255, 220); font-size: 18px; font-weight: bold; letter-spacing: 2px;")
        container_layout.addWidget(self.header)
        
        # --- THE ORB (Custom Widget) ---
        self.orb_container = QWidget()
        self.orb_container.setFixedSize(150, 150)
        self.orb_layout = QVBoxLayout(self.orb_container)
        container_layout.addWidget(self.orb_container, alignment=Qt.AlignCenter)
        
        # --- CHAT LOG ---
        self.chat_log = QTextEdit()
        self.chat_log.setReadOnly(True)
        self.chat_log.setStyleSheet("""
            QTextEdit {
                background: transparent;
                border: none;
                color: rgba(255, 255, 255, 180);
                font-size: 13px;
                font-family: 'Segoe UI';
            }
        """)
        container_layout.addWidget(self.chat_log)
        
        # --- STATUS INDICATOR ---
        self.status_bar = QLabel("INITIALIZING...")
        self.status_bar.setAlignment(Qt.AlignCenter)
        self.status_bar.setStyleSheet("color: rgba(0, 255, 255, 150); font-size: 11px; font-style: italic;")
        container_layout.addWidget(self.status_bar)
        
        # --- INPUT AREA ---
        input_frame = QFrame()
        input_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 15);
                border-radius: 15px;
                padding: 5px;
            }
        """)
        input_layout = QHBoxLayout(input_frame)
        input_layout.setContentsMargins(10, 5, 10, 5)
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Type command...")
        self.input_field.setStyleSheet("""
            QLineEdit {
                background: transparent;
                border: none;
                color: white;
                font-size: 14px;
            }
        """)
        self.input_field.returnPressed.connect(self.handle_send)
        input_layout.addWidget(self.input_field)
        
        container_layout.addWidget(input_frame)
        
        self.main_layout.addWidget(self.container)
        
        # --- ANIMATION STATE ---
        self.orb_radius = 40
        self.pulse_dir = 1
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_ui)
        self.timer.start(30)
        
    def handle_send(self):
        text = self.input_field.text().strip()
        if text:
            self.chat_log.append(f"<b style='color: #00ffff;'>You:</b> {text}")
            self.new_command_signal.emit(text)
            self.input_field.clear()
            
    def update_ui(self):
        # Pulse Animation
        if self.pulse_dir == 1:
            self.orb_radius += 0.5
            if self.orb_radius >= 50: self.pulse_dir = -1
        else:
            self.orb_radius -= 0.5
            if self.orb_radius <= 40: self.pulse_dir = 1
            
        # Status Update
        if status.IS_SPEAKING:
            self.status_bar.setText("TRANSMITTING...")
            self.status_bar.setStyleSheet("color: #ff3232;") # Red
        elif status.IS_AWAKE:
            self.status_bar.setText("LISTENING...")
            self.status_bar.setStyleSheet("color: #00ffff;") # Cyan
        else:
            self.status_bar.setText("IDLE")
            self.status_bar.setStyleSheet("color: rgba(255, 255, 255, 100);")

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Find Center of Orb Container
        orb_center = self.orb_container.mapTo(self, self.orb_container.rect().center())
        cx, cy = orb_center.x(), orb_center.y()
        
        color = QColor(0, 255, 255) if not status.IS_SPEAKING else QColor(255, 50, 50)
        
        # 1. Glow Effect (Outer)
        for i in range(3):
            alpha = 50 - (i * 15)
            painter.setBrush(QBrush(QColor(color.red(), color.green(), color.blue(), alpha)))
            painter.setPen(Qt.NoPen)
            r = self.orb_radius + (i * 15)
            painter.drawEllipse(int(cx - r), int(cy - r), int(r * 2), int(r * 2))
            
        # 2. Core (Inner)
        painter.setBrush(QBrush(color))
        r_inner = self.orb_radius * 0.6
        painter.drawEllipse(int(cx - r_inner), int(cy - r_inner), int(r_inner * 2), int(r_inner * 2))
        
        # 3. Spinning Ring (Static for now, but looks cool)
        pen = QPen(color, 2)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        r_ring = self.orb_radius + 5
        painter.drawEllipse(int(cx - r_ring), int(cy - r_ring), int(r_ring * 2), int(r_ring * 2))

    def _internal_add_text(self, text):
        """Thread-safe update of the chat log"""
        self.chat_log.append(f"<b style='color: #ffffff;'>Jarvis:</b> {text}")
        # Scroll to bottom
        self.chat_log.verticalScrollBar().setValue(self.chat_log.verticalScrollBar().maximum())

    def _internal_update_status(self, text):
        """Update the small status bar at the bottom"""
        self.status_bar.setText(text.upper())
        if "LISTENING" in text or "AWAKE" in text:
            self.status_bar.setStyleSheet("color: #00ffff;")
        elif "TRANSMITTING" in text or "SPEAKING" in text:
            self.status_bar.setStyleSheet("color: #ff3232;")
        else:
            self.status_bar.setStyleSheet("color: rgba(255, 255, 255, 100);")

# --- PUBLIC INTERFACE ---

def set_text(text):
    if _app_window:
        _app_window.add_text_signal.emit(str(text))

def set_status(text):
    """Call this to update the status bar without spamming chat"""
    if _app_window:
        _app_window.update_status_signal.emit(str(text))

def run_gui(command_queue):
    global _app_window
    app = QApplication(sys.argv)
    _app_window = JarvisGUI()
    
    # Connect signal to the queue
    _app_window.new_command_signal.connect(lambda cmd: command_queue.put(cmd))
    
    _app_window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    from queue import Queue
    run_gui(Queue())