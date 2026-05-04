import os, json, logging, re, datetime, ast
from google import genai
from groq import Groq
try:
    from mistralai import Mistral
except ImportError:
    Mistral = None
from dotenv import load_dotenv
from features import skills

logging.basicConfig(filename='jarvis.log', level=logging.INFO, format='%(asctime)s - %(message)s')
load_dotenv()

USER_NAME, BOT_NAME = "Yuvraj", "Jarvis"

# --- CONSTANTS ---
SYSTEM_PROMPT = """You are Jarvis, a highly advanced agentic AI assistant.
1. Output strictly JSON for actions. 
2. You can perform complex, multi-step tasks by calling tools sequentially.
3. For GUI automation, use 'gui_action'. If you need to click something, ask for a screenshot first or use vision to estimate coordinates (1920x1080 scale).
4. For coding, you can open VS Code, write files, run terminal commands to compile/run, and fix errors based on output.
5. If a task is not finished, continue calling tools. Once finished, use the 'response' tool with the final result.

TOOLS:
- {"tool": "gui_action", "args": {"action": "click|type|hotkey|press", "x": 100, "y": 200, "text": "...", "keys": ["ctrl", "s"], "key": "enter"}}
- {"tool": "run_command", "args": {"command": "shell command"}}
- {"tool": "find_setting", "args": {"query": "setting name"}}
- {"tool": "system_control", "args": {"command": "volume 50|brightness 100|play|pause|next|previous|mute|shutdown"}}
- {"tool": "open_application", "args": {"app_name": "..."}}
- {"tool": "create_file", "args": {"filename": "...", "content": "..."}}
- {"tool": "read_file", "args": {"filename": "..."}}
- {"tool": "google_search", "args": {"query": "..."}}
- {"tool": "send_whatsapp", "args": {"to": "name/number", "message": "..."}}
- {"tool": "send_email", "args": {"to": "...", "subject": "...", "body": "..."}}
- {"tool": "calculate", "args": {"expression": "..."}}
- {"tool": "response", "args": {"message": "..."}}
- {"tool": "see_screen", "args": {}} 
"""

class ModelManager:
    def __init__(self):
        self.history = []
        self.memory = skills.get_all_memories()
        
        self.google_key = os.getenv("GOOGLE_API_KEY")
        if self.google_key:
            self.gemini_client = genai.Client(api_key=self.google_key)
        
        self.groq = Groq(api_key=os.getenv("GROQ_API_KEY")) if os.getenv("GROQ_API_KEY") else None
        self.mistral = Mistral(api_key=os.getenv("MISTRAL_API_KEY")) if (Mistral and os.getenv("MISTRAL_API_KEY")) else None

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
            if tool == "create_file": return skills.create_file(a.get("filename"), a.get("content"))
            if tool == "gui_action": return skills.gui_action(a.get("action"), **a)
            if tool == "run_command": return skills.run_command(a.get("command"))
            if tool == "find_setting": return skills.find_setting(a.get("query"))
            if tool == "see_screen": return "Screen captured and analyzed." # Handled in agent loop
            
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
        
        # --- AGENT LOOP (JARVIS 2.0) ---
        max_steps = 10
        current_step = 0
        conversation_log = f"User: {USER_NAME}\nQuery: {query}\n"
        
        while current_step < max_steps:
            current_step += 1
            
            # Decide if we need vision
            task_type = self.assign_task(query)
            context = f"{SYSTEM_PROMPT}\n\nCONVERSATION SO FAR:\n{conversation_log}\n\nWhat is your next action? Output JSON."
            
            try:
                # Use Gemini for all agentic reasoning due to vision & complex instruction following
                if "see" in query.lower() or "screen" in query.lower() or current_step > 1:
                    screenshot = skills.capture_screen_for_ai()
                    try:
                        response = self.gemini_client.models.generate_content(
                            model='gemini-2.0-flash', 
                            contents=[context, screenshot]
                        )
                    except Exception as e:
                        if "429" in str(e) or "404" in str(e):
                            # Fallback to the latest stable flash model
                            response = self.gemini_client.models.generate_content(
                                model='gemini-flash-latest', 
                                contents=[context, screenshot]
                            )
                        else: raise e
                    response_text = response.text
                else:
                    try:
                        response = self.gemini_client.models.generate_content(
                            model='gemini-2.0-flash', 
                            contents=context
                        )
                    except Exception as e:
                        if "429" in str(e) or "404" in str(e):
                            response = self.gemini_client.models.generate_content(
                                model='gemini-flash-latest', 
                                contents=context
                            )
                        else: raise e
                    response_text = response.text
                
                # Parse actions
                clean = re.sub(r'```json\s*|```', '', response_text).strip()
                start, end = clean.find('{'), clean.rfind('}')
                
                if start == -1: # Just a text response
                    return response_text
                
                json_str = clean[start:end+1]
                try: data = json.loads(json_str)
                except: data = ast.literal_eval(json_str)
                
                if isinstance(data, dict):
                    tool = data.get("tool")
                    args = data.get("args", {})
                    
                    if tool == "response":
                        return args.get("message", response_text)
                    
                    print(f"Executing: {tool}({args})")
                    result = self.execute_tool_call(tool, args)
                    conversation_log += f"\nAction: {tool}({args})\nResult: {result}\n"
                    
                    if "Error" in str(result) and current_step > 5:
                        return f"I encountered an error I couldn't fix: {result}"
                else:
                    return response_text # Fallback
                    
            except Exception as e:
                return f"Agent Error: {e}"
                
        return "Task took too many steps. Please be more specific."