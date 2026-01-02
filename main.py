import threading
import time
import sys
import os
import status
import hotword
from ears import listen
from skills import speak
from brain import ModelManager
import queue 

try:
    import gui 
    HAS_GUI = True
except ImportError:
    HAS_GUI = False

command_queue = queue.Queue()

def text_listener():
    print("\n💻 TYPE MODE ENABLED: You can type commands below without wake word.")
    while True:
        try:
            cmd = input("👉 TYPE COMMAND: ")
            if cmd:
                command_queue.put(cmd)
        except EOFError:
            break
        except Exception:
            continue

def wake_word_listener():
    while True:
        try:
            if hotword.listen_for_wake_word():
                status.IS_AWAKE = True
                print("\n[Voice] Wake Word Detected")
        except Exception:
            pass

if not hasattr(status, 'IS_AWAKE'):
    status.IS_AWAKE = False

def jarvis_logic():
    print("Intelligence Online.")
    bot = ModelManager()
    status.IS_SPEAKING = False
    status.IS_MUSIC_PLAYING = False
    
    last_interaction_time = 0
    SLEEP_TIMEOUT = 30
    consecutive_silence = 0
    MAX_SILENCE_COUNT = 3
    
    # Optional: Speak at startup
    # speak("Systems online.") 
    
    if HAS_GUI:
        gui.set_text("READY")

    while True:
        try:
            current_time = time.time()
            
            # --- CHECK TYPED COMMANDS ---
            try:
                cmd = command_queue.get_nowait()
                status.IS_AWAKE = True
                last_interaction_time = current_time
                consecutive_silence = 0
                
                cmd_lower = cmd.lower()
                if any(x in cmd_lower for x in ["exit", "quit"]):
                    speak("Goodbye.")
                    os._exit(0)
                if any(x in cmd_lower for x in ["sleep", "go to sleep"]):
                    status.IS_AWAKE = False
                    speak("Sleeping.")
                    continue

                print(f"\nUser: {cmd}")
                if HAS_GUI:
                    gui.set_text(f"USER: {cmd[:30].upper()}...")

                try:
                    response = bot.process_request(cmd)
                    print(f"Jarvis: {response}\n")
                    
                    if HAS_GUI:
                        display_resp = str(response)[:35] + "..." if len(str(response)) > 35 else str(response)
                        gui.set_text(f"JARVIS: {display_resp.upper()}")

                    response_str = str(response).strip()
                    if not any(char in response_str[:50] for char in ['{', '[', '```']):
                        speak(response_str)
                except Exception as e:
                    print(f"Error: {e}")
            except queue.Empty:
                pass

            # --- VOICE LOGIC ---
            if status.IS_AWAKE:
                time_since_last = current_time - last_interaction_time
                if time_since_last > SLEEP_TIMEOUT:
                    status.IS_AWAKE = False
                    consecutive_silence = 0
                    if HAS_GUI: gui.set_text("SLEEP MODE")
                    speak("Entering sleep mode.")
                    continue

                if HAS_GUI:
                    remaining = int(SLEEP_TIMEOUT - time_since_last)
                    gui.set_text(f"LISTENING ({remaining}s)")

                command = listen()
                if command:
                    consecutive_silence = 0
                    last_interaction_time = current_time 
                    
                    print(f"\nUser: {command}")
                    if HAS_GUI:
                        gui.set_text(f"YOU: {command[:35].upper()}...")

                    cmd_lower = command.lower()
                    if any(x in cmd_lower for x in ["goodbye", "shut down", "exit"]):
                        speak("Goodbye.")
                        os._exit(0)
                    if any(x in cmd_lower for x in ["sleep", "sleep mode"]):
                        status.IS_AWAKE = False
                        speak("Sleeping.")
                        continue

                    try:
                        response = bot.process_request(command)
                        print(f"Jarvis: {response}\n")
                        
                        if HAS_GUI:
                            display_resp = str(response)[:35] + "..." if len(str(response)) > 35 else str(response)
                            gui.set_text(f"JARVIS: {display_resp.upper()}")

                        response_str = str(response).strip()
                        if not any(char in response_str[:50] for char in ['{', '[', '```']):
                            speak(response_str)
                    except Exception as e:
                        print(f"Error: {e}")
                else:
                    consecutive_silence += 1
                    if consecutive_silence >= MAX_SILENCE_COUNT:
                        status.IS_AWAKE = False
                        consecutive_silence = 0
                        if HAS_GUI: gui.set_text("IDLE TIMEOUT")
                        speak("Standing by.")

            # --- SLEEP MODE ---
            if not status.IS_AWAKE:
                if HAS_GUI: gui.set_text("SAY 'JARVIS' OR TYPE")
                time.sleep(0.1)
            else:
                time.sleep(0.1)

        except KeyboardInterrupt:
            print("\nShutting down...")
            speak("Shutting down.")
            os._exit(0)
        except Exception as e:
            print(f"Critical Error: {e}")
            time.sleep(1)

def main():
    print("\n     J.A.R.V.I.S. - Personal Assistant")
    print("Initializing systems...")
    
    if not hasattr(status, 'IS_AWAKE'): status.IS_AWAKE = False
    
    wake_thread = threading.Thread(target=wake_word_listener, daemon=True)
    wake_thread.start()
    
    text_thread = threading.Thread(target=text_listener, daemon=True)
    text_thread.start()
    
    brain_thread = threading.Thread(target=jarvis_logic, daemon=True)
    brain_thread.start()
    
    if HAS_GUI:
        gui.run_gui()
    else:
        try:
            while True: time.sleep(1)
        except KeyboardInterrupt:
            print("Goodbye!")
            os._exit(0)

if __name__ == "__main__":
    main()