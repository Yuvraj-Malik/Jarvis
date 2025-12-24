import threading
import time
import sys
import os
import status
import hotword
from ears import listen
from skills import speak
from brain import ModelManager

# GUI Import
try:
    import gui 
    HAS_GUI = True
except ImportError:
    HAS_GUI = False
    print("⚠️ GUI not available (optional)")

def jarvis_logic():
    """Main Jarvis intelligence loop"""
    print("   (🧠 Jarvis Core Online...)")
    bot = ModelManager()
    
    # Initialize flags
    status.IS_SPEAKING = False
    status.IS_MUSIC_PLAYING = False
    
    # State management
    is_awake = False
    last_interaction_time = 0
    SLEEP_TIMEOUT = 30  # Increased from 10 to 30 seconds
    consecutive_silence = 0
    MAX_SILENCE_COUNT = 3  # Sleep after 3 consecutive silent listens
    
    # Startup
    speak("Systems online. How may I assist you, sir?")
    if HAS_GUI:
        gui.set_text("READY")

    while True:
        try:
            current_time = time.time()
            
            # =========================================
            # PHASE 1: SLEEPING (GUARD MODE)
            # =========================================
            if not is_awake:
                if HAS_GUI:
                    gui.set_text("SAY 'JARVIS'")
                
                # Block until wake word detected
                wake_detected = hotword.listen_for_wake_word()
                
                if wake_detected:
                    is_awake = True
                    last_interaction_time = current_time
                    consecutive_silence = 0
                    
                    if HAS_GUI:
                        gui.set_text("LISTENING")
                    speak("Yes, sir?")
                else:
                    # Hotword detection failed, retry
                    continue

            # =========================================
            # PHASE 2: AWAKE MODE (ACTIVE LISTENING)
            # =========================================
            
            # Check for timeout (user went silent)
            time_since_last = current_time - last_interaction_time
            
            if time_since_last > SLEEP_TIMEOUT:
                is_awake = False
                consecutive_silence = 0
                
                if HAS_GUI:
                    gui.set_text("SLEEP MODE")
                speak("Entering sleep mode.")
                continue

            # Display status
            if HAS_GUI:
                remaining = int(SLEEP_TIMEOUT - time_since_last)
                gui.set_text(f"LISTENING ({remaining}s)")
            
            # Listen for command
            command = listen()
            
            # Handle empty response
            if not command:
                consecutive_silence += 1
                
                # If too many silent attempts, go to sleep
                if consecutive_silence >= MAX_SILENCE_COUNT:
                    is_awake = False
                    consecutive_silence = 0
                    
                    if HAS_GUI:
                        gui.set_text("IDLE TIMEOUT")
                    speak("Standing by.")
                
                continue  # Skip to next iteration
            
            # Valid command received
            consecutive_silence = 0
            last_interaction_time = time.time()  # Reset timer
            
            print(f"\n👂 USER: '{command}'")
            
            if HAS_GUI:
                display_cmd = command[:35] + "..." if len(command) > 35 else command
                gui.set_text(f"YOU: {display_cmd.upper()}")

            # =========================================
            # SPECIAL COMMANDS
            # =========================================
            cmd_lower = command.lower()
            
            # Exit commands
            if any(x in cmd_lower for x in ["goodbye jarvis", "shut down", "exit", "quit"]):
                speak("Goodbye, sir. Systems shutting down.")
                if HAS_GUI:
                    gui.set_text("SHUTDOWN")
                time.sleep(2)
                os._exit(0)
            
            # Sleep commands
            if any(x in cmd_lower for x in ["sleep", "sleep mode", "go to sleep", 
                                             "cancel", "never mind", "forget it"]):
                is_awake = False
                consecutive_silence = 0
                speak("Sleeping.")
                continue

            # =========================================
            # PROCESS WITH BRAIN
            # =========================================
            try:
                response = bot.process_request(command)
                print(f"🤖 JARVIS: {response}\n")
                
                # Display response in GUI
                if HAS_GUI:
                    display_resp = str(response)[:35] + "..." if len(str(response)) > 35 else str(response)
                    gui.set_text(f"JARVIS: {display_resp.upper()}")

                # Speak response (skip if it contains raw JSON)
                response_str = str(response).strip()
                
                # Don't speak if response looks like code/JSON
                if not any(char in response_str[:50] for char in ['{', '[', '```']):
                    speak(response_str)
                else:
                    # Generic confirmation for tool executions
                    speak("Done.")
                    
            except Exception as e:
                print(f"❌ Brain Error: {e}")
                if HAS_GUI:
                    gui.set_text("ERROR - RETRY")
                speak("I encountered an error. Please try again.")
                
        except KeyboardInterrupt:
            print("\n🛑 Shutting down...")
            speak("Shutting down.")
            os._exit(0)
            
        except Exception as e:
            print(f"❌ Critical Error: {e}")
            if HAS_GUI:
                gui.set_text("SYSTEM ERROR")
            time.sleep(2)

def main():
    """Entry point"""
    print("\n" + "="*50)
    print("     J.A.R.V.I.S. - Personal AI Assistant")
    print("="*50 + "\n")
    
    print("🔧 Initializing systems...")
    
    # Start brain in separate thread
    brain_thread = threading.Thread(target=jarvis_logic, daemon=True)
    brain_thread.start()
    
    # Run GUI (blocking) or keep main thread alive
    if HAS_GUI:
        print("🔮 Launching visual interface...")
        gui.run_gui()
    else:
        print("💬 Running in console mode")
        print("   (Press Ctrl+C to exit)\n")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            os._exit(0)

if __name__ == "__main__":
    main()