import os, json, logging, re, datetime, ast
import google.generativeai as genai
from groq import Groq
from mistralai import Mistral
from dotenv import load_dotenv
import skills

logging.basicConfig(filename='jarvis.log', level=logging.INFO, format='%(asctime)s - %(message)s')
load_dotenv()

USER_NAME, BOT_NAME = "Yuvraj", "Jarvis"

# --- CONSTANTS ---
SYSTEM_PROMPT = """You are Jarvis, a helpful and intelligent AI assistant.
1. Output strictly JSON for actions.
2. For communication tools (send_email, send_whatsapp), be polite and professional. Expand the user's short command into a full, coherent message. 
   Example: If user says 'say hello', write 'Hello, I hope you are doing well.'
   (Unless the user specifies 'exact words' or 'verbatim').
3. For system commands, include the full detail (e.g., 'volume 50', 'brightness 100').

TOOLS:
- {"tool": "system_control", "args": {"command": "FULL COMMAND STRING. Include numbers for brightness/volume (e.g. 'volume 50', 'brightness 100'). For media use: 'play', 'resume', 'pause', 'next', 'previous', 'mute', 'shutdown'"}}
- {"tool": "play_music", "args": {"song": "..."}}
- {"tool": "google_search", "args": {"query": "..."}}
- {"tool": "send_whatsapp", "args": {"to": "name/number", "message": "..."}}
- {"tool": "send_email", "args": {"to": "...", "subject": "...", "body": "..."}}
- {"tool": "remember", "args": {"key": "...", "value": "..."}}
- {"tool": "recall", "args": {"key": "..."}}
- {"tool": "calculate", "args": {"expression": "..."}}
- {"tool": "response", "args": {"message": "..."}}
"""

class ModelManager:
    def __init__(self):
        self.history = []
        self.memory = skills.get_all_memories()
        
        self.google_key = os.getenv("GOOGLE_API_KEY")
        if self.google_key:
            genai.configure(api_key=self.google_key)
            self.gemini = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        self.groq = Groq(api_key=os.getenv("GROQ_API_KEY")) if os.getenv("GROQ_API_KEY") else None
        self.mistral = Mistral(api_key=os.getenv("MISTRAL_API_KEY")) if os.getenv("MISTRAL_API_KEY") else None

    def get_arg(self, args, keys):
        for k in keys:
            if args.get(k): return args.get(k)
        return ""

    def fast_track(self, q):
        q = q.lower().strip()
        if "time" in q and "what" in q: return f"It is {skills.get_current_time()}."
        if "who are you" in q: return f"I am {BOT_NAME}."
        if "open" in q or "focus" in q:
            app = q.replace("open", "").replace("focus on", "").replace("focus", "").strip()
            return skills.open_application(app)
        return None

    def analyze_screen(self, query):
        try:
            return self.gemini.generate_content([query, skills.capture_screen_for_ai()]).text
        except: return "Vision unavailable."

    def assign_task(self, q):
        q = q.lower()
        if any(x in q for x in ["see", "screen", "image"]): return "vision"
        if any(x in q for x in ["volume", "mute", "brightness", "pause", "play", "stop", "next", "status", "health"]): 
            return "system"
        return "general"

    def execute_tool_call(self, tool, args):
        try:
            a = args if args else {}
            if tool == "response": return str(a.get("message") or a)

            if tool == "system_control": return skills.system_control(self.get_arg(a, ["command", "action"]))
            if tool == "play_music": return skills.play_music(self.get_arg(a, ["song", "topic", "query"]))
            if tool == "google_search": return skills.google_search(a.get("query"))
            if tool == "visit_website": return skills.visit_website(a.get("url"))
            if tool == "open_application": return skills.open_application(a.get("app_name"))
            
            if tool == "send_whatsapp": 
                return skills.send_whatsapp(self.get_arg(a, ["to", "recipient"]), self.get_arg(a, ["message", "text"]))
            
            if tool == "send_email":
                return skills.send_email(
                    self.get_arg(a, ["to", "recipient"]), 
                    self.get_arg(a, ["subject"]), 
                    self.get_arg(a, ["body"])
                )
            
            if tool == "add_contact": return skills.add_contact(a.get("name"), a.get("phone"))
            if tool == "get_contact": return skills.get_contact_number(a.get("name"))
            if tool == "remember": return skills.remember(a.get("key"), a.get("value"))
            if tool == "recall": return skills.recall(a.get("key"))
            if tool == "calculate": return skills.calculate(a.get("expression"))
            if tool == "read_file": return skills.read_file(a.get("filename"))
            
            return f"Tool '{tool}' not recognized."
        except Exception as e: return f"Error executing {tool}: {e}"

    def parse_and_execute(self, text):
        try:
            clean = re.sub(r'```json\s*|```', '', text).strip()
            start, end = clean.find('{'), clean.rfind('}')
            if start != -1 and end != -1:
                json_str = clean[start:end+1]
                try: 
                    data = json.loads(json_str)
                except: 
                    try: data = ast.literal_eval(json_str)
                    except: return text
                if isinstance(data, dict):
                    return self.execute_tool_call(data.get("tool"), data.get("args"))
                elif isinstance(data, list):
                    return "\n".join([str(self.execute_tool_call(i.get("tool"), i.get("args"))) for i in data if isinstance(i, dict)])
            return text 
        except Exception as e: return text

    def process_request(self, query):
        if fast := self.fast_track(query): return fast
        task_type = self.assign_task(query)
        if task_type == "vision": return self.analyze_screen(query)
        
        model = self.groq if self.groq else (self.mistral if self.mistral else self.gemini)
        agent_name = "groq" if self.groq else "backup"
        
        try:
            context = f"User: {USER_NAME}\nPrompt: {SYSTEM_PROMPT}\nQuery: {query}"
            if agent_name == "groq":
                msgs = [{"role": "user", "content": context}]
                response = model.chat.completions.create(model="llama-3.3-70b-versatile", messages=msgs).choices[0].message.content
            else:
                response = self.gemini.generate_content(context).text
            return self.parse_and_execute(response)
        except Exception as e: return f"Connection Error: {e}"