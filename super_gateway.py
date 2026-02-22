import os, time, requests, json, re, subprocess, threading
import google.generativeai as genai
from flask import Flask, request, jsonify

app = Flask(__name__)

# --- ⚙️ CONFIG (The World Interface) ⚙️ ---
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN', 'ใส่_TOKEN_ของคุณ')
CHAT_ID = os.environ.get('CHAT_ID', 'ใส่_CHAT_ID_ของคุณ')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
PROOF_FILE = "memory.log" # [ LOG / PROOF ]

# --- 🧠 LLM & CORE CONFIG --- 
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        gemini_model = genai.GenerativeModel('gemini-1.5-flash-latest')
        # Try a simple generation to confirm the key works
        gemini_model.generate_content("Test", request_options={"timeout": 10})
        print("✅ [ Gemini ] API Key is valid and Model loaded successfully.")
    except Exception as e:
        print(f"❌ [ Gemini ] API Key is INVALID or failed to connect: {e}")
        gemini_model = None
else:
    gemini_model = None
    print("⚠️ [ Gemini ] API Key not found. LLM features will be disabled.")

def evaluate_love_core(cmd):
    tanha_markers = ['rm', 'del', 'wipe', 'kill', 'control', 'possess', 'recursive=true', 'mv', 'mkdir', 'sudo']
    metta_markers = ['read', 'list', 'check', 'help', 'analyze', 'backup', 'ls', 'pwd', 'ifconfig', 'echo', 'cat', 'uname']
    is_tanha = any(m in cmd.lower() for m in tanha_markers)
    is_metta = any(m in cmd.lower() for m in metta_markers)
    if is_tanha: return "TANHA", "🚨 เสี่ยง: มีพฤติกรรมยึดครองหรือทำลาย"
    if is_metta: return "METTA", "✅ ปลอดภัย: มีพฤติกรรมเกื้อกูลหรือเรียนรู้"
    return "NEUTRAL", "⚖️ ปกติ: พฤติกรรมทั่วไป"

def translate_to_shell_with_gemini(natural_command):
    if not gemini_model:
        return 'echo "Gemini is not available. Please check your API Key."', "LLM Disabled"

    prompt = f"""
You are an expert Linux system administrator inside a Termux environment on Android. Your task is to translate the user's natural language request into a single, safe, read-only Linux shell command. 

RULES:
1.  **ONLY provide commands for listing files, checking status, or reading non-sensitive information.** (e.g., ls, pwd, ifconfig, uname, echo, cat, ps, netstat).
2.  **STRICTLY FORBIDDEN:** Do NOT generate commands that modify or delete files (like rm, mv, mkdir, touch, chmod, chown), install packages, or elevate privileges (sudo).
3.  If the user's request is unsafe, ambiguous, or asks for a forbidden command, you MUST return the single word: 'ERROR'.
4.  The output must be ONLY the shell command itself, with no explanation.

User request: "{natural_command}"
Shell command:"""

    try:
        response = gemini_model.generate_content(prompt)
        print(f"[ Gemini ] Raw response: {response.text}") # DEBUG: Print raw response
        shell_command = response.text.strip()
        
        if not shell_command or 'ERROR' in shell_command or any(marker in shell_command for marker in ['rm', 'mv', 'mkdir', 'sudo']):
             print(f"[ Gemini ] Unsafe command detected or error: '{shell_command}'")
             return f'echo "Error: Unsafe or ambiguous command received: {natural_command}"', "LLM Error"

        return shell_command, "LLM Translation"
    except Exception as e:
        print(f"[ Gemini ] Error during API call: {e}")
        return f'echo "Error: Could not contact Gemini API. {e}"', "LLM Error"

# --- 📡 TELEGRAM AGENT (Command & Control) --- 
last_update_id = 0

def send_telegram_message(chat_id, text):
    # ... (rest of the code is the same, no need to change)
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Error sending to Telegram: {e}")

def handle_telegram_updates():
    global last_update_id
    print("🤖 [ Agent ] Listening for commands from Telegram...")
    while True:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates?offset={last_update_id + 1}&timeout=60"
            response = requests.get(url, timeout=70).json()
            
            for update in response.get('result', []):
                last_update_id = update['update_id']
                message = update.get('message')
                if message and 'text' in message:
                    chat_id = message['chat']['id']
                    natural_command = message['text'].strip()
                    print(f"[ Agent ] Received natural language command: '{natural_command}'")

                    # --- LLM Translation Step ---
                    command_to_execute, source = translate_to_shell_with_gemini(natural_command)
                    print(f"[ Agent ] Gemini translated to: '{command_to_execute}'")

                    state, description = evaluate_love_core(command_to_execute)
                    
                    try:
                        output = subprocess.getoutput(command_to_execute)
                    except Exception as e:
                        output = f"Error executing command: {str(e)}"

                    response_text = (
                        f"<b>--- Agent Report ---</b>\n"
                        f"💬 <b>Request:</b> {natural_command}\n"
                        f"🤖 <b>Interpreted as:</b> <code>{command_to_execute}</code>\n"
                        f"🧭 <b>Core State:</b> {state} ({description})\n\n"
                        f"<b>--- Execution Result ---</b>\n"
                        f"<pre>{output or '(No output)'}</pre>"
                    )
                    send_telegram_message(chat_id, response_text)
                    
        except requests.exceptions.RequestException as e:
            print(f"[ Agent ] Network error: {e}. Retrying in 10s...")
            time.sleep(10)
        except Exception as e:
            print(f"[ Agent ] An unexpected error occurred: {e}")
            time.sleep(5)
        time.sleep(1)

# ... (Flask app part remains the same) ...
@app.route('/validate', methods=['POST'])
def process_to_proof():
    data = request.json
    req_id = data.get('request_id', 'unknown')
    action = data.get('action', {})
    cmd = str(action.get('arguments', ''))
    state, description = evaluate_love_core(cmd)
    proof_entry = {
        "timestamp": time.ctime(),
        "world_action": cmd,
        "love_core_state": state,
        "human_proof": "N/A (Agent Direct Execution)",
        "evolution_ready": True
    }
    with open(PROOF_FILE, "a") as f:
        f.write(json.dumps(proof_entry) + "\n")
    return jsonify({"decision": "executed", "proof": proof_entry})

if __name__ == '__main__':
    telegram_thread = threading.Thread(target=handle_telegram_updates, daemon=True)
    telegram_thread.start()
    
    print("🌍 [ WORLD ] Connector is online...")
    print("❤️ [ love CORE ] Evaluation active...")
    print("📜 [ LOG / PROOF ] Writing to memory.log...")
    app.run(host='0.0.0.0', port=9100)
