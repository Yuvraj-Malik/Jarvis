import speech_recognition as sr
from utils import status
import time

_MIC_AVAILABLE = True

class AdaptiveListener:
    """Smart microphone that adapts to environment"""
    
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.mic_calibrated = False
        self.failed_attempts = 0
        self.max_failures = 3
        
    def calibrate(self, source):
        """One-time calibration at startup"""
        if not self.mic_calibrated:
            print("   (🎤 Calibrating microphone...)")
            self.recognizer.adjust_for_ambient_noise(source, duration=1.5)
            self.mic_calibrated = True
            print(f"   (✅ Threshold set to {self.recognizer.energy_threshold})")
    
    def listen(self):
        """Listen with smart error recovery"""
        global _MIC_AVAILABLE
        
        # Don't listen while Jarvis is speaking
        if status.IS_SPEAKING:
            return ""

        if not _MIC_AVAILABLE:
            return ""

        try:
            with sr.Microphone() as source:
                # Calibrate once at first use
                self.calibrate(source)
                
                # Dynamic sensitivity based on environment
                if status.IS_MUSIC_PLAYING:
                    # High threshold for noisy environment
                    self.recognizer.energy_threshold = 500
                    self.recognizer.dynamic_energy_threshold = False
                else:
                    # Adaptive threshold for quiet environment
                    self.recognizer.dynamic_energy_threshold = True
                    # Prevent threshold from going too low
                    self.recognizer.energy_threshold = max(300, self.recognizer.energy_threshold)
                
                # Adjust response time
                self.recognizer.pause_threshold = 0.7  # Wait 0.7s after speech ends
                self.recognizer.phrase_threshold = 0.3  # Min speech duration
                
                try:
                    # Listen with timeout
                    audio = self.recognizer.listen(
                        source,
                        timeout=6,           # Wait 6s for speech to start
                        phrase_time_limit=10  # Max 10s of speech
                    )
                    
                    # Transcribe using Google (fastest, free)
                    text = self.recognizer.recognize_google(audio).strip()
                    
                    # Success - reset failure counter
                    self.failed_attempts = 0
                    return text
                    
                except sr.WaitTimeoutError:
                    return ""
                except sr.UnknownValueError:
                    self.failed_attempts += 1
                    if self.failed_attempts >= self.max_failures:
                        self.recognizer.adjust_for_ambient_noise(source, duration=1)
                        self.failed_attempts = 0
                    return ""
                except sr.RequestError:
                    time.sleep(2)
                    return ""
        except Exception as e:
            # Handle PyAudio missing or other Mic errors
            if "PyAudio" in str(e) or "Microphone" in str(e):
                if _MIC_AVAILABLE:
                    print(f"   (⚠️ Microphone unavailable: {e})")
                    _MIC_AVAILABLE = False
            else:
                print(f"   (❌ Microphone error: {e})")
            return ""

# Global listener instance
_listener = AdaptiveListener()

def listen():
    """Main function called by main.py"""
    return _listener.listen()