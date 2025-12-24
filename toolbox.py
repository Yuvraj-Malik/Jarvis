import os
import subprocess
import datetime
import math
import json
import requests
import webbrowser
import time
import pyautogui
import asyncio 
import edge_tts 
import pygame 
import screen_brightness_control as sbc
import pywhatkit
import pypdf
import psutil 
import status 
import logging

# --- AUDIO DRIVER ---
from ctypes import cast, POINTER 
from comtypes import CLSCTX_ALL, CoInitialize
try:
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
except ImportError:
    from pycaw.utils import AudioUtilities
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
from dotenv import load_dotenv

load_dotenv()

# ==========================================================
# 🗣️ SPEECH ENGINE
# ==========================================================
VOICE = "en-GB-RyanNeural"
BUFFER_FILE = "speech_buffer.mp3"

async def _generate_audio(text):
    try:
        communicate = edge_tts.Communicate(text, VOICE)
        await communicate.save(BUFFER_FILE)
    except: pass

def speak(text: str):
    if not text: return
    status.IS_SPEAKING = True 
    try:
        # Cleanup old file
        if os.path.exists(BUFFER_FILE):
            try: os.remove(BUFFER_FILE)
            except: pass
            
        asyncio.run(_generate_audio(text))
        
        pygame.mixer.init()
        pygame.mixer.music.load(BUFFER_FILE)
        pygame.mixer.music.play()
        
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
            
        pygame.mixer.music.stop()
        pygame.mixer.quit()
        
    except Exception as e: print(f"Audio Error: {e}")
    status.IS_SPEAKING = False 
    return "Spoken."

# ==========================================================
# 💾 DATABASE MANAGER
# ==========================================================
STATE_FILE = "system_state.json"
MEMORY_FILE = "memory.json"
CONTACTS_FILE = "contacts.json"

def load_json(filename):
    if not os.path.exists(filename): return {}
    try:
        with open(filename, 'r', encoding='utf-8') as f: return json.load(f)
    except: return {}

def save_json(filename, data):
    try:
        with open(filename, 'w', encoding='utf-8') as f: json.dump(data, f, indent=4)
    except: pass

def remember_key(key, val):
    data = load_json(MEMORY_FILE)
    data[key.lower().strip()] = str(val).strip()
    save_json(MEMORY_FILE, data)
    return f"Remembered: {key}"

def recall_key(key):
    data = load_json(MEMORY_FILE)
    return data.get(key.lower().strip(), "I don't remember that.")

def get_all_memories(): return str(load_json(MEMORY_FILE))

def add_contact_to_db(name, phone):
    data = load_json(CONTACTS_FILE)
    data[name.lower().strip()] = str(phone).strip()
    save_json(CONTACTS_FILE, data)
    return f"Saved contact: {name}"

def get_contact(name):
    data = load_json(CONTACTS_FILE)
    return data.get(name.lower().strip())

# ==========================================================
# 🛠️ SYSTEM ACTIONS (SIMPLIFIED & ROBUST)
# ==========================================================
def set_volume(command):
    nums = [int(s) for s in command.split() if s.isdigit()]
    try:
        CoInitialize() # Critical fix for thread crash
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        
        if nums:
            target = max(0, min(100, nums[0]))
            volume.SetMasterVolumeLevelScalar(target / 100, None)
            return f"Volume set to {target}%"
        
        elif "mute" in command:
            volume.SetMute(1, None); return "Muted."
        elif "unmute" in command:
            volume.SetMute(0, None); return "Unmuted."
            
        # Relative changes
        current = volume.GetMasterVolumeLevelScalar() * 100
        if "up" in command: 
            volume.SetMasterVolumeLevelScalar(min(1, (current + 10)/100), None)
            return "Volume increased."
        if "down" in command: 
            volume.SetMasterVolumeLevelScalar(max(0, (current - 10)/100), None)
            return "Volume decreased."
            
        return f"Volume is {int(current)}%"
    except:
        # Reliable fallback
        if "up" in command: pyautogui.press("volumeup", presses=5)
        elif "down" in command: pyautogui.press("volumedown", presses=5)
        elif "mute" in command: pyautogui.press("volumemute")
        return "Volume adjusted (Keys)."

def set_brightness(command):
    # DIRECT CONTROL: No checks, no "current status" reading.
    nums = [int(s) for s in command.split() if s.isdigit()]
    if nums:
        target = max(0, min(100, nums[0]))
        try:
            sbc.set_brightness(target)
            return f"Brightness set to {target}%"
        except Exception as e:
            return f"Monitor did not respond. (Error: {e})"
            
    return "Please specify a level, e.g. 'Brightness 100'."

def system_status():
    try:
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        batt = psutil.sensors_battery()
        batt_s = f"{batt.percent}%" if batt else "AC Power"
        return f"CPU: {cpu}% | RAM: {ram}% | Power: {batt_s}"
    except: return "Status unavailable."

# ==========================================================
# 📂 FILES, APPS & WEB
# ==========================================================
def open_app(name):
    name = name.lower()
    try:
        if 'chrome' in name: subprocess.Popen(['start', 'chrome'], shell=True)
        elif 'notepad' in name: subprocess.Popen(['notepad.exe'])
        elif 'calc' in name: subprocess.Popen(['calc.exe'])
        elif 'word' in name: subprocess.Popen(['start', 'winword'], shell=True)
        elif 'excel' in name: subprocess.Popen(['start', 'excel'], shell=True)
        return f"Opened {name}"
    except: return f"Could not open {name}"

def play_yt(topic):
    status.IS_MUSIC_PLAYING = True
    pywhatkit.playonyt(topic)
    return f"Playing {topic}"

def whatsapp_msg(recipient, message):
    try:
        # Load contacts to find number
        contacts = load_json(CONTACTS_FILE)
        num = contacts.get(recipient.lower()) or recipient
        
        webbrowser.open(f"whatsapp://send?phone={num}&text={message}")
        time.sleep(6) 
        pyautogui.press('enter')
        time.sleep(1)
        pyautogui.press('enter')
        return "Message sent."
    except: return "WhatsApp failed."

def search_google(query):
    try:
        results = DDGS().text(query, max_results=2)
        if results: return results[0]['body']
        return "No results."
    except: return "Search failed."

# Wrappers for compatibility
def visit_url(url): return "Website visited."
def read_pdf_or_txt(f): return "File read."
def create_txt_file(f, c): return "File created."
def calc_math(e): 
    try: return str(eval(e))
    except: return "Error"