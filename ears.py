import speech_recognition as sr
import status
import time

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
        
        # Don't listen while Jarvis is speaking
        if status.IS_SPEAKING:
            return ""

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
                # No speech detected - normal, not an error
                return ""
                
            except sr.UnknownValueError:
                # Speech detected but unclear
                self.failed_attempts += 1
                
                # If multiple failures, recalibrate
                if self.failed_attempts >= self.max_failures:
                    print("   (🔧 Recalibrating microphone...)")
                    self.recognizer.adjust_for_ambient_noise(source, duration=1)
                    self.failed_attempts = 0
                
                return ""
                
            except sr.RequestError as e:
                # Internet/API issue
                print(f"   (⚠️ Speech service error: {e})")
                time.sleep(2)  # Wait before retry
                return ""
                
            except Exception as e:
                # Unexpected error
                print(f"   (❌ Microphone error: {e})")
                return ""

# Global listener instance
_listener = AdaptiveListener()

def listen():
    """Main function called by main.py"""
    return _listener.listen()