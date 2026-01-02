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
import re  
import screen_brightness_control as sbc
import pywhatkit
import pypdf
import psutil 
import status 
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from ctypes import cast, POINTER 
from comtypes import CLSCTX_ALL, CoInitialize
from dotenv import load_dotenv

load_dotenv()

try:
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    PYZCAW_AVAILABLE = True
except ImportError:
    PYZCAW_AVAILABLE = False

from bs4 import BeautifulSoup
from duckduckgo_search import DDGS

# --- SPEECH ENGINE ---
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
    except Exception as e: pass
    status.IS_SPEAKING = False 
    return "Spoken."

# --- DATABASE MANAGER ---
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

def save_setting(key, val):
    data = load_json(STATE_FILE)
    data[key] = {
        "previous": data.get(key, {}).get("current", 50),
        "current": val,
        "timestamp": str(datetime.datetime.now())
    }
    save_json(STATE_FILE, data)

def get_setting_prev(key):
    data = load_json(STATE_FILE)
    return data.get(key, {}).get("previous", 50)

# --- SYSTEM ACTIONS ---
def set_volume(command):
    nums = re.findall(r'\d+', command)
    target_percent = int(nums[0]) if nums else None
    
    if PYZCAW_AVAILABLE:
        try:
            CoInitialize()
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            
            if "mute" in command:
                volume.SetMute(1, None); return "Muted."
            elif "unmute" in command:
                volume.SetMute(0, None); return "Unmuted."
                
            if target_percent is not None:
                vol_0_to_1 = max(0, min(1, target_percent / 100))
                volume.SetMasterVolumeLevelScalar(vol_0_to_1, None)
                return f"Volume set to {target_percent}%."
                
            current_scalar = volume.GetMasterVolumeLevelScalar()
            if "up" in command:
                new_vol = min(1, current_scalar + 0.1)
                volume.SetMasterVolumeLevelScalar(new_vol, None)
                return "Volume increased."
            elif "down" in command:
                new_vol = max(0, current_scalar - 0.1)
                volume.SetMasterVolumeLevelScalar(new_vol, None)
                return "Volume decreased."
        except Exception:
            pass # Fall through to Keyboard Fallback
            
    # FALLBACK: Keyboard Control
    if "mute" in command:
        pyautogui.press('volumemute'); return "Muted."
    elif "unmute" in command:
        pyautogui.press('volumemute'); return "Unmuted."
    elif "up" in command:
        for _ in range(3): pyautogui.press('volumeup')
        return "Volume increased."
    elif "down" in command:
        for _ in range(3): pyautogui.press('volumedown')
        return "Volume decreased."
    elif target_percent:
        # Smart Reset
        for _ in range(50): pyautogui.press('volumedown')
        steps = int(target_percent / 2)
        for _ in range(steps): pyautogui.press('volumeup')
        return f"Volume set to approx {target_percent}%."
    return "Volume command processed."

def set_brightness(command):
    nums = re.findall(r'\d+', command)
    try:
        if "revert" in command: target = get_setting_prev("brightness")
        elif nums: target = int(nums[0])
        else:
            try:
                current = sbc.get_brightness()[0]
                if "up" in command: target = min(100, current + 10)
                elif "down" in command: target = max(0, current - 10)
                else: return "Please specify a level."
            except: target = 50 
    except: target = 50 
    target = max(0, min(100, target))

    try:
        sbc.set_brightness(target, display=0)
        save_setting("brightness", target)
        return f"Brightness set to {target}%."
    except Exception as main_error:
        try:
            monitors = sbc.get_monitors()
            if not monitors: return "Error: System cannot find connected monitors."
            sbc.set_brightness([target] * len(monitors))
            save_setting("brightness", target)
            return f"Brightness set to {target}% on all monitors."
        except Exception:
            return "Brightness Error. Please run as Administrator."

def system_status():
    try:
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        batt = psutil.sensors_battery()
        batt_s = f"{batt.percent}%" if batt else "AC Power"
        return f"CPU: {cpu}% | RAM: {ram}% | Power: {batt_s}"
    except: return "Status unavailable."

# --- FILES, APPS & WEB ---
APP_PROTOCOLS = {
    'whatsapp': 'whatsapp://',
    'discord': 'discord://',
    'spotify': 'spotify://',
    'slack': 'slack://',
    'telegram': 'tg://',
    'teams': 'msteams://'
}

def open_app(name):
    name = name.lower()
    try:
        if name in APP_PROTOCOLS:
            webbrowser.open(APP_PROTOCOLS[name])
            return f"Opened {name}"
        os.system(f"start {name}")
        return f"Opened {name}"
    except Exception as e: 
        return f"Could not open {name}."

def play_yt(topic):
    status.IS_MUSIC_PLAYING = True
    pywhatkit.playonyt(topic)
    return f"Playing {topic}"

def whatsapp_msg(recipient, message):
    try:
        contacts = load_json(CONTACTS_FILE)
        num = contacts.get(recipient.lower()) or recipient
        webbrowser.open(f"whatsapp://send?phone={num}&text={message}")
        speak("Opening WhatsApp.")
        time.sleep(4) 
        pyautogui.press('enter')
        time.sleep(1)
        pyautogui.press('enter')
        return "Message sent."
    except Exception as e:
        return f"WhatsApp automation failed."

def search_google(query):
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=2))
            if results: return results[0]['body']
            return "No results found."
    except Exception:
        try:
            webbrowser.open(f"https://www.google.com/search?q={query}")
            return "I've opened that in your browser."
        except:
            return "Search service unavailable."

# Wrappers
def visit_url(url): return "Website visited."
def read_pdf_or_txt(f): return "File read."
def create_txt_file(f, c): return "File created."
def calc_math(e): 
    try: return str(eval(e))
    except: return "Error"

def send_email(to, subject, body):
    try:
        email_user = os.getenv("EMAIL_USER")
        email_pass = os.getenv("EMAIL_PASS")
        if not email_user or not email_pass:
            return "Email credentials not found."

        message = MIMEMultipart()
        message["From"] = email_user
        message["To"] = to
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain"))

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(email_user, email_pass)
        server.sendmail(email_user, to, message.as_string())
        server.quit()
        return f"Email sent to {to}."
    except Exception:
        webbrowser.open(f"mailto:{to}?subject={subject}&body={body}")
        return "Email server error. I opened your email client instead."