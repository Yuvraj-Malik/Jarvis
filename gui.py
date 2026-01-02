import sys
import threading
import time
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread, pyqtSlot
from PyQt5.QtGui import QColor, QPainter, QPen, QFont
import status  # To check global flags (IS_SPEAKING, etc.)

# --- GLOBAL APP REFERENCE ---
# This allows external threads (like main.py) to update the GUI
_app_window = None

class JarvisOverlay(QWidget):
    # Signals must be defined at class level
    update_text_signal = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        # Transparent, Top-Most, Frameless Window
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        screen = QApplication.primaryScreen().availableGeometry()
        width = 400
        height = 400
        # Position: Right side of screen, but ensure it fits
        x = screen.width() - width - 50 
        y = 100
        self.setGeometry(x, y, width, height)
        
        # Layout & Label
        self.layout = QVBoxLayout()
        self.status_label = QLabel("SYSTEM ONLINE")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setFont(QFont("Consolas", 12, QFont.Bold))
        self.status_label.setStyleSheet("color: rgba(0, 255, 255, 200);") 
        self.layout.addStretch()
        self.layout.addWidget(self.status_label)
        self.layout.addStretch()
        self.setLayout(self.layout)

        # Animation State
        self.circle_size = 100
        self.growing = True
        self.color = QColor(0, 255, 255) 
        self.status_mode = "listening" 

        # Connect Signal
        self.update_text_signal.connect(self._update_label_safe)

        # Animation Timer (60 FPS approx)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate_pulse)
        self.timer.start(20)

    @pyqtSlot(str)
    def _update_label_safe(self, text):
        """Thread-safe way to update text"""
        if len(text) > 40: text = text[:37] + "..."
        self.status_label.setText(text.upper())

    def animate_pulse(self):
        """
        Updates the Orb's color and pulse speed based on 'status.py' flags.
        This reads the global flags set by main.py.
        """
        
        # 1. READ GLOBAL STATUS
        if status.IS_SPEAKING:
            self.status_mode = "speaking"
            self.color = QColor(255, 50, 50) # RED
            text_state = "SPEAKING"
        elif status.IS_MUSIC_PLAYING:
            self.status_mode = "music"
            self.color = QColor(138, 43, 226) # PURPLE
            text_state = "MUSIC ACTIVE"
        else:
            self.status_mode = "listening"
            self.color = QColor(0, 255, 255) # CYAN
            text_state = "LISTENING"

        # (Optional) Update text only if it's generic status
        # If main.py sent specific text (like a reply), we don't overwrite it immediately
        # self.status_label.setText(text_state) 

        # 2. CALCULATE SPEED
        if self.status_mode == "listening": speed, max_s, min_s = 0.5, 110, 90
        elif self.status_mode == "music": speed, max_s, min_s = 0.8, 115, 95
        elif self.status_mode == "speaking": speed, max_s, min_s = 4.0, 130, 80
        else: speed, max_s, min_s = 1, 100, 100

        # 3. GROW / SHRINK
        if self.growing:
            self.circle_size += speed
            if self.circle_size >= max_s: self.growing = False
        else:
            self.circle_size -= speed
            if self.circle_size <= min_s: self.growing = True
            
        self.update() # Trigger paintEvent

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Setup Pen (Outline)
        pen = QPen(self.color, 4)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        
        # Draw Outer Ring
        center_x, center_y = self.width() // 2, self.height() // 2
        radius = int(self.circle_size)
        painter.drawEllipse(center_x - radius, center_y - radius, radius * 2, radius * 2)
        
        # Draw Inner Core (Semi-transparent)
        painter.setBrush(self.color)
        painter.setOpacity(0.3)
        core_radius = radius // 2
        painter.drawEllipse(center_x - core_radius, center_y - core_radius, core_radius * 2, core_radius * 2)

# --- PUBLIC FUNCTIONS FOR MAIN.PY ---

def set_text(text):
    """Call this from main.py to change the Orb's text"""
    if _app_window:
        _app_window.update_text_signal.emit(str(text))

def run_gui():
    """Starts the PyQt5 Event Loop. Blocking call."""
    global _app_window
    app = QApplication(sys.argv)
    _app_window = JarvisOverlay()
    _app_window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    run_gui()