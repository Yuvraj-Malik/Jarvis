import os
import datetime
import pyautogui
import toolbox 
import status
import psutil

# ==========================================
# 🧩 ROUTER (The Control Hub)
# ==========================================
def system_control(command: str):
    """
    Decides which hardware tool to use based on the command.
    """
    command = command.lower()
    
    # --- PRIORITY 1: HARDWARE & STATUS ---
    # We check these FIRST so keywords like "Previous" don't trigger media
    if "brightness" in command: 
        return toolbox.set_brightness(command)
        
    if "volume" in command or "mute" in command or "unmute" in command: 
        return toolbox.set_volume(command)
        
    if "status" in command or "health" in command: 
        return toolbox.system_status()

    # --- PRIORITY 2: MEDIA CONTROLS ---
    # FIX: Explicitly check for resume/play
    if "play" in command or "resume" in command or "unpause" in command: 
        pyautogui.press("playpause"); return "Media Resumed."
        
    if "pause" in command or "stop" in command: 
        pyautogui.press("playpause"); return "Media Paused."
        
    if "next" in command or "skip" in command: 
        pyautogui.press("nexttrack"); return "Next Track."
        
    if "previous" in command or "back" in command: 
        pyautogui.press("prevtrack"); return "Previous Track."
    
    # --- PRIORITY 3: SECURITY ---
    if "lock" in command: 
        os.system("rundll32.exe user32.dll,LockWorkStation"); return "Locked."
    if "shutdown" in command: 
        toolbox.speak("Goodbye."); os._exit(0)
    
    return "System command not recognized."

# ==========================================
# 🔗 WRAPPERS
# ==========================================
def speak(text): return toolbox.speak(text)
def play_music(topic): return toolbox.play_yt(topic)
def google_search(query): return toolbox.search_google(query)
def send_whatsapp(to, message): return toolbox.whatsapp_msg(to, message)
def get_current_time(): return datetime.datetime.now().strftime("%I:%M %p")
def capture_screen_for_ai(): return pyautogui.screenshot()
def open_application(app_name): return toolbox.open_app(app_name)
def read_file(filename): return toolbox.read_pdf_or_txt(filename)
def create_file(filename, content): return toolbox.create_txt_file(filename, content)
def open_file(filename): 
    if os.path.exists(filename): os.startfile(filename); return "Opened."
    return "Not found."
def visit_website(url): return toolbox.visit_url(url)
def calculate(expression): return toolbox.calc_math(expression)
def remember(key, value): return toolbox.remember_key(key, value)
def recall(key): return toolbox.recall_key(key)
def get_all_memories(): return toolbox.get_all_memories()
def add_contact(name, phone): return toolbox.add_contact_to_db(name, phone)
def get_contact_number(name): return toolbox.get_contact(name)
def get_system_status(): return toolbox.system_status()
# Change this from "return 'Email tool ready'" to this:
def send_email(to, subject, body): return toolbox.send_email(to, subject, body)

tool_list = [
    get_current_time, open_application, google_search, visit_website, create_file, 
    read_file, open_file, calculate, send_email, remember, recall, add_contact, 
    send_whatsapp, get_contact_number, speak, play_music, system_control,
    get_system_status
]

